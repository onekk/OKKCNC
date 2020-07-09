#!/usr/bin/bash

cd ./OKKCNC/ &&
	echo "Launching OKKCNC from ${DIR}" ||
	echo "Launching local installation of OKKCNC"

#Launch

python3 -m OKKCNC $*
