# Environment deployer for Inuithy on board
# @author: Zex Li <top_zlynch@yahoo.com>
#

temp_templ='/tmp/teeth-deploy-XXXXXX'
deploy_log=/tmp/teeth-deploy.log

function deploy_cust()
{
    echo -e "\033[01;36m[Deploying customized packages on `hostname`]\033[00m"
    for pack in `find deploy/cust -regex ".*\.tar\..*"`; do
        echo -e "`date` \033[01;32m[$pack]\033[00m"
        temp=`mktemp -d $temp_templ`
        tar xf $pack -C$temp > /dev/null 2>> $deploy_log
        pushd $temp > /dev/null
        bash install.sh /media/card 1> /dev/null 2>> $deploy_log
        if [ ! -z $? ] ;then popd > /dev/null; echo "[ERR]: install $pack"  >> $deploy_log; exit -1; fi
        popd > /dev/null
        rm -rf $temp
    done
}

function deploy_py()
{
    echo -e "\033[01;36m[Deploying Python standard packages on `hostname`]\033[00m"
    for pack in `find deploy/pysetup -regex ".*\.tar\..*"`; do
        echo -e "`date` \033[01;32m[$pack]\033[00m"
        temp=`mktemp -d $temp_templ`
        tar xf $pack -C$temp > /dev/null 2>> $deploy_log
        pushd $temp/* > /dev/null
        python setup.py install 1> /dev/null 2>> $deploy_log
        if [ ! -z $? ] ;then popd > /dev/null; echo "[ERR]: install $pack"  >> $deploy_log; exit -1; fi
        popd > /dev/null
        rm -rf $temp
    done
}

function env_chk()
{
    pypy -c 'print(1)' &> /dev/null
    if [ ! -z $? ]; then extract_env; deploy_cust; fi
    pypy -c 'from enum import Enum' &> /dev/null
    if [ ! -z $? ]; then extract_env; deploy_py; fi
    pypy -c 'import paho.mqtt.client' &> /dev/null
    if [ ! -z $? ]; then extract_env; deploy_py; fi
    pypy -c 'import yaml' &> /dev/null
    if [ ! -z $? ]; then extract_env; deploy_py; fi
    pypy -c 'import serial' &> /dev/null
    if [ ! -z $? ]; then extract_env; deploy_py; fi
}

function extract_env()
{
    if [ ! -d deploy ]; then
        tar xf deploy_env.tar.bz2 > /dev/null 2>> $deploy_log
    fi
}
