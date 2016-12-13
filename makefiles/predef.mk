## Predefinition for make
# Author: Zex Li <top_zlynch@yahoo.com>
#
ECHO    := @echo -e
TAR     := @tar
FIND    := @find
RM      := @rm -rf
MKDIR   := @mkdir -p
AWK     := @awk
PYTHON  := python
TAILMON := @tail -f
SFOOD   := @sfood
DOT     := @dot
TAILEND := @tail -1
PS2PDF  := @ps2pdf
VIM     := @vim
ULIMIT  := @ulimit
CD      := @cd
CP      := @cp -ra
MV      := @mv
MAKE    := make
CAT     := @cat
CHMOD	:= @chmod
PYLINT  := pylint

BUILD            := $(shell pwd)/build
BUILD_DOCS       := $(BUILD)/docs
THIRDPARTY       := thirdparty
VERSION_PATH     := inuithy/common/version.py
PROJECT_PATH     := /opt/inuithy
LOGBASE          := /var/log/inuithy/
LOGPATH          := $(LOGBASE)/inuithy.log
LASTGENID        := lastgenid
LASTREPORT       := lastreport
ALLGENID         := allgenid
REPORTBASE       := $(LOGBASE)/report
MOSQUITTO_CONFIG := inuithy/config/mosquitto.conf
MONGODB_CONFIG   := inuithy/config/mongod.conf
INSTALL_PREFIX   := /opt

$(BUILD):
	$(MKDIR) $@    

$(BUILD_DOCS):
	$(MKDIR) $@

$(REPORTBASE):
	$(MKDIR) $@

$(LOGBASE):
	$(MKDIR) $@

$(LASTGENID):
	$(TAILEND) $(LOGBASE)/inuithy.genid

$(ALLGENID):
	$(CAT) $(LOGBASE)/inuithy.genid

