#!/bin/bash

#Show help
[ -z "$1" ] || [ "$1" = "-h" ] && {
	echo "
	Dummy GRBL simulator (allows connecting and streaming)

	Usage:
		$0 -h		#Show this help
		$0 /tmp/ttyFAKE	#Listen at fake serial port
	"
	exit
}

#Create fake tty device and listen on it
[ "$1" != "-c" ] && {
	echo Listening at fake serial port: "$1"
	#socat -dd PTY,raw,link="$1",echo=0 "EXEC:'$0' -c,pty,raw,echo=0"
	socat -ddd -ddd PTY,raw,echo=0 "EXEC:'python ./fake_grbl.py',pty,raw,echo=0"
	exit
	}
