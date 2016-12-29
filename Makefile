## Makefile for Inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
PROJECT         := Inuithy
MAJOR_VERSION   := 0
MINOR_VERSION   := 1
REVISION        := $(shell [ -d .git ] && git rev-parse --short HEAD)
VERSION         := $(MAJOR_VERSION).$(MINOR_VERSION).$(REVISION)
AGENT_ARCH		:= armv7l

include makefiles/predef.mk
include makefiles/pack.mk

.PHONY: $(VERSION_PATH) $(OUTPUT_TAR_PATH) $(BUILD) clean version sample_config traffic_config_chk run_controller run_tsh $(LOGBASE) install run_agent run_mosquitto deploy

all: deploy

version: $(VERSION_PATH)

clean:
	$(ECHO) "\033[01;32m[Cleaning]\033[00m"
	$(FIND) . -name __pycache__ -exec rm -rf {} \;
	$(FIND) . -name *.pyc -delete 
	$(RM) $(VERSION_PATH)
	$(RM) $(BUILD)

sample_config: inuithy/util/config_manager.py
	$(PYTHON) $<

traffic_config_chk: inuithy/common/traffic.py
	$(PYTHON) $<

run_controller: inuithy/controller.py
	$(ECHO) "" > $(LOGPATH)
	$(ULIMIT) -u unlimited
	python3 $<

run_tsh: inuithy/controller.py
	$(ECHO) "" > $(LOGPATH)
	$(PYTHON) $<

run_agent: inuithy/agent.py
	$(PYTHON) $<

run_mosquitto:
	mosquitto -c $(MOSQUITTO_CONFIG) &

run_mongod:
	mongod -f $(MONGODB_CONFIG)

logmon:
	$(TAILMON) $(LOGPATH)

run_all_agents:
	ssh root@127.0.0.1 "pushd $(PROJECT_PATH) > /dev/null;$(PYTHON) inuithy/agent.py &> /tmp/inuithy.nohup; exit" &

viewlog:
	$(VIM) $(LOGPATH)

sfood: $(BUILD_DOCS)
	$(SFOOD) --follow --internal inuithy | sfood-graph > $(BUILD_DOCS)/inuithy.dot
	$(DOT) -Tps $(BUILD_DOCS)/inuithy.dot > $(BUILD_DOCS)/inuithy.ps
	$(PS2PDF) $(BUILD_DOCS)/inuithy.ps $(BUILD_DOCS)/inuithy.pdf
	$(RM) $(BUILD_DOCS)/inuithy.dot $(BUILD_DOCS)/inuithy.ps

preset: $(LOGBASE) $(REPORTBASE)                      

install: preset install_dir
	$(ECHO) "\033[01;36m[Installing Inuithy]\033[00m"
	$(CP) $(OUTPUT_TAR_SOURCE) $(INSTALL_PREFIX)/$(PROJECT_ALIAS)
	$(ECHO) "\033[01;32m[Inuithy installed @ $(INSTALL_PREFIX)/$(PROJECT_ALIAS)]\033[00m"

install_dir:
	$(ECHO) "\033[01;36m[Creating target directory]\033[00m"
	$(MKDIR) $(INSTALL_PREFIX)/$(PROJECT_ALIAS)

pylint:
	$(MKDIR) $(PYLINT_OUTPUT)
	$(PYLINT) --files-output=y $(PROJECT_ALIAS)
#	$(MV) pylint*.txt $(PYLINT_OUTPUT)

deploy: latest
	$(RM) $(OUTPUT_DEPEND)
	make $(OUTPUT_DEPEND)

latest: $(OUTPUT_TAR_PATH)
	$(RM) $(BUILD)/latest
	ln -s $(OUTPUT_TAR_PATH) $(BUILD)/latest 

