#!/usr/bin/python
# -*- coding: ascii -*-
#
# Author: carlo.dormeletti@gmail.com
# Date: 26 Oct 2019
"""
Sender.py
"""

from __future__ import absolute_import
from __future__ import print_function

import os
import re
import sys
import glob
import traceback
import time
import threading
# import webbrowser
from datetime import datetime

import rexx

try:
    import serial
except ImportError:
    serial = None

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

import OCV
from CNC import WAIT, MSG, UPDATE, CNC, GCode
import Utils
import Pendant
#from _GenericGRBL import ERROR_CODES

#WIKI = "https://github.com/vlachoudis/bCNC/wiki"

SERIAL_POLL = 0.125
SERIAL_TIMEOUT = 0.10
G_POLL = 10
RX_BUFFER_SIZE = 128

GPAT = re.compile(r"[A-Za-z]\s*[-+]?\d+.*")
FEEDPAT = re.compile(r"^(.*)[fF](\d+\.?\d+)(.*)$")

CONNECTED = "Connected"
NOT_CONNECTED = "Not connected"

STATECOLORDEF = "LightYellow"  # Default color for unknown types?
STATECOLOR = {
    "Idle": "Yellow",
    "Run": "LightGreen",
    "Alarm": "Red",
    "Jog": "Green",
    "Home": "Green",
    "Check": "Magenta2",
    "Sleep": "LightBlue",
    "Hold": "Orange",
    "Hold:0": "Orange",
    "Hold:1": "OrangeRed",
    "Queue": "OrangeRed",
    "Door": "Red",
    "Door:0": "OrangeRed",
    "Door:1": "Red",
    "Door:2": "Red",
    "Door:3": "OrangeRed",
    CONNECTED: "Yellow",
    NOT_CONNECTED: "OrangeRed"
    }


