#!/bin/bash

byzanz-record --delay=0 --exec "xterm -maximize -e 'sleep 1 && cat do_snmpwalk.sh && ./do_snmpwalk.sh && sleep 5'" snmpwalk_bgp.gif
