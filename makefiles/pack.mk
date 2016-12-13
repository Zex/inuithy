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
DEPLOY_SH	   		   := deploy_on_board.sh
OUTPUT_DEPLOY_SH	   := $(BUILD)/$(DEPLOY_SH)

$(OUTPUT_TAR_PATH): $(BUILD) $(VERSION_PATH)
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(TAR) cfj $(OUTPUT_TAR_PATH) $(OUTPUT_TAR_SOURCE) $(OUTPUT_TAR_EXCLUDES:%=--exclude=%) --owner=root --group=root --total -l

$(VERSION_PATH):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(ECHO) "\"\"\" Inuithy version info - AUTO GENERATED ON `date`\"\"\"" > $@
	$(ECHO) "" >> $@
	$(ECHO) "MAJOR_VERSION = \""$(MAJOR_VERSION)"\"" >> $@
	$(ECHO) "MINOR_VERSION = \""$(MINOR_VERSION)"\"" >> $@
	$(ECHO) "REVISION = \""$(REVISION)"\"" >> $@
	$(ECHO) "__version__ = \""$(VERSION)"\"" >> $@
	$(ECHO) "__package__ = \""$(PROJECT_ALIAS)"\"" >> $@
	$(ECHO) "DEPLOY_SH = \""$(DEPLOY_SH)"\"" >> $@
	$(ECHO) "PROJECT_PATH = \""$(PROJECT_PATH)"\"" >> $@
	$(ECHO) "INUITHY_ROOT = \""$(PROJECT_PATH)/inuithy"\"" >> $@
	$(ECHO) "" >> $@

grab_logs: $(BUILD)
	$(ECHO) "\033[01;36m[Packing log $(OUTPUT_LOGTAR_PATH)]\033[00m"
	$(shell cd $(LOGBASE); tar cfj $(OUTPUT_LOGTAR_PATH) . --total -l)

$(OUTPUT_DEPLOY_SH):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(ECHO) "# Inuithy deploy script - AUTO GENERATED ON `date`" > $@
	$(ECHO) "" >> $@
	$(ECHO) "latest_version=inuithy-$(VERSION)" >> $@
	$(ECHO) -e "latest_pack=\$$latest_version.tar.bz2" >> $@
	$(ECHO) "dest_base=/opt" >> $@
	$(ECHO) "tmp_base=opt/inuithy" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "pushd /media/card" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "if [ ! -f \$$latest_pack ]" >> $@
	$(ECHO) "then" >> $@
	$(ECHO) "    echo "\$$latest_pack not found"" >> $@
	$(ECHO) "    exit -1" >> $@
	$(ECHO) "fi" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "if [ -d \$$tmp_base ] ;then rm -rf \$$tmp_base; fi" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "mkdir -p \$$tmp_base" >> $@
	$(ECHO) "tar xf \$$latest_pack --no-same-owner -C \$$tmp_base 1> /dev/null 2> /tmp/inuithy.update" >> $@
	$(ECHO) "pushd \$$tmp_base" >> $@
	$(ECHO) "make preset 1> /dev/null 2>> /tmp/inuithy.update" >> $@
	$(ECHO) "popd" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "if [ ! -d \$$dest_base ] ;then" >> $@
	$(ECHO) "    echo "\$$dest_base not exists, creating ..."" >> $@
	$(ECHO) "    ln -s \`pwd\`/opt / " >> $@
	$(ECHO) "fi" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "popd" >> $@
	$(CHMOD) +x $@

