# -*- coding: ascii -*-
"""ProbePage.py


Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""
from __future__ import absolute_import
from __future__ import print_function

import sys
# import time
import math

try:
    from Tkinter import *
    import tkMessageBox
except ImportError:
    from tkinter import *
    import tkinter.messagebox as tkMessageBox

import OCV
from CNC import CNC
import CNCRibbon
import Block
import Camera
import IniFile
import Ribbon
import tkExtra
import Utils


PROBE_CMD = [
    _("G38.2 stop on contact else error"),
    _("G38.3 stop on contact"),
    _("G38.4 stop on loss contact else error"),
    _("G38.5 stop on loss contact")
    ]

TOOL_POLICY = [
    _("Send M6 commands"),  # 0
    _("Ignore M6 commands"),  # 1
    _("Manual Tool Change (WCS)"),  # 2
    _("Manual Tool Change (TLO)"),  # 3
    _("Manual Tool Change (NoProbe)")  # 4
    ]

TOOL_WAIT = [
    _("ONLY before probing"),
    _("BEFORE & AFTER probing")
    ]

CAMERA_LOCATION = {
    "Gantry"       : NONE,
    "Top-Left"     : NW,
    "Top"          : N,
    "Top-Right"    : NE,
    "Left"         : W,
    "Center"       : CENTER,
    "Right"        : E,
    "Bottom-Left"  : SW,
    "Bottom"       : S,
    "Bottom-Right" : SE,
    }

CAMERA_LOCATION_ORDER = [
    "Gantry",
    "Top-Left",
    "Top",
    "Top-Right",
    "Left",
    "Center",
    "Right",
    "Bottom-Left",
    "Bottom",
    "Bottom-Right"]


#===============================================================================
# Probe Tab Group
#===============================================================================
class ProbeTabGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Probe"), app)

        self.tab = StringVar()

        col, row = 0, 0
        b = Ribbon.LabelRadiobutton(
                self.frame,
                image=OCV.icons["probe32"],
                text=_("Probe"),
                compound=TOP,
                variable=self.tab,
                value="Probe",
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=5, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Simple probing along a direction"))

        # ---
        col += 1
        b = Ribbon.LabelRadiobutton(
                self.frame,
                image=OCV.icons["level32"],
                text=_("Autolevel"),
                compound=TOP,
                variable=self.tab,
                value="Autolevel",
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=5, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Autolevel Z surface"))

        # ---
        col += 1
        b = Ribbon.LabelRadiobutton(self.frame,
                image=OCV.icons["camera32"],
                text=_("Camera"),
                compound=TOP,
                variable=self.tab,
                value="Camera",
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=5, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Work surface camera view and alignment"))
        if Camera.cv is None: b.config(state=DISABLED)

        # ---
        col += 1
        b = Ribbon.LabelRadiobutton(self.frame,
                image=OCV.icons["endmill32"],
                text=_("Tool"),
                compound=TOP,
                variable=self.tab,
                value="Tool",
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=5, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Setup probing for manual tool change"))

        self.frame.grid_rowconfigure(0, weight=1)


#===============================================================================
# Autolevel Group
#===============================================================================
class AutolevelGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "Probe:Autolevel", app)
        self.label["background"] = OCV.BACKGROUND_GROUP2
        self.grid3rows()

        # ---
        col,row=0,0
        b = Ribbon.LabelButton(self.frame, self, "<<AutolevelMargins>>",
                image=OCV.icons["margins"],
                text=_("Margins"),
                compound=LEFT,
                anchor=W,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Get margins from gcode file"))
        self.addWidget(b)

        # ---
        row += 1
        b = Ribbon.LabelButton(self.frame, self, "<<AutolevelZero>>",
                image=OCV.icons["origin"],
                text=_("Zero"),
                compound=LEFT,
                anchor=W,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Set current XY location as autoleveling Z-zero (recalculate probed data to be relative to this XY origin point)"))
        self.addWidget(b)

        # ---
        row += 1
        b = Ribbon.LabelButton(self.frame, self, "<<AutolevelClear>>",
                image=OCV.icons["clear"],
                text=_("Clear"),
                compound=LEFT,
                anchor=W,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Clear probe data"))
        self.addWidget(b)

        # ---
        row = 0
        col += 1
        b = Ribbon.LabelButton(self.frame, self, "<<AutolevelScanMargins>>",
                image=OCV.icons["margins"],
                text=_("Scan"),
                compound=LEFT,
                anchor=W,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Scan Autolevel Margins"))
        self.addWidget(b)

        row += 1
        b = Ribbon.LabelButton(self.frame,
                image=OCV.icons["level"],
                text=_("Autolevel"),
                compound=LEFT,
                anchor=W,
                command=lambda a=app:a.insertCommand("AUTOLEVEL",True),
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Modify selected G-Code to match autolevel"))
        self.addWidget(b)

        # ---
        col,row=2,0
        b = Ribbon.LabelButton(self.frame, self, "<<AutolevelScan>>",
                image=OCV.icons["gear32"],
                text=_("Scan"),
                compound=TOP,
                justify=CENTER,
                width=48,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NSEW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Scan probed area for level information on Z plane"))


#===============================================================================
# Probe Common Offset
#===============================================================================
class ProbeCommonFrame(CNCRibbon.PageFrame):
    probeFeed = None
    tlo       = None
    probeCmd  = None

    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "ProbeCommon", app)

        lframe = tkExtra.ExLabelFrame(self, text=_("Common"), foreground="DarkBlue")
        lframe.pack(side=TOP, fill=X)
        frame = lframe.frame

        # ----
        row = 0
        col = 0

        # ----
        # Fast Probe Feed
        Label(frame, text=_("Fast Probe Feed:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.fastProbeFeed = StringVar()
        self.fastProbeFeed.trace("w", lambda *_: ProbeCommonFrame.probeUpdate())
        ProbeCommonFrame.fastProbeFeed = tkExtra.FloatEntry(frame,
                            background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5,
                            textvariable=self.fastProbeFeed)
        ProbeCommonFrame.fastProbeFeed.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(ProbeCommonFrame.fastProbeFeed,
            _("Set initial probe feed rate for tool change and calibration"))
        self.addWidget(ProbeCommonFrame.fastProbeFeed)

        # ----
        # Probe Feed
        row += 1
        col  = 0
        Label(frame, text=_("Probe Feed:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.probeFeedVar = StringVar()
        self.probeFeedVar.trace("w", lambda *_: ProbeCommonFrame.probeUpdate())
        ProbeCommonFrame.probeFeed = tkExtra.FloatEntry(frame, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5,
                                textvariable=self.probeFeedVar)
        ProbeCommonFrame.probeFeed.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(ProbeCommonFrame.probeFeed, _("Set probe feed rate"))
        self.addWidget(ProbeCommonFrame.probeFeed)

        # ----
        # Tool offset
        row += 1
        col  = 0
        Label(frame, text=_("TLO")).grid(row=row, column=col, sticky=E)
        col += 1
        ProbeCommonFrame.tlo = tkExtra.FloatEntry(frame, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        ProbeCommonFrame.tlo.grid(row=row, column=col, sticky=EW)

        tkExtra.Balloon.set(ProbeCommonFrame.tlo, _("Set tool offset for probing"))

        self.addWidget(ProbeCommonFrame.tlo)
        self.tlo.bind("<Return>",   self.tloSet)
        self.tlo.bind("<KP_Enter>", self.tloSet)

        col += 1
        b = Button(frame, text=_("set"),
                command=self.tloSet,
                padx=2, pady=1)
        b.grid(row=row, column=col, sticky=EW)
        self.addWidget(b)

        # ---
        # feed command
        row += 1
        col  = 0
        Label(frame, text=_("Probe Command")).grid(row=row, column=col, sticky=E)
        col += 1
        ProbeCommonFrame.probeCmd = tkExtra.Combobox(frame, True,
                        background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                        width=16,
                        command=ProbeCommonFrame.probeUpdate)
        ProbeCommonFrame.probeCmd.grid(row=row, column=col, sticky=EW)
        ProbeCommonFrame.probeCmd.fill(PROBE_CMD)
        self.addWidget(ProbeCommonFrame.probeCmd)

        frame.grid_columnconfigure(1, weight=1)
        self.loadConfig()

        try:
            OCV.CD["TLO"] = float(ProbeCommonFrame.tlo.get())
            cmd = "G43.1 Z{0:f}".format(ProbeCommonFrame.tlo.get())
            self.sendGCode(cmd)
        except:
            pass
        OCV.MCTRL.viewParameters()

    @staticmethod
    def probeUpdate():
        try:
            OCV.CD["fastprbfeed"] = float(ProbeCommonFrame.fastProbeFeed.get())
            OCV.CD["prbfeed"]     = float(ProbeCommonFrame.probeFeed.get())
            OCV.CD["prbcmd"]      = str(ProbeCommonFrame.probeCmd.get().split()[0])
            return False
        except:
            return True

    #------------------------------------------------------------------------
    def updateTlo(self):
        try:
            if self.focus_get() is not ProbeCommonFrame.tlo:
                state = ProbeCommonFrame.tlo.cget("state")
                state = ProbeCommonFrame.tlo["state"] = NORMAL
                ProbeCommonFrame.tlo.set(str(OCV.CD.get("TLO","")))
                state = ProbeCommonFrame.tlo["state"] = state
        except:
            pass

    def tloSet(self):
        pass

    #-----------------------------------------------------------------------
    def saveConfig(self):
        IniFile.set_value("Probe", "fastfeed", ProbeCommonFrame.fastProbeFeed.get())
        IniFile.set_value("Probe", "feed", ProbeCommonFrame.probeFeed.get())
        IniFile.set_value("Probe", "tlo",  ProbeCommonFrame.tlo.get())
        IniFile.set_value("Probe", "cmd",  ProbeCommonFrame.probeCmd.get().split()[0])

    def loadConfig(self):
        ProbeCommonFrame.fastProbeFeed.set(IniFile.get_float(
                "Probe", "fastfeed"))
        ProbeCommonFrame.probeFeed.set(IniFile.get_float("Probe", "feed"))
        ProbeCommonFrame.tlo.set(      IniFile.get_float("Probe", "tlo"))
        cmd = IniFile.get_str("Probe", "cmd")
        for p in PROBE_CMD:
            if p.split()[0] == cmd:
                ProbeCommonFrame.probeCmd.set(p)
                break


class ProbeFrame(CNCRibbon.PageFrame):
    """Probe Frame"""
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "Probe:Probe", app)

        #----------------------------------------------------------------
        # Record point
        #----------------------------------------------------------------

        recframe = tkExtra.ExLabelFrame(self, text=_("Record"), foreground="DarkBlue")
        recframe.pack(side=TOP, expand=YES, fill=X)

        #Label(lframe(), text=_("Diameter:")).pack(side=LEFT)
        #self.diameter = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        #self.diameter.pack(side=LEFT, expand=YES, fill=X)

        self.recz=IntVar()
        self.reczb = Checkbutton(recframe(), text=_("Z"),
            variable=self.recz, #onvalue=1, offvalue=0,
            activebackground="LightYellow",
            padx=2, pady=1)
        tkExtra.Balloon.set(self.reczb, _("Record Z coordinate?"))
        self.reczb.pack(side=LEFT, expand=YES, fill=X)
        self.addWidget(self.reczb)

        self.rr = Button(recframe(), text=_("RAPID"),
            command=self.recordRapid,
            activebackground="LightYellow",
            padx=2, pady=1)
        self.rr.pack(side=LEFT, expand=YES, fill=X)
        self.addWidget(self.rr)

        self.rr = Button(recframe(), text=_("FEED"),
            command=self.recordFeed,
            activebackground="LightYellow",
            padx=2, pady=1)
        self.rr.pack(side=LEFT, expand=YES, fill=X)
        self.addWidget(self.rr)

        self.rr = Button(recframe(), text=_("POINT"),
            command=self.recordPoint,
            activebackground="LightYellow",
            padx=2, pady=1)
        self.rr.pack(side=LEFT, expand=YES, fill=X)
        self.addWidget(self.rr)

        self.rr = Button(recframe(), text=_("CIRCLE"),
            command=self.recordCircle,
            activebackground="LightYellow",
            padx=2, pady=1)
        self.rr.pack(side=LEFT, expand=YES, fill=X)
        self.addWidget(self.rr)

        self.rr = Button(recframe(), text=_("FINISH"),
            command=self.recordFinishAll,
            activebackground="LightYellow",
            padx=2, pady=1)
        self.rr.pack(side=LEFT, expand=YES, fill=X)
        self.addWidget(self.rr)

        self.recsiz = tkExtra.FloatEntry(recframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        tkExtra.Balloon.set(self.recsiz, _("Circle radius"))
        self.recsiz.set(10)
        self.recsiz.pack(side=BOTTOM, expand=YES, fill=X)
        self.addWidget(self.recsiz)

        #----------------------------------------------------------------
        # Single probe
        #----------------------------------------------------------------
        lframe = tkExtra.ExLabelFrame(self, text=_("Probe"), foreground="DarkBlue")
        lframe.pack(side=TOP, fill=X)

        row,col = 0,0
        Label(lframe(), text=_("Probe:")).grid(row=row, column=col, sticky=E)

        col += 1
        self._probeX = Label(lframe(), foreground="DarkBlue", background="gray90")
        self._probeX.grid(row=row, column=col, padx=1, sticky=EW+S)

        col += 1
        self._probeY = Label(lframe(), foreground="DarkBlue", background="gray90")
        self._probeY.grid(row=row, column=col, padx=1, sticky=EW+S)

        col += 1
        self._probeZ = Label(lframe(), foreground="DarkBlue", background="gray90")
        self._probeZ.grid(row=row, column=col, padx=1, sticky=EW+S)

        # ---
        col += 1
        self.probeautogotonext = False
        self.probeautogoto=IntVar()
        self.autogoto = Checkbutton(lframe(), "",
            variable=self.probeautogoto, #onvalue=1, offvalue=0,
            activebackground="LightYellow",
            padx=2, pady=1)
        self.autogoto.select()
        tkExtra.Balloon.set(self.autogoto, _("Automatic GOTO after probing"))
        #self.autogoto.pack(side=LEFT, expand=YES, fill=X)
        self.autogoto.grid(row=row, column=col, padx=1, sticky=EW)
        self.addWidget(self.autogoto)

        # ---
        col += 1
        b = Button(lframe(),
                image=OCV.icons["rapid"],
                text=_("Goto"),
                compound=LEFT,
                command=self.goto2Probe,
#                width=48,
                padx=5, pady=0)
        b.grid(row=row, column=col, padx=1, sticky=EW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Rapid goto to last probe location"))

        # ---
        row,col = row+1,0
        Label(lframe(), text=_("Pos:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.probeXdir = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.probeXdir.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeXdir, _("Probe along X direction"))
        self.addWidget(self.probeXdir)

        col += 1
        self.probeYdir = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.probeYdir.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeYdir, _("Probe along Y direction"))
        self.addWidget(self.probeYdir)

        col += 1
        self.probeZdir = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.probeZdir.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeZdir, _("Probe along Z direction"))
        self.addWidget(self.probeZdir)

        # ---
        col += 2
        b = Button(lframe(), #"<<Probe>>",
                image=OCV.icons["probe32"],
                text=_("Probe"),
                compound=LEFT,
                command=self.probe,
#                width=48,
                padx=5, pady=0)
        b.grid(row=row, column=col, padx=1, sticky=EW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Perform a single probe cycle"))


        lframe().grid_columnconfigure(1,weight=1)
        lframe().grid_columnconfigure(2,weight=1)
        lframe().grid_columnconfigure(3,weight=1)

        #----------------------------------------------------------------
        # Center probing
        #----------------------------------------------------------------
        lframe = tkExtra.ExLabelFrame(self, text=_("Center"), foreground="DarkBlue")
        lframe.pack(side=TOP, expand=YES, fill=X)

        Label(lframe(), text=_("Diameter:")).pack(side=LEFT)
        self.diameter = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.diameter.pack(side=LEFT, expand=YES, fill=X)
        tkExtra.Balloon.set(self.diameter, _("Probing ring internal diameter"))
        self.addWidget(self.diameter)

        # ---
        b = Button(lframe(),
                image=OCV.icons["target32"],
                text=_("Center"),
                compound=TOP,
                command=self.probeCenter,
                width=48,
                padx=5, pady=0)
        b.pack(side=RIGHT)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Center probing using a ring"))

        #----------------------------------------------------------------
        # Align / Orient / Square ?
        #----------------------------------------------------------------
        lframe = tkExtra.ExLabelFrame(self, text=_("Orient"), foreground="DarkBlue")
        lframe.pack(side=TOP, expand=YES, fill=X)

        # ---
        row, col = 0,0

        Label(lframe(), text=_("Markers:")).grid(row=row, column=col, sticky=E)
        col += 1

        self.scale_orient = Scale(lframe(),
                    from_=0, to_=0,
                    orient=HORIZONTAL,
                    showvalue=1,
                    state=DISABLED,
                    command=self.changeMarker)
        self.scale_orient.grid(row=row, column=col, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(self.scale_orient, _("Select orientation marker"))

        # Add new point
        col += 2
        b = Button(lframe(), text=_("Add"),
                image=OCV.icons["add"],
                compound=LEFT,
                command=lambda s=self: s.event_generate("<<AddMarker>>"),
                padx = 1,
                pady = 1)
        b.grid(row=row, column=col, sticky=NSEW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Add an orientation marker. " \
                "Jog first the machine to the marker position " \
                "and then click on canvas to add the marker."))

        # ----
        row += 1
        col = 0
        Label(lframe(), text=_("Gcode:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.x_orient = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.x_orient.grid(row=row, column=col, sticky=EW)
        self.x_orient.bind("<FocusOut>", self.orientUpdate)
        self.x_orient.bind("<Return>",   self.orientUpdate)
        self.x_orient.bind("<KP_Enter>", self.orientUpdate)
        tkExtra.Balloon.set(self.x_orient, _("GCode X coordinate of orientation point"))

        col += 1
        self.y_orient = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.y_orient.grid(row=row, column=col, sticky=EW)
        self.y_orient.bind("<FocusOut>", self.orientUpdate)
        self.y_orient.bind("<Return>",   self.orientUpdate)
        self.y_orient.bind("<KP_Enter>", self.orientUpdate)
        tkExtra.Balloon.set(self.y_orient, _("GCode Y coordinate of orientation point"))

        # Buttons
        col += 1
        b = Button(lframe(), text=_("Delete"),
                image=OCV.icons["x"],
                compound=LEFT,
                command = self.orientDelete,
                padx = 1,
                pady = 1)
        b.grid(row=row, column=col, sticky=EW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Delete current marker"))

        # ---
        row += 1
        col = 0

        Label(lframe(), text=_("WPos:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.xm_orient = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.xm_orient.grid(row=row, column=col, sticky=EW)
        self.xm_orient.bind("<FocusOut>", self.orientUpdate)
        self.xm_orient.bind("<Return>",   self.orientUpdate)
        self.xm_orient.bind("<KP_Enter>", self.orientUpdate)
        tkExtra.Balloon.set(self.xm_orient, _("Machine X coordinate of orientation point"))

        col += 1
        self.ym_orient = tkExtra.FloatEntry(lframe(), background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.ym_orient.grid(row=row, column=col, sticky=EW)
        self.ym_orient.bind("<FocusOut>", self.orientUpdate)
        self.ym_orient.bind("<Return>",   self.orientUpdate)
        self.ym_orient.bind("<KP_Enter>", self.orientUpdate)
        tkExtra.Balloon.set(self.ym_orient, _("Machine Y coordinate of orientation point"))

        # Buttons
        col += 1
        b = Button(lframe(), text=_("Clear"),
                image=OCV.icons["clear"],
                compound=LEFT,
                command = self.orientClear,
                padx = 1,
                pady = 1)
        b.grid(row=row, column=col, sticky=EW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Delete all markers"))

        # ---
        row += 1
        col = 0
        Label(lframe(), text=_("Angle:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.angle_orient = Label(lframe(), foreground="DarkBlue", background="gray90", anchor=W)
        self.angle_orient.grid(row=row, column=col, columnspan=2, sticky=EW, padx=1, pady=1)

        # Buttons
        col += 2
        b = Button(lframe(), text=_("Orient"),
                image=OCV.icons["setsquare32"],
                compound=TOP,
                command = lambda a=app:a.insertCommand("ORIENT",True),
                padx = 1,
                pady = 1)
        b.grid(row=row, rowspan=3, column=col, sticky=EW)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Align GCode with the machine markers"))

        # ---
        row += 1
        col = 0
        Label(lframe(), text=_("Offset:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.xo_orient = Label(lframe(), foreground="DarkBlue", background="gray90", anchor=W)
        self.xo_orient.grid(row=row, column=col, sticky=EW, padx=1)

        col += 1
        self.yo_orient = Label(lframe(), foreground="DarkBlue", background="gray90", anchor=W)
        self.yo_orient.grid(row=row, column=col, sticky=EW, padx=1)

        # ---
        row += 1
        col = 0
        Label(lframe(), text=_("Error:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.err_orient = Label(lframe(), foreground="DarkBlue", background="gray90", anchor=W)
        self.err_orient.grid(row=row, column=col, columnspan=2, sticky=EW, padx=1, pady=1)

        lframe().grid_columnconfigure(1, weight=1)
        lframe().grid_columnconfigure(2, weight=1)

        #----------------------------------------------------------------
        self.warn = True
        self.loadConfig()

    #-----------------------------------------------------------------------
    def loadConfig(self):
        self.probeXdir.set(IniFile.get_str("Probe", "x"))
        self.probeYdir.set(IniFile.get_str("Probe", "y"))
        self.probeZdir.set(IniFile.get_str("Probe", "z"))
        self.diameter.set(IniFile.get_str("Probe", "center"))
        self.warn = IniFile.get_bool("Warning", "probe", self.warn)

    #-----------------------------------------------------------------------
    def saveConfig(self):
        IniFile.set_value("Probe", "x", self.probeXdir.get())
        IniFile.set_value("Probe", "y", self.probeYdir.get())
        IniFile.set_value("Probe", "z", self.probeZdir.get())
        IniFile.set_value("Probe", "center", self.diameter.get())
        IniFile.set_value("Warning","probe",  self.warn)

    #-----------------------------------------------------------------------
    def updateProbe(self):
        try:
            self._probeX["text"] = OCV.CD.get("prbx")
            self._probeY["text"] = OCV.CD.get("prby")
            self._probeZ["text"] = OCV.CD.get("prbz")
        except:
            return

        if self.probeautogotonext:
            self.probeautogotonext = False
            self.goto2Probe()


    #-----------------------------------------------------------------------
    def warnMessage(self):
        if self.warn:
            ans = tkMessageBox.askquestion(_("Probe connected?"),
                _("Please verify that the probe is connected.\n\nShow this message again?"),
                icon='warning',
                parent=self.winfo_toplevel())
            if ans != YES:
                self.warn = False

    #-----------------------------------------------------------------------
    # Probe one Point
    #-----------------------------------------------------------------------
    def probe(self, event=None):
        if self.probeautogoto.get() == 1:
            self.probeautogotonext = True

        if ProbeCommonFrame.probeUpdate():
            tkMessageBox.showerror(_("Probe Error"),
                _("Invalid probe feed rate"),
                parent=self.winfo_toplevel())
            return
        self.warnMessage()

        cmd = str(OCV.CD["prbcmd"])
        ok = False

        v = self.probeXdir.get()
        if v != "":
            cmd += "X"+str(v)
            ok = True

        v = self.probeYdir.get()
        if v != "":
            cmd += "Y"+str(v)
            ok = True

        v = self.probeZdir.get()
        if v != "":
            cmd += "Z"+str(v)
            ok = True

        v = ProbeCommonFrame.probeFeed.get()
        if v != "":
            cmd += "F"+str(v)

        if ok:
            self.sendGCode(cmd)
        else:
            tkMessageBox.showerror(_("Probe Error"),
                    _("At least one probe direction should be specified"))

    #-----------------------------------------------------------------------
    # Rapid move to the last probed location
    #-----------------------------------------------------------------------
    def goto2Probe(self, event=None):
        try:
            cmd = "G53 G0 X%g Y%g Z%g\n"%(OCV.CD["prbx"], OCV.CD["prby"], OCV.CD["prbz"])
        except:
            return
        self.sendGCode(cmd)

    #-----------------------------------------------------------------------
    # Probe Center
    #-----------------------------------------------------------------------
    def probeCenter(self, event=None):
        self.warnMessage()

        cmd = "G91 %s F%s"%(OCV.CD["prbcmd"], OCV.CD["prbfeed"])
        try:
            diameter = abs(float(self.diameter.get()))
        except:
            diameter = 0.0

        if diameter < 0.001:
            tkMessageBox.showerror(_("Probe Center Error"),
                    _("Invalid diameter entered"),
                    parent=self.winfo_toplevel())
            return

        lines = []
        lines.append("%s x-%s"%(cmd,diameter))
        lines.append("%wait")
        lines.append("tmp=prbx")
        lines.append("g53 g0 x[prbx+%g]"%(diameter/10))
        lines.append("%wait")
        lines.append("%s x%s"%(cmd,diameter))
        lines.append("%wait")
        lines.append("g53 g0 x[0.5*(tmp+prbx)]")
        lines.append("%wait")
        lines.append("%s y-%s"%(cmd,diameter))
        lines.append("%wait")
        lines.append("tmp=prby")
        lines.append("g53 g0 y[prby+%g]"%(diameter/10))
        lines.append("%wait")
        lines.append("%s y%s"%(cmd,diameter))
        lines.append("%wait")
        lines.append("g53 g0 y[0.5*(tmp+prby)]")
        lines.append("%wait")
        lines.append("g90")
        OCV.APP.run(lines=lines)

    #-----------------------------------------------------------------------
    # Solve the system and update fields
    #-----------------------------------------------------------------------
    def orientSolve(self, event=None):
        try:
            phi, xo, yo = OCV.APP.gcode.orient.solve()
            self.angle_orient["text"]="%*f"%(OCV.digits, math.degrees(phi))
            self.xo_orient["text"]="%*f"%(OCV.digits, xo)
            self.yo_orient["text"]="%*f"%(OCV.digits, yo)

            minerr, meanerr, maxerr = OCV.APP.gcode.orient.error()
            self.err_orient["text"] = "Avg:%*f  Max:%*f  Min:%*f"%\
                (OCV.digits, meanerr, OCV.digits, maxerr, OCV.digits, minerr)

        except:
            self.angle_orient["text"] = sys.exc_info()[1]
            self.xo_orient["text"]    = ""
            self.yo_orient["text"]    = ""
            self.err_orient["text"]   = ""

    #-----------------------------------------------------------------------
    # Delete current orientation point
    #-----------------------------------------------------------------------
    def orientDelete(self, event=None):
        marker = self.scale_orient.get()-1
        if marker<0 or marker >= len(OCV.APP.gcode.orient): return
        OCV.APP.gcode.orient.clear(marker)
        self.orientUpdateScale()
        self.changeMarker(marker+1)
        self.orientSolve()
        self.event_generate("<<DrawOrient>>")

    #-----------------------------------------------------------------------
    # Clear all markers
    #-----------------------------------------------------------------------
    def orientClear(self, event=None):
        if self.scale_orient.cget("to") == 0: return
        ans = tkMessageBox.askquestion(_("Delete all markers"),
            _("Do you want to delete all orientation markers?"),
            parent=self.winfo_toplevel())
        if ans!=tkMessageBox.YES: return
        OCV.APP.gcode.orient.clear()
        self.orientUpdateScale()
        self.event_generate("<<DrawOrient>>")

    #-----------------------------------------------------------------------
    # Update orientation scale
    #-----------------------------------------------------------------------
    def orientUpdateScale(self):
        n = len(OCV.APP.gcode.orient)
        if n:
            self.scale_orient.config(state=NORMAL, from_=1, to_=n)
        else:
            self.scale_orient.config(state=DISABLED, from_=0, to_=0)

    #-----------------------------------------------------------------------
    def orientClearFields(self):
        self.x_orient.delete(0,END)
        self.y_orient.delete(0,END)
        self.xm_orient.delete(0,END)
        self.ym_orient.delete(0,END)
        self.angle_orient["text"] = ""
        self.xo_orient["text"]    = ""
        self.yo_orient["text"]    = ""
        self.err_orient["text"]   = ""

    #-----------------------------------------------------------------------
    # Update orient with the current marker
    #-----------------------------------------------------------------------
    def orientUpdate(self, event=None):
        marker = self.scale_orient.get()-1
        if marker<0 or marker >= len(OCV.APP.gcode.orient):
            self.orientClearFields()
            return
        xm,ym,x,y = OCV.APP.gcode.orient[marker]
        try:    x = float(self.x_orient.get())
        except: pass
        try:    y = float(self.y_orient.get())
        except: pass
        try:    xm = float(self.xm_orient.get())
        except: pass
        try:    ym = float(self.ym_orient.get())
        except: pass
        OCV.APP.gcode.orient.markers[marker] = xm,ym,x,y

        self.orientUpdateScale()
        self.changeMarker(marker+1)
        self.orientSolve()
        self.event_generate("<<DrawOrient>>")

    #-----------------------------------------------------------------------
    # The index will be +1 to appear more human starting from 1
    #-----------------------------------------------------------------------
    def changeMarker(self, marker):
        marker = int(marker)-1
        if marker<0 or marker >= len(OCV.APP.gcode.orient):
            self.orientClearFields()
            self.event_generate("<<OrientChange>>", data=-1)
            return

        xm,ym,x,y = OCV.APP.gcode.orient[marker]
        #self.x_orient.set("%*f"%(d,x))
        self.x_orient.set("{0:.{1}%}".format(x, OCV.digits))
        #self.y_orient.set("%*f"%(d,y))
        self.y_orient.set("{0:.{1}%}".format(y, OCV.digits))
        #self.xm_orient.set("%*f"%(d,xm))
        self.xm_orient.set("{0:.{1}%}".format(xm, OCV.digits))
        #self.ym_orient.set("%*f"%(d,ym))
        self.ym_orient.set("{0:.{1}%}".format(ym, OCV.digits))
        self.orientSolve()
        self.event_generate("<<OrientChange>>", data=marker)

    #-----------------------------------------------------------------------
    # Select marker
    #-----------------------------------------------------------------------
    def selectMarker(self, marker):
        self.orientUpdateScale()
        self.scale_orient.set(marker+1)

    def recordAppend(self, line):
        hasblock = None
        for bid,block in enumerate(OCV.APP.gcode):
            if block._name == 'recording':
                hasblock = bid
                eblock = block

        if hasblock is None:
            hasblock = -1
            eblock = Block('recording')
            OCV.APP.gcode.insBlocks(hasblock, [eblock], "Recorded point")

        eblock.append(line)
        OCV.APP.refresh()
        OCV.APP.setStatus(_("Pointrec"))

        #print "hello",x,y,z
        #print OCV.APP.editor.getSelectedBlocks()

    def recordCoords(self, gcode='G0', point=False):
        #print "Z",self.recz.get()
        x = OCV.CD["wx"]
        y = OCV.CD["wy"]
        z = OCV.CD["wz"]

        coords = "X%s Y%s"%(x, y)
        if self.recz.get() == 1:
            coords += " Z%s"%(z)

        if point:
            self.recordAppend('G0 Z%s'%(OCV.CD["safe"]))
        self.recordAppend('%s %s'%(gcode, coords))
        if point:
            self.recordAppend('G1 Z0')

    def recordRapid(self):
        self.recordCoords()

    def recordFeed(self):
        self.recordCoords('G1')

    def recordPoint(self):
        self.recordCoords('G0', True)

    def recordCircle(self):
        r = float(self.recsiz.get())
        #self.recordCoords('G02 R%s'%(r))
        x = OCV.CD["wx"]-r
        y = OCV.CD["wy"]
        z = OCV.CD["wz"]

        coords = "X%s Y%s"%(x, y)
        if self.recz.get() == 1:
            coords += " Z%s"%(z)

        #self.recordAppend('G0 %s R%s'%(coords, r))
        self.recordAppend('G0 %s'%(coords))
        self.recordAppend('G02 %s I%s'%(coords, r))

    def recordFinishAll(self):
        for bid,block in enumerate(OCV.APP.gcode):
            if block._name == 'recording':
                OCV.APP.gcode.setBlockNameUndo(bid, 'recorded')
        OCV.APP.refresh()
        OCV.APP.setStatus(_("Finished recording"))


#===============================================================================
# Autolevel Frame
#===============================================================================
class AutolevelFrame(CNCRibbon.PageFrame):
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "Probe:Autolevel", app)

        lframe = LabelFrame(self, text=_("Autolevel"), foreground="DarkBlue")
        lframe.pack(side=TOP, fill=X)

        row,col = 0,0
        # Empty
        col += 1
        Label(lframe, text=_("Min")).grid(row=row, column=col, sticky=EW)
        col += 1
        Label(lframe, text=_("Max")).grid(row=row, column=col, sticky=EW)
        col += 1
        Label(lframe, text=_("Step")).grid(row=row, column=col, sticky=EW)
        col += 1
        Label(lframe, text=_("N")).grid(row=row, column=col, sticky=EW)

        # --- X ---
        row += 1
        col = 0
        Label(lframe, text=_("X:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.probeXmin = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeXmin.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeXmin, _("X minimum"))
        self.addWidget(self.probeXmin)

        col += 1
        self.probeXmax = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeXmax.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeXmax, _("X maximum"))
        self.addWidget(self.probeXmax)

        col += 1
        self.probeXstep = Label(lframe, foreground="DarkBlue",
                    background="gray90", width=5)
        self.probeXstep.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeXstep, _("X step"))

        col += 1
        self.probeXbins = Spinbox(lframe,
                    from_=2, to_=1000,
                    command=self.draw,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    width=3)
        self.probeXbins.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeXbins, _("X bins"))
        self.addWidget(self.probeXbins)

        # --- Y ---
        row += 1
        col  = 0
        Label(lframe, text=_("Y:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.probeYmin = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeYmin.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeYmin, _("Y minimum"))
        self.addWidget(self.probeYmin)

        col += 1
        self.probeYmax = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeYmax.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeYmax, _("Y maximum"))
        self.addWidget(self.probeYmax)

        col += 1
        self.probeYstep = Label(lframe,  foreground="DarkBlue",
                    background="gray90", width=5)
        self.probeYstep.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeYstep, _("Y step"))

        col += 1
        self.probeYbins = Spinbox(lframe,
                    from_=2, to_=1000,
                    command=self.draw,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    width=3)
        self.probeYbins.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeYbins, _("Y bins"))
        self.addWidget(self.probeYbins)

        # Max Z
        row += 1
        col  = 0

        Label(lframe, text=_("Z:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.probeZmin = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeZmin.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeZmin, _("Z Minimum depth to scan"))
        self.addWidget(self.probeZmin)

        col += 1
        self.probeZmax = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeZmax.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeZmax, _("Z safe to move"))
        self.addWidget(self.probeZmax)

        lframe.grid_columnconfigure(1,weight=2)
        lframe.grid_columnconfigure(2,weight=2)
        lframe.grid_columnconfigure(3,weight=1)

        self.loadConfig()

    def setValues(self):
        probe = OCV.APP.gcode.probe
        self.probeXmin.set(str(probe.xmin))
        self.probeXmax.set(str(probe.xmax))
        self.probeXbins.delete(0,END)
        self.probeXbins.insert(0,probe.xn)
        self.probeXstep["text"] = str(probe.xstep())

        self.probeYmin.set(str(probe.ymin))
        self.probeYmax.set(str(probe.ymax))
        self.probeYbins.delete(0,END)
        self.probeYbins.insert(0,probe.yn)
        self.probeYstep["text"] = str(probe.ystep())

        self.probeZmin.set(str(probe.zmin))
        self.probeZmax.set(str(probe.zmax))

    def saveConfig(self):
        IniFile.set_value("Probe", "xmin", self.probeXmin.get())
        IniFile.set_value("Probe", "xmax", self.probeXmax.get())
        IniFile.set_value("Probe", "xn", self.probeXbins.get())
        IniFile.set_value("Probe", "ymin", self.probeYmin.get())
        IniFile.set_value("Probe", "ymax", self.probeYmax.get())
        IniFile.set_value("Probe", "yn", self.probeYbins.get())
        IniFile.set_value("Probe", "zmin", self.probeZmin.get())
        IniFile.set_value("Probe", "zmax", self.probeZmax.get())

    #-----------------------------------------------------------------------
    def loadConfig(self):
        self.probeXmin.set(IniFile.get_float("Probe","xmin"))
        self.probeXmax.set(IniFile.get_float("Probe","xmax"))
        self.probeYmin.set(IniFile.get_float("Probe","ymin"))
        self.probeYmax.set(IniFile.get_float("Probe","ymax"))
        self.probeZmin.set(IniFile.get_float("Probe","zmin"))
        self.probeZmax.set(IniFile.get_float("Probe","zmax"))

        self.probeXbins.delete(0,END)
        self.probeXbins.insert(0,max(2,IniFile.get_int("Probe","xn",5)))

        self.probeYbins.delete(0,END)
        self.probeYbins.insert(0,max(2,IniFile.get_int("Probe","yn",5)))
        self.change(False)

    #-----------------------------------------------------------------------
    def getMargins(self, event=None):
        self.probeXmin.set(str(OCV.CD["xmin"]))
        self.probeXmax.set(str(OCV.CD["xmax"]))
        self.probeYmin.set(str(OCV.CD["ymin"]))
        self.probeYmax.set(str(OCV.CD["ymax"]))
        self.draw()

    #-----------------------------------------------------------------------
    def change(self, verbose=True):
        probe = OCV.APP.gcode.probe
        error = False
        try:
            probe.xmin = float(self.probeXmin.get())
            probe.xmax = float(self.probeXmax.get())
            probe.xn   = max(2,int(self.probeXbins.get()))
            self.probeXstep["text"] = "%.5g"%(probe.xstep())
        except ValueError:
            self.probeXstep["text"] = ""
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                        _("Invalid X probing region"),
                        parent=self.winfo_toplevel())
            error = True

        if probe.xmin >= probe.xmax:
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                        _("Invalid X range [xmin>=xmax]"),
                        parent=self.winfo_toplevel())
            error = True

        try:
            probe.ymin = float(self.probeYmin.get())
            probe.ymax = float(self.probeYmax.get())
            probe.yn   = max(2,int(self.probeYbins.get()))
            self.probeYstep["text"] = "%.5g"%(probe.ystep())
        except ValueError:
            self.probeYstep["text"] = ""
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                        _("Invalid Y probing region"),
                        parent=self.winfo_toplevel())
            error = True

        if probe.ymin >= probe.ymax:
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                        _("Invalid Y range [ymin>=ymax]"),
                        parent=self.winfo_toplevel())
            error = True

        try:
            probe.zmin  = float(self.probeZmin.get())
            probe.zmax  = float(self.probeZmax.get())
        except ValueError:
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                    _("Invalid Z probing region"),
                    parent=self.winfo_toplevel())
            error = True

        if probe.zmin >= probe.zmax:
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                        _("Invalid Z range [zmin>=zmax]"),
                        parent=self.winfo_toplevel())
            error = True

        if ProbeCommonFrame.probeUpdate():
            if verbose:
                tkMessageBox.showerror(_("Probe Error"),
                    _("Invalid probe feed rate"),
                    parent=self.winfo_toplevel())
            error = True

        return error

    #-----------------------------------------------------------------------
    def draw(self):
        if not self.change():
            self.event_generate("<<DrawProbe>>")

    #-----------------------------------------------------------------------
    def setZero(self, event=None):
        x = OCV.CD["wx"]
        y = OCV.CD["wy"]
        OCV.APP.gcode.probe.setZero(x,y)
        self.draw()

    #-----------------------------------------------------------------------
    def clear(self, event=None):
        ans = tkMessageBox.askquestion(_("Delete autolevel information"),
            _("Do you want to delete all autolevel in formation?"),
            parent=self.winfo_toplevel())
        if ans!=tkMessageBox.YES: return
        OCV.APP.gcode.probe.clear()
        self.draw()

    #-----------------------------------------------------------------------
    # Probe an X-Y area
    #-----------------------------------------------------------------------
    def scan(self, event=None):
        if self.change(): return
        self.event_generate("<<DrawProbe>>")
        # absolute
        OCV.APP.run(lines=OCV.APP.gcode.probe.scan())

    #-----------------------------------------------------------------------
    # Scan autolevel margins
    #-----------------------------------------------------------------------
    def scanMargins(self, event=None):
        if self.change(): return
        OCV.APP.run(lines=OCV.APP.gcode.probe.scanMargins())


#===============================================================================
# Camera Group
#===============================================================================
class CameraGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "Probe:Camera", app)
        self.label["background"] = OCV.BACKGROUND_GROUP2
        self.grid3rows()

        self.switch = BooleanVar()
        self.edge   = BooleanVar()
        self.freeze = BooleanVar()

        # ---
        col,row=0,0
        self.switchButton = Ribbon.LabelCheckbutton(self.frame,
                image=OCV.icons["camera32"],
                text=_("Switch To"),
                compound=TOP,
                variable=self.switch,
                command=self.switchCommand,
                background=OCV.BACKGROUND)
        self.switchButton.grid(row=row, column=col, rowspan=3, padx=5, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(self.switchButton, _("Switch between camera and spindle"))

        # ---
        col,row=1,0
        b = Ribbon.LabelCheckbutton(self.frame,
                image=OCV.icons["edge"],
                text=_("Edge Detection"),
                compound=LEFT,
                variable=self.edge,
                anchor=W,
                command=self.edgeDetection,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Turn on/off edge detection"))

        # ---
        row += 1
        b = Ribbon.LabelCheckbutton(self.frame,
                image=OCV.icons["freeze"],
                text=_("Freeze"),
                compound=LEFT,
                variable=self.freeze,
                anchor=W,
                command=self.freezeImage,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Turn on/off freeze image"))

    #-----------------------------------------------------------------------
    # Move camera to spindle location and change coordinates to relative
    # to camera via g92
    #-----------------------------------------------------------------------
    def switchCommand(self, event=None):
        wx = OCV.CD["wx"]
        wy = OCV.CD["wy"]
        dx = OCV.CANVAS_F.canvas.cameraDx
        dy = OCV.CANVAS_F.canvas.cameraDy
        z  = OCV.CANVAS_F.canvas.cameraZ
        if self.switch.get():
            self.switchButton.config(image=OCV.icons["endmill32"])
            self.sendGCode("G92X%gY%g"%(dx+wx,dy+wy))
            OCV.CANVAS_F.canvas.cameraSwitch = True
        else:
            self.switchButton.config(image=OCV.icons["camera32"])
            self.sendGCode("G92.1")
            OCV.CANVAS_F.canvas.cameraSwitch = False
        if z is None:
            self.sendGCode("G0X%gY%g"%(wx,wy))
        else:
            self.sendGCode("G0X%gY%gZ%g"%(wx,wy,z))

    #-----------------------------------------------------------------------
    def switchCamera(self, event=None):
        self.switch.set(not self.switch.get())
        self.switchCommand()

    #-----------------------------------------------------------------------
    def edgeDetection(self):
        OCV.CANVAS_F.canvas.cameraEdge = self.edge.get()

    #-----------------------------------------------------------------------
    def freezeImage(self):
        OCV.CANVAS_F.canvas.cameraFreeze(self.freeze.get())


#===============================================================================
# Camera Frame
#===============================================================================
class CameraFrame(CNCRibbon.PageFrame):
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "Probe:Camera", app)

        # ==========
        lframe = LabelFrame(self, text=_("Camera"), foreground="DarkBlue")
        lframe.pack(side=TOP, fill=X, expand=YES)

        # ----
        row = 0
        Label(lframe, text=_("Location:")).grid(row=row, column=0, sticky=E)
        self.location = tkExtra.Combobox(lframe, True,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    width=16)
        self.location.grid(row=row, column=1, columnspan=3, sticky=EW)
        self.location.fill(CAMERA_LOCATION_ORDER)
        self.location.set(CAMERA_LOCATION_ORDER[0])
        tkExtra.Balloon.set(self.location, _("Camera location inside canvas"))

        # ----
        row += 1
        Label(lframe, text=_("Rotation:")).grid(row=row, column=0, sticky=E)
        self.rotation = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.rotation.grid(row=row, column=1, sticky=EW)
        self.rotation.bind("<Return>",   self.updateValues)
        self.rotation.bind("<KP_Enter>", self.updateValues)
        self.rotation.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.rotation, _("Camera rotation [degrees]"))
        # ----
        row += 1
        Label(lframe, text=_("Haircross Offset:")).grid(row=row, column=0, sticky=E)
        self.xcenter = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.xcenter.grid(row=row, column=1, sticky=EW)
        self.xcenter.bind("<Return>",   self.updateValues)
        self.xcenter.bind("<KP_Enter>", self.updateValues)
        self.xcenter.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.xcenter, _("Haircross X offset [unit]"))

        self.ycenter = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.ycenter.grid(row=row, column=2, sticky=EW)
        self.ycenter.bind("<Return>",   self.updateValues)
        self.ycenter.bind("<KP_Enter>", self.updateValues)
        self.ycenter.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.ycenter, _("Haircross Y offset [unit]"))
        # ----

        row += 1
        Label(lframe, text=_("Scale:")).grid(row=row, column=0, sticky=E)
        self.scale = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.scale.grid(row=row, column=1, sticky=EW)
        self.scale.bind("<Return>",   self.updateValues)
        self.scale.bind("<KP_Enter>", self.updateValues)
        self.scale.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.scale, _("Camera scale [pixels / unit]"))

        # ----
        row += 1
        Label(lframe, text=_("Crosshair:")).grid(row=row, column=0, sticky=E)
        self.diameter = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.diameter.grid(row=row, column=1, sticky=EW)
        self.diameter.bind("<Return>",   self.updateValues)
        self.diameter.bind("<KP_Enter>", self.updateValues)
        self.diameter.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.diameter, _("Camera cross hair diameter [units]"))

        b = Button(lframe, text=_("Get"), command=self.getDiameter, padx=1, pady=1)
        b.grid(row=row, column=2, sticky=W)
        tkExtra.Balloon.set(b, _("Get diameter from active endmill"))

        # ----
        row += 1
        Label(lframe, text=_("Offset:")).grid(row=row, column=0, sticky=E)
        self.dx = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.dx.grid(row=row, column=1, sticky=EW)
        self.dx.bind("<Return>",   self.updateValues)
        self.dx.bind("<KP_Enter>", self.updateValues)
        self.dx.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.dx, _("Camera offset from gantry"))

        self.dy = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.dy.grid(row=row, column=2, sticky=EW)
        self.dy.bind("<Return>",   self.updateValues)
        self.dy.bind("<KP_Enter>", self.updateValues)
        self.dy.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.dy, _("Camera offset from gantry"))

        self.z = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.z.grid(row=row, column=3, sticky=EW)
        self.z.bind("<Return>",   self.updateValues)
        self.z.bind("<KP_Enter>", self.updateValues)
        self.z.bind("<FocusOut>", self.updateValues)
        tkExtra.Balloon.set(self.z, _("Spindle Z position when camera was registered"))

        row += 1
        Label(lframe, text=_("Register:")).grid(row=row, column=0, sticky=E)
        b = Button(lframe, text=_("1. Spindle"),
                command=self.registerSpindle,
                padx=1,
                pady=1)
        tkExtra.Balloon.set(b, _("Mark spindle position for calculating offset"))
        b.grid(row=row, column=1, sticky=EW)
        b = Button(lframe, text=_("2. Camera"),
                command=self.registerCamera,
                padx=1,
                pady=1)
        tkExtra.Balloon.set(b, _("Mark camera position for calculating offset"))
        b.grid(row=row, column=2, sticky=EW)

        lframe.grid_columnconfigure(1, weight=1)
        lframe.grid_columnconfigure(2, weight=1)
        lframe.grid_columnconfigure(3, weight=1)

        self.loadConfig()
        self.location.config(command=self.updateValues)
        self.spindleX = None
        self.spindleY = None

    def saveConfig(self):
        IniFile.set_value("Camera", "aligncam_anchor", self.location.get())
        IniFile.set_value("Camera", "aligncam_d", self.diameter.get())
        IniFile.set_value("Camera", "aligncam_scale", self.scale.get())
        IniFile.set_value("Camera", "aligncam_dx", self.dx.get())
        IniFile.set_value("Camera", "aligncam_dy", self.dy.get())
        IniFile.set_value("Camera", "aligncam_z", self.z.get())
        IniFile.set_value("Camera", "aligncam_rotation", self.rotation.get())
        IniFile.set_value("Camera", "aligncam_xcenter", self.xcenter.get())
        IniFile.set_value("Camera", "aligncam_ycenter", self.ycenter.get())

    def loadConfig(self):
        self.location.set(IniFile.get_str("Camera",  "aligncam_anchor"))
        self.diameter.set(IniFile.get_float("Camera", "aligncam_d"))
        self.scale.set(IniFile.get_float("Camera", "aligncam_scale"))
        self.dx.set(IniFile.get_float("Camera", "aligncam_dx"))
        self.dy.set(IniFile.get_float("Camera", "aligncam_dy"))
        self.z.set(IniFile.get_float("Camera", "aligncam_z", ""))
        self.rotation.set(IniFile.get_float("Camera", "aligncam_rotation"))
        self.xcenter.set(IniFile.get_float("Camera", "aligncam_xcenter"))
        self.ycenter.set(IniFile.get_float("Camera", "aligncam_ycenter"))
        self.updateValues()

    def cameraAnchor(self):
        """Return camera Anchor"""
        return CAMERA_LOCATION.get(self.location.get(),CENTER)

    def getDiameter(self):
        self.diameter.set(OCV.CD["diameter"])
        self.updateValues()

    #-----------------------------------------------------------------------
    # Update canvas with values
    #-----------------------------------------------------------------------
    def updateValues(self, *args):
        OCV.CANVAS_F.canvas.cameraAnchor = self.cameraAnchor()
        try: OCV.CANVAS_F.canvas.cameraRotation = float(self.rotation.get())
        except ValueError: pass
        try: OCV.CANVAS_F.canvas.cameraXCenter = float(self.xcenter.get())
        except ValueError: pass
        try: OCV.CANVAS_F.canvas.cameraYCenter = float(self.ycenter.get())
        except ValueError: pass
        try: OCV.CANVAS_F.canvas.cameraScale = max(0.0001, float(self.scale.get()))
        except ValueError: pass
        try: OCV.CANVAS_F.canvas.cameraR = float(self.diameter.get())/2.0
        except ValueError: pass
        try: OCV.CANVAS_F.canvas.cameraDx = float(self.dx.get())
        except ValueError: pass
        try: OCV.CANVAS_F.canvas.cameraDy = float(self.dy.get())
        except ValueError: pass
        try:
            OCV.CANVAS_F.canvas.cameraZ  = float(self.z.get())
        except ValueError:
            OCV.CANVAS_F.canvas.cameraZ  = None
        OCV.CANVAS_F.canvas.cameraUpdate()

    #-----------------------------------------------------------------------
    # Register spindle position
    #-----------------------------------------------------------------------
    def registerSpindle(self):
        self.spindleX = OCV.CD["wx"]
        self.spindleY = OCV.CD["wy"]
        self.event_generate("<<Status>>", data=_("Spindle position is registered"))

    #-----------------------------------------------------------------------
    # Register camera position
    #-----------------------------------------------------------------------
    def registerCamera(self):
        if self.spindleX is None:
            tkMessageBox.showwarning(_("Spindle position is not registered"),
                    _("Spindle position must be registered before camera"),
                    parent=self)
            return
        self.dx.set(str(self.spindleX - OCV.CD["wx"]))
        self.dy.set(str(self.spindleY - OCV.CD["wy"]))
        self.z.set(str(OCV.CD["wz"]))
        self.event_generate("<<Status>>", data=_("Camera offset is updated"))
        self.updateValues()

#    #-----------------------------------------------------------------------
#    def findScale(self):
#        return
#        OCV.CANVAS_F.canvas.cameraMakeTemplate(30)
#
#        OCV.APP.control.jog_x_up()
#        #OCV.APP.wait4Idle()
#        time.sleep(2)
#        dx,dy = OCV.CANVAS_F.canvas.cameraMatchTemplate()    # right
#
#        OCV.APP.control.jog_x_down()
#        OCV.APP.control.jog_x_down()
#        #OCV.APP.wait4Idle()
#        time.sleep(2)
#        dx,dy = OCV.CANVAS_F.canvas.cameraMatchTemplate()    # left
#
#        OCV.APP.control.jog_x_up()
#        OCV.APP.control.jog_y_up()
#        #OCV.APP.wait4Idle()
#        time.sleep(2)
#        dx,dy = OCV.CANVAS_F.canvas.cameraMatchTemplate()    # top
#
#        OCV.APP.control.jog_y_down()
#        OCV.APP.control.jog_y_down()
#        #OCV.APP.wait4Idle()
#        time.sleep(2)
#        dx,dy = OCV.CANVAS_F.canvas.cameraMatchTemplate()    # down
#
#        OCV.APP.control.jog_y_up()

    #-----------------------------------------------------------------------
    # Move camera to spindle location and change coordinates to relative
    # to camera via g92
    #-----------------------------------------------------------------------
#    def switch2Camera(self, event=None):
#        print "Switch to camera"
#        wx = OCV.CD["wx"]
#        wy = OCV.CD["wy"]
#        dx = float(self.dx.get())
#        dy = float(self.dy.get())
#        if self.switchVar.get():
#            self.sendGCode("G92X%gY%g"%(dx+wx,dy+wy))
#        else:
#            self.sendGCode("G92.1")
#        self.sendGCode("G0X%gY%g"%(wx,wy))


#===============================================================================
# Tool Group
#===============================================================================
class ToolGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "Probe:Tool", app)
        self.label["background"] = OCV.BACKGROUND_GROUP2

        b = Ribbon.LabelButton(self.frame, self, "<<ToolCalibrate>>",
                image=OCV.icons["calibrate32"],
                text=_("Calibrate"),
                compound=TOP,
                width=48,
                background=OCV.BACKGROUND)
        b.pack(side=LEFT, fill=BOTH, expand=YES)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Perform a single a tool change cycle to set the calibration field"))

        b = Ribbon.LabelButton(self.frame, self, "<<ToolChange>>",
                image=OCV.icons["endmill32"],
                text=_("Change"),
                compound=TOP,
                width=48,
                background=OCV.BACKGROUND)
        b.pack(side=LEFT, fill=BOTH, expand=YES)
        self.addWidget(b)
        tkExtra.Balloon.set(b, _("Perform a tool change cycle"))


#===============================================================================
# Tool Frame
#===============================================================================
class ToolFrame(CNCRibbon.PageFrame):
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "Probe:Tool", app)

        lframe = LabelFrame(self, text=_("Manual Tool Change"), foreground="DarkBlue")
        lframe.pack(side=TOP, fill=X)

        # --- Tool policy ---
        row,col = 0,0
        Label(lframe, text=_("Policy:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.toolPolicy = tkExtra.Combobox(lframe, True,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    command=self.policyChange,
                    width=16)
        self.toolPolicy.grid(row=row, column=col, columnspan=3, sticky=EW)
        self.toolPolicy.fill(TOOL_POLICY)
        self.toolPolicy.set(TOOL_POLICY[0])
        tkExtra.Balloon.set(self.toolPolicy, _("Tool change policy"))
        self.addWidget(self.toolPolicy)

        # ----
        row += 1
        col  = 0
        Label(lframe, text=_("Pause:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.toolWait = tkExtra.Combobox(lframe, True,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    command=self.waitChange,
                    width=16)
        self.toolWait.grid(row=row, column=col, columnspan=3, sticky=EW)
        self.toolWait.fill(TOOL_WAIT)
        self.toolWait.set(TOOL_WAIT[1])
        self.addWidget(self.toolWait)

        # ----
        row += 1
        col  = 1
        Label(lframe, text=_("MX")).grid(row=row, column=col, sticky=EW)
        col += 1
        Label(lframe, text=_("MY")).grid(row=row, column=col, sticky=EW)
        col += 1
        Label(lframe, text=_("MZ")).grid(row=row, column=col, sticky=EW)

        # --- Tool Change position ---
        row += 1
        col = 0
        Label(lframe, text=_("Change:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.changeX = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.changeX.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.changeX, _("Manual tool change Machine X location"))
        self.addWidget(self.changeX)
        self.changeX.bind('<KeyRelease>',   self.setProbeParams)
        self.changeX.bind('<FocusOut>',   self.setProbeParams)

        col += 1
        self.changeY = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.changeY.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.changeY, _("Manual tool change Machine Y location"))
        self.addWidget(self.changeY)
        self.changeY.bind('<KeyRelease>',   self.setProbeParams)
        self.changeY.bind('<FocusOut>',   self.setProbeParams)

        col += 1
        self.changeZ = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.changeZ.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.changeZ, _("Manual tool change Machine Z location"))
        self.addWidget(self.changeZ)
        self.changeZ.bind('<KeyRelease>',   self.setProbeParams)
        self.changeZ.bind('<FocusOut>', self.setProbeParams)

        col += 1
        b = Button(lframe, text=_("get"),
                command=self.getChange,
                padx=2, pady=1)
        b.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(b, _("Get current gantry position as machine tool change location"))
        self.addWidget(b)

        # --- Tool Probe position ---
        row += 1
        col = 0
        Label(lframe, text=_("Probe:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.probeX = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeX.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeX, _("Manual tool change Probing MX location"))
        self.addWidget(self.probeX)
        self.probeX.bind('<KeyRelease>',   self.setProbeParams)
        self.probeX.bind('<FocusOut>', self.setProbeParams)

        col += 1
        self.probeY = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeY.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeY, _("Manual tool change Probing MY location"))
        self.addWidget(self.probeY)
        self.probeY.bind('<KeyRelease>',   self.setProbeParams)
        self.probeY.bind('<FocusOut>', self.setProbeParams)

        col += 1
        self.probeZ = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeZ.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeZ, _("Manual tool change Probing MZ location"))
        self.addWidget(self.probeZ)
        self.probeZ.bind('<KeyRelease>',   self.setProbeParams)
        self.probeZ.bind('<FocusOut>', self.setProbeParams)

        col += 1
        b = Button(lframe, text=_("get"),
                command=self.getProbe,
                padx=2, pady=1)
        b.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(b, _("Get current gantry position as machine tool probe location"))
        self.addWidget(b)

        # --- Probe Distance ---
        row += 1
        col = 0
        Label(lframe, text=_("Distance:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.probeDistance = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.probeDistance.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.probeDistance,
                _("After a tool change distance to scan starting from ProbeZ"))
        self.addWidget(self.probeDistance)
        self.probeDistance.bind('<KeyRelease>',   self.setProbeParams)
        self.probeDistance.bind('<FocusOut>', self.setProbeParams)

        # --- Calibration ---
        row += 1
        col = 0
        Label(lframe, text=_("Calibration:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.toolHeight = tkExtra.FloatEntry(lframe, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.toolHeight.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.toolHeight, _("Tool probe height"))
        self.addWidget(self.toolHeight)

        col += 1
        b = Button(lframe, text=_("Calibrate"),
                command=self.calibrate,
                padx=2, pady=1)
        b.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(b, _("Perform a calibration probing to determine the height"))
        self.addWidget(b)

        lframe.grid_columnconfigure(1,weight=1)
        lframe.grid_columnconfigure(2,weight=1)
        lframe.grid_columnconfigure(3,weight=1)

        self.loadConfig()

    #-----------------------------------------------------------------------
    def saveConfig(self):
        IniFile.set_value(
                "Probe", "toolpolicy",
                TOOL_POLICY.index(self.toolPolicy.get()))
        IniFile.set_value(
                "Probe", "toolwait",
                TOOL_WAIT.index(self.toolWait.get()))
        IniFile.set_value("Probe", "toolchangex", self.changeX.get())
        IniFile.set_value("Probe", "toolchangey", self.changeY.get())
        IniFile.set_value("Probe", "toolchangez", self.changeZ.get())

        IniFile.set_value("Probe", "toolprobex", self.probeX.get())
        IniFile.set_value("Probe", "toolprobey", self.probeY.get())
        IniFile.set_value("Probe", "toolprobez", self.probeZ.get())

        IniFile.set_value("Probe", "tooldistance",self.probeDistance.get())
        IniFile.set_value("Probe", "toolheight",  self.toolHeight.get())
        IniFile.set_value("Probe", "toolmz",      OCV.CD.get("toolmz",0.))

    #-----------------------------------------------------------------------
    def loadConfig(self):
        self.changeX.set(IniFile.get_float("Probe","toolchangex"))
        self.changeY.set(IniFile.get_float("Probe","toolchangey"))
        self.changeZ.set(IniFile.get_float("Probe","toolchangez"))

        self.probeX.set(IniFile.get_float("Probe","toolprobex"))
        self.probeY.set(IniFile.get_float("Probe","toolprobey"))
        self.probeZ.set(IniFile.get_float("Probe","toolprobez"))

        self.probeDistance.set(IniFile.get_float("Probe","tooldistance"))
        self.toolHeight.set(   IniFile.get_float("Probe","toolheight"))
        self.toolPolicy.set(TOOL_POLICY[IniFile.get_int("Probe","toolpolicy",0)])
        self.toolWait.set(TOOL_WAIT[IniFile.get_int("Probe","toolwait",1)])
        OCV.CD["toolmz"] = IniFile.get_float("Probe","toolmz")
        self.set()

    #-----------------------------------------------------------------------
    def set(self):
        self.policyChange()
        self.waitChange()
        try:
            OCV.CD["toolchangex"]  = float(self.changeX.get())
            OCV.CD["toolchangey"]  = float(self.changeY.get())
            OCV.CD["toolchangez"]  = float(self.changeZ.get())
        except:
            tkMessageBox.showerror(_("Probe Tool Change Error"),
                    _("Invalid tool change position"),
                    parent=self.winfo_toplevel())
            return

        try:
            OCV.CD["toolprobex"]   = float(self.probeX.get())
            OCV.CD["toolprobey"]   = float(self.probeY.get())
            OCV.CD["toolprobez"]   = float(self.probeZ.get())
        except:
            tkMessageBox.showerror(_("Probe Tool Change Error"),
                    _("Invalid tool probe location"),
                    parent=self.winfo_toplevel())
            return

        try:
            OCV.CD["tooldistance"] = abs(float(self.probeDistance.get()))
        except:
            tkMessageBox.showerror(_("Probe Tool Change Error"),
                    _("Invalid tool scanning distance entered"),
                    parent=self.winfo_toplevel())
            return

        try:
            OCV.CD["toolheight"]   = float(self.toolHeight.get())
        except:
            tkMessageBox.showerror(_("Probe Tool Change Error"),
                    _("Invalid tool height or not calibrated"),
                    parent=self.winfo_toplevel())
            return


    def check4Errors(self):
        if OCV.CD["tooldistance"] <= 0.0:
            tkMessageBox.showerror(_("Probe Tool Change Error"),
                    _("Invalid tool scanning distance entered"),
                    parent=self.winfo_toplevel())
            return True
        return False


    def policyChange(self):
        OCV.toolPolicy = int(TOOL_POLICY.index(self.toolPolicy.get()))


    def waitChange(self):
        OCV.toolWaitAfterProbe = int(TOOL_WAIT.index(self.toolWait.get()))


    def setProbeParams(self, dummy=None):
        print("probe chg handler")
        OCV.CD["toolchangex"] = float(self.changeX.get())
        OCV.CD["toolchangey"] = float(self.changeY.get())
        OCV.CD["toolchangez"] = float(self.changeZ.get())
        OCV.CD["toolprobex"] = float(self.probeX.get())
        OCV.CD["toolprobey"] = float(self.probeY.get())
        OCV.CD["toolprobez"] = float(self.probeZ.get())
        OCV.CD["toolprobez"] = float(self.probeZ.get())
        OCV.CD["tooldistance"] = float(self.probeDistance.get())

    #-----------------------------------------------------------------------
    def getChange(self):
        self.changeX.set(OCV.CD["mx"])
        self.changeY.set(OCV.CD["my"])
        self.changeZ.set(OCV.CD["mz"])
        self.setProbeParams()

    #-----------------------------------------------------------------------
    def getProbe(self):
        self.probeX.set(OCV.CD["mx"])
        self.probeY.set(OCV.CD["my"])
        self.probeZ.set(OCV.CD["mz"])
        self.setProbeParams()

    #-----------------------------------------------------------------------
    def updateTool(self):
        state = self.toolHeight.cget("state")
        self.toolHeight.config(state=NORMAL)
        self.toolHeight.set(OCV.CD["toolheight"])
        self.toolHeight.config(state=state)

    #-----------------------------------------------------------------------
    def calibrate(self, event=None):
        self.set()
        if self.check4Errors(): return
        lines = []
        lines.append("g53 g0 z[toolchangez]")
        lines.append("g53 g0 x[toolchangex] y[toolchangey]")
        lines.append("g53 g0 x[toolprobex] y[toolprobey]")
        lines.append("g53 g0 z[toolprobez]")
        if OCV.CD["fastprbfeed"]:
            prb_reverse = {"2": "4", "3": "5", "4": "2", "5": "3"}
            OCV.CD["prbcmdreverse"] = (OCV.CD["prbcmd"][:-1] +
                        prb_reverse[OCV.CD["prbcmd"][-1]])
            currentFeedrate = OCV.CD["fastprbfeed"]
            while currentFeedrate > OCV.CD["prbfeed"]:
                lines.append("%wait")
                lines.append("g91 [prbcmd] {0} z[toolprobez-mz-tooldistance]".format(
                        CNC.fmt('f',currentFeedrate)))
                lines.append("%wait")
                lines.append("[prbcmdreverse] {0} z[toolprobez-mz]".format(
                        CNC.fmt('f',currentFeedrate)))
                currentFeedrate /= 10
        lines.append("%wait")
        lines.append("g91 [prbcmd] f[prbfeed] z[toolprobez-mz-tooldistance]")
        lines.append("g4 p1")    # wait a sec
        lines.append("%wait")
        lines.append("%global toolheight; toolheight=wz")
        lines.append("%global toolmz; toolmz=prbz")
        lines.append("%update toolheight")
        lines.append("g53 g0 z[toolchangez]")
        lines.append("g53 g0 x[toolchangex] y[toolchangey]")
        lines.append("g90")
        OCV.APP.run(lines=lines)

    #-----------------------------------------------------------------------
    # FIXME should be replaced with the CNC.toolChange()
    #-----------------------------------------------------------------------
    def change(self, event=None):
        self.set()
        if self.check4Errors(): return
        lines = OCV.APP.cnc.toolChange(0)
        OCV.APP.run(lines=lines)

##===============================================================================
## Help Frame
##===============================================================================
#class HelpFrame(CNCRibbon.PageFrame):
#    def __init__(self, master, app):
#        CNCRibbon.PageFrame.__init__(self, master, "Help", app)
#
#        lframe = tkExtra.ExLabelFrame(self, text="Help", foreground="DarkBlue")
#        lframe.pack(side=TOP, fill=X)
#        frame = lframe.frame
#
#        self.text = Label(frame,
#                text="One\nTwo\nThree",
#                image=OCV.icons["gear32"],
#                compound=TOP,
#                anchor=W,
#                justify=LEFT)
#        self.text.pack(fill=BOTH, expand=YES)


#===============================================================================
# Probe Page
#===============================================================================
class ProbePage(CNCRibbon.Page):
    __doc__ = _("Probe configuration and probing")
    _name_  = "Probe"
    _icon_  = "measure"

    #-----------------------------------------------------------------------
    # Add a widget in the widgets list to enable disable during the run
    #-----------------------------------------------------------------------
    def register(self):
        self._register((ProbeTabGroup, AutolevelGroup, CameraGroup, ToolGroup),
            (ProbeCommonFrame, ProbeFrame, AutolevelFrame, CameraFrame, ToolFrame))

        self.tabGroup = CNCRibbon.Page.groups["Probe"]
        self.tabGroup.tab.set("Probe")
        self.tabGroup.tab.trace('w', self.tabChange)

    #-----------------------------------------------------------------------
    def tabChange(self, a=None, b=None, c=None):
        tab = self.tabGroup.tab.get()
        self.master._forgetPage()

        # remove all page tabs with ":" and add the new ones
        self.ribbons = [ x for x in self.ribbons if ":" not in x[0].name ]
        self.frames  = [ x for x in self.frames  if ":" not in x[0].name ]

        try:
            self.addRibbonGroup("Probe:%s"%(tab))
        except KeyError:
            pass
        try:
            self.addPageFrame("Probe:%s"%(tab))
        except KeyError:
            pass

        self.master.changePage(self)
