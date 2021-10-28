#! /usr/bin/python3 -u
# -*- coding:Utf-8 -*-
# Option -u is needed for communication with snmpd
#
# Modifications to support SRL Copyright (C) 2021 Nokia, all rights reserved
#
# Copyright (C) 2020-2021 NVIDIA Corporation. ALL RIGHTS RESERVED.
# Copyright 2016 Cumulus Networks LLC, all rights reserved
#
# Implementation of the BGP4 MIB (RFC 4273) which includes
# the bgpPeerTable
# bgp4PathAttrTable omitted
#
# To activate this script, snmpd must be running and this
# script should be installed /usr/share/snmp/bgp4_pp.py
# and include the following line in /etc/snmp/snmpd.conf
#
#   pass_persist .1.3.6.1.2.1.15  /usr/share/snmp/bgp4_pp.py
#

import subprocess
import sys
import json
import syslog
import ipaddress, struct, socket, datetime
import snmp_passpersist as snmp

BGP4_MIB = '.1.3.6.1.2.1.15'
pp = snmp.PassPersist(BGP4_MIB)

peerstate = {'idle':1,
             'connect':2,
             'active':3,
             'opensent':4,
             'openconfirm':5,
             'established':6}

adminstate = { 'disable' : 1, 'enable' : 2 }

#bgpPeerEntryRows = ['bgpPeerIdentifier', 'bgpPeerState', 'bgpPeerAdminStatus',
#                    'bgpPeerNegotiatedVersion', 'bgpPeerLocalAddr', 'bgpPeerLocalPort',
#                    'bgpPeerRemoteAddr', 'bgpPeerRemotePort', 'bgpPeerRemoteAs',
#                    'bgpPeerInUpdates', 'bgpPeerOutUpdates', 'bgpPeerInTotalMessages',
#                    'bgpPeerOutTotalMessages',
#                    # 'bgpPeerLastError',
#                    'bgpPeerFsmEstablishedTransitions',
#                    # 'bgpPeerFsmEstablishedTime',
#                    'bgpPeerConnectRetryInterval', 'bgpPeerHoldTime', 'bgpPeerKeepAlive',
#                    'bgpPeerHoldTimeConfigured', 'bgpPeerKeepAliveConfigured',
#                    # 'bgpPeerMinASOriginationInterval',
#                    'bgpPeerMinRouteAdvertisementInterval',
#                    # 'bgpPeerInUpdateElapsedTime'
#                  ]
# bgpPeerEntryList = list(enumerate(bgpPeerEntryRows, start=1))

