
PDFTOOL=`which evince`
LASTGID=`make lastgenid|awk -F, '{print $1}'`

python3 inuithy/analysis/pandas_plugin.py $LASTGID

[ -z $PDFTOOL ] && echo "PDF view not found" && exit -1
$PDFTOOL /var/log/inuithy/report/$LASTGID.pdf &

