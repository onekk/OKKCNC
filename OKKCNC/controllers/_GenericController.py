# Generic motion controller definition
# All controller plugins inherit features from this one

from __future__ import absolute_import
from __future__ import print_function

from tkinter.constants import END

import OCV
from CNC import CNC, WCS
import time
import re

STATUSPAT = re.compile(r"^<(\w*?),MPos:([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),WPos:([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),?(.*)>$")
POSPAT      = re.compile(r"^\[(...):([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),([+\-]?\d*\.\d*):?(\d*)\]$")
TLOPAT      = re.compile(r"^\[(...):([+\-]?\d*\.\d*)\]$")
DOLLARPAT = re.compile(r"^\[G\d* .*\]$")
SPLITPAT  = re.compile(r"[:,]")
VARPAT    = re.compile(r"^\$(\d+)=(\d*\.?\d*) *\(?.*")



class _GenericController:

    line_sent = 0

    def test(self):
        print("test supergen")

    def executeCommand(self, oline, line, cmd):
        return False

    def hardResetPre(self):
        pass

    def hardResetAfter(self):
        pass

    def viewStartup(self):
        pass

    def checkGcode(self):
        pass

    def viewSettings(self):
        pass

    def grblRestoreSettings(self):
        pass

    def grblRestoreWCS(self):
        pass

    def grblRestoreAll(self):
        pass

    def purgeControllerExtra(self):
        pass

    def overrideSet(self):
        pass

    def hardReset(self):
        self.master.busy()
        if self.master.serial is not None:
            self.hardResetPre()
            self.master.openClose()
            self.hardResetAfter()
        self.master.openClose()
        self.master.stopProbe()
        self.master._alarm = False
        OCV.CD["_OvChanged"] = True    # force a feed change if any
        self.master.notBusy()

    #----------------------------------------------------------------------
    def softReset(self, clearAlarm=True):
        if self.master.serial:
            self.master.serial.write(b"\030")
        self.master.stopProbe()
        if clearAlarm: self.master._alarm = False
        OCV.CD["_OvChanged"] = True    # force a feed change if any

    #----------------------------------------------------------------------
    def unlock(self, clearAlarm=True):
        if clearAlarm: self.master._alarm = False
        self.master.sendGCode("$X")

    #----------------------------------------------------------------------
    def home(self, event=None):
        self.master._alarm = False
        self.master.sendGCode("$H")

    def viewStatusReport(self):
        self.master.serial.write(b"?")
        self.master.sio_status = True

    def viewParameters(self):
        self.master.sendGCode("$#")

    def viewState(self): #Maybe rename to viewParserState() ???
        self.master.sendGCode("$G")

    #----------------------------------------------------------------------
    def jog(self, dir):
        #print("jog",dir)
        self.master.sendGCode("G91G0{0}".format(dir))
        self.master.sendGCode("G90")

    #----------------------------------------------------------------------
    def goto(self, x=None, y=None, z=None):
        cmd = "G90G0"
        if x is not None: cmd += "X{0:0.{1}f}".format(x, OCV.digits)
        if y is not None: cmd += "Y{0:0.{1}f}".format(y, OCV.digits)
        if z is not None: cmd += "Z{0:0.{1}f}".format(z, OCV.digits)
        self.master.sendGCode("{0}".format(cmd))

    #----------------------------------------------------------------------
    def _wcsSet(self, x, y, z):
        p = WCS.index(OCV.CD["WCS"])
        if p<6:
            cmd = "G10L20P{0:d}".format(p+1)
        elif p==6:
            cmd = "G28.1"
        elif p==7:
            cmd = "G30.1"
        elif p==8:
            cmd = "G92"

        pos = ""
        if x is not None and abs(float(x))<10000.0: pos += "X"+str(x)
        if y is not None and abs(float(y))<10000.0: pos += "Y"+str(y)
        if z is not None and abs(float(z))<10000.0: pos += "Z"+str(z)
        cmd += pos
        self.master.sendGCode(cmd)
        self.viewParameters()
        self.master.event_generate("<<Status>>",
            data=(_("Set workspace {0} to {1}").format(WCS[p],pos)))
            #data=(_("Set workspace %s to %s")%(WCS[p],pos)).encode("utf8"))
        self.master.event_generate("<<CanvasFocus>>")

    #----------------------------------------------------------------------
    def feedHold(self, event=None):
        if event is not None and not self.master.acceptKey(True): return
        if self.master.serial is None: return
        self.master.serial.write(b"!")
        self.master.serial.flush()
        self.master._pause = True

    #----------------------------------------------------------------------
    def resume(self, event=None):
        if event is not None and not self.master.acceptKey(True): return
        if self.master.serial is None: return
        self.master.serial.write(b"~")
        self.master.serial.flush()
        self.master._msg   = None
        self.master._alarm = False
        self.master._pause = False

    #----------------------------------------------------------------------
    def pause(self, event=None):
        if self.master.serial is None: return
        if self.master._pause:
            self.master.resume()
        else:
            self.master.feedHold()

    #----------------------------------------------------------------------
    # Purge the buffer of the controller. Unfortunately we have to perform
    # a reset to clear the buffer of the controller
    #---------------------------------------------------------------------
    def purgeController(self):
        self.master.serial.write(b"!")
        self.master.serial.flush()
        time.sleep(1)
        # remember and send all G commands
        G = " ".join([x for x in OCV.CD["G"] if x[0]=="G"])    # remember $G
        TLO = OCV.CD["TLO"]
        self.softReset(False)            # reset controller
        self.purgeControllerExtra()
        self.master.runEnded()
        self.master.stopProbe()
        if G: self.master.sendGCode(G)            # restore $G
        self.master.sendGCode("G43.1Z{0}".format(TLO))    # restore TLO
        self.viewState()


    #----------------------------------------------------------------------
    def parseLine(self, line, cline, sline):
        if not line:
            return True

        elif line[0]=="<":
            if not self.master.sio_status:
                self.master.log.put((self.master.MSG_RECEIVE, line))
            else:
                self.parseBracketAngle(line, cline)

        elif line[0]=="[":
            self.master.log.put((self.master.MSG_RECEIVE, line))
            self.parseBracketSquare(line)

        elif "error:" in line or "ALARM:" in line:
            self.master.log.put((self.master.MSG_ERROR, line))
            self.master._gcount += 1
            #print "gcount ERROR=",self._gcount
            if cline: del cline[0]
            if sline: OCV.CD["errline"] = sline.pop(0)
            if not self.master._alarm: self.master._posUpdate = True
            self.master._alarm = True
            OCV.CD["state"] = line
            if self.master.running:
                self.master._stop = True

        elif line.find("ok")>=0:
            self.master.log.put((self.master.MSG_OK, line))
            self.master._gcount += 1
            if cline: del cline[0]
            if sline:
                #print (">",sline[0],"<")
                if sline[0].strip() not in ("$G","$#"):
                    ldesc = "{0:4s} > {1}".format(
                            str(self.line_sent),
                            sline[0].strip())
                    self.line_sent += 1
                    self.master.proc_line.set(ldesc)

                del sline[0]


        elif line[0] == "$":
            self.master.log.put((self.master.MSG_RECEIVE, line))
            pat = VARPAT.match(line)
            if pat:
                OCV.CD["grbl_{0}".format(pat.group(1))] = pat.group(2)

        elif line[:4]=="Grbl" or line[:13]=="CarbideMotion": # and self.running:
            #tg = time.time()
            self.master.log.put((self.master.MSG_RECEIVE, line))
            self.master._stop = True
            del cline[:] # After reset clear the buffer counters
            del sline[:]
            OCV.CD["version"] = line.split()[1]
            # Detect controller
            if self.master.controller in ("GRBL0", "GRBL1"):
                self.master.controllerSet("GRBL{0:d}".format(int(OCV.CD["version"][0])))

        else:
            #We return false in order to tell that we can't parse this line
            #Sender will log the line in such case
            return False

        #Parsing succesfull
        return True
