#
# Inspired by http://www.haproxy.org/download/contrib/netsnmp-perl/haproxy.pl
#
# Supports SNMP GETNEXT and GET requests for an arbitrary OID subtree.
# For example: the BGP MIB as found in the default network-instance (using gNMI)
# From /usr/share/mibs/ietf/BGP4-MIB (RFC4271)
#
# Root OID: 1.3.6.1.2.1.15
#
# 1.3.6.1.2.1.15.1 bgpVersion => 0x2
# 1.3.6.1.2.1.15.2 bgpLocalAS => e.g. 65000
# 1.3.6.1.2.1.15.3 bgpPeerID <peer IP octets> e.g. 1.3.6.1.2.1.15.3.1.2.3.4 = IP
# 1.3.6.1.2.1.15.4 bgpPeerStatus <IP>         e.g. 1.3.6.1.2.1.15.4.1.2.3.4 = 6 (established)
# ... etc. ...
#
# This Perl script simply parses the output of a Shell script: get_bgp_tree.sh
# It assumes the client is doing an SNMP walk of the entire tree, i.e.
# snmpwalk -v 2c -c private -m /usr/share/mibs/ietf/BGP4-MIB 172.20.20.2 1.3.6.1.2.1.15

use NetSNMP::OID (':all');
use NetSNMP::agent (':all');

use strict;

use constant OID_BGP_ROOT => '1.3.6.1.2.1.15';
# use constant OID_HAPROXY_STATS => OID_HAPROXY . '.1';

my $oid_bgp = new NetSNMP::OID(OID_BGP_ROOT);

sub get_bgp_mib {
	my($handler, $registration_info, $request_info, $requests) = @_;

	my $mib_entries = `/opt/demo-agents/snmp-set/scripts/get_bgp_tree.sh`;
	my %mib_hash = ();
	my %mib_next = ();
	my $prev;
	foreach ($mib_entries) {
	    my($suboid, $val) = /(\S+)=(.*)/;
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

$agent->register('BGP MIB', $oid_bgp, \&get_bgp_mib);