# construct the peer entry table dictionary
bgpPeerEntry = {'bgpPeerIdentifier' : {'oid' : 1, 'type' : pp.add_ip,
                                       'jsonName' : [], 'default' : '0.0.0.0'},
            'bgpPeerState' : {'oid' : 2, 'type' : pp.add_int, 'map': peerstate,
                              'jsonName' : ['session-state'], 'default' : 1},
            'bgpPeerAdminStatus' : {'oid' : 3, 'type' : pp.add_int, 'map': adminstate,
                                    'jsonName' : ['admin-state'], 'default' : 2},
            'bgpPeerNegotiatedVersion' : {'oid' : 4, 'type' : pp.add_int,
                                          'jsonName' : [],
                                          'default' : 0},
            'bgpPeerLocalAddr' : {'oid' : 5, 'type' : pp.add_ip,
                                  'jsonName' : ['transport','local-address'],
                                  'default' : '0.0.0.0'},
            'bgpPeerLocalPort' : {'oid' : 6, 'type' : pp.add_int,
                                  'jsonName' : ['transport','local-port'],
                                  'default' : 0},
            'bgpPeerRemoteAddr' : {'oid' : 7, 'type' : pp.add_ip,
                                   'jsonName' : ['peer-address'],
                                   'default' : '0.0.0.0'},
            'bgpPeerRemotePort' : {'oid' : 8, 'type' : pp.add_int,
                                   'jsonName' : ['transport','remote-port'],
                                   'default' : 0},
            'bgpPeerRemoteAs' : {'oid' : 9, 'type' : pp.add_int,
                                 'jsonName' : ['peer-as'], 'default' : 0},
            'bgpPeerInUpdates' : {'oid' : 10, 'type' : pp.add_cnt_32bit,
                                  'jsonName' : ["received-messages", "total-updates"],
                                  'default' : 0},
            'bgpPeerOutUpdates' : {'oid' : 11, 'type' : pp.add_cnt_32bit,
                                   'jsonName' : ["sent-messages", "total-updates"],
                                   'default' : 0},
            'bgpPeerInTotalMessages' : {'oid' : 12, 'type' : pp.add_cnt_32bit,
                                        'jsonName' : ["received-messages", "total-messages"],
                                        'default' : 0},
            'bgpPeerOutTotalMessages' : {'oid' : 13, 'type' : pp.add_cnt_32bit,
                                         'jsonName' : ["sent-messages", "total-messages"],
                                         'default' : 0},
            'bgpPeerLastError' : {'oid' : 14, 'type' : pp.add_oct,
                                  'jsonName' : [],
                                  'default' : '00 00'},
            'bgpPeerFsmEstablishedTransitions' : {'oid' : 15,
                                                  'type' : pp.add_cnt_32bit,
                               'jsonName' : ['established-transitions'],
                                               'default' : 0},
            # 'bgpPeerFsmEstablishedTime' : {'oid' : 16, 'type' : pp.add_gau,
            #                                'jsonName' : ['bgpTimerUp'],
            #                                'default' : 0},
            'bgpPeerConnectRetryInterval' : {'oid' : 17, 'type' : pp.add_int,
                                             'jsonName' : ['timers','connect-retry'],
                                             'default' : 0},
            'bgpPeerHoldTime' : {'oid' : 18, 'type' : pp.add_int,
                                 'jsonName' : ['timers','hold-time'],
                                 'default' : 0},
            'bgpPeerKeepAlive' : {'oid' : 19, 'type' : pp.add_int,
                                  'jsonName' : ['timers','keepalive-interval'],
                                  'default' : 0},
            'bgpPeerHoldTimeConfigured' : {'oid' : 20, 'type' : pp.add_int,
                          'jsonName' : ['timers','negotiated-hold-time'],
                          'default' : 0},
            'bgpPeerKeepAliveConfigured' : {'oid' : 21, 'type' : pp.add_int,
                          'jsonName' : ['timers','negotiated-keepalive-interval'],
                          'default' : 0},
            # 'bgpPeerMinASOriginationInterval' : {'oid' : 22, 'type' : pp.add_int,
            #                                      'jsonName' : [], 'default' : 0},
            'bgpPeerMinRouteAdvertisementInterval' : {'oid' : 23, 'type' : pp.add_int,
                          'jsonName' : ['timers','minimum-advertisement-interval'],
                          'default' : 0},
            # 'bgpPeerInUpdateElapsedTime' : {'oid' : 24, 'type' : pp.add_gau,
            #               'jsonName' : ["bgpInUpdateElapsedTimeMsecs"],
            #               'default' : 0}
            }

def traverse(obj, key, default):
    '''
    recursive func where obj is a dictionary and key is a list.
    we need to grab subdictionaries and remove a key
    if we get an obj as a list, then just grab the first one since we
    are only dealing with IPv4 (IPv6 can have multiple nexthops (linklocal).
    '''
    if len(key) <= 1:
        # we only return if we have one key left
        try:
            if type(obj) is list:
                obj = obj[0]
            value = obj[key[0]]
        except (KeyError, IndexError):
            value = default
        return(value)
    return(traverse(obj[key[0]], key[1:], default))

def getValue(peer=None, rowname=None, state=None, default=None,
             jsonList=None):
    '''
    Handle getting the actual value as this can vary depending on
    state and the actual row we are trying to get.
    '''
    if rowname == 'bgpPeerIdentifier':
        # we cannot show the actual peer identifier unless the state is one of these
        if state == 'established' or state == 'openconfirm':
            value = peer['peer-router-id']
        else:
            value = default
    elif rowname == 'bgpPeerNegotiatedVersion':
        # only show the negotiated version if we are established or openconfirm
        # if state == 'established' or state == 'openconfirm':
        #    value = traverse(peer, jsonList, default)
        # else:
        value = default
    elif rowname == 'bgpPeerLastError':
        # the last error must be 4 character hex string with first two being error code
        # and second two being error subcode.  This may or may not exist.
        if "last-notification-error-code" in peer:
          ec = peer[ "last-notification-error-code" ]
          error_codes = {
            'Message Header Error': 1,
            'OPEN Message Error':   2,
            'UPDATE Message Error': 3,
            'Hold Timer Expired':   4,
            'Finite State Machine Error': 5,
            'Cease': 6,
          }
          if ec in error_codes:
             error_code = error_codes[ec]
          else: # XXX strings may not be correct
             syslog.warning( f"Unmapped error code: {ec}" )
             error_code = 0
        else:
          error_code = 0
        if "last-notification-error-subcode" in peer:
          sc = peer[ "last-notification-error-subcode" ]
          sub_codes = {
            "Connection Collision Resolution": 1, # Not synchronized
          }
          if sc in sub_codes:
             sub_code = sub_codes[sc]
          else:
             syslog.warning( f"Unmapped error subcode: {sc}" )
             sub_code = 0 # Unmapped
        else:
          sub_code = 0
        value = f'{error_code:1x}{sub_code:1x}' # Length 2 in RFC
