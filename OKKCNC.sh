#!/usr/bin/env sh

#Autodetect python version
[ .$PYTHON = . ] && PYTHON=`which python2`
[ .$PYTHON = . ] && PYTHON=python

#Autodetect bCNC install
#If this script is placed in directory with OKKCNC module it will launch it
#When placed somewhere else (eg. /usr/bin) it will launch OKKCNC from system
DIR=`dirname $0`
[ -f "${DIR}"/OKKCNC/__main__.py ] && cd "${DIR}" &&
	echo "Launching OKKCNC from ${DIR}" ||
	echo "Launching local installation of OKKCNC"

#Launch
"$PYTHON" -m OKKCNC $*
