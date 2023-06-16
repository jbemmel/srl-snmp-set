ARG SR_BASEIMG
ARG SR_LINUX_RELEASE

FROM $SR_BASEIMG:$SR_LINUX_RELEASE AS target

RUN sudo curl -sL https://github.com/openconfig/gnmic/releases/download/v0.31.0/gnmic_0.31.0_Linux_x86_64.rpm -o /tmp/gnmic.rpm && \
    sudo yum localinstall -y /tmp/gnmic.rpm && sudo rm -f /tmp/gnmic.rpm

RUN sudo yum install -y epel-release && \
    sudo yum install -y net-snmp-perl jq && \
    sudo pip3 install snmp_passpersist

# Turn on debugging for SNMP daemon, and replace with /usr/sbin/snmpd
# Dont read default config
# Can do -DALL or -Ducd-snmp/pass_persist
RUN sudo sed -i.orig 's|./snmp_server -M|/usr/sbin/snmpd -C -Lo -Ducd-snmp/pass_persist|g' /opt/srlinux/appmgr/sr_linux_mgr_config.yml

RUN sudo mkdir --mode=0755 -p /opt/demo-agents/
COPY --chown=srlinux:srlinux ./snmp-set-agent.yml /etc/opt/srlinux/appmgr
COPY --chown=srlinux:srlinux ./src /opt/demo-agents/

# Using a build arg to set the release tag, set a default for running docker build manually
ARG SRL_SNMP_SET_RELEASE="[custom build]"
ENV SRL_SNMP_SET_RELEASE=$SRL_SNMP_SET_RELEASE
