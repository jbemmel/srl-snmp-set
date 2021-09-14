LAST_COMMIT := $(shell sh -c "git log -1 --pretty=%h")
TODAY       := $(shell sh -c "date +%Y%m%d_%H%M")
TAG         := ${TODAY}.${LAST_COMMIT}
# HTTP_PROXY  := "http://proxy.server.com:8000"

ifndef SR_LINUX_RELEASE
override SR_LINUX_RELEASE="latest"
endif

.PHONY: build do-build build-snmp-and-evpn-proxy
build: BASEIMG=srl/custombase
build: NAME=srl/snmp-set
build: do-build

do-build:
	sudo DOCKER_BUILDKIT=1 docker build --build-arg SRL_SNMP_SET_RELEASE=${TAG} \
	                  --build-arg http_proxy=${HTTP_PROXY} \
										--build-arg https_proxy=${HTTP_PROXY} \
										--build-arg SR_BASEIMG="${BASEIMG}" \
	                  --build-arg SR_LINUX_RELEASE="${SR_LINUX_RELEASE}" \
	                  -f ./Dockerfile -t ${NAME}:${TAG} .
	sudo docker tag ${NAME}:${TAG} ${NAME}:latest

#
# This builds a combined SNMP set/EVPN proxy image
#
build-snmp-and-evpn-proxy: BASEIMG=srl/evpn-proxy-agent
build-snmp-and-evpn-proxy: NAME=srl/snmp-plus-evpn-proxy-agent
build-snmp-and-evpn-proxy: do-build
