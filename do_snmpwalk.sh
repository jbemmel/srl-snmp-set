#!/bin/bash

ssh admin@clab-snmp-set-lab-leaf1 <<< "show network-instance default protocols bgp neighbor"

# Walk BGP4 MIB on leaf1
snmpwalk -v 2c -c private clab-snmp-set-lab-leaf1 1.3.6.1.2.1.15
