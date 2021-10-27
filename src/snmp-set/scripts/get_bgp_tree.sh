#!/usr/bin/env bash

# Simple demo script for testing purposes
# 1.3.6.1.2.1.15 tree
echo "mib-2.15:Sequence="    # Enable SNMP walk starting from .15
echo "mib-2.15.1:OctetString=2" # bgpVersion: snmpget -v 2c -c private -m /usr/share/mibs/ietf/BGP4-MIB 172.20.20.2 1.3.6.1.2.1.15.1
echo "mib-2.15.2:Integer32=65000" # bgpLocalAS
echo "mib-2.15.3:Sequence=" # bgpPeerTable (sequence)
echo "mib-2.15.3.1.1:Sequence=" # bgpPeerTable (sequence)
echo "mib-2.15.3.1.1.5.6.7.8:IpAddress=5.6.7.8" # bgpPeerIdentifier
echo "mib-2.15.3.1.2.5.6.7.8:INTEGER=6"       # bgpPeerState, 6="established"

exit 0
