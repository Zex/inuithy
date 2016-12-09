## Create package
# Author: Zex Li <top_zlynch@yahoo.com>
#
ifndef PROJECT
$(error "PROJECT not defined")
endif

ifndef VERSION
$(error "VERSION not defined")
endif

ifndef VERSION_PATH
$(error "VERSION_PATH not defined")
endif

PROJECT_ALIAS		   := $(shell tr A-Z a-z <<< $(PROJECT))
OUTPUT_TAR	           := $(strip $(PROJECT_ALIAS))-$(strip $(VERSION)).tar.bz2
OUTPUT_TAR_SOURCE	   := inuithy thirdparty tools Makefile makefiles
OUTPUT_TAR_PATH        := $(BUILD)/$(OUTPUT_TAR)
OUTPUT_LOGTAR          := $(strip $(PROJECT_ALIAS))-log-$(shell date +'%d%m%Y-%H%M').tar.bz2
OUTPUT_LOGTAR_PATH     := $(BUILD)/$(OUTPUT_LOGTAR)
OUTPUT_TAR_EXCLUDES	   := $(BUILD) *.pyc .git .svn .*.swp docs *~ *.cache *__pycache__*
PYLINT_OUTPUT		   := $(BUILD)/pylint

$(OUTPUT_TAR_PATH): $(BUILD) $(VERSION_PATH)
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(TAR) cfj $(OUTPUT_TAR_PATH) $(OUTPUT_TAR_SOURCE) $(OUTPUT_TAR_EXCLUDES:%=--exclude=%) --total -l

$(VERSION_PATH):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(ECHO) "\"\"\" Inuithy version info - AUTO GENERATED ON `date`\"\"\"" > $@
	$(ECHO) "" >> $@
	$(ECHO) "__version__ = \""$(VERSION)"\"" >> $@
	$(ECHO) "PROJECT_PATH = \""$(PROJECT_PATH)"\"" >> $@
	$(ECHO) "INUITHY_ROOT = \""$(PROJECT_PATH)/inuithy"\"" >> $@
	$(ECHO) "" >> $@

grab_logs: $(BUILD)
	$(ECHO) "\033[01;36m[Packing log $(OUTPUT_LOGTAR_PATH)]\033[00m"
	$(shell cd $(LOGBASE); tar cfj $(OUTPUT_LOGTAR_PATH) . --total -l)


