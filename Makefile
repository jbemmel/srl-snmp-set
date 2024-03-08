LAST_COMMIT := $(shell sh -c "git log -1 --pretty=%h")
TODAY       := $(shell sh -c "date +%Y%m%d_%H%M")
TAG         := ${TODAY}.${LAST_COMMIT}
# HTTP_PROXY  := "http://proxy.server.com:8000"

ifndef SR_LINUX_RELEASE
override SR_LINUX_RELEASE="latest"
endif

.PHONY: build do-build
build: BASEIMG=ghcr.io/nokia/srlinux
# build: BASEIMG=srl/custombase
build: NAME=srl/snmp-set
build: do-build ## Builds the agent

do-build:
	sudo DOCKER_BUILDKIT=1 docker build --build-arg SRL_SNMP_SET_RELEASE=${TAG} \
	                  --build-arg http_proxy=${HTTP_PROXY} \
										--build-arg https_proxy=${HTTP_PROXY} \
										--build-arg SR_BASEIMG="${BASEIMG}" \
	                  --build-arg SR_LINUX_RELEASE="${SR_LINUX_RELEASE}" \
	                  -f ./Dockerfile -t ${NAME}:${TAG} .
	sudo docker tag ${NAME}:${TAG} ${NAME}:${SR_LINUX_RELEASE}

.DEFAULT_GOAL := help

.PHONY: help deploy-clab-ci destroy-clab-ci run-tests

# TESTS := $(shell find test/ci -name '*.py')

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

deploy-clab-ci: build ## Deploy "ci" test topology
	sudo clab deploy -t srl-snmp-set.clab.yml

destroy-clab-ci: ## Destroy "ci" test topology
	sudo clab destroy -t srl-snmp-set.clab.yml

run-tests: # $(TESTS) ## Run all CI tests under test/ci
	# PYTHONPATH="." python3 $<
	snmpset -v 2c -c private 172.20.20.2 .1.3.6.1.2.1.2.2.1.7.1073758206 i 0 # Disable
	snmpset -v 2c -c private 172.20.20.2 .1.3.6.1.2.1.2.2.1.7.1073758206 i 1 # Enable
	snmpget -v 2c -c private 172.20.20.2 .1.3.6.1.2.1.2.2.1.7.1073758206
