use NetSNMP::OID (':all');
use NetSNMP::agent (':all');
# use NetSNMP::ASN (':all');

#
# Handler routine to deal with SNMP requests
# See https://net-snmp.sourceforge.io/wiki/index.php/Tut:Extending_snmpd_using_perl
#
sub myhandler {
    my  ($handler, $registration_info, $request_info, $requests) = @_;

    for ($request = $requests; $request; $request = $request->next()) {
        #
        #  Work through the list of varbinds
        #
        $oid = $request->getOID();
        print STDERR "\n$program @ $oid";
        if ($request_info->getMode() == MODE_SET) {
          my $ifindex = (split '\.', $oid)[-1];
          # 1 = enable, 2 = disable (int)
          my $val = ($request->getValue() == 1) ? "enable" : "disable";
          print STDERR "\nCalling gnmic-set-ifstatus.sh SET $oid $ifindex = $val";
          system("/opt/demo-agents/snmp-set/scripts/gnmic-set-ifstatus.sh $ifindex $val")
        }
    }
}

{
    #
    # Associate the handler with a particular OID tree, in this case interface adminStatus
    # iso(1) org(3) dod(6) internet(1) mgmt(2) mib(1) interfaces(2) ifTable(2) ifEntry(1) ifAdminStatus(7)
    my $rootOID = ".1.3.6.1.2.1.2.2.1.7";
    my $regoid = new NetSNMP::OID($rootOID);
    $agent->register("snmp_interface_mgmt", $regoid, \&myhandler);
    print STDERR "Registered SET handler for $rootOID\n";
}
