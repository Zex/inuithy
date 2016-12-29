# Installer for Inuithy Agent - AUTO GENERATED ON Thu Dec 29 19:12:00 CST 2016

pack_base=..
srcs="$pack_base/deploy_env.tar.bz2 tools/deploy_on_board.sh $pack_base/inuithy-0.1.a29b4d8.tar.bz2"
if [ 1 -gt $# ];then echo No hosts given; exit 0; fi
dests=$@
for dest in $dests; do
	echo -e "[01;31m[Sending to $dest][00m"
	ssh root@$dest "cd /media/card/;rm -rf deploy deploy_env.tar.bz2 deploy_on_board.sh inuithy-0.1.a29b4d8.tar.bz2"
	scp -r $srcs root@$dest:/media/card
	echo -e "[01;34m[Deploying Inuithy on $dest][00m"
	ssh root@$dest /media/card/deploy_on_board.sh
done
