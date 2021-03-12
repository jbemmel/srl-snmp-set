use NetSNMP::OID (':all'); 
use NetSNMP::agent (':all'); 
use NetSNMP::ASN (':all');

    #
    # Handler routine to deal with SNMP requests
    #
sub myhandler {
    my  ($handler, $registration_info, $request_info, $requests) = @_;

    for ($request = $requests; $request; $request = $request->next()) { 
        #
        #  Work through the list of varbinds
        #
        $oid = $request->getOID(); 
        print STDERR "$program @ $oid ";
        if ($request_info->getMode() == MODE_SET) {
          my $ifindex = (split '\.', $oid)[-1];
          my $eth = $ifindex - 53;  # Eth1/1 == ifindex 54
          # 1 = enable, 2 = disable (int)
          my $val = ($request->getValue() == 1) ? "enable" : "disable";
          system("/usr/local/bin/gnmic -a 127.0.0.1:57400 -u admin -p admin --skip-verify set --update-path /interface[name=ethernet-1/$eth]/admin-state --update-value $val -e json_ietf")
        }
    }
}

{
    #
    # Associate the handler with a particular OID tree, in this case interface adminStatus
    #
    my $rootOID = ".1.3.6.1.2.1.2.2.1.7";
    my $regoid = new NetSNMP::OID($rootOID); 
    $agent->register("snmp_interface_mgmt", $regoid, \&myhandler);
}
