# GRBL 1.0+ motion controller plugin

from __future__ import absolute_import
from __future__ import print_function

import OCV
from _GenericGRBL import _GenericGRBL
from _GenericController import STATUSPAT, POSPAT, TLOPAT, DOLLARPAT, SPLITPAT, VARPAT

from CNC import CNC
# import time

# Extended override commands
OV_FEED_100 = b'\x90'
OV_FEED_i10 = b'\x91'
OV_FEED_d10 = b'0x92'
OV_FEED_i1 = b'0x93'
OV_FEED_d1 = b'0x94'

OV_RAPID_100 = b'0x95'
OV_RAPID_50 = b'0x96'
OV_RAPID_25 = b'0x97'

OV_SPINDLE_100 = b'0x99'
OV_SPINDLE_i10 = b'0x9A'
OV_SPINDLE_d10 = b'0x9B'
OV_SPINDLE_i1 = b'0x9C'
OV_SPINDLE_d1 = b'0x9D'

OV_SPINDLE_STOP = b'0x9E'

OV_FLOOD_TOGGLE = b'0xA0'
OV_MIST_TOGGLE = b'0xA1'

W_MSG1 = "Garbage receive {0}: {1}"


class Controller(_GenericGRBL):
    def __init__(self, master):
        self.gcode_case = 0
        self.has_override = True
        self.master = master
        # print("grbl1 loaded")

    def jog(self, move):
        self.master.sendGCode("$J=G91 {0} F100000".format(move))

    def overrideSet(self):
        OCV.CD["_OvChanged"] = False  # Temporary
        # Check feed
        diff = OCV.CD["_OvFeed"] - OCV.CD["OvFeed"]
        if diff == 0:
            pass
        elif OCV.CD["_OvFeed"] == 100:
            self.master.serial_write_byte(OV_FEED_100)
        elif diff >= 10:
            self.master.serial_write_byte(OV_FEED_i10)
            OCV.CD["_OvChanged"] = diff > 10
        elif diff <= -10:
            self.master.serial_write_byte(OV_FEED_d10)
            OCV.CD["_OvChanged"] = diff < -10
        elif diff >= 1:
            self.master.serial_write_byte(OV_FEED_i1)
            OCV.CD["_OvChanged"] = diff > 1
        elif diff <= -1:
            self.master.serial_write_byte(OV_FEED_d1)
            OCV.CD["_OvChanged"] = diff < -1
        # Check rapid
        target = OCV.CD["_OvRapid"]
        current = OCV.CD["OvRapid"]
        if target == current:
            pass
        elif target == 100:
            self.master.serial_write_byte(OV_RAPID_100)
        elif target == 75:
            # FIXME: GRBL protocol does not specify 75% override
            # command at all
            self.master.serial_write_byte(OV_RAPID_50)
        elif target == 50:
            self.master.serial_write_byte(OV_RAPID_50)
        elif target == 25:
            self.master.serial_write_byte(OV_RAPID_25)
        # Check Spindle
        diff = OCV.CD["_OvSpindle"] - OCV.CD["OvSpindle"]
        if diff == 0:
            pass
        elif OCV.CD["_OvSpindle"] == 100:
            self.master.serial_write_byte(OV_SPINDLE_100)
        elif diff >= 10:
            self.master.serial_write_byte(OV_SPINDLE_i10)
            OCV.CD["_OvChanged"] = diff > 10
        elif diff <= -10:
            self.master.serial_write_byte(OV_SPINDLE_d10)
            OCV.CD["_OvChanged"] = diff < -10
        elif diff >= 1:
            self.master.serial_write_byte(OV_SPINDLE_i1)
            OCV.CD["_OvChanged"] = diff > 1
        elif diff <= -1:
            self.master.serial_write_byte(OV_SPINDLE_d1)
            OCV.CD["_OvChanged"] = diff < -1

    def parseBracketAngle(self, line, cline):
        self.master.sio_status = False
        fields = line[1:-1].split("|")
        OCV.CD["pins"] = ""

        # Report if state has changed
        if OCV.c_state != fields[0] or OCV.s_runningPrev != OCV.s_running:
            self.master.controllerStateChange(fields[0])
        OCV.s_runningPrev = OCV.s_running
        OCV.c_state = fields[0]

        for field in fields[1:]:
            word = SPLITPAT.split(field)
            if word[0] == "MPos":
                try:
                    OCV.CD["mx"] = float(word[1])
                    OCV.CD["my"] = float(word[2])
                    OCV.CD["mz"] = float(word[3])
                    OCV.CD["wx"] = round(OCV.CD["mx"]-OCV.CD["wcox"], OCV.digits)
                    OCV.CD["wy"] = round(OCV.CD["my"]-OCV.CD["wcoy"], OCV.digits)
                    OCV.CD["wz"] = round(OCV.CD["mz"]-OCV.CD["wcoz"], OCV.digits)
                    self.master._posUpdate = True
                except (ValueError,IndexError):
                    OCV.c_state = W_MSG1.format(word[0], line)
                    self.master.log.put((self.master.MSG_RECEIVE, OCV.c_state))
                    break
            elif word[0] == "F":
                try:
                    OCV.CD["curfeed"] = float(word[1])
                except (ValueError, IndexError):
                    OCV.c_state = W_MSG1.format(word[0], line)
                    self.master.log.put((self.master.MSG_RECEIVE, OCV.c_state))
                    break
            elif word[0] == "FS":
                try:
                    OCV.CD["curfeed"]    = float(word[1])
                    OCV.CD["curspindle"] = float(word[2])
                except (ValueError, IndexError):
                    OCV.c_state = W_MSG1.format(word[0], line)
                    self.master.log.put((self.master.MSG_RECEIVE, OCV.c_state))
                    break
            elif word[0] == "Bf":
                try:
                    OCV.CD["planner"] = int(word[1])
                    OCV.CD["rxbytes"] = int(word[2])
                except (ValueError, IndexError):
                    OCV.c_state = W_MSG1.format(word[0], line)
                    self.master.log.put((self.master.MSG_RECEIVE, OCV.c_state))
                    break
            elif word[0] == "Ov":
                try:
                    OCV.CD["OvFeed"]    = int(word[1])
                    OCV.CD["OvRapid"]   = int(word[2])
                    OCV.CD["OvSpindle"] = int(word[3])
                except (ValueError, IndexError):
                    OCV.c_state = W_MSG1.format(word[0], line)
                    self.master.log.put((self.master.MSG_RECEIVE, OCV.c_state))
                    break
            elif word[0] == "WCO":
                try:
                    OCV.CD["wcox"] = float(word[1])
                    OCV.CD["wcoy"] = float(word[2])
                    OCV.CD["wcoz"] = float(word[3])
                except (ValueError,IndexError):
                    OCV.c_state = W_MSG1.format(word[0],line)
                    self.master.log.put((self.master.MSG_RECEIVE, OCV.c_state))
                    break
            elif word[0] == "Pn":
                try:
                    OCV.CD["pins"] = word[1]
                    if 'S' in word[1]:
                        if OCV.c_state == 'Idle' and not OCV.s_running:
                            print("Stream requested by CYCLE START machine button")
                            self.master.event_generate("<<Run>>", when = 'tail')
                        else:
                            print(
                                    "Ignoring machine stream request, because of state: ",
                                    OCV.c_state, OCV.s_running)
                except (ValueError,IndexError):
                    break

        # Machine is Idle buffer is empty stop waiting and go on
        if self.master.sio_wait and not cline and fields[0] not in ("Run", "Jog", "Hold"):
            self.master.sio_wait = False
            self.master._gcount += 1

    def parseBracketSquare(self, line):
        word = SPLITPAT.split(line[1:-1])
        # print word
        if word[0] == "PRB":
            OCV.CD["prbx"] = float(word[1])
            OCV.CD["prby"] = float(word[2])
            OCV.CD["prbz"] = float(word[3])

            self.master.gcode.probe.add(
                 OCV.CD["prbx"]-OCV.CD["wcox"],
                 OCV.CD["prby"]-OCV.CD["wcoy"],
                 OCV.CD["prbz"]-OCV.CD["wcoz"])
            self.master._probeUpdate = True
            OCV.CD[word[0]] = word[1:]
        if word[0] == "G92":
            OCV.CD["G92X"] = float(word[1])
            OCV.CD["G92Y"] = float(word[2])
            OCV.CD["G92Z"] = float(word[3])
            OCV.CD[word[0]] = word[1:]
            self.master._gUpdate = True
        if word[0] == "G28":
            OCV.CD["G28X"] = float(word[1])
            OCV.CD["G28Y"] = float(word[2])
            OCV.CD["G28Z"] = float(word[3])
            OCV.CD[word[0]] = word[1:]
            self.master._gUpdate = True
        if word[0] == "G30":
            OCV.CD["G30X"] = float(word[1])
            OCV.CD["G30Y"] = float(word[2])
            OCV.CD["G30Z"] = float(word[3])
            OCV.CD[word[0]] = word[1:]
            self.master._gUpdate = True
        elif word[0] == "GC":
            OCV.CD["G"] = word[1].split()
            CNC.updateG()
            self.master._gUpdate = True
        elif word[0] == "TLO":
            OCV.CD[word[0]] = word[1]
            self.master._probeUpdate = True
            self.master._gUpdate = True
        elif word[0] == "MSG:" and word[1:] == "Pgm End":
            # Catch the program end message as sometimes it hangs in Run state.
            print("Program End Catched")
            OCV.s_stop = True
        else:
            OCV.CD[word[0]] = word[1:]
