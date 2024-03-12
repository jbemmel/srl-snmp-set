ARG SR_BASEIMG
ARG SR_LINUX_RELEASE

FROM $SR_BASEIMG:$SR_LINUX_RELEASE AS target

# Latest version 0.36.1 has issue connecting with local unix socket without port component
RUN sudo bash -c "$(curl -sL https://get-gnmic.openconfig.net)" -- -v 0.33.0

RUN sudo apt update && sudo apt install -y libsnmp-perl

# Turn on debugging for SNMP daemon, and replace with /usr/sbin/snmpd
# Dont read default config
# Can do -DALL or -Ducd-snmp/pass_persist
# RUN sudo sed -i.orig 's|./sr_snmp_server -M -c {0}|/usr/sbin/snmpd -C -Lo -Ducd-snmp/pass_persist -M /opt/srlinux/snmp/MIBs:/usr/share/snmp/mibs -c /etc/snmp/snmpd-{0}.conf|g' /opt/srlinux/appmgr/sr_linux_mgr_config.yml

RUN sudo mkdir --mode=0755 -p /opt/demo-agents/
COPY --chown=srlinux:srlinux ./snmp-set-agent.yml /etc/opt/srlinux/appmgr
COPY --chown=srlinux:srlinux ./src /opt/demo-agents/

# Using a build arg to set the release tag, set a default for running docker build manually
ARG SRL_SNMP_SET_RELEASE="[custom build]"
ENV SRL_SNMP_SET_RELEASE=$SRL_SNMP_SET_RELEASE
