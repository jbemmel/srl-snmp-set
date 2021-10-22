ARG SR_BASEIMG
ARG SR_LINUX_RELEASE

FROM $SR_BASEIMG:$SR_LINUX_RELEASE AS target

RUN sudo curl -sL https://github.com/karimra/gnmic/releases/download/v0.20.0/gnmic_0.20.0_Linux_x86_64.rpm -o /tmp/gnmic.rpm && sudo yum localinstall -y /tmp/gnmic.rpm

RUN sudo yum install -y epel-release && \
    sudo yum install -y net-snmp-perl jq

# Turn on debugging for SNMP daemon
RUN sudo sed -i.orig 's/snmp_server -M/snmp_server -DALL -M/g' /opt/srlinux/appmgr/sr_linux_mgr_config.yml

RUN sudo mkdir --mode=0755 -p /opt/demo-agents/

COPY ./src /opt/demo-agents/

# Using a build arg to set the release tag, set a default for running docker build manually
ARG SRL_SNMP_SET_RELEASE="[custom build]"
ENV SRL_SNMP_SET_RELEASE=$SRL_SNMP_SET_RELEASE
