#!/bin/sh
thisName=$(basename $0)
die(){ echo "$@" >&2; exit 1; }

usage(){
	echo "Usage: ${thisName} (deploy | save <msg>)"
}

flag_verbose=1
case "$1" in
	"--help"|"-h") usage; exit 0 ;;
	"--quiet"|"-q") flag_verbose=0; shift ;;
	-*) die "Error: Unknown Option: $1" ;;
esac

LOGDIR="$(dirname $0)/logs"
OUTLOG="${LOGDIR}/${thisName%.sh}.out.log"
[ -d "${LOGDIR}" ] || mkdir -p "${LOGDIR}"
[ -d "${LOGDIR}" ] || die "Error: Log directory dNE: ${LOGDIR}"
logThis(){ #argv: <msg>...
	echo "#$(date +%Y%m%d-%H%M%S)] $@" >> "${OUTLOG}"
}
pprint(){ #argv: [--log] <msg>
	[ "$1" == "--log" ] && shift && logThis "$@"
	[ $flag_verbose == 1 ] && echo -e "$@"
}

#----------------
object_files='git_versioning.py'
install_dir="${HOME}/.config/libreoffice/4-suse/user/Scripts/python/"

commit_msg=''

#----------------
deploy(){
	cp -a $object_files "${install_dir}"
}

save_to_git(){
	git commit -am $commit_msg
}

#----------------

case "$1" in
	"deploy") deploy ;;
	"save") commit_msg="$2"; shift; save_to_git ;;
	*) die "Error: Unknown command: $1" ;;
esac
shift



exit 0
#eof
