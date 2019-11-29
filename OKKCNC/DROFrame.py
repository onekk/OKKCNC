#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 15:23:15 2019

@author: carlo
"""
from __future__ import absolute_import
from __future__ import print_function

try:
    import Tkinter as Tk
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import OCV
import CNCRibbon
import Commands as cmd
import Utils
import Sender
import tkExtra


class DROFrame(CNCRibbon.PageFrame):
    """DRO Frame"""
    dro_status = ('Helvetica', 12, 'bold')
    dro_wpos = ('Helvetica', 12, 'bold')
    dro_mpos = ('Helvetica', 12)

    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "DRO", app)

        print("DROFrame self.app", self.app)

        DROFrame.dro_status = Utils.getFont("dro.status", DROFrame.dro_status)
        DROFrame.dro_wpos = Utils.getFont("dro.wpos", DROFrame.dro_wpos)
        DROFrame.dro_mpos = Utils.getFont("dro.mpos", DROFrame.dro_mpos)

        row = 0
        col = 0
        Tk.Label(self, text=_("Status:")).grid(row=row, column=col, sticky=Tk.E)
        col += 1
        self.state = Tk.Button(
            self,
            text=Sender.NOT_CONNECTED,
            font=DROFrame.dro_status,
            command=cmd.showState,
            cursor="hand1",
            background=Sender.STATECOLOR[Sender.NOT_CONNECTED],
            activebackground="LightYellow")
        self.state.grid(row=row, column=col, columnspan=3, sticky=Tk.EW)
        tkExtra.Balloon.set(
            self.state,
            _("Show current state of the machine\n"
              "Click to see details\n"
              "Right-Click to clear alarm/errors"))
        #self.state.bind("<Button-3>", lambda e,s=self : s.event_generate("<<AlarmClear>>"))
        self.state.bind("<Button-3>", self.stateMenu)

        row += 1
        col = 0
        Tk.Label(self, text=_("WPos:")).grid(row=row, column=col, sticky=Tk.E)

        # work
        col += 1
        self.xwork = Tk.Entry(
            self,
            font=DROFrame.dro_wpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            relief=Tk.FLAT,
            borderwidth=0,
            justify=Tk.RIGHT)
        self.xwork.grid(row=row, column=col, padx=1, sticky=Tk.EW)
        tkExtra.Balloon.set(self.xwork, _("X work position (click to set)"))
        self.xwork.bind('<FocusIn>', cmd.workFocus)
        self.xwork.bind('<Return>', self.setX)
        self.xwork.bind('<KP_Enter>', self.setX)

        # ---
        col += 1
        self.ywork = Tk.Entry(
            self,
            font=DROFrame.dro_wpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            relief=Tk.FLAT,
            borderwidth=0,
            justify=Tk.RIGHT)
        self.ywork.grid(row=row, column=col, padx=1, sticky=Tk.EW)
        tkExtra.Balloon.set(self.ywork, _("Y work position (click to set)"))
        self.ywork.bind('<FocusIn>', cmd.workFocus)
        self.ywork.bind('<Return>', self.setY)
        self.ywork.bind('<KP_Enter>', self.setY)

        # ---
        col += 1
        self.zwork = Tk.Entry(
            self, font=DROFrame.dro_wpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            relief=Tk.FLAT,
            borderwidth=0,
            justify=Tk.RIGHT)
        self.zwork.grid(row=row, column=col, padx=1, sticky=Tk.EW)
        tkExtra.Balloon.set(self.zwork, _("Z work position (click to set)"))
        self.zwork.bind('<FocusIn>', cmd.workFocus)
        self.zwork.bind('<Return>', self.setZ)
        self.zwork.bind('<KP_Enter>', self.setZ)

        # Machine
        row += 1
        col = 0
        Tk.Label(self, text=_("MPos:")).grid(row=row, column=col, sticky=Tk.E)

        col += 1
        self.xmachine = Tk.Label(
            self,
            font=DROFrame.dro_mpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            anchor=Tk.E)

        self.xmachine.grid(row=row, column=col, padx=1, sticky=Tk.EW)

        col += 1
        self.ymachine = Tk.Label(
            self,
            font=DROFrame.dro_mpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            anchor=Tk.E)

        self.ymachine.grid(row=row, column=col, padx=1, sticky=Tk.EW)

        col += 1
        self.zmachine = Tk.Label(
            self,
            font=DROFrame.dro_mpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            anchor=Tk.E)

        self.zmachine.grid(row=row, column=col, padx=1, sticky=Tk.EW)

        # Set buttons
        row += 1
        col = 1

        self.xzero = Tk.Button(
            self,
            text=_("X=0"),
            font=OCV.DRO_ZERO_FONT,
            command=cmd.setX0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.xzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(self.xzero, _("Set X coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.xzero)

        col += 1
        self.yzero = Tk.Button(
            self,
            text=_("Y=0"),
            font=OCV.DRO_ZERO_FONT,
            command=cmd.setY0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.yzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(self.yzero, _("Set Y coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.yzero)

        col += 1
        self.zzero = Tk.Button(
            self,
            text=_("Z=0"),
            font=OCV.DRO_ZERO_FONT,
            command=cmd.setZ0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.zzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(self.zzero, _("Set Z coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.zzero)

        # Set buttons
        row += 1
        col = 1
        self.xyzero = Tk.Button(
            self,
            text=_("XY=0"),
            font=OCV.DRO_ZERO_FONT,
            command=cmd.setXY0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.xyzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(self.xyzero, _("Set XY coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.xyzero)

        col += 1
        self.xyzzero = Tk.Button(
            self,
            text=_("XYZ=0"),
            font=OCV.DRO_ZERO_FONT,
            command=cmd.setXYZ0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.xyzzero.grid(row=row, column=col, pady=0, sticky=Tk.EW, columnspan=2)
        tkExtra.Balloon.set(self.xyzzero, _("Set XYZ coordinate to zero (or to typed coordinate in WPos)"))
        self.addWidget(self.xyzzero)

        # Set buttons
        row += 1
        col = 1
        f = Tk.Frame(self)
        f.grid(row=row, column=col, columnspan=3, pady=0, sticky=Tk.EW)

        b = Tk.Button(
            f,
            text=_("Set WPOS"),
            font=OCV.DRO_ZERO_FONT,
            image=Utils.icons["origin"],
            compound=Tk.LEFT,
            activebackground="LightYellow",
            command=lambda s=self: s.event_generate("<<SetWPOS>>"),
            padx=2, pady=1)
        b.pack(side=Tk.LEFT, fill=Tk.X, expand=Tk.YES)
        tkExtra.Balloon.set(b, _("Set WPOS to mouse location"))
        self.addWidget(b)

        #col += 2
        b = Tk.Button(
            f,
            text=_("Move Gantry"),
            font=OCV.DRO_ZERO_FONT,
            image=Utils.icons["gantry"],
            compound=Tk.LEFT,
            activebackground="LightYellow",
            command=lambda s=self: s.event_generate("<<MoveGantry>>"),
            padx=2, pady=1)
        #b.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        b.pack(side=Tk.RIGHT, fill=Tk.X, expand=Tk.YES)
        tkExtra.Balloon.set(b, _("Move gantry to mouse location [g]"))
        self.addWidget(b)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

    #----------------------------------------------------------------------
    def stateMenu(self, event=None):
        menu = Tk.Menu(self, tearoff=0)

        menu.add_command(
            label=_("Show Info"),
            image=Utils.icons["info"],
            compound=Tk.LEFT,
            command=cmd.showState)

        menu.add_command(
            label=_("Clear Message"),
            image=Utils.icons["clear"],
            compound=Tk.LEFT,
            command=lambda s=self: s.event_generate("<<AlarmClear>>"))

        menu.add_separator()

        menu.add_command(
            label=_("Feed hold"),
            image=Utils.icons["pause"],
            compound=Tk.LEFT,
            command=lambda s=self: s.event_generate("<<FeedHold>>"))

        menu.add_command(
            label=_("Resume"),
            image=Utils.icons["start"],
            compound=Tk.LEFT,
            command=lambda s=self: s.event_generate("<<Resume>>"))

        menu.tk_popup(event.x_root, event.y_root)

    #----------------------------------------------------------------------
    def updateState(self):
        msg = OCV.application._msg or OCV.c_state
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
            self.xwork.delete(0, Tk.END)
            self.xwork.insert(0, cmd.padFloat(OCV.drozeropad, OCV.CD["wx"]))
        if focus is not self.ywork:
            self.ywork.delete(0, Tk.END)
            self.ywork.insert(0, cmd.padFloat(OCV.drozeropad, OCV.CD["wy"]))
        if focus is not self.zwork:
            self.zwork.delete(0, Tk.END)
            self.zwork.insert(0, cmd.padFloat(OCV.drozeropad, OCV.CD["wz"]))

        self.xmachine["text"] = cmd.padFloat(OCV.drozeropad, OCV.CD["mx"])
        self.ymachine["text"] = cmd.padFloat(OCV.drozeropad, OCV.CD["my"])
        self.zmachine["text"] = cmd.padFloat(OCV.drozeropad, OCV.CD["mz"])


    def setX(self, event=None):
        if OCV.application.running: return
        try:
            value = round(eval(self.xwork.get(), None, OCV.CD), 3)
            OCV.mcontrol.wcs_set(value, None, None)
        except:
            pass

    #----------------------------------------------------------------------
    def setY(self, event=None):
        if OCV.application.running: return
        try:
            value = round(eval(self.ywork.get(), None, OCV.CD), 3)
            OCV.mcontrol.wcs_set(None, value, None)
        except:
            pass

    #----------------------------------------------------------------------
    def setZ(self, event=None):
        if OCV.application.running: return
        try:
            value = round(eval(self.zwork.get(), None, OCV.CD), 3)
            OCV.mcontrol.wcs_set(None, None, value)
        except:
            pass