class Sender(object):
    """OKKCNC Sender class"""
    # Messages types for log Queue
    MSG_BUFFER = 0  # write to buffer one command
    MSG_SEND = 1  # send message
    MSG_RECEIVE = 2  # receive message from controller
    MSG_OK = 3  # ok response from controller, move top most command to queue
    MSG_ERROR = 4  # error message or exception
    MSG_RUNEND = 5  # run ended
    MSG_CLEAR = 6  # clear buffer

    def __init__(self):
        self.history = []
        self._historyPos = None
        print("Init Sender > ", self)
        self.controllers = {}
        self.controllerLoad()
        self.controllerSet("GRBL1")

        CNC.loadConfig(Utils.config)
        self.gcode = GCode()
        self.cnc = self.gcode.cnc

        self.log = Queue()  # Log queue returned from GRBL
        self.queue = Queue()  # Command queue to be send to GRBL
        self.pendant = Queue()  # Command queue to be executed from Pendant
        self.serial = None
        self.thread = None

        self._posUpdate = False  # Update position
        self._probeUpdate = False  # Update probe
        self._gUpdate = False  # Update $G
        self._update = None  # Generic update

        self.running = False
        self.runningPrev = None
        self.cleanAfter = False
        self._runLines = 0
        self._quit = 0        # Quit counter to exit program
        OCV.s_stop = False   # Raise to stop current run
        OCV.s_stop_req = False  # Indicator that a stop is requested by user
        OCV.s_pause = False  # machine is on Hold
        OCV.s_alarm = True   # Display alarm message if true
        self._msg = None
        self._sumcline = 0
        self._lastFeed = 0
        self._newFeed = 0

        self._onStart = ""
        self._onStop = ""

    def controllerLoad(self):
        """Find plugins in the controllers directory and load them"""
        for f in glob.glob("{0}/controllers/*.py".format(Utils.prgpath)):
            name, ext = os.path.splitext(os.path.basename(f))
            if name[0] == '_':
                continue
            # print("Loaded motion controller plugin: %s"%(name))
            try:
                exec("import {0}".format(name))
                self.controllers[name] = eval(
                    "{format}.Controller(self)".format(name))
            except (ImportError, AttributeError):
                typ, val, tb = sys.exc_info()
                traceback.print_exception(typ, val, tb)


    def controllerList(self):
        #print("ctrlist")
        #self.controllers["GRBL1"].test()
        #if len(self.controllers.keys()) < 1: self.controllerLoad()
        return sorted(self.controllers.keys())

    def controllerSet(self, ctl):
        # print("Activating motion controller plugin: %s"%(ctl))
        if ctl in self.controllers.keys():
            self.controller = ctl
            OCV.CD["controller"] = ctl
            OCV.mcontrol = self.controllers[ctl]
            # OCV.mcontrol.test()

    def quit(self, event=None):
        self.saveConfig()
        Pendant.stop()

    def loadConfig(self):
        self.controllerSet(Utils.getStr("Connection", "controller"))
        Pendant.port = Utils.getInt("Connection", "pendantport", Pendant.port)
        GCode.LOOP_MERGE = Utils.getBool("File", "dxfloopmerge")
        self.loadHistory()

    def saveConfig(self):
        self.saveHistory()

    def loadHistory(self):
        try:
            f = open(Utils.hisFile, "r")
        except Exception:
            return
        self.history = [x.strip() for x in f]
        f.close()

    def saveHistory(self):
        try:
            f = open(Utils.hisFile, "w")
        except Exception:
            return
        f.write("\n".join(self.history))
        f.close()

    def evaluate(self, line):
        """
        Evaluate a line for possible expressions
        can return a python exception, needs to be catched
        """
        return self.gcode.evaluate(CNC.compileLine(line, True), self)

    def executeGcode(self, line):
        """
        Execute a line as gcode if pattern matches
        @return True on success
        False otherwise
        """
        if isinstance(line, tuple) or \
           line[0] in ("$", "!", "~", "?", "(", "@") or GPAT.match(line):
            self.sendGCode(line)
            return True
        return False

    def executeCommand(self, line):
        """Execute a single command"""

        #print
        #print "<<<",line
        #try:
        #    line = self.gcode.evaluate(CNC.compileLine(line,True))
        #except:
        #    return "Evaluation error", sys.exc_info()[1]
        #print ">>>",line

        if line is None:
            return

        oline = line.strip()
        line = oline.replace(",", " ").split()
        cmd = line[0].upper()

        # ABS*OLUTE: Set absolute coordinates
        if rexx.abbrev("ABSOLUTE", cmd, 3):
            self.sendGCode("G90")

        # HELP: open browser to display help
        elif cmd == "HELP":
            self.help()

        # HOME: perform a homing cycle
        elif cmd == "HOME":
            OCV.mcontrol.home()

        # LO*AD [filename]: load filename containing g-code
        elif rexx.abbrev("LOAD", cmd, 2):
            self.load(line[1])

        # OPEN: open serial connection to grbl
        # CLOSE: close serial connection to grbl
        elif cmd in ("OPEN", "CLOSE"):
            OCV.application.openClose()

        # QU*IT: quit program
        # EX*IT: exit program
        elif rexx.abbrev("QUIT", cmd, 2) or rexx.abbrev("EXIT", cmd, 2):
            self.quit()

        # PAUSE: pause cycle
        elif cmd == "PAUSE":
            self.pause()

        # RESUME: resume
        elif cmd == "RESUME":
            self.resume()

        # FEEDHOLD: feedhold
        elif cmd == "FEEDHOLD":
            OCV.mcontrol.feedHold(None)

        # REL*ATIVE: switch to relative coordinates
        elif rexx.abbrev("RELATIVE", cmd, 3):
            self.sendGCode("G91")

        # RESET: perform a soft reset to grbl
        elif cmd == "RESET":
            OCV.mcontrol.softReset(True)

        # RUN: run g-code
        elif cmd == "RUN":
            OCV.application.run()

        # SAFE [z]: safe z to move
        elif cmd == "SAFE":
            try:
                OCV.CD["safe"] = float(line[1])
            except Exception:
                pass

            OCV.application.statusbar["text"] = "Safe Z= {0:.4f}".format(
                OCV.CD["safe"])

        # SA*VE [filename]: save to filename or to default name
        elif rexx.abbrev("SAVE", cmd, 2):
            if len(line) > 1:
                self.save(line[1])
            else:
                self.saveAll()

        # SENDHEX: send a hex-char in grbl
        elif cmd == "SENDHEX":
            self.sendHex(line[1])

        # SET [x [y [z]]]: set x,y,z coordinates to current workspace
        elif cmd == "SET":
            try:
                x = float(line[1])
            except Exception:
                x = None

            try:
                y = float(line[2])
            except Exception:
                y = None

            try:
                z = float(line[3])
            except Exception:
                z = None

            OCV.mcontrol.wcs_set(x, y, z)

        elif cmd == "SET0":
            OCV.mcontrol.wcs_set(0., 0., 0.)

        elif cmd == "SETX":
            try:
                x = float(line[1])
            except Exception:
                x = 0.0

            OCV.mcontrol.wcs_set(x, None, None)

        elif cmd == "SETY":
            try:
                y = float(line[1])
            except Exception:
                y = 0.0

            OCV.mcontrol.wcs_set(None, y, None)

        elif cmd == "SETZ":
            try:
                z = float(line[1])
            except Exception:
                z = 0.0

            OCV.mcontrol.wcs_set(None, None, z)

        # STOP: stop current run
        elif cmd == "STOP":
            self.stopRun()

        # UNL*OCK: unlock grbl
        elif rexx.abbrev("UNLOCK", cmd, 3):
            OCV.mcontrol.unlock(True)

        # Send commands to SMOOTHIE
        elif OCV.mcontrol.executeCommand(oline, line, cmd):
            pass

        else:
            return _("unknown command"), _("Invalid command {0}").format(oline)

    def help(self, event=None):
        pass
        # webbrowser.open(WIKI,new=2)

    def loadRecent(self, recent):
        filename = Utils.getRecent(recent)

        if filename is None:
            return

        self.load(filename)

    def _loadRecent0(self, event):
        self.loadRecent(0)

    def _loadRecent1(self, event):
        self.loadRecent(1)

    def _loadRecent2(self, event):
        self.loadRecent(2)

    def _loadRecent3(self, event):
        self.loadRecent(3)


    def _loadRecent4(self, event):
        self.loadRecent(4)


    def _loadRecent5(self, event):
        self.loadRecent(5)


    def _loadRecent6(self, event):
        self.loadRecent(6)


    def _loadRecent7(self, event):
        self.loadRecent(7)


    def _loadRecent8(self, event):
        self.loadRecent(8)


    def _loadRecent9(self, event):
        self.loadRecent(9)


    def _saveConfigFile(self, filename=None):
        if filename is None:
            filename = self.gcode.filename
        Utils.setUtf("File", "dir", os.path.dirname(os.path.abspath(filename)))
        Utils.setUtf("File", "file", os.path.basename(filename))
        Utils.setUtf("File", "probe", os.path.basename(self.gcode.probe.filename))


    def load(self, filename):
        """Load a file into editor"""
        fn, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == ".probe":
            if filename is not None:
                self.gcode.probe.filename = filename
                self._saveConfigFile()
            self.gcode.probe.load(filename)
        elif ext == ".orient":
            # save orientation file
            self.gcode.orient.load(filename)
        else:
            self.gcode.load(filename)
            self._saveConfigFile()
        Utils.addRecent(filename)


    def save(self, filename):
        fn, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == ".probe" or ext == ".xyz":
            # save probe
            if not self.gcode.probe.isEmpty():
                self.gcode.probe.save(filename)
            if filename is not None:
                self._saveConfigFile()
        elif ext == ".orient":
            # save orientation file
            return self.gcode.orient.save(filename)
        elif ext == ".txt":
            # save gcode as txt (only enabled blocks and no OKKCNC metadata)
            return self.gcode.saveTXT(filename)
        else:
            if filename is not None:
                self.gcode.filename = filename
                self._saveConfigFile()
            Utils.addRecent(self.gcode.filename)
            return self.gcode.save()

    def saveAll(self, event=None):
        if self.gcode.filename:
            self.save(self.gcode.filename)
            if self.gcode.probe.filename:
                self.save(self.gcode.probe.filename)
        return "break"

    def serial_write(self, data):
        """Serial write"""

        try:
            ret = self.serial.write(data.encode('ascii'))
        except UnicodeEncodeError:
            print("s_write string > ", data)

        return ret


    def serial_write_byte(self, data):
        """Serial write a byte character > 128 decimal"""

        if OCV.COM_DEBUG is True:
            print("s_write byte > ", data)
            #print("s_write type > ", type(data))

        ret = self.serial.write(data)
        return ret


    # Open serial port

    def open(self, device, baudrate):
        #self.serial = serial.Serial(
        self.serial = serial.serial_for_url(
            device.replace('\\', '\\\\'), #Escape for windows
            baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=SERIAL_TIMEOUT,
            xonxoff=False,
            rtscts=False)
        # Toggle DTR to reset Arduino
        try:
            self.serial.setDTR(0)
        except IOError:
            pass
        time.sleep(1)
        OCV.c_state = CONNECTED
        OCV.CD["color"] = STATECOLOR[OCV.c_state]
        #self.state.config(text=OCV.c_state,
        #        background=OCV.CD["color"])
        # toss any data already received, see
        # http://pyserial.sourceforge.net/pyserial_api.html#serial.Serial.flushInput
        self.serial.flushInput()
        try:
            self.serial.setDTR(1)
        except IOError:
            pass
        time.sleep(1)
        self.serial_write("\n\n")
        self._gcount = 0
        OCV.s_alarm = True
        self.thread = threading.Thread(target=self.serialIO)
        self.thread.start()
        return True

    def close(self):
        """Close serial port"""
        if self.serial is None:
            return

        try:
            self.stopRun()
        except Exception:
            pass

        self._runLines = 0
        self.thread = None
        time.sleep(1)

        try:
            self.serial.close()
        except Exception:
            pass

        self.serial = None
        OCV.c_state = NOT_CONNECTED
        OCV.CD["color"] = STATECOLOR[OCV.c_state]

    def sendGCode(self, cmd):
        """
        Send to controller a gcode or command
        WARNING: it has to be a single line!
        """
        if self.serial and not self.running:

            if OCV.COM_DEBUG is True:
                print("Cmd      > ", cmd)
                print("Cmd type > ", type(cmd))

            if isinstance(cmd, tuple):
                self.queue.put(cmd)
            else:
                self.queue.put(cmd + "\n")

    def sendHex(self, hexcode):
        if self.serial is None:
            return

        self.serial_write(chr(int(hexcode, 16)))
        self.serial.flush()

    def resume(self):
        but = OCV.RUN_GROUP.frame.nametowidget("run_pause")
        but.config(background=OCV.BACKGROUND)
        OCV.mcontrol.resume(None)

    def pause(self):
        but = OCV.RUN_GROUP.frame.nametowidget("run_pause")
        but.config(background=STATECOLOR["Hold:0"])
        OCV.mcontrol.pause(None)

    def emptyQueue(self):
        while self.queue.qsize() > 0:
            try:
                self.queue.get_nowait()
            except Empty:
                break

    def stopProbe(self):
        if self.gcode.probe.start:
            self.gcode.probe.clear()

    def getBufferFill(self):
        return self._sumcline * 100. / RX_BUFFER_SIZE

    def initRun(self):
        self._quit = 0
        OCV.s_pause = False
        self._paths = None
        self.running = True
        OCV.application.disable()
        self.emptyQueue()
        time.sleep(1)

    def runEnded(self):
        """Called when run is finished"""
        if self.running:
            self.log.put((Sender.MSG_RUNEND, _("Run ended")))

            self.log.put((Sender.MSG_RUNEND, str(OCV.CD["msg"])))
            if self._onStop:
                try:
                    os.system(self._onStop)
                except:
                    pass
        self._runLines = 0
        self._quit = 0
        self._msg = None

        if OCV.s_pause is True:
            OCV.s_pause = False
            but = OCV.RUN_GROUP.frame.nametowidget("run_pause")
            but.config(background=OCV.BACKGROUND)

        if OCV.s_stop_req is True:
            OCV.s_stop_req = False
            but = OCV.RUN_GROUP.frame.nametowidget("run_stop")
            but.config(background=OCV.BACKGROUND)

        self.running = False
        OCV.CD["running"] = False
        OCV.s_stop = False

    def stopRun(self, event=None):
        """Stop the current run"""
        OCV.mcontrol.feedHold(None)
        self.log.put((Sender.MSG_RUNEND, "Stop Requested: " + str(datetime.now())))
        but = OCV.RUN_GROUP.frame.nametowidget("run_stop")
        but.config(background=STATECOLOR["Hold:0"])
        OCV.s_stop_req = True
        print("Controller state", OCV.c_state)
        if OCV.c_state == "Hold:0":
            if OCV.s_stop_req is True:
                self.running = False
                self.runEnded()
                self.jobDone()

    def jobDone(self):
        """
        This should be called everytime that milling of g-code file is finished
        So we can purge the controller for the next job
        See https://github.com/vlachoudis/bCNC/issues/1035
        """
        if OCV.COM_DEBUG is True:
            print(
                "Job done. Purging the controller. (Running: {0})".format(
                    self.running))
        OCV.mcontrol.purgeController()

    def controllerStateChange(self, state):
        """
        This is called everytime that motion controller changes the state
        YOU SHOULD PASS ONLY REAL HW STATE TO THIS, NOT ONEKKCNC STATE
        Right now the primary idea is to detect when job stopped running
        """
        if OCV.COM_DEBUG is True:
            print(
                "Controller state changed to: {0} (Running: {1})".format(
                    state,
                    self.running))

        if state in ("Idle",):
            OCV.mcontrol.viewParameters()
            OCV.mcontrol.viewState()

        if self.cleanAfter is True and self.running is False and \
                state in ("Idle",):
            self.cleanAfter = False
            self.jobDone()

    def serialIO(self):
        """thread performing I/O on serial line"""
        # wait for commands to complete (status change to Idle)
        self.sio_wait = False
        # waiting for status <...> report
        self.sio_status = False
        cline = []  # length of pipeline commands
        sline = []  # pipeline commands
        tosend = None  # next string to send
        tr = tg = time.time()  # last time a ? or $G was send to grbl

        while self.thread:
            t = time.time()
            # refresh machine position?
            if t-tr > SERIAL_POLL:
                OCV.mcontrol.viewStatusReport()
                tr = t

                # If Override change, attach feed
                if OCV.CD["_OvChanged"]:
                    OCV.mcontrol.overrideSet()

            # Fetch new command to send if...
            if tosend is None and not self.sio_wait and \
                    not OCV.s_pause and self.queue.qsize() > 0:

                try:
                    tosend = self.queue.get_nowait()
                    # print( "+++",repr(tosend))
                    if isinstance(tosend, tuple):
                        # print "gcount tuple=",self._gcount
                        # wait to empty the grbl buffer and status is Idle
                        if tosend[0] == WAIT:
                            # Don't count WAIT until we are idle!
                            self.sio_wait = True
