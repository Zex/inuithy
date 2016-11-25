# Pack last report
# @author: Zex Li <top_zlynch@yahoo.com>
#
PDFTOOL=`which evince`
LASTGID="`make lastgenid|awk -F, '{print $1}'`"
REPORTTAR=`pwd`"/build/report-$LASTGID-"`date +'%d%m%Y-%H%M'`".tar.bz2"
REPORTBASE="/var/log/inuithy/report"
#python3 inuithy/analysis/pandas_plugin.py $LASTGID
#[ -z $PDFTOOL ] && echo "PDF view not found" && exit -1
#$PDFTOOL /var/log/inuithy/report/$LASTGID.pdf &

pushd $REPORTBASE
echo "$REPORTTAR"
tar cfj "$REPORTTAR" "$LASTGID"*
popd
#echo "$REPORTTAR created" 

