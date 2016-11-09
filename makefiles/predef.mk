## Predefinition for make
# Author: Zex Li <top_zlynch@yahoo.com>
#
ECHO		:= @echo
TAR			:= @tar
FIND		:= @find
RM			:= @rm -rf
MKDIR		:= @mkdir -p
AWK			:= @awk
PYTHON		:= @python3
TAILMON		:= @tail -f
SFOOD		:= @sfood
DOT			:= @dot
TAILEND		:= @tail -1
PS2PDF		:= @ps2pdf
VIM			:= @vim


BUILD		     := build
BUILD_DOCS		 := $(BUILD)/docs
THIRDPARTY		 := thirdparty
VERSION_PATH     := inuithy/common/version.py
PROJECT_PATH	 := /opt/inuithy
LOGBASE			 := /var/log/inuithy/
LOGPATH			 := $(LOGBASE)/inuithy.log
LASTGENID		 := lastgenid
REPORTBASE		 := $(LOGBASE)/report
MOSQUITTO_CONFIG := inuithy/config/mosquitto.conf
MONGODB_CONFIG	 := inuithy/config/mongod.conf

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


