#!/usr/bin/env python
# coding=utf-8

import grpc
import datetime
import sys
import logging
import os
import re
import time
import json
import signal

import sdk_service_pb2
import sdk_service_pb2_grpc
import config_service_pb2

from logging.handlers import RotatingFileHandler

############################################################
## Agent will start with this name
############################################################
agent_name='snmp_set_agent'

############################################################
## Open a GRPC channel to connect to sdk_mgr on the dut
## sdk_mgr will be listening on 50053
############################################################
#channel = grpc.insecure_channel('unix:///opt/srlinux/var/run/sr_sdk_service_manager:50053')
channel = grpc.insecure_channel('127.0.0.1:50053')
metadata = [('agent_name', agent_name)]
stub = sdk_service_pb2_grpc.SdkMgrServiceStub(channel)

# Requires Unix socket to be enabled in config
# gnmi = gNMIclient(target=('unix:///opt/srlinux/var/run/sr_gnmi_server',57400),
#                  username="admin",password="admin",insecure=True)

############################################################
## Subscribe to required event
## This proc handles subscription of: Interface, LLDP,
##                      Route, Network Instance, Config
############################################################
def Subscribe(stream_id, option):
    op = sdk_service_pb2.NotificationRegisterRequest.AddSubscription
    if option == 'cfg':
        entry = config_service_pb2.ConfigSubscriptionRequest()
        request = sdk_service_pb2.NotificationRegisterRequest(op=op, stream_id=stream_id, config=entry)

    subscription_response = stub.NotificationRegister(request=request, metadata=metadata)
    print('Status of subscription response for {}:: {}'.format(option, subscription_response.status))

############################################################
## Subscribe to all the events that Agent needs
############################################################
def Subscribe_Notifications(stream_id):
    '''
    Agent will receive notifications to what is subscribed here.
    '''
    if not stream_id:
        logging.info("Stream ID not sent.")
        return False

    # Subscribe to config changes, first
    Subscribe(stream_id, 'cfg')

def EnableSNMPSetInterface( network_instance ):
    """
    Modifies the SNMP daemon configuration to enable SNMP set
    """
    logging.info( f"EnableSNMPSetInterface network-instance={network_instance}" )

    conf_file = f'/etc/snmp/snmpd-{network_instance}.conf' # Changed in 23.10

    # Wait till it exists
    while not os.path.exists( conf_file ):
       logging.info( f"Waiting for {conf_file} to be created...")
       time.sleep(1)

    try:
      from pathlib import Path
      conf = Path(conf_file).read_text()
      logging.info( f"Old conf: \n{conf}" )
      new_conf = re.sub( 'access converted "" v2c noauth exact supported-views none none',
       '# Custom config by snmp-set-agent to enable interface up/down\n' +
       'access converted "" v2c noauth exact supported-views rwview none\n' +
       # 'view supported-views included .1.3.6.1.2.1.15\n' +
       # 'perl do "/opt/demo-agents/snmp-set/scripts/snmp_get_tree.pl";\n'
       # 'pass_persist .1.3.6.1.2.1.15 /opt/demo-agents/snmp-set/bgp4_pp.py\n' +
       # 'view rwview included interfaces.ifTable.ifEntry.ifAdminStatus\n' +
       'view rwview included .1.3.6.1.2.1.2.2.1.7\n' +
       'perl do "/opt/demo-agents/snmp-set/scripts/snmp_write_handler.pl";\n'
       # 'view supported-views included .1.3.6.1.3.53.9.0\n' +
       # 'extend .1.3.6.1.3.53.9.0 /bin/echo hello\n'
       # 'view supported-views included .1.3.6.1.4.1.8072.9999.9999\n' +
       # 'perl do "/opt/demo-agents/snmp-set/scripts/hello_snmp_world.pl";\n'
       , conf )
      logging.info( f"New conf: \n{new_conf}" )

      with open( conf_file, "w+" ) as f:
        f.write( new_conf )

      # Try different SNMP binary
      # cur = './snmp_server -DALL -M -c {0} {1}'
      # new = '/usr/sbin/snmpd -DALL -c {0} {1}'
      # cmd = f"sudo /usr/bin/sed -i.orig 's|{cur}|{new}|g' /opt/srlinux/appmgr/sr_linux_mgr_config.yml"
      # logging.info( cmd )
      # os.system( cmd )

      # Check if snmpd is already running, if so restart it
      with os.popen('/usr/bin/ps -AlF') as ps:
        psline = f"sr_snmp_server -M -c {network_instance}"
        if psline in ps.read():
          logging.info( f"Restarting SNMP daemon...using {conf_file}" )
          os.system(f"/usr/bin/ps -AlF | grep '{psline}' | grep -v grep | awk '{{print $4}}' | xargs kill -9")
        else:
          logging.info( f"SNMP daemon not yet running...assuming it will use {conf_file}" )

      # After restart, change search-command too? Now done in 1 step
    except Exception as ex:
      logging.error( ex )

