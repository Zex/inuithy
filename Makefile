## Makefile for Inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
PROJECT		           := Inuithy
VERSION		           := 0.0.1

include makefiles/predef.mk
include makefiles/pack.mk

.PHONY: $(VERSION_PATH) $(OUTPUT_TAR_PATH) $(BUILD) clean version sample_config traffic_config_chk run_controller run_tsh $(LOGBASE) install run_agent run_mosquitto

all: $(OUTPUT_TAR_PATH)

version: $(VERSION_PATH)

clean:
	$(ECHO) "-----------------Cleaning-------------------"
	$(FIND) . -name *.pyc -delete 
	$(FIND) . -name __pycache__ -exec rm -rf {} \;
	$(RM) $(VERSION_PATH)
	$(RM) $(BUILD)

sample_config: inuithy/util/config_manager.py
	$(PYTHON) $<

traffic_config_chk: inuithy/common/traffic.py
	$(PYTHON) $<

run_controller: inuithy/controller.py
	$(PYTHON) $<

run_tsh: inuithy/util/console.py
	$(PYTHON) $<

run_agent: inuithy/agent.py
	$(PYTHON) $<

run_mosquitto:
	mosquitto -c $(MOSQUITTO_CONFIG)

$(BUILD):
	$(MKDIR) $@	

$(LOGBASE):
	$(MKDIR) $@

logmon:
	$(TAILMON) $(LOGPATH)

install: $(LOGPATH)

	
