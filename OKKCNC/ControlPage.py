# -*- coding: ascii -*-
# $Id$
#
# Author: carlo.dormeletti@gmail.com
# Date: 26 Oct 2019

from __future__ import absolute_import
from __future__ import print_function

__author__  = "Carlo Dormeletti (onekk)"
__email__   = "carlo.dormeletti@gmail.com"

try:
    from Tkinter import *
    import tkMessageBox
    import tkSimpleDialog
except ImportError:
    from tkinter import *
    import tkinter.messagebox as tkMessageBox

import math
from math import * #Math in DRO

import OCV
#from CNC import CNC
import Utils
import Ribbon
import Sender
import tkExtra
import Unicode
import CNCRibbon
#import CNCCanvas
import CAMGen
from Sender import ERROR_CODES
from CNC import Block,WCS, DISTANCE_MODE, FEED_MODE, UNITS, PLANE

_LOWSTEP   = 0.0001
_HIGHSTEP  = 1000.0
_HIGHZSTEP = 10.0
_NOZSTEP = 'XY'

OVERRIDES = ["Feed", "Rapid", "Spindle"]


#===============================================================================
# Connection Group
#===============================================================================
class ConnectionGroup(CNCRibbon.ButtonMenuGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(self, master, N_("Connection"), app,
            [(_("Hard Reset"), "reset", app.hardReset)])
        self.grid2rows()

        # ---
        col,row = 0, 0
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["home32"],
                text=_("Home"),
                compound=TOP,
                anchor=W,
                command=app.home,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Perform a homing cycle [$H]"))
        self.addWidget(b)

        # ---
        col,row = 1, 0
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["unlock"],
                text=_("Unlock"),
                compound=LEFT,
                anchor=W,
                command=app.mcontrol.unlock(True),
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Unlock controller [$X]"))
        self.addWidget(b)

        row += 1
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["serial"],
                text=_("Connection"),
                compound=LEFT,
                anchor=W,
                command=lambda s=self : s.event_generate("<<Connect>>"),
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Open/Close connection"))
        self.addWidget(b)

        row += 1
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["reset"],
                text=_("Reset"),
                compound=LEFT,
                anchor=W,
                command=app.mcontrol.softReset(True),
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Software reset of controller [ctrl-x]"))
        self.addWidget(b)


#===============================================================================
# User Group
#===============================================================================
class UserGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "User", app)
        self.grid3rows()

        n = Utils.getInt("Buttons","n",6)
        for i in range(1,n):
            b = Utils.UserButton(self.frame, self.app, i,
                    anchor=W,
                    background=OCV.BACKGROUND)
            col,row = divmod(i-1,3)
            b.grid(row=row, column=col, sticky=NSEW)
            self.addWidget(b)


#===============================================================================
# Run Group
#===============================================================================
class RunGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "Run", app)

        b = Ribbon.LabelButton(self.frame, self, "<<Run>>",
                image=Utils.icons["start32"],
                text=_("Start"),
                compound=TOP,
                background=OCV.BACKGROUND)
        b.pack(side=LEFT, fill=BOTH)
        tkExtra.Balloon.set(b, _("Run g-code commands from editor to controller"))
        self.addWidget(b)

        b = Ribbon.LabelButton(self.frame, self, "<<Pause>>",
                image=Utils.icons["pause32"],
                text=_("Pause"),
                compound=TOP,
                background=OCV.BACKGROUND)
        b.pack(side=LEFT, fill=BOTH)
        tkExtra.Balloon.set(b, _("Pause running program. Sends either FEED_HOLD ! or CYCLE_START ~"))

        b = Ribbon.LabelButton(self.frame, self, "<<Stop>>",
                image=Utils.icons["stop32"],
                text=_("Stop"),
                compound=TOP,
                background=OCV.BACKGROUND)
        b.pack(side=LEFT, fill=BOTH)
        tkExtra.Balloon.set(b, _("Pause running program and soft reset controller to empty the buffer."))


