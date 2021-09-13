#!/bin/bash

# Script parameters: SNMP_ifIndex adminStatus('enable' or 'disable')
IFINDEX="$1"
ADMINSTATUS="$2"
GNMIC="/usr/local/bin/gnmic -a 127.0.0.1:57400 -u admin -p admin --skip-verify -e json_ietf"
IFNAME=`$GNMIC get --path /interface/ifindex | \
        jq -r --arg i "$IFINDEX" '.[].updates[].values[""]["srl_nokia-interfaces:interface"][] | select (.ifindex == ($i|tonumber))|.name'`
[[ "$IFNAME" != "" ]] && $GNMIC set --update-path /interface[name="$IFNAME"]/admin-state --update-value $ADMINSTATUS

exit $?
