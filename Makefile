## Makefile for Inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
PROJECT		           := Inuithy
VERSION		           := 0.0.1

include makefiles/predef.mk
include makefiles/pack.mk

.PHONY: $(VERSION_PATH) $(OUTPUT_TAR_PATH) $(BUILD) clean version

all: $(OUTPUT_TAR_PATH)

version: $(VERSION_PATH)

clean:
	$(ECHO) "-----------------Cleaning-------------------"
	$(FIND) . -name *.pyc -delete 
	$(FIND) . -name __pycache__ -exec rm -rf {} \;
	$(RM) $(VERSION_PATH)
	$(RM) $(BUILD)

$(BUILD):
	$(MKDIR) $@	