#===============================================================================
# DRO Frame
#===============================================================================
class DROFrame(CNCRibbon.PageFrame):
    dro_status = ('Helvetica',12,'bold')
    dro_wpos   = ('Helvetica',12,'bold')
    dro_mpos   = ('Helvetica',12)

    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "DRO", app)

        DROFrame.dro_status = Utils.getFont("dro.status", DROFrame.dro_status)
        DROFrame.dro_wpos   = Utils.getFont("dro.wpos",   DROFrame.dro_wpos)
        DROFrame.dro_mpos   = Utils.getFont("dro.mpos",   DROFrame.dro_mpos)

        row = 0
        col = 0
        Label(self,text=_("Status:")).grid(row=row,column=col,sticky=E)
        col += 1
        self.state = Button(self,
                text=Sender.NOT_CONNECTED,
                font=DROFrame.dro_status,
                command=self.showState,
                cursor="hand1",
                background=Sender.STATECOLOR[Sender.NOT_CONNECTED],
                activebackground="LightYellow")
        self.state.grid(row=row,column=col, columnspan=3, sticky=EW)
        tkExtra.Balloon.set(self.state,
                _("Show current state of the machine\n"
                  "Click to see details\n"
                  "Right-Click to clear alarm/errors"))
        #self.state.bind("<Button-3>", lambda e,s=self : s.event_generate("<<AlarmClear>>"))
        self.state.bind("<Button-3>", self.stateMenu)

        row += 1
        col = 0
        Label(self,text=_("WPos:")).grid(row=row,column=col,sticky=E)

        # work
        col += 1
        self.xwork = Entry(self, font=DROFrame.dro_wpos,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    relief=FLAT,
                    borderwidth=0,
                    justify=RIGHT)
        self.xwork.grid(row=row,column=col,padx=1,sticky=EW)
        tkExtra.Balloon.set(self.xwork, _("X work position (click to set)"))
        self.xwork.bind('<FocusIn>',  self.workFocus)
        self.xwork.bind('<Return>',   self.setX)
        self.xwork.bind('<KP_Enter>', self.setX)

        # ---
        col += 1
        self.ywork = Entry(self, font=DROFrame.dro_wpos,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    relief=FLAT,
                    borderwidth=0,
                    justify=RIGHT)
        self.ywork.grid(row=row,column=col,padx=1,sticky=EW)
        tkExtra.Balloon.set(self.ywork, _("Y work position (click to set)"))
        self.ywork.bind('<FocusIn>',  self.workFocus)
        self.ywork.bind('<Return>',   self.setY)
        self.ywork.bind('<KP_Enter>', self.setY)

        # ---
        col += 1
        self.zwork = Entry(self, font=DROFrame.dro_wpos,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    relief=FLAT,
                    borderwidth=0,
                    justify=RIGHT)
        self.zwork.grid(row=row,column=col,padx=1,sticky=EW)
        tkExtra.Balloon.set(self.zwork, _("Z work position (click to set)"))
        self.zwork.bind('<FocusIn>',  self.workFocus)
        self.zwork.bind('<Return>',   self.setZ)
        self.zwork.bind('<KP_Enter>', self.setZ)

        # Machine
        row += 1
        col = 0
        Label(self,text=_("MPos:")).grid(row=row,column=col,sticky=E)

        col += 1
        self.xmachine = Label(self, font=DROFrame.dro_mpos, background=tkExtra.GLOBAL_CONTROL_BACKGROUND,anchor=E)
        self.xmachine.grid(row=row,column=col,padx=1,sticky=EW)

        col += 1
        self.ymachine = Label(self, font=DROFrame.dro_mpos, background=tkExtra.GLOBAL_CONTROL_BACKGROUND,anchor=E)
        self.ymachine.grid(row=row,column=col,padx=1,sticky=EW)

        col += 1
        self.zmachine = Label(self, font=DROFrame.dro_mpos, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, anchor=E)
        self.zmachine.grid(row=row,column=col,padx=1,sticky=EW)

        # Set buttons
        row += 1
        col = 1

        self.xzero = Button(self, text=_("X=0"),
                command=self.setX0,
                activebackground="LightYellow",
                padx=2, pady=1)
        self.xzero.grid(row=row, column=col, pady=0, sticky=EW)
        tkExtra.Balloon.set(self.xzero, _("Set X coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.xzero)

        col += 1
        self.yzero = Button(self, text=_("Y=0"),
                command=self.setY0,
                activebackground="LightYellow",
                padx=2, pady=1)
        self.yzero.grid(row=row, column=col, pady=0, sticky=EW)
        tkExtra.Balloon.set(self.yzero, _("Set Y coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.yzero)

        col += 1
        self.zzero = Button(self, text=_("Z=0"),
                command=self.setZ0,
                activebackground="LightYellow",
                padx=2, pady=1)
        self.zzero.grid(row=row, column=col, pady=0, sticky=EW)
        tkExtra.Balloon.set(self.zzero, _("Set Z coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.zzero)

        # Set buttons
        row += 1
        col = 1
        self.xyzero = Button(self, text=_("XY=0"),
                command=self.setXY0,
                activebackground="LightYellow",
                padx=2, pady=1)
        self.xyzero.grid(row=row, column=col, pady=0, sticky=EW)
        tkExtra.Balloon.set(self.xyzero, _("Set XY coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.xyzero)

        col += 1
        self.xyzzero = Button(self, text=_("XYZ=0"),
                command=self.setXYZ0,
                activebackground="LightYellow",
                padx=2, pady=1)
        self.xyzzero.grid(row=row, column=col, pady=0, sticky=EW, columnspan=2)
        tkExtra.Balloon.set(self.xyzzero, _("Set XYZ coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.xyzzero)

        # Set buttons
        row += 1
        col = 1
        f = Frame(self)
        f.grid(row=row, column=col, columnspan=3, pady=0, sticky=EW)

        b = Button(f, text=_("Set WPOS"),
                image=Utils.icons["origin"],
                compound=LEFT,
                activebackground="LightYellow",
                command=lambda s=self: s.event_generate("<<SetWPOS>>"),
                padx=2, pady=1)
        b.pack(side=LEFT,fill=X,expand=YES)
        tkExtra.Balloon.set(b, _("Set WPOS to mouse location"))
        self.addWidget(b)

        #col += 2
        b = Button(f, text=_("Move Gantry"),
                image=Utils.icons["gantry"],
                compound=LEFT,
                activebackground="LightYellow",
                command=lambda s=self: s.event_generate("<<MoveGantry>>"),
                padx=2, pady=1)
        #b.grid(row=row, column=col, pady=0, sticky=EW)
        b.pack(side=RIGHT,fill=X,expand=YES)
        tkExtra.Balloon.set(b, _("Move gantry to mouse location [g]"))
        self.addWidget(b)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

    #----------------------------------------------------------------------
    def stateMenu(self, event=None):
        menu = Menu(self, tearoff=0)

        menu.add_command(label=_("Show Info"), image=Utils.icons["info"], compound=LEFT,
                    command=self.showState)
        menu.add_command(label=_("Clear Message"), image=Utils.icons["clear"], compound=LEFT,
                    command=lambda s=self: s.event_generate("<<AlarmClear>>"))
        menu.add_separator()

        menu.add_command(label=_("Feed hold"), image=Utils.icons["pause"], compound=LEFT,
                    command=lambda s=self: s.event_generate("<<FeedHold>>"))
        menu.add_command(label=_("Resume"), image=Utils.icons["start"], compound=LEFT,
                    command=lambda s=self: s.event_generate("<<Resume>>"))

        menu.tk_popup(event.x_root, event.y_root)

    #----------------------------------------------------------------------
    def updateState(self):
        msg = self.app._msg or OCV.CD["state"]
        if OCV.CD["pins"] is not None and OCV.CD["pins"] != "":
            msg += " ["+OCV.CD["pins"]+"]"
        self.state.config(text=msg, background=OCV.CD["color"])

    #----------------------------------------------------------------------
    def updateCoords(self):
        try:
            focus = self.focus_get()
        except:
            focus = None
        if focus is not self.xwork:
            self.xwork.delete(0,END)
            self.xwork.insert(0,self.padFloat(OCV.drozeropad,OCV.CD["wx"]))
        if focus is not self.ywork:
            self.ywork.delete(0,END)
            self.ywork.insert(0,self.padFloat(OCV.drozeropad,OCV.CD["wy"]))
        if focus is not self.zwork:
            self.zwork.delete(0,END)
            self.zwork.insert(0,self.padFloat(OCV.drozeropad,OCV.CD["wz"]))

        self.xmachine["text"] = self.padFloat(OCV.drozeropad,OCV.CD["mx"])
        self.ymachine["text"] = self.padFloat(OCV.drozeropad,OCV.CD["my"])
        self.zmachine["text"] = self.padFloat(OCV.drozeropad,OCV.CD["mz"])

    #----------------------------------------------------------------------
    def padFloat(self, decimals, value):
        if decimals>0:
            return "%0.*f"%(decimals, value)
        else:
            return value

    #----------------------------------------------------------------------
    # Do not give the focus while we are running
    #----------------------------------------------------------------------
    def workFocus(self, event=None):
        if self.app.running:
            self.app.focus_set()

    #----------------------------------------------------------------------
    def setX0(self, event=None):
        self.app.mcontrol._wcsSet("0",None,None)

    #----------------------------------------------------------------------
    def setY0(self, event=None):
        self.app.mcontrol._wcsSet(None,"0",None)

    #----------------------------------------------------------------------
    def setZ0(self, event=None):
        self.app.mcontrol._wcsSet(None,None,"0")

    #----------------------------------------------------------------------
    def setXY0(self, event=None):
        self.app.mcontrol._wcsSet("0","0",None)

    #----------------------------------------------------------------------
    def setXYZ0(self, event=None):
        self.app.mcontrol._wcsSet("0","0","0")

    #----------------------------------------------------------------------
    def setX(self, event=None):
        if self.app.running: return
        try:
            value = round(eval(self.xwork.get(), None, OCV.CD), 3)
            self.app.mcontrol._wcsSet(value,None,None)
        except:
            pass

    #----------------------------------------------------------------------
    def setY(self, event=None):
        if self.app.running: return
        try:
            value = round(eval(self.ywork.get(), None, OCV.CD), 3)
            self.app.mcontrol._wcsSet(None,value,None)
        except:
            pass

    #----------------------------------------------------------------------
    def setZ(self, event=None):
        if self.app.running: return
        try:
            value = round(eval(self.zwork.get(), None, OCV.CD), 3)
            self.app.mcontrol._wcsSet(None,None,value)
        except:
            pass

    def showState(self):
        err = OCV.CD["errline"]
        if err:
            msg  = _("Last error: %s\n")%(OCV.CD["errline"])
        else:
            msg = ""

        state = OCV.CD["state"]
        msg += ERROR_CODES.get(state,
                _("No info available.\nPlease contact the author."))
        tkMessageBox.showinfo(_("State: %s")%(state), msg, parent=self)

#===============================================================================
# ControlFrame
#===============================================================================
class ControlFrame(CNCRibbon.PageLabelFrame):

    z_step_font = ('Helvetica',7,'bold')
    memA_Set = False
    memB_Set = False

    def __init__(self, master, app):
        CNCRibbon.PageLabelFrame.__init__(self, master, "Control", _("Control"), app)

        Label(self, text="Y").grid(row=6, column=3)

        Label(self,"",width=1).grid(row=1,column=10)

        b_width = 2
        b_height = 2

        z_step_font = Utils.getFont("z_step.font", ControlFrame.z_step_font)

        Utils.SetSteps()

        row = 0

        zstep = Utils.config.get("Control","zstep")
        self.zstep = tkExtra.Combobox(self, width=4, background="White")
        self.zstep.grid(row=row, column=0, columnspan=4, sticky=EW)
        self.zstep.set(zstep)
        self.zstep.fill(map(float, Utils.config.get("Control","zsteplist").split()))
        tkExtra.Balloon.set(self.zstep, _("Step for Z move operation"))
        self.addWidget(self.zstep)

        b = Button(self, text="%s"%(OCV.step1),
                name="step_1",
                command=self.setStep1,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column = 4, columnspan = 2, sticky=EW)
        b.bind("<Button-3>", lambda event: self.InputValue("S0"))
        tkExtra.Balloon.set(b, _("Use step1"))
        self.addWidget(b)


        b = Button(self, text="%s"%(OCV.step2),
                name="step_2",
                command=self.setStep2,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column = 6, columnspan = 2, sticky=EW)
        b.bind("<Button-3>", lambda event: self.InputValue("S1"))
        tkExtra.Balloon.set(b, _("Use step2"))
        self.addWidget(b)


        b = Button(self, text="%s"%(OCV.step3),
                name="step_3",
                command=self.setStep3,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=8, columnspan = 2, sticky=EW)
        b.bind("<Button-3>", lambda event: self.InputValue("S2"))
        tkExtra.Balloon.set(b, _("Use step3"))
        self.addWidget(b)

        row = 1

        b = Button(self, text=u"\u00F75",
                    command=self.divStep,
                    width=3,
                    padx=1, pady=1)
        b.grid(row=row, column=4, sticky=EW)
        tkExtra.Balloon.set(b, _("Divide step by 5"))
        self.addWidget(b)

        b = Button(self, text=u"\u00D75",
                command=self.mulStep,
                width=3,
                padx=1, pady=1)
        b.grid(row=row, column=5, sticky=EW)
        tkExtra.Balloon.set(b, _("Multiply step by 5"))
        self.addWidget(b)

        self.step = tkExtra.Combobox(self, width=6, background="White")
        self.step.grid(row=row, column=6, columnspan=2, sticky=EW)
        self.step.set(Utils.config.get("Control","step"))
        self.step.fill(map(float, Utils.config.get("Control","steplist").split()))
        tkExtra.Balloon.set(self.step, _("Step for coarse move operation"))
        self.addWidget(self.step)

        b = Button(self, text="<",
                    command=self.decStep,
                    width=3,
                    padx=1, pady=1)
        b.grid(row=row, column=8, sticky=EW)
        tkExtra.Balloon.set(b, _("Decrease step"))
        self.addWidget(b)

        b = Button(self, text=">",
                command=self.incStep,
                width=3,
                padx=1, pady=1)
        b.grid(row=row, column=9, sticky=EW)
        tkExtra.Balloon.set(b, _("Increase step"))
        self.addWidget(b)

        row = 2

        b = Button(self, text="-",
                command=self.decZStep,
                padx=1, pady=1)
        b.grid(row=row, column=0, sticky=EW)
        tkExtra.Balloon.set(b, _("Decrease zstep"))
        self.addWidget(b)

        b = Button(self, text="+",
                command=self.incZStep,
                padx=1, pady=1)
        b.grid(row=row, column=1, sticky=EW)
        tkExtra.Balloon.set(b, _("Increase zstep"))
        self.addWidget(b)

        b = Button(self, text="-",
                    command=self.decStepF,
                    width=3,
                    padx=1, pady=1)
        b.grid(row=row, column=8, sticky=EW)
        tkExtra.Balloon.set(b, _("Decrease step fine"))
        self.addWidget(b)

        b = Button(self, text="+",
                command=self.incStepF,
                width=3,
                padx=1, pady=1)
        b.grid(row=row, column=9, sticky=EW)
        tkExtra.Balloon.set(b, _("Increase step fine"))
        self.addWidget(b)

        row = 3

        Label(self, text="Z").grid(row=3, column=0, columnspan=2)
        Label(self, text="X").grid(row=3,column=6, columnspan=2)

        row = 4

        b = Button(self, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
                    command=self.moveZup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=0,columnspan=2,rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move +Z"))
        self.addWidget(b)

        b = Button(self, text=Unicode.UPPER_LEFT_TRIANGLE,
                    command=self.moveXdownYup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")

        b.grid(row=row, column=4, columnspan=2,rowspan=2,  sticky=EW)
        tkExtra.Balloon.set(b, _("Move -X +Y"))
        self.addWidget(b)

        b = Button(self, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
                    command=self.moveYup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=6, columnspan=2, rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move +Y"))
        self.addWidget(b)

        b = Button(self, text=Unicode.UPPER_RIGHT_TRIANGLE,
                    command=self.moveXupYup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=8, columnspan=2, rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move +X +Y"))
        self.addWidget(b)

        row = 6

        b = Button(self, text="%s"%(OCV.zstep1),
                name="zstep_1",
                font =  z_step_font,
                command=self.setZStep1,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=0, columnspan = 1, sticky=EW)
        b.bind("<Button-3>" ,lambda event: self.InputValue("ZS0"))
        tkExtra.Balloon.set(b, "Zstep1 = %s"%(OCV.zstep1))
        self.addWidget(b)

        b = Button(self, text="%s"%(OCV.zstep2),
                name="zstep_2",
                font =  z_step_font,
                command=self.setZStep2,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=1, columnspan = 1, sticky=EW)
        tkExtra.Balloon.set(b,"Zstep2 = %s"%(OCV.zstep2))
        self.addWidget(b)


        b = Button(self, text=Unicode.BLACK_LEFT_POINTING_TRIANGLE,
                    command=self.moveXdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=4, columnspan=2, rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move -X"))
        self.addWidget(b)

        b = Utils.UserButton(self, self.app, 0, text=Unicode.LARGE_CIRCLE,
                    command=self.go2origin,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=6, columnspan=2, rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move to Origin.\nUser configurable button.\nRight click to configure."))
        self.addWidget(b)

        b = Button(self, text=Unicode.BLACK_RIGHT_POINTING_TRIANGLE,
                    command=self.moveXup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=8, columnspan=2, rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move +X"))
        self.addWidget(b)


        row = 7

        b = Button(self, text="%s"%(OCV.zstep3),
                name="zstep_3",
                font =  z_step_font,
                command=self.setZStep3,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=0, columnspan = 1, sticky=EW)
        tkExtra.Balloon.set(b, "Zstep3 = %s"%(OCV.zstep3))
        self.addWidget(b)

        b = Button(self, text="%s"%(OCV.zstep4),
                name="zstep_4",
                font =  z_step_font,
                command=self.setZStep4,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=1, columnspan = 1, sticky=EW)
        tkExtra.Balloon.set(b, "Zstep4 = %s"%(OCV.zstep4))
        self.addWidget(b)

        row = 8

        b = Button(self, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
                    command=self.moveZdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=0, columnspan=2, rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move -Z"))
        self.addWidget(b)


        b = Button(self, text=Unicode.LOWER_LEFT_TRIANGLE,
                    command=self.moveXdownYdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=4,columnspan=2,rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move -X -Y"))
        self.addWidget(b)

        b = Button(self, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
                    command=self.moveYdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=6,columnspan=2,rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move -Y"))
        self.addWidget(b)

        b = Button(self, text=Unicode.LOWER_RIGHT_TRIANGLE,
                    command=self.moveXupYdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=8,columnspan=2,rowspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Move +X -Y"))
        self.addWidget(b)

        #----------------
        #- CAM controls -
        #----------------
        column = 11
        b_padx = 0
        b_pady = -1

        b = Button(self, text="RST",
                    name = "rst",
                    command=self.resetAll,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    background = "salmon",
                    activebackground="LightYellow")
        b.grid(row=0, column=column, columnspan=2, rowspan=1, sticky=EW)
        tkExtra.Balloon.set(b, _("Reset Gcode"))
        self.addWidget(b)

        b = Button(self, text="m A",
                    name = "memA",
                    command=self.memA,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    background = "orchid1",
                    activebackground="LightYellow")
        b.grid(row=1, column=column, columnspan=2, rowspan=1, sticky=EW)
        tkExtra.Balloon.set(b, _("Mem A"))
        self.addWidget(b)


        b = Button(self, text="m B",
                    name = "memB",
                    command=self.memB,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    background = "orchid1",
                    activebackground="LightYellow")
        b.grid(row=2, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Mem B"))
        self.addWidget(b)

        b = Button(self, text="line",
                    command=self.line,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=3, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Cut Line from memA to memB"))
        self.addWidget(b)

        b = Button(self, text="r_pt",
                    command=self.pocket,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=4, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Cut Pocket from memA to memB"))
        self.addWidget(b)



        b = Button(self, text="RmA",
                    command=self.retA,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=5, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Return to mem A"))
        self.addWidget(b)

        b = Button(self, text="RmB",
                    command=self.retB,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=6, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Return to mem B"))
        self.addWidget(b)

        b = Button(self, text="M_X",
                    command=self.memX,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=7, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Store position to mem N"))
        self.addWidget(b)

        b = Button(self, text="D_X",
                    command=self.del_memX,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=8, column=column, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(b, _("Delete mem N"))
        self.addWidget(b)


        try:
#            self.grid_anchor(CENTER)
            self.tk.call("grid","anchor",self,CENTER)
        except TclError:
            pass

    #----------------------------------------------------------------------
    def InputValue(self,caller):
        title_d = _("Enter A Value")
        title_c = ""
        c_t = 0
        if caller == "S0":
            title_c = "Enter Value for Step1:"
            min_value = 0.001
            max_value = 100.0
        elif caller == "S1":
            title_c = "Enter Value for Step2:"
            min_value = 0.001
            max_value = 1000.0
        elif caller == "S2":
            title_c = "Enter Value for Step3:"
            min_value = 0.001
            max_value = 1000.0
        elif caller == "ZS0":
            title_c = "Enter Value for Z Step1:"
            min_value = 0.001
            max_value = 10.0
        elif caller == "TD":
            title_c = "Enter Target Depth "
            min_value = -35.0
            max_value = 0.0
        elif caller == "MN":
            title_c = "Enter Memory Number"
            min_value = 2
            max_value = 99
            c_t = 1
        else:
            title_c = "Enter a float Value"
            min_value = 0.001
            max_value = 100.0

        if c_t == 0:
            prompt = "{0}\n (min: {1:.04f} max: {2:.04f})".format(title_c,
                      min_value,
                      max_value)
            retval = tkSimpleDialog.askfloat(title_d, prompt, parent = self,
                                             minvalue = min_value,
                                             maxvalue = max_value)
        elif c_t == 1:
            prompt = "{0}\n (min: {1:d} max: {2:d})".format(title_c,
                      min_value,
                      max_value)
            retval = tkSimpleDialog.askinteger(title_d, prompt, parent = self,
                                               minvalue = min_value,
                                               maxvalue = max_value)

        if caller == "S0":
            wd = self.nametowidget("step_1")
            OCV.step1 = retval
            Utils.setFloat("Control", "step1", retval)
        elif caller == "S1":
            wd = self.nametowidget("step_2")
            OCV.step2 = retval
            Utils.setFloat("Control", "step2", retval)
        elif caller == "S2":
            wd = self.nametowidget("step_3")
            OCV.step3 = retval
            Utils.setFloat("Control", "step3", retval)
        elif caller == "ZS0":
            wd = self.nametowidget("zstep_1")
            OCV.zstep1 = retval
            Utils.setFloat("Control", "zstep1", retval)
        else:
            return retval

        if wd is not None:
            wd.configure(text = retval)


    def saveConfig(self):
        Utils.setFloat("Control", "step", self.step.get())
        Utils.setFloat("Control", "zstep", self.zstep.get())

    def resetAll(self):
        self.event_generate("<<ClearEditor>>")
        wd = self.nametowidget("memA")
        tkExtra.Balloon.set(wd, "Empty")
        wd.configure(background = "orchid1")

        OCV.WK_mem = 0 # memA
        self.event_generate("<<ClrMem>>")
        self.memA_Set = False

        OCV.WK_mem = 1 # memB
        wd = self.nametowidget("memB")
        tkExtra.Balloon.set(wd, "Empty")
        wd.configure(background = "orchid1")

        self.event_generate("<<ClrMem>>")
        self.memB_Set = False

    def memA(self):
        if OCV.CD["state"] == "Idle":
            mBx = OCV.CD["wx"]
            mBy = OCV.CD["wy"]
            mBz = OCV.CD["wz"]
            OCV.WK_mem = 0 # 1= memB

            mem_name = "memA"
            OCV.WK_mems["mem_0"] = [mBx,mBy,mBz]
            wd = self.nametowidget(mem_name)

            wdata =  "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(mem_name,mBx, mBy, mBz)

            tkExtra.Balloon.set(wd, wdata)
            wd.configure(background = "aquamarine")

            self.event_generate("<<SetMem>>")
            self.memA_Set = True
        else:
            pass


    def memB(self):
        if OCV.CD["state"] == "Idle":
            mBx = OCV.CD["wx"]
            mBy = OCV.CD["wy"]
            mBz = OCV.CD["wz"]
            OCV.WK_mem = 1 # 1= memB

            mem_name = "memB"
            OCV.WK_mems["mem_1"] = [mBx,mBy,mBz]
            wd = self.nametowidget(mem_name)

            wdata =  "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(mem_name,mBx, mBy, mBz)

            tkExtra.Balloon.set(wd, wdata)
            wd.configure(background = "aquamarine")

            self.event_generate("<<SetMem>>")
            self.memB_Set = True
        else:
            pass

    def memX(self):
        if OCV.CD["state"] == "Idle":
            mBx = OCV.CD["wx"]
            mBy = OCV.CD["wy"]
            mBz = OCV.CD["wz"]

            OCV.WK_mem = self.InputValue("MN")

            if OCV.WK_mem == None:
                return
            elif OCV.WK_mem < 2 or OCV.WK_mem > 99:
                return
            else:
                pass

            mem_name = "mem_{0}".format(OCV.WK_mem)
            OCV.WK_mems[mem_name] = [mBx,mBy,mBz]

            self.event_generate("<<SetMem>>")

        else:
            pass

    def del_memX(self):
        if OCV.CD["state"] == "Idle":

            OCV.WK_mem = self.InputValue("MN")

            if OCV.WK_mem == None:
                return
            elif OCV.WK_mem < 2 or OCV.WK_mem > 99:
                return
            else:
                pass

            mem_name = "mem_{0}".format(OCV.WK_mem)
            OCV.WK_mems[mem_name] = [None,None,None]

            self.event_generate("<<ClrMem>>")

        else:
            pass

    def retA(self):
        if OCV.CD["state"] == "Idle":
            self.sendGCode("G90")
            self.sendGCode("G0 X{0:f} Y{1:f}".format( OCV.WK_mems["mem_0"][0],
                            OCV.WK_mems["mem_0"][1]))
        else:
            pass

    def retB(self):
        if OCV.CD["state"] == "Idle":
            self.sendGCode("G90")
            self.sendGCode("G0 X{0:f} Y{1:f}".format( OCV.WK_mems["mem_1"][0],
                            OCV.WK_mems["mem_1"][1]))
        else:
            pass

    def line(self):
        # avoid a dry run if both mem pos are not set
        if (self.memA_Set == True ) and (self.memB_Set == True ):

            endDepth = self.InputValue("TD")

            if endDepth is None:
                return

            CAMGen.line(self, self.app, endDepth, "mem_0", "mem_1")

    def pocket(self):

        # avoid a dry run if both mem pos are not set
        if (self.memA_Set == True ) and (self.memB_Set == True ):
            endDepth = self.InputValue("TD")

            if endDepth is None:
                return

            CAMGen.pocket(self, self.app, endDepth, "mem_0", "mem_1")


    #----------------------------------------------------------------------
    # Jogging
    #----------------------------------------------------------------------

    def moveXup(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f}".format("X", float(self.step.get())))

    def moveXdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f}".format("X-", float(self.step.get())))

    def moveYup(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f}".format("Y",float(self.step.get())))

    def moveYdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f}".format("Y-", float(self.step.get())))

    def moveXdownYup(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X-", float(self.step.get()),
                "Y", float(self.step.get())))

    def moveXupYup(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X", float(self.step.get()),
                "Y", float(self.step.get())))

    def moveXdownYdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X-", float(self.step.get()),
                "Y-", float(self.step.get())))

    def moveXupYdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X", float(self.step.get()),
                "Y-", float(self.step.get())))

    def moveZup(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f}".format("Z", float(self.zstep.get())))

    def moveZdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.app.mcontrol.jog("{0}{1:f}".format("Z-", float(self.zstep.get())))

    def go2origin(self, event=None):
        self.sendGCode("G90")
        self.sendGCode("G0Z{0:.{1}f}".format(OCV.CD['safe'], OCV.digits))
        self.sendGCode("G0X0Y0")
        self.sendGCode("G0Z0")


    def setStep(self, s, zs=None,fs=None):
        self.step.set("{0:.4f}".format(float(s)))

        if fs is not None:
            self.stepf.set("{0:.4f}".format(fs))

        if self.zstep is self.step or zs is None:
            self.event_generate("<<Status>>",
                data=_("Step: {0:.4f}".format(float(s))))
        else:
            self.zstep.set("{0:.4f}".format(float(zs)))
            self.event_generate("<<Status>>",
                data=_("Step: {0:.4f}    Zstep: {1:.4f} ".format(float(s),float(zs))))

    #----------------------------------------------------------------------
    @staticmethod
    def _stepPower(step):
        try:
            step = float(step)
            if step <= 0.0: step = 1.0
        except:
            step = 1.0
        power = math.pow(10.0,math.floor(math.log10(step)))
        return round(step/power)*power, power

    #----------------------------------------------------------------------
    def incStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step+power
        zs = None
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def incStepF(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(OCV.step1)
        s = float(self.step.get()) + power
        zs = None
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def incZStep(self, event=None):
        step, power = ControlFrame._stepPower(self.zstep.get())
        s = float(self.step.get())
        zs = step+power
        if zs<_LOWSTEP: zs = _LOWSTEP
        elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
        self.setStep(s,zs)

    #----------------------------------------------------------------------
    def decStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step - power
        zs = None
        if s<=0.0: s = step-power/10.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def decStepF(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(OCV.step1)
        s = float(self.step.get()) - power
        zs = None
        if s<=0.0: s = step-power/10.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def decZStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.zstep.get())
        s = float(self.step.get())
        zs = step-power
        if zs<=0.0: zs = step-power/10.0
        if zs<_LOWSTEP: zs = _LOWSTEP
        elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
        self.setStep(s,zs)

    #----------------------------------------------------------------------
    def mulStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step*5.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        zs=None
        self.setStep(s, zs)

    #----------------------------------------------------------------------
    def divStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step/5.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        zs=None
        self.setStep(s, zs)

    def setZStep1(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep1)

    #----------------------------------------------------------------------
    def setZStep2(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep2)

    #----------------------------------------------------------------------
    def setZStep3(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep3)

   #----------------------------------------------------------------------
    def setZStep4(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep4)

    #-----------------------------------------------------------------------
    def zstep1_set(self, event=None):
        return
        """
        OCV.zstep1 = float(self.zstep.get())
        self.setStep(float(self.step.get()), OCV.zstep1)
        return
        """
    #----------------------------------------------------------------------
    def setStep1(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(OCV.step1, float(self.zstep.get()))

    #----------------------------------------------------------------------
    def setStep2(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(OCV.step2, float(self.zstep.get()))

    #----------------------------------------------------------------------
    def setStep3(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(OCV.step3, float(self.zstep.get()))

#===============================================================================
# StateFrame
#===============================================================================
class StateFrame(CNCRibbon.PageExLabelFrame):
    def __init__(self, master, app):
        global wcsvar
        CNCRibbon.PageExLabelFrame.__init__(self, master, "State", _("State"), app)
        self._gUpdate = False

        # State
        f = Frame(self())
        f.pack(side=TOP, fill=X)

        # ===
        col,row=0,0
        f2 = Frame(f)
        f2.grid(row=row, column=col, columnspan=5,sticky=EW)
        for p,w in enumerate(WCS):
            col += 1
            b = Radiobutton(f2, text=w,
                    foreground="DarkRed",
                    font = "Helvetica,14",
                    padx=1, pady=1,
                    variable=wcsvar,
                    value=p,
                    indicatoron=FALSE,
                    activebackground="LightYellow",
                    command=self.wcsChange)
            b.pack(side=LEFT, fill=X, expand=YES)
            tkExtra.Balloon.set(b, _("Switch to workspace %s")%(w))
            self.addWidget(b)

        # Absolute or relative mode
        row += 1
        col = 0
        Label(f, text=_("Distance:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.distance = tkExtra.Combobox(f, True,
                    command=self.distanceChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.distance.fill(sorted(DISTANCE_MODE.values()))
        self.distance.grid(row=row, column=col, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(self.distance, _("Distance Mode [G90,G91]"))
        self.addWidget(self.distance)

        # populate gstate dictionary
        self.gstate = {}    # $G state results widget dictionary
        for k,v in DISTANCE_MODE.items():
            self.gstate[k] = (self.distance, v)

        # Units mode
        col += 2
        Label(f, text=_("Units:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.units = tkExtra.Combobox(f, True,
                    command=self.unitsChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.units.fill(sorted(UNITS.values()))
        self.units.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.units, _("Units [G20, G21]"))
        for k,v in UNITS.items(): self.gstate[k] = (self.units, v)
        self.addWidget(self.units)

        # Tool
        row += 1
        col = 0
        Label(f, text=_("Tool:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.toolEntry = tkExtra.IntegerEntry(f, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.toolEntry.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.toolEntry, _("Tool number [T#]"))
        self.addWidget(self.toolEntry)

        col += 1
        b = Button(f, text=_("set"),
                command=self.setTool,
                padx=1, pady=1)
        b.grid(row=row, column=col, sticky=W)
        self.addWidget(b)

        # Plane
        col += 1
        Label(f, text=_("Plane:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.plane = tkExtra.Combobox(f, True,
                    command=self.planeChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.plane.fill(sorted(PLANE.values()))
        self.plane.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.plane, _("Plane [G17,G18,G19]"))
        self.addWidget(self.plane)

        for k,v in PLANE.items(): self.gstate[k] = (self.plane, v)

        # Feed speed
        row += 1
        col = 0
        Label(f, text=_("Feed:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.feedRate = tkExtra.FloatEntry(f, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, disabledforeground="Black", width=5)
        self.feedRate.grid(row=row, column=col, sticky=EW)
        self.feedRate.bind('<Return>',   self.setFeedRate)
        self.feedRate.bind('<KP_Enter>', self.setFeedRate)
        tkExtra.Balloon.set(self.feedRate, _("Feed Rate [F#]"))
        self.addWidget(self.feedRate)

        col += 1
        b = Button(f, text=_("set"),
                command=self.setFeedRate,
                padx=1, pady=1)
        b.grid(row=row, column=col, columnspan=2, sticky=W)
        self.addWidget(b)

        #Feed mode
        col += 1
        Label(f, text=_("Mode:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.feedMode = tkExtra.Combobox(f, True,
                    command=self.feedModeChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.feedMode.fill(sorted(FEED_MODE.values()))
        self.feedMode.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.feedMode, _("Feed Mode [G93, G94, G95]"))
        for k,v in FEED_MODE.items(): self.gstate[k] = (self.feedMode, v)
        self.addWidget(self.feedMode)

        # TLO
        row += 1
        col = 0
        Label(f, text=_("TLO:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.tlo = tkExtra.FloatEntry(f, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, disabledforeground="Black", width=5)
        self.tlo.grid(row=row, column=col, sticky=EW)
        self.tlo.bind('<Return>',   self.setTLO)
        self.tlo.bind('<KP_Enter>', self.setTLO)
        tkExtra.Balloon.set(self.tlo, _("Tool length offset [G43.1#]"))
        self.addWidget(self.tlo)

        col += 1
        b = Button(f, text=_("set"),
                command=self.setTLO,
                padx=1, pady=1)
        b.grid(row=row, column=col, columnspan=2, sticky=W)
        self.addWidget(b)

        # g92
        col += 1
        Label(f, text=_("G92:")).grid(row=row, column=col, sticky=E)

        col += 1
        self.g92 = Label(f, text="")
        self.g92.grid(row=row, column=col, columnspan=3, sticky=EW)
        tkExtra.Balloon.set(self.g92, _("Set position [G92 X# Y# Z#]"))
        self.addWidget(self.g92)


        # ---
        f.grid_columnconfigure(1, weight=1)
        f.grid_columnconfigure(4, weight=1)

        # Spindle
        f = Frame(self())
        f.pack(side=BOTTOM, fill=X)

        self.override = IntVar()
        self.override.set(100)
        self.spindle = BooleanVar()
        self.spindleSpeed = IntVar()

        col,row=0,0
        self.overrideCombo = tkExtra.Combobox(f, width=8, command=self.overrideComboChange)
        self.overrideCombo.fill(OVERRIDES)
        self.overrideCombo.grid(row=row, column=col, pady=0, sticky=EW)
        tkExtra.Balloon.set(self.overrideCombo, _("Select override type."))

        b = Button(f, text=_("Reset"), pady=0, command=self.resetOverride)
        b.grid(row=row+1, column=col, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Reset override to 100%"))

        col += 1
        self.overrideScale = Scale(f,
                command=self.overrideChange,
                variable=self.override,
                showvalue=True,
                orient=HORIZONTAL,
                from_=25,
                to_=200,
                resolution=1)
        self.overrideScale.bind("<Double-1>", self.resetOverride)
        self.overrideScale.bind("<Button-3>", self.resetOverride)
        self.overrideScale.grid(row=row, column=col, rowspan=2, columnspan=4, sticky=EW)
        tkExtra.Balloon.set(self.overrideScale, _("Set Feed/Rapid/Spindle Override. Right or Double click to reset."))

        self.overrideCombo.set(OVERRIDES[0])

        # ---
        row += 2
        col = 0
        b = Checkbutton(f, text=_("Spindle"),
                image=Utils.icons["spinningtop"],
                command=self.spindleControl,
                compound=LEFT,
                indicatoron=False,
                variable=self.spindle,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(b, _("Start/Stop spindle (M3/M5)"))
        b.grid(row=row, column=col, pady=0, sticky=NSEW)
        self.addWidget(b)

        col += 1
        b = Scale(f,    variable=self.spindleSpeed,
                command=self.spindleControl,
                showvalue=True,
                orient=HORIZONTAL,
                from_=Utils.config.get("CNC","spindlemin"),
                to_=Utils.config.get("CNC","spindlemax"))
        tkExtra.Balloon.set(b, _("Set spindle RPM"))
        b.grid(row=row, column=col, sticky=EW, columnspan=3)
        self.addWidget(b)

        f.grid_columnconfigure(1, weight=1)

        # Coolant control

        self.coolant = BooleanVar()
        self.mist = BooleanVar()
        self.flood = BooleanVar()


        row += 1
        col = 0
        Label(f, text=_("Coolant:")).grid(row=row, column=col, sticky=E)
        col += 1

        coolantDisable = Checkbutton(f, text=_("OFF"),
                command=self.coolantOff,
                indicatoron=False,
                variable=self.coolant,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(coolantDisable, _("Stop cooling (M9)"))
        coolantDisable.grid(row=row, column=col, pady=0, sticky=NSEW)
        self.addWidget(coolantDisable)

        col += 1
        floodEnable = Checkbutton(f, text=_("Flood"),
                command=self.coolantFlood,
                indicatoron=False,
                variable=self.flood,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(floodEnable, _("Start flood (M8)"))
        floodEnable.grid(row=row, column=col, pady=0, sticky=NSEW)
        self.addWidget(floodEnable)

        col += 1
        mistEnable = Checkbutton(f, text=_("Mist"),
                command=self.coolantMist,
                indicatoron=False,
                variable=self.mist,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(mistEnable, _("Start mist (M7)"))
        mistEnable.grid(row=row, column=col, pady=0, sticky=NSEW)
        self.addWidget(mistEnable)
        f.grid_columnconfigure(1, weight=1)

    #----------------------------------------------------------------------
    def overrideChange(self, event=None):
        n = self.overrideCombo.get()
        c = self.override.get()
        OCV.CD["_Ov"+n] = c
        OCV.CD["_OvChanged"] = True

    #----------------------------------------------------------------------
    def resetOverride(self, event=None):
        self.override.set(100)
        self.overrideChange()

    #----------------------------------------------------------------------
    def overrideComboChange(self):
        n = self.overrideCombo.get()
        if n=="Rapid":
            self.overrideScale.config(to_=100, resolution=25)
        else:
            self.overrideScale.config(to_=200, resolution=1)
        self.override.set(OCV.CD["_Ov"+n])

    #----------------------------------------------------------------------
    def _gChange(self, value, dictionary):
        for k,v in dictionary.items():
            if v==value:
                self.sendGCode(k)
                return

    #----------------------------------------------------------------------
    def distanceChange(self):
        if self._gUpdate: return
        self._gChange(self.distance.get(), DISTANCE_MODE)

    #----------------------------------------------------------------------
    def unitsChange(self):
        if self._gUpdate: return
        self._gChange(self.units.get(), UNITS)

    #----------------------------------------------------------------------
    def feedModeChange(self):
        if self._gUpdate: return
        self._gChange(self.feedMode.get(), FEED_MODE)

    #----------------------------------------------------------------------
    def planeChange(self):
        if self._gUpdate: return
        self._gChange(self.plane.get(), PLANE)

    #----------------------------------------------------------------------
    def setFeedRate(self, event=None):
        if self._gUpdate: return
        try:
            feed = float(self.feedRate.get())
            self.sendGCode("F%g"%(feed))
            self.event_generate("<<CanvasFocus>>")
        except ValueError:
            pass

    #----------------------------------------------------------------------
    def setTLO(self, event=None):
        #if self._probeUpdate: return
        try:
            tlo = float(self.tlo.get())
            #print("G43.1Z%g"%(tlo))
            self.sendGCode("G43.1Z%g"%(tlo))
            self.app.mcontrol.viewParameters()
            self.event_generate("<<CanvasFocus>>")
        except ValueError:
            pass

    #----------------------------------------------------------------------
    def setTool(self, event=None):
        pass

    #----------------------------------------------------------------------
    def spindleControl(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.CD["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED): return
        if self.spindle.get():
            self.sendGCode("M3 S%d"%(self.spindleSpeed.get()))
        else:
            self.sendGCode("M5")

    #----------------------------------------------------------------------
    def coolantMist(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.CD["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED):
            self.mist.set(FALSE)
            return
        self.coolant.set(FALSE)
        self.mist.set(TRUE)
        self.sendGCode("M7")

    #----------------------------------------------------------------------
    def coolantFlood(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.CD["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED):
            self.flood.set(FALSE)
            return
        self.coolant.set(FALSE)
        self.flood.set(TRUE)
        self.sendGCode("M8")

    #----------------------------------------------------------------------
    def coolantOff(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.CD["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED):
            self.coolant.set(FALSE)
            return
        self.flood.set(FALSE)
        self.mist.set(FALSE)
        self.coolant.set(TRUE)
        self.sendGCode("M9")

    #----------------------------------------------------------------------
    def updateG(self):
        global wcsvar
        self._gUpdate = True
        try:
            focus = self.focus_get()
        except:
            focus = None

        try:
            wcsvar.set(WCS.index(OCV.CD["WCS"]))
            self.feedRate.set(str(OCV.CD["feed"]))
            self.feedMode.set(FEED_MODE[OCV.CD["feedmode"]])
            self.spindle.set(OCV.CD["spindle"]=="M3")
            self.spindleSpeed.set(int(OCV.CD["rpm"]))
            self.toolEntry.set(OCV.CD["tool"])
            self.units.set(UNITS[OCV.CD["units"]])
            self.distance.set(DISTANCE_MODE[OCV.CD["distance"]])
            self.plane.set(PLANE[OCV.CD["plane"]])
            self.tlo.set(str(OCV.CD["TLO"]))
            self.g92.config(text=str(OCV.CD["G92"]))
        except KeyError:
            pass

        self._gUpdate = False

    #----------------------------------------------------------------------
    def updateFeed(self):
        if self.feedRate.cget("state") == DISABLED:
            self.feedRate.config(state=NORMAL)
            self.feedRate.delete(0,END)
            self.feedRate.insert(0, OCV.CD["curfeed"])
            self.feedRate.config(state=DISABLED)

    #----------------------------------------------------------------------
    def wcsChange(self):
        global wcsvar
        self.sendGCode(WCS[wcsvar.get()])
        self.app.mcontrol.viewState()


#===============================================================================
# Control Page
#===============================================================================
class ControlPage(CNCRibbon.Page):
    __doc__ = _("CNC communication and control")
    _name_  = N_("Control")
    _icon_  = "control"

    #----------------------------------------------------------------------
    # Add a widget in the widgets list to enable disable during the run
    #----------------------------------------------------------------------
    def register(self):
        global wcsvar
        wcsvar = IntVar()
        wcsvar.set(0)

        self._register((ConnectionGroup, UserGroup, RunGroup),
            (DROFrame, ControlFrame, StateFrame))