##################################################################
## Proc to process the config Notifications received by snmp-set agent
## At present processing config from js_path = .fib-agent
##################################################################
def Handle_Notification(obj):
    if obj.HasField('config'):
        logging.info(f"GOT CONFIG :: {obj.config.key.js_path}")
        if obj.config.key.js_path == ".system.snmp.network_instance":
            ni_name = obj.config.key.keys[0]
            logging.info(f"Got config for agent, now will handle it :: \n{obj.config}\
                            Operation :: {obj.config.op}\nData :: {obj.config.data.json}")
            if obj.config.op == 2:
                logging.info("Delete snmp-agent cli scenario")
                # if file_name != None:
                #    Update_Result(file_name, action='delete')
                response=stub.AgentUnRegister(request=sdk_service_pb2.AgentRegistrationRequest(), metadata=metadata)
                logging.info('Handle_Config: Unregister response:: {}'.format(response))
            else:
                data = json.loads(obj.config.data.json)
                if 'network_instance' in data:
                  ni = data['network_instance']
                  if 'enable_set_interface' in ni:
                    enable = ni['enable_set_interface']['value']
                    if enable:
                        logging.info( f"Enabling SNMP SET for net_inst={ni_name}" )
                        return ni_name
                logging.info( f"NOT enabling SNMP SET; data={data}" )

    else:
        logging.info(f"Unexpected notification : {obj}")

    return None

##################################################################################################
## This is the main proc where all processing for auto_config_agent starts.
## Agent registration, notification registration, Subscrition to notifications.
## Waits on the subscribed Notifications and once any config is received, handles that config
## If there are critical errors, Unregisters the fib_agent gracefully.
##################################################################################################
def Run():
    sub_stub = sdk_service_pb2_grpc.SdkNotificationServiceStub(channel)

    response = stub.AgentRegister(request=sdk_service_pb2.AgentRegistrationRequest(), metadata=metadata)
    logging.info(f"Registration response : {response.status}")

    request=sdk_service_pb2.NotificationRegisterRequest(op=sdk_service_pb2.NotificationRegisterRequest.Create)
    create_subscription_response = stub.NotificationRegister(request=request, metadata=metadata)
    stream_id = create_subscription_response.stream_id
    logging.info(f"Create subscription response received. stream_id : {stream_id}")

    Subscribe_Notifications(stream_id)

    stream_request = sdk_service_pb2.NotificationStreamRequest(stream_id=stream_id)
    stream_response = sub_stub.NotificationStream(stream_request, metadata=metadata)

    count = 1
    try:
        net_instances = {}
        for r in stream_response:
            logging.info(f"Count :: {count}  NOTIFICATION:: \n{r.notification}")
            count += 1
            for obj in r.notification:
                if obj.HasField('config') and obj.config.key.js_path == ".commit.end":
                    logging.info( f"COMMIT: {net_instances}" )
                    if len(net_instances) > 0:
                        logging.info( f"Enabling SNMP set for: {net_instances}" )
                        for ni in net_instances:
                            EnableSNMPSetInterface(ni)
                else:
                    net_instance = Handle_Notification(obj)
                    if net_instance is not None:
                        net_instances[ net_instance ] = True

    except Exception as e:
        # traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        logging.error(f'Exception caught :: {e}')
    finally:
        Exit_Gracefully(0,0)

############################################################
## Gracefully handle SIGTERM signal
## When called, will unregister Agent and gracefully exit
############################################################
def Exit_Gracefully(signum, frame):
    logging.info("Caught signal :: {}\n will unregister snmp_set_agent".format(signum))
    try:
        response=stub.AgentUnRegister(request=sdk_service_pb2.AgentRegistrationRequest(), metadata=metadata)
        logging.error('try: Unregister response:: {}'.format(response))
    except grpc._channel._Rendezvous as err:
        logging.info('GOING TO EXIT NOW: {}'.format(err))
    finally:
        sys.exit()

##################################################################################################
## Main from where the Agent starts
## Log file is written to: /var/log/srlinux/stdout/auto_config_agent.log
## Signals handled for graceful exit: SIGTERM
##################################################################################################
if __name__ == '__main__':
    # hostname = socket.gethostname()
    stdout_dir = '/var/log/srlinux/stdout' # PyTEnv.SRL_STDOUT_DIR
    signal.signal(signal.SIGTERM, Exit_Gracefully)
    if not os.path.exists(stdout_dir):
        os.makedirs(stdout_dir, exist_ok=True)
    log_filename = f'{stdout_dir}/{agent_name}.log'
    logging.basicConfig(
      handlers=[RotatingFileHandler(log_filename, maxBytes=3000000,backupCount=5)],
      format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
      datefmt='%H:%M:%S', level=logging.INFO)

    logging.info("START TIME :: {}".format(datetime.datetime.now()))
    Run()