#                            print "+++ WAIT ON"
#                            print "gcount=",self._gcount, self._runLines
                        elif tosend[0] == MSG:
                            # Count executed commands as well
                            self._gcount += 1
                            if tosend[1] is not None:
                                # show our message on machine status
                                self._msg = tosend[1]
                        elif tosend[0] == UPDATE:
                            # Count executed commands as well
                            self._gcount += 1
                            self._update = tosend[1]
                        else:
                            # Count executed commands as well
                            self._gcount += 1
                        tosend = None

                    elif not isinstance(tosend, str):
                        try:
                            tosend = self.gcode.evaluate(tosend)
#                            if isinstance(tosend, list):
#                                cline.append(len(tosend[0]))
#                                sline.append(tosend[0])
                            if isinstance(tosend, str):
                                tosend += "\n"
                            else:
                                # Count executed commands as well
                                self._gcount += 1
#                                print "gcount str=",self._gcount
#                            print( "+++ eval=",repr(tosend),type(tosend))
                        except:
                            for s in str(sys.exc_info()[1]).splitlines():
                                self.log.put((Sender.MSG_ERROR, s))
                            self._gcount += 1
                            tosend = None
                except Empty:
                    break

                if tosend is not None:
                    # All modification in tosend should be
                    # done before adding it to cline

                    # Keep track of last feed
                    pat = FEEDPAT.match(str(tosend))
                    if pat is not None:
                        self._lastFeed = pat.group(2)

                    # Modify sent g-code to reflect overrided feed
                    # for controllers without override support
                    if not OCV.mcontrol.has_override:
                        if OCV.CD["_OvChanged"]:
                            OCV.CD["_OvChanged"] = False
                            self._newFeed = float(
                                self._lastFeed)*OCV.CD["_OvFeed"]/100.0
                            if pat is None and self._newFeed != 0 \
                               and not tosend.startswith("$"):
                                tosend = "f{0:f}{1}".format(
                                    self._newFeed,
                                    tosend)

                        # Apply override Feed
                        if OCV.CD["_OvFeed"] != 100 and self._newFeed != 0:
                            pat = FEEDPAT.match(tosend)
                            if pat is not None:
                                try:
                                    tosend = "{0}f{1:f}{2}\n".format(
                                        pat.group(1),
                                        self._newFeed,
                                        pat.group(3))
                                except:
                                    pass

                    # Bookkeeping of the buffers
                    sline.append(tosend)
                    cline.append(len(tosend))

            # Anything to receive?
            if self.serial.inWaiting() or tosend is None:
                try:
                    line = str(self.serial.readline().decode()).strip()
