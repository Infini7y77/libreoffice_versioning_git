#!/bin/sh
thisName=$(basename $0)
die(){ echo "$@" >&2; exit 1; }

usage(){
	echo "Usage: ${thisName} (spruce-up | clean | save [<msg>] | deploy)"
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
clean_reports=''
#----------------

clean_reports="${clean_reports} pylint"
pylint_er(){
	logThis " Pylint..er"
	local _app="pylint"
	[ -x "/usr/bin/${_app}" ] && ${_app} *.py > __${_app}_report.txt 2> __${_app}_errors.txt
}

lint__fix_up_commas(){
	logThis "Fixing comma spaces"
	for f in *.py; do
		sed -i -e 's/,\b/, /g' -e "s/,'/, '/g" -e 's/,"/, "/g' "$f"
	done
}

lint__tabs_to_spaces(){
	logThis "Tabs to Spaces"
	for f in *.py; do
		sed -e 's/\t/    /g' "$f" > "${f}__no-tabs.tmp"
	done
}

clean_reports="${clean_reports} pyflakes"
pyflakes_er(){
	logThis "Pyflakes..er"
	local _app="pyflakes"
	[ -x "/usr/bin/${_app}" ] && ${_app} *.py > __${_app}_report.txt 2> __${_app}_errors.txt
}

spruce_up(){
	logThis "Sprucing up, sweep..sweep..."
	lint__fix_up_commas
	#lint__tabs_to_spaces
	pylint_er
	pyflakes_er
}

clean_up(){
	logThis "Cleaning up directory"
	rm -I *.pyc >/dev/null 2>&1
	rm -I *.tmp >/dev/null 2>&1
	for item in $clean_reports; do
		[ -e "__${item}_report.txt" ] && rm -I __${item}_*.txt
	done
}

save_to_git(){
	logThis "Saving to Git repo"
	git add .
	[ -n "$commit_msg" ] && git commit -m "$commit_msg"
}

deploy(){
	logThis "Deploying"
	#TODO: Check if dst is older than src
	for f in $object_files; do
		cp -a "$f" "${install_dir}"
	done
}

#----------------

#while [ $# -gt 0 ]; do
case "$1" in
	"spruce-up") spruce_up ;;
	"no-tabs") lint__tabs_to_spaces ;;
	"pylint") pylint_er ;;
	"pyflakes") pyflakes_er ;;
	#
	"clean") clean_up ;;
	"save") commit_msg="$2"; shift; save_to_git ;;
	"deploy") deploy ;;
	*) usage; die "Error: Unknown command: $1" ;;
esac
shift
#done

exit 0
#eof
