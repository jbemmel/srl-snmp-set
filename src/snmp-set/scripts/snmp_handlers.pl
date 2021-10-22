use NetSNMP::OID (':all');
use NetSNMP::agent (':all');
# use NetSNMP::ASN (':all');

#
# Handler routine to deal with SNMP requests
# See https://net-snmp.sourceforge.io/wiki/index.php/Tut:Extending_snmpd_using_perl
#
sub set_if_handler {
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

sub get_bgp_mib {
	my($handler, $registration_info, $request_info, $requests) = @_;

	my $mib_entries = `/opt/demo-agents/snmp-set/scripts/get_bgp_tree.sh`;
	print STDERR "\nget_bgp_mib mib_entries = '$mib_entries'";
	my %mib_hash = ();
	my %mib_next = ();
	my $prev;
	foreach ($mib_entries) {
	    my($suboid, $val) = /(\S+)=(.*)/;
			print STDERR "\nget_bgp_mib read '$suboid' = '$val'";
      $mib_hash{$suboid} = $val;
	    if defined($prev) {
        $mib_next{$prev} = $suboid;
	    }
	    $prev = $suboid;
	    next;
	}

	for(my $request = $requests; $request; $request = $request->next()) {
	   my $oid = $request->getOID();
     my $mode = $request_info->getMode();
     if ($mode == MODE_GETNEXT) {
	      if defined($mib_next{$oid}) {
	         $request->setOID($mib_next{$oid});
	      }
	      $mode = MODE_GET;
	   }
	   if ($mode == MODE_GET) {
	      next if !defined($mib_hash{$oid});
	      $request->setValue(ASN_OCTET_STR, $mib_hash{$oid});
	   }
     next;
   }
}

{
    #
    # Associate the handler with a particular OID tree, in this case interface adminStatus
    # iso(1) org(3) dod(6) internet(1) mgmt(2) mib(1) interfaces(2) ifTable(2) ifEntry(1) ifAdminStatus(7)
    my $rootOID = ".1.3.6.1.2.1.2.2.1.7";
    my $regoid = new NetSNMP::OID($rootOID);
    $agent->register("snmp_interface_mgmt", $regoid, \&set_if_handler);
    print STDERR "Registered SET handler for $rootOID\n";

    use constant OID_BGP_ROOT => '.1.3.6.1.2.1.15';
    my $oid_bgp = new NetSNMP::OID($OID_BGP_ROOT);
    $agent->register("snmp_bgp_mib", $oid_bgp, \&get_bgp_mib);
    print STDERR "Registered GET handler for BGP MIB $OID_BGP_ROOT\n";
}