#                    print("Received line > ", line)
                except:
                    self.log.put((Sender.MSG_RECEIVE, str(sys.exc_info()[1])))
                    self.emptyQueue()
                    self.close()
                    return
#                print ("<R<",repr(line))
#                print ("*-* stack=",sline,"sum=",sum(cline),"pause=",OCV.s_pause)
                if not line:
                    pass
                elif OCV.mcontrol.parseLine(line, cline, sline):
                    pass
                else:
                    self.log.put((Sender.MSG_RECEIVE, line))

            # Received external message to stop
            if OCV.s_stop:
                self.emptyQueue()
                tosend = None
                self.log.put((Sender.MSG_CLEAR, ""))
                # WARNING if runLines == maxint then it means we are
                # still preparing/sending lines from from OKKCNC.run(),
                # so don't stop
                if self._runLines != sys.maxsize:
                    OCV.s_stop = False

#            print "tosend='%s'"%(repr(tosend)),"stack=",sline,
#                "sum=",sum(cline),"wait=",wait,"pause=",OCV.s_pause
            if tosend is not None and sum(cline) < RX_BUFFER_SIZE:
                self._sumcline = sum(cline)
#                if isinstance(tosend, list):
#                    self.serial_write(str(tosend.pop(0)))
#                    if not tosend: tosend = None

#                print ">S>",repr(tosend),"stack=",sline,"sum=",sum(cline)
                if OCV.mcontrol.gcode_case > 0:
                    tosend = tosend.upper()

                if OCV.mcontrol.gcode_case < 0:
                    tosend = tosend.lower()

                self.serial_write(tosend)

                self.log.put((Sender.MSG_BUFFER, tosend))

                tosend = None
                if not self.running and t-tg > G_POLL:
                    tosend = "$G\n"  # FIXME: move to controller specific class
                    sline.append(tosend)
                    cline.append(len(tosend))
                    tg = t
