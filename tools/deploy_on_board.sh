latest_version=inuithy-0.0.1
latest_pack=$latest_version.tar.bz2
dest_base=/opt
tmp_base=opt/inuithy

pushd /media/card

if [ ! -f $latest_pack ]
then
    echo "$latest_pack not found"
    exit -1
fi

if [ -d $tmp_base ] ;then rm -rf $tmp_base; fi

mkdir -p $tmp_base
tar xf $latest_pack --no-same-owner -C $tmp_base 1> /dev/null
pushd $tmp_base
make preset
popd

if [ ! -d $dest_base ]
then
    echo "$dest_base not exists, creating ..."
    ln -s `pwd`/opt / 
fi

popd

