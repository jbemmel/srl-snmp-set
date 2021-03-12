# How to use Perl and gNMIc to extend the SRLinux net-snmp module with SET commands to enable/disable interfaces

Nokia SRLinux comes with an SNMP module based on https://github.com/net-snmp/net-snmp. However, the default configuration only supports read access, and sometimes that is not enough.

For example, some people have a use case for enabling and disabling interfaces via SNMP. net-snmp has support for various extensions to do this, in this example we will be using a custom Perl module.

# Prerequisites
The Perl module requires the following packages to be installed:
`sudo yum install -y net-snmp-perl gnmic` (using containerlab, you may need to reduce the default system interface MTU to 1400)

* Place the following content in /usr/share/snmp/snmp_perl.pl:
````
    ##
    ## SNMPD perl initialization file.
    ##

    use NetSNMP::agent;
    $agent = new NetSNMP::agent('dont_init_agent' => 1,
                                'dont_init_lib' => 1);
````
* Copy the file snmp_write_handler.pl to /usr/share/snmp/snmp_write_handler.pl
* Temporarily edit /etc/snmp/ to include:
````
    access custom_grp "" any noauth exact sys2view **rwview** none
    view rwview included interfaces.ifTable.ifEntry.ifAdminStatus
    perl do "/usr/share/snmp/snmp_write_handler.pl";
