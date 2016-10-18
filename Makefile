## Makefile for Inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
VERSION	:= 0.0.0
VERSION_PATH := inuithy/common/version.py

.PHONY: $(VERSION_PATH) clean

all: $(VERSION_PATH)

$(VERSION_PATH):
	@echo "## AUTO GENERATED ON `date`" > $@
	@echo "" >> $@
	@echo "INUITHY_VERSION = \""$(VERSION)"\"" >> $@
	@echo "" >> $@

clean:
	find . -name *.pyc -delete 
	rm -f $(VERSION_PATH)
