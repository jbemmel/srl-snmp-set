NOTE: !! This repository is no longer being maintained, please contact your Nokia representative for support !!
It seems that SR Linux GRPC management ports have changed, and the agent can no longer connect

NOTE: !! This code now requires SR Linux 23.10 or later, older versions no longer supported !!

# How to use Perl and gNMIc to extend the SR Linux net-snmp module with SET commands to enable/disable interfaces

Nokia SR Linux comes with an SNMP module based on https://github.com/net-snmp/net-snmp. However, the default configuration only supports read access to a small set of OIDs, and sometimes that is not enough. 

Some people have a use case for enabling and disabling interfaces via SNMP. net-snmp has support for various extensions to do this, in this example we will be using a custom Perl module.

# Prerequisites
Enable SNMP in SR Linux:
````
enter candidate
/system snmp
community private
network-instance mgmt admin-state enable source-address [172.20.20.2]
commit stay
````
# Agent
In order to overcome the limitations of manual configuration and to make things manageable through a single configuration file, a sample Python agent is included.
This agent performs the necessary SNMP configuration as described above, when enabled:
```
A:leaf1# /system snmp                                                                                                                                                                                              
--{ + running }--[ system snmp ]--                                                                                                                                                                                 
A:leaf1# info                                                                                                                                                                                                      
    community $aes$73MtC3Nkc1zg=$hxMfoH62G7g5IgBMzT46vg==
    network-instance mgmt {
        admin-state enable
        enable-set-interface true  !!! Agent enabled
        source-address [
            172.20.20.2
        ]
    }
```

# Usage
The following examples assume interface lo0 has index 1073758206:

## Admin Enable
```
snmpset -v 2c -c private 172.20.20.2 .1.3.6.1.2.1.2.2.1.7.1073758206 i 1
```
You may be able to use 'ifAdminStatus' instead of the OID '.1.3.6.1.2.1.2.2.1.7' when the corresponding SNMP MIBs are installed

## Admin Disable
```
snmpset -v 2c -c private 172.20.20.2 .1.3.6.1.2.1.2.2.1.7.1073758206 i 2
````

## Limitations
When done manually, the configuration is not persisted across reboots

The lab setup includes a minimal complete config file for a "leaf" node, and a delta config file (with only changes relative to the default system configuration) for the "spine"
