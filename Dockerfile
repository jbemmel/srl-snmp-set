ARG SR_LINUX_RELEASE
FROM ghcr.io/nokia/srlinux:$SR_LINUX_RELEASE

RUN sudo curl -sL https://github.com/karimra/gnmic/releases/download/v0.18.0/gnmic_0.18.0_Linux_x86_64.rpm -o /tmp/gnmic.rpm && sudo yum localinstall -y /tmp/gnmic.rpm

RUN sudo yum install -y epel-release && \
    sudo yum install -y net-snmp-perl jq

RUN sudo mkdir -p /opt/srlinux/agents/

COPY ./src /opt/srlinux/agents/

# Using a build arg to set the release tag, set a default for running docker build manually
ARG SRL_SNMP_SET_RELEASE="[custom build]"
ENV SRL_SNMP_SET_RELEASE=$SRL_SNMP_SET_RELEASE