#    elif rowname in ['bgpPeerFsmEstablishedTime', 'bgpPeerHoldTime', 'bgpPeerKeepAlive',
#                     'bgpPeerHoldTimeConfigured', 'bgpPeerKeepAliveConfigured',
#                     'bgpPeerMinRouteAdvertisementInterval', 'bgpPeerInUpdateElapsedTime']:
#        # time was given to us in ms, convert to seconds
#        value = int(traverse(peer, jsonList, default) or 0)/1000

    elif rowname == 'bgpPeerRemoteAs': # for iBGP peer-as is not set
        if 'peer-as' in peer:
            value = peer['peer-as']
        else:
            value = peer['local-as'][0]['as-number']
    elif rowname == 'bgpPeerFsmEstablishedTime':
        # Calculate diff with "last-established" string
        last_established = datetime.datetime.strptime(peer['last-established'],"%Y-%m-%dT%H:%M:%S.%fZ")
        value = int((datetime.datetime.now()-last_established).total_seconds())
    elif jsonList == []:
        value = default
    else:
        # for all else, just get it
        value = traverse(peer, jsonList, default) or 0

    e = bgpPeerEntry[rowname]
    return e['map'].get( value, 0 ) if 'map' in e else value

def call_gnmic(path):
    # gnmic -a localhost -u admin -p admin --skip-verify -e json_ietf get --path /network-instance[name=default]/protocols/bgp/neighbor
    gnmic_cmd = [ '/usr/local/bin/gnmic', '-a', 'localhost', '-u', 'admin',
                  '-p', 'admin', '--skip-verify', '-e', 'json_ietf',
                  'get', '--path', path ]
    try:
        result = json.loads(subprocess.check_output(gnmic_cmd,shell=False),encoding="latin-1")
    except Exception as e:
        result = {}
        syslog.syslog('Error: command %s EXCEPTION=%s' % \
                      (' '.join(gnmic_cmd), e))
    return result

def update():
    """
    Simply grab the output of vtysh commands and stick them in our hashed array
    """

    # version is a vector of supported protocol versions with MSB of first octet
    # as bit 0 and version is i+1 if bit i is set.  We hardcode this to version 4.
    bgpVersion = '10'
    # return a hex string
    pp.add_oct( "1", bgpVersion)
    # grab an array of neighbor entries
    # we have created showpeers and showpaths to simplify sudoers.d/snmp
    # ipBgpNeig = get_json_output(commandList=['sudo', '/usr/share/snmp/showpeers'])
    # ipBgpSummary = get_json_output(commandList=['sudo', '/usr/share/snmp/showsummary'])
    srlBgp = call_gnmic( '/network-instance[name=default]/protocols/bgp' )
    bgp = srlBgp[0]['updates'][0]['values']['srl_nokia-network-instance:network-instance/protocols/srl_nokia-bgp:bgp']
    peerList = bgp['neighbor']
    ipv4PeerList = []
    for peer in peerList:
        try:
            if ipaddress.ip_network(peer['peer-address']).version == 4:
                ipv4PeerList.append(peer)
        except ValueError:
            # ignore IPv6 since this rfc cannot handle it
            continue
    try:
        bgpLocalAs = bgp['autonomous-system']
    except:
        bgpLocalAs = 0
    pp.add_int( "2", bgpLocalAs)
    ##################### bgpPeerEntryTable ####################################
    bgpPeerEntryTable = "3.1"

    # peers should be sorted by ip address because snmp expects it.
    ipv4PeerList = sorted(ipv4PeerList,
                          key=lambda p: struct.unpack("!L", socket.inet_aton(p['peer-address']))[0])
    for rowname, e in bgpPeerEntry.items():
        # show all peers for each row
        for peer in ipv4PeerList:
            newOid = "%s.%s.%s" % (bgpPeerEntryTable, e['oid'], peer['peer-address'])
            jsonList =  e['jsonName']
            default =  e['default']
            state = peer['session-state']
            myval = getValue(peer=peer, rowname=rowname, state=state, default=default,
                             jsonList=jsonList)
            func = e['type']
            func(newOid, myval)

    # local system identifier IP address
    bgpIdentifier = bgp['router-id']
    pp.add_ip('4', bgpIdentifier )
    return

################################################################################
# in debug/shadow/other.log.shadow
syslog.syslog("starting...")

pp.debug = len( sys.argv ) > 1

if pp.debug:
    update()
else:
    pp.start(update, 60) # every 60s
