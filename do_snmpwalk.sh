#!/bin/bash

# on leaf1
snmpwalk -v 2c -c private 172.20.20.3 1.3.6.1.2.1.15
