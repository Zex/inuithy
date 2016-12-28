#!/usr/bin/env bash

SOURCES="
/var/log/inuithy
"
TAR_PATH="inuithy_logs/inuithy_log-`date +%b%d%Y%H%M`.tar.bz2"

mkdir -p `dirname $TAR_PATH`
tar cfj $TAR_PATH $SOURCES 2> /dev/null



