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
OUTPUT_TAR_BASE        := $(strip $(PROJECT_ALIAS))-$(strip $(VERSION))
OUTPUT_TAR	           := $(OUTPUT_TAR_BASE).tar.bz2
OUTPUT_TAR_SOURCE	   := inuithy thirdparty tools Makefile makefiles
OUTPUT_TAR_PATH        := $(BUILD)/$(OUTPUT_TAR)
OUTPUT_LOGTAR          := $(strip $(PROJECT_ALIAS))-log-$(shell date +'%d%m%Y-%H%M').tar.bz2
OUTPUT_LOGTAR_PATH     := $(BUILD)/$(OUTPUT_LOGTAR)
OUTPUT_TAR_EXCLUDES	   := $(BUILD) *.pyc .git .svn .*.swp docs *~ *.cache *__pycache__*
PYLINT_OUTPUT		   := $(BUILD)/pylint
DEPLOY_SH	   		   := deploy_on_board.sh
INSTALL_BOARD_SH	   := install_board.sh
OUTPUT_INSTALL_BOARD_SH:= tools/$(INSTALL_BOARD_SH)
OUTPUT_DEPLOY_SH	   := tools/$(DEPLOY_SH)
OUTPUT_DEPEND_TAR	   := deploy_env.tar.bz2
OUTPUT_DEPEND		   := $(BUILD)/$(OUTPUT_DEPEND_TAR)
DEPLOY_ENV_SH	   	   := tools/deploy_env.sh
OUTPUT_DEPEND_SOURCE   := deploy

$(OUTPUT_TAR_PATH): $(BUILD) $(VERSION_PATH)
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(RM) $(OUTPUT_INSTALL_BOARD_SH)
	make $(OUTPUT_INSTALL_BOARD_SH)
	$(RM) $(OUTPUT_DEPLOY_SH)
	make $(OUTPUT_DEPLOY_SH)
	$(MKDIR) $(OUTPUT_TAR_BASE)
	$(CP) $(OUTPUT_TAR_SOURCE) $(OUTPUT_TAR_BASE)
	$(TAR) cfj $(OUTPUT_TAR_PATH) $(OUTPUT_TAR_BASE) $(OUTPUT_TAR_EXCLUDES:%=--exclude=%) --owner=root --group=root --total -l
	$(RM) $(OUTPUT_TAR_BASE)

$(VERSION_PATH):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(ECHO) "\"\"\" Inuithy version info - AUTO GENERATED ON `date`\"\"\"" > $@
	$(ECHO) "" >> $@
	$(ECHO) "MAJOR_VERSION = \""$(MAJOR_VERSION)"\"" >> $@
	$(ECHO) "MINOR_VERSION = \""$(MINOR_VERSION)"\"" >> $@
	$(ECHO) "REVISION = \""$(REVISION)"\"" >> $@
	$(ECHO) "__version__ = \""$(VERSION)"\"" >> $@
	$(ECHO) "__package__ = \""$(PROJECT_ALIAS)"\"" >> $@
	$(ECHO) "PROJECT = \""$(PROJECT_ALIAS)"\"" >> $@
	$(ECHO) "DEPLOY_SH = \""$(DEPLOY_SH)"\"" >> $@
	$(ECHO) "PROJECT_PATH = \""$(PROJECT_PATH)"\"" >> $@
	$(ECHO) "INUITHY_ROOT = '{}/{}'.format(PROJECT_PATH, PROJECT)" >> $@
	$(ECHO) "INUITHY_AGENT_INTERPRETER = \""$(PYTHON)"\"" >> $@
	$(ECHO) "" >> $@

grab_logs: $(BUILD)
	$(ECHO) "\033[01;36m[Packing log $(OUTPUT_LOGTAR_PATH)]\033[00m"
	$(shell cd $(LOGBASE); tar cfj $(OUTPUT_LOGTAR_PATH) . --total -l)

