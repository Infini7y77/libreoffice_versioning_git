#!/bin/sh
thisName=$(basename $0)
die(){ echo "$@" >&2; exit 1; }

usage(){
	echo "Usage: ${thisName} (clean-up | spruce-up | deploy | save [<msg>])"
}

flag_verbose=1
case "$1" in
	"--help"|"-h") usage; exit 0 ;;
	"--quiet"|"-q") flag_verbose=0; shift ;;
	-*) die "Error: Unknown Option: $1" ;;
esac

LOGDIR="$(dirname $0)/_logs"
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

clean_up(){
	logThis "Cleaning up directory"
	rm -I *.pyc >/dev/null 2>&1
	[ -e __pylint_report.txt ] && rm -I __pylint_*.txt
}

spruce_py(){
	logThis "Sprucing up, sweep..sweep..."
	for f in *.py; do
		#fixup those commas
		sed -i -e 's/,\b/, /g' -e "s/,'/, '/g" -e 's/,"/, "/g' "$f"
	done

	logThis " Pylint..er"
	pylint *.py > __pylint_report.txt 2> __pylint_errors.txt
}

deploy(){
	logThis "Deploying"
	cp -a $object_files "${install_dir}"
}

save_to_git(){
	logThis "Saving to Git repo"
	git add .
	[ -n "$commit_msg" ] && git commit -m "$commit_msg"
}

#----------------

case "$1" in
	"clean-up") clean_up ;;
	"spruce-up") spruce_py ;;
	"deploy") deploy ;;
	"save") commit_msg="$2"; shift; save_to_git ;;
	*) usage; die "Error: Unknown command: $1" ;;
esac
shift

exit 0
#eof
