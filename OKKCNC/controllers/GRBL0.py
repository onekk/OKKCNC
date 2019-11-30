# GRBL <=0.9 motion controller plugin

from __future__ import absolute_import
from __future__ import print_function
from _GenericGRBL import _GenericGRBL
from _GenericController import STATUSPAT, POSPAT, TLOPAT, DOLLARPAT, SPLITPAT, VARPAT

import OCV
from CNC import CNC
import time


class Controller(_GenericGRBL):
    def __init__(self, master):
        self.gcode_case = 0
        self.has_override = False
        self.master = master
        #print("grbl0 loaded")

    def parseBracketAngle(self, line, cline):
        self.master.sio_status = False
        pat = STATUSPAT.match(line)
        if pat:
            if not OCV.s_alarm:
                OCV.c_state = pat.group(1)
            OCV.CD["mx"] = float(pat.group(2))
            OCV.CD["my"] = float(pat.group(3))
            OCV.CD["mz"] = float(pat.group(4))
            OCV.CD["wx"] = float(pat.group(5))
            OCV.CD["wy"] = float(pat.group(6))
            OCV.CD["wz"] = float(pat.group(7))
            OCV.CD["wcox"] = OCV.CD["mx"] - OCV.CD["wx"]
            OCV.CD["wcoy"] = OCV.CD["my"] - OCV.CD["wy"]
            OCV.CD["wcoz"] = OCV.CD["mz"] - OCV.CD["wz"]
            self.master._posUpdate = True
            if pat.group(1)[:4] != "Hold" and self.master._msg:
                self.master._msg = None

            # Machine is Idle buffer is empty
            # stop waiting and go on
            #print "<<< WAIT=",wait,sline,pat.group(1),sum(cline)
            #print ">>>", line
            if self.master.sio_wait and not cline and pat.group(1) not in ("Run", "Jog", "Hold"):
                #print ">>>",line
                self.master.sio_wait = False
                #print "<<< NO MORE WAIT"
                self.master._gcount += 1
            else:
                self.master.log.put((self.master.MSG_RECEIVE, line))

    def parseBracketSquare(self, line):
        pat = POSPAT.match(line)
        if pat:
            if pat.group(1) == "PRB":
                OCV.CD["prbx"] = float(pat.group(2))
                OCV.CD["prby"] = float(pat.group(3))
                OCV.CD["prbz"] = float(pat.group(4))

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
