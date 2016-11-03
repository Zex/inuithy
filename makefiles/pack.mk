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

OUTPUT_TAR	           := $(strip $(PROJECT))-$(strip $(VERSION)).tar.bz2
OUTPUT_TAR_SOURCE	   := inuithy thirdparty tools
OUTPUT_TAR_PATH        := $(BUILD)/$(OUTPUT_TAR)
OUTPUT_TAR_EXCLUDES	   := $(BUILD) *.pyc .git .svn .*.swp docs *~ *.cache *__pycache__*

$(OUTPUT_TAR_PATH): $(BUILD) $(VERSION_PATH)
	$(ECHO) "---------------Creating $@------------------"
	$(TAR) cfj $(OUTPUT_TAR_PATH) $(OUTPUT_TAR_SOURCE) $(OUTPUT_TAR_EXCLUDES:%=--exclude=%) --total -l

$(VERSION_PATH):
	$(ECHO) "---------------Creating $@------------------"
	$(ECHO) "## AUTO GENERATED ON `date`" > $@
	$(ECHO) "" >> $@
	$(ECHO) "INUITHY_VERSION = \""$(VERSION)"\"" >> $@
	$(ECHO) "PROJECT_PATH = \""$(PROJECT_PATH)"\"" >> $@
	$(ECHO) "INUITHY_ROOT = \""$(PROJECT_PATH)/inuithy"\"" >> $@
	$(ECHO) "" >> $@