$(OUTPUT_DEPLOY_SH):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(ECHO) "# Inuithy deploy script - AUTO GENERATED ON `date`" > $@
	$(ECHO) "" >> $@
	$(ECHO) "[ ! $(AGENT_ARCH) == \`uname -m\` ] && exit 0" >> $@
	$(ECHO) "# Reference to $(DEPLOY_ENV_SH)" >> $@
	$(CAT) >> $@ < $(DEPLOY_ENV_SH)
	$(ECHO) "" >> $@
	$(ECHO) "latest_version=inuithy-$(VERSION)" >> $@
	$(ECHO) "latest_pack=\$$latest_version.tar.bz2" >> $@
	$(ECHO) "dest_base=/opt" >> $@
	$(ECHO) "tmp_base=opt/inuithy" >> $@
	$(ECHO) "# $(DEPLOY_ENV_SH) END" >> $@
	$(ECHO) "pushd /media/card > /dev/null" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "env_chk" >> $@
	$(ECHO) "if [ ! -f \$$latest_pack ]" >> $@
	$(ECHO) "then" >> $@
	$(ECHO) "    echo "\$$latest_pack not found"" >> $@
	$(ECHO) "    exit -1" >> $@
	$(ECHO) "fi" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "if [ -d \$$tmp_base ] ;then rm -rf \$$tmp_base; fi" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "tar xf \$$latest_pack --no-same-owner 1> /dev/null 2> /tmp/inuithy.update" >> $@
	$(ECHO) "mv $(OUTPUT_TAR_BASE) \$$tmp_base" >> $@
	$(ECHO) "pushd \$$tmp_base > /dev/null" >> $@
	$(ECHO) "make preset 1> /dev/null 2>> /tmp/inuithy.update" >> $@
	$(ECHO) "popd > /dev/null" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "if [ ! -d \$$dest_base ] ;then" >> $@
	$(ECHO) "    echo "\$$dest_base not exists, creating ..."" >> $@
	$(ECHO) "    ln -s \`pwd\`/opt / " >> $@
	$(ECHO) "fi" >> $@
	$(ECHO) "" >> $@
	$(ECHO) "popd > /dev/null" >> $@
	$(ECHO) "rm -rf \$$latest_pack" >> $@
	$(ECHO) "rm -rf $(OUTPUT_DEPEND_TAR) $(OUTPUT_DEPEND_SOURCE)" >> $@
	$(CHMOD) +x $@

$(OUTPUT_DEPEND):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(TAR) cfj $@ $(OUTPUT_DEPEND_SOURCE) $(OUTPUT_TAR_EXCLUDES:%=--exclude=%) --owner=root --group=root --total -l

$(OUTPUT_INSTALL_BOARD_SH):
	$(ECHO) "\033[01;36m[Creating $@]\033[00m"
	$(ECHO) "# Installer for Inuithy Agent - AUTO GENERATED ON `date`" > $@
	$(ECHO) "" >> $@
	$(ECHO) "pack_base=.." >> $@
	$(ECHO) "srcs=\"\$$pack_base/$(OUTPUT_DEPEND_TAR) tools/$(DEPLOY_SH) \$$pack_base/$(OUTPUT_TAR)\"" >> $@
	$(ECHO) "if [ 1 -gt \$$# ];then echo "No hosts given"; exit 0; fi" >> $@
	$(ECHO) "dests=\$$@" >> $@
	$(ECHO) "for dest in \$$dests; do" >> $@
	$(ECHO) "	echo -e \"\033[01;31m[Sending to \$$dest]\033[00m\"" >> $@
	$(ECHO) "	ssh root@\$$dest \"cd /media/card/;rm -rf deploy $(OUTPUT_DEPEND_TAR) $(DEPLOY_SH) $(OUTPUT_TAR)\"" >> $@
	$(ECHO) "	scp -r \$$srcs root@\$$dest:/media/card" >> $@
	$(ECHO) "	echo -e \"\033[01;34m[Deploying Inuithy on \$$dest]\033[00m\"" >> $@
	$(ECHO) "	ssh root@\$$dest /media/card/$(DEPLOY_SH)" >> $@
	$(ECHO) "done" >> $@
	$(CHMOD) +x $@
	

