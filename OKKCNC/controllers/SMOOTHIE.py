# Smoothieboard motion controller plugin

from __future__ import absolute_import
from __future__ import print_function
from _GenericController import _GenericController
from _GenericController import STATUSPAT, POSPAT, TLOPAT, DOLLARPAT, SPLITPAT, VARPAT

import OCV
from CNC import CNC
import time


class Controller(_GenericController):
	def __init__(self, master):
		self.gcode_case = 1
		self.has_override = False
		self.master = master
		#print("smoothie loaded")

	def executeCommand(self, oline, line, cmd):
		if line[0] in ( "help", "version", "mem", "ls",
				"cd", "pwd", "cat", "rm", "mv",
				"remount", "play", "progress", "abort",
				"reset", "dfu", "break", "config-get",
				"config-set", "get", "set_temp", "get",
				"get", "net", "load", "save", "upload",
				"calc_thermistor", "thermistors", "md5sum",
				"fire", "switch"):
			if self.master.serial:
				self.master.serial_write(oline+"\n")
			return True
		return False

	def hardResetPre(self):
		self.master.serial_write("reset\n")

	def hardResetAfter(self):
		time.sleep(6)

	def viewBuild(self):
		self.master.serial_write("version\n")
		self.master.sendGCode("$I")

	def grblHelp(self):
		self.master.serial_write("help\n")

	def parseBracketAngle(self, line, cline):
		# <Idle|MPos:68.9980,-49.9240,40.0000,12.3456|WPos:68.9980,-49.9240,40.0000|F:12345.12|S:1.2>
		ln= line[1:-1] # strip off < .. >

		# split fields
		l= ln.split('|')

		# strip off status
		OCV.CD["state"]= l[0]

		# strip of rest into a dict of name: [values,...,]
		d= { a: [float(y) for y in b.split(',')] for a, b in [x.split(':') for x in l[1:]] }
		OCV.CD["mx"] = float(d['MPos'][0])
		OCV.CD["my"] = float(d['MPos'][1])
		OCV.CD["mz"] = float(d['MPos'][2])
		OCV.CD["wx"] = float(d['WPos'][0])
		OCV.CD["wy"] = float(d['WPos'][1])
		OCV.CD["wz"] = float(d['WPos'][2])
		OCV.CD["wcox"] = OCV.CD["mx"] - OCV.CD["wx"]
		OCV.CD["wcoy"] = OCV.CD["my"] - OCV.CD["wy"]
		OCV.CD["wcoz"] = OCV.CD["mz"] - OCV.CD["wz"]
		if 'F' in d:
		        OCV.CD["curfeed"] = float(d['F'][0])
		self.master._posUpdate = True

		# Machine is Idle buffer is empty
		# stop waiting and go on
		if self.master.sio_wait and not cline and l[0] not in ("Run","Jog", "Hold"):
		        self.master.sio_wait = False
		        self.master._gcount += 1

	def parseBracketSquare(self, line):
		pat = POSPAT.match(line)
		if pat:
			if pat.group(1) == "PRB":
				OCV.CD["prbx"] = float(pat.group(2))
				OCV.CD["prby"] = float(pat.group(3))
				OCV.CD["prbz"] = float(pat.group(4))
				#if self.running:
				self.master.gcode.probe.add(
					 OCV.CD["prbx"]
					+OCV.CD["wx"]
					-OCV.CD["mx"],
					 OCV.CD["prby"]
					+OCV.CD["wy"]
					-OCV.CD["my"],
					 OCV.CD["prbz"]
					+OCV.CD["wz"]
					-OCV.CD["mz"])
				self.master._probeUpdate = True
			OCV.CD[pat.group(1)] = \
				[float(pat.group(2)),
				 float(pat.group(3)),
				 float(pat.group(4))]
		else:
			pat = TLOPAT.match(line)
			if pat:
				OCV.CD[pat.group(1)] = pat.group(2)
				self.master._probeUpdate = True
			elif DOLLARPAT.match(line):
				OCV.CD["G"] = line[1:-1].split()
				CNC.updateG()
				self.master._gUpdate = True
