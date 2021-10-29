#!/bin/bash

byzanz-record --delay=0 --exec "xterm -maximize -e 'sleep 1 && cat do_snmpwalk.sh && ./do_snmpwalk.sh && sleep 10'" snmpwalk_bgp.gif
