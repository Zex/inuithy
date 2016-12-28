# Pack report with genid
# @author: Zex Li <top_zlynch@yahoo.com>
#
DATEFMT='%d%m%Y' #-%H%M'
PDFTOOL=`which evince`
LASTGID="`make lastgenid|awk -F, '{print $1}'`"

pack_lastreport()
{
    pack_report $LASTGID
}

pack_report()
{
    echo -e "\033[01;36mPacking report with GENID: $1\033[00m"
    gid=$1
    reporttar=`pwd`"/build/report-$gid-"`date +$DATEFMT`".tar.bz2"
    reportbase="/var/log/inuithy/report"
    
    if [ ! -d $reportbase/$gid ] ;then
        echo -e "\033[01;31mReport with GENID $gid not found\033[00m"
        return
    fi

    pushd $reportbase
    tar cfj "$reporttar" "$gid"*
    if [ $? -eq 0 ] ;then
        echo -e "\033[01;33mCreated $reporttar\033[00m"
    else
        echo -e "\033[01;36mReport pack generation failed\033[00m"
    fi
    popd
}

pack_listed()
{
    for gid in $@ ; do
        pack_report $gid
    done
}

if [ $# -gt 0 ]; then
    pack_listed $@
fi


