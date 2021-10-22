#!/usr/bin/env bash

# Simple demo script for testing purposes
echo "1.3.6.1.2.1.15.1=2" # bgpVersion
echo "1.3.6.1.2.1.15.2=65000" # bgpLocalAS
echo "1.3.6.1.2.1.15.3.1.2.3.4=1.2.3.4" # bgpPeerID
echo "1.3.6.1.2.1.15.4.1.2.3.4=6" # bgpPeerStatus, 6="established"

exit 0
