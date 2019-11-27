# -*- coding: ascii -*-
# $Id$
#
# Author: carlo.dormeletti@gmail.com
# Date: 26 Oct 2019

from __future__ import absolute_import
from __future__ import print_function

try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
import Utils
import Ribbon
import tkExtra

import CNCRibbon


#===============================================================================
# Terminal Group
#===============================================================================
class TerminalGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Terminal"), app)

        but = Ribbon.LabelButton(
            self.frame,
            self, "<<TerminalClear>>",
            image=Utils.icons["clean32"],
            text=_("Clear"),
            compound=Tk.TOP,
            background=OCV.BACKGROUND)

        but.pack(fill=Tk.BOTH, expand=Tk.YES)

        tkExtra.Balloon.set(but, _("Clear terminal"))



class CommandsGroup(CNCRibbon.ButtonMenuGroup):
    """Commands Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(
            self, master,
            N_("Commands"), app,
            [(_("Restore Settings"), "grbl_settings", OCV.application.grblRestoreSettings),
             (_("Restore Workspace"), "grbl_params", OCV.application.grblRestoreWCS),
             (_("Restore All"), "reset", OCV.application.grblRestoreAll),
            ])

        self.grid3rows()

        # Disable state for some SMOOTHIE commands
        state = OCV.application.controller in ("GRBL0", "GRBL1") and Tk.NORMAL or Tk.DISABLED,

        # ---
        col, row = 0, 0
        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_settings"],
            text=_("Settings"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            state=state,
            command=OCV.application.viewSettings,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)
        tkExtra.Balloon.set(but, _("$$ Display settings of Grbl"))

        if state == Tk.NORMAL:
            self.addWidget(but)

        row += 1
        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_params"],
            text=_("Parameters"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.application.viewParameters,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$# Display parameters of Grbl"))
        self.addWidget(but)

        row += 1
        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_state"],
            text=_("State"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.application.viewState,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$G Display state of Grbl"))

        self.addWidget(but)

        # ---
        col += 1
        row = 0

        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_build"],
            text=_("Build"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.application.viewBuild,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$I Display build information of Grbl"))

        self.addWidget(but)

        row += 1

        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_startup"],
            text=_("Startup"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            state=state,
            command=OCV.application.viewStartup,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$N Display startup configuration of Grbl"))

        if state == Tk.NORMAL:
            self.addWidget(but)

        row += 1
        # FIXME Checkbutton!!!!!
        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_check"],
            text=_("Check gcode"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            state=state,
            command=OCV.application.checkGcode,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$C Enable/Disable checking of gcode"))

        if state == Tk.NORMAL:
            self.addWidget(but)

        # ---
        col += 1
        row = 1

        but = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["grbl_help"],
            text=_("Help"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.application.grblHelp,
            background=OCV.BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$ Display build information of Grbl"))

        self.addWidget(but)


#===============================================================================
class TerminalFrame(CNCRibbon.PageFrame):
    """TerminalFrame class"""
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, N_("Terminal"), app)

        # ---
        self.terminal = Tk.Listbox(
            self,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            selectmode=Tk.EXTENDED,
            height=5)

        self.terminal.grid(row=0, column=0, sticky=Tk.NSEW)

        scb = Tk.Scrollbar(
            self,
            orient=Tk.VERTICAL,
            command=self.terminal.yview)

        scb.grid(row=0, column=1, sticky=Tk.NS)

        self.terminal.config(yscrollcommand=scb.set)
        self.terminal.bind("<<Copy>>", self.copy)
        self.terminal.bind("<Control-Key-c>", self.copy)
        tkExtra.Balloon.set(self.terminal, _("Terminal communication with controller"))

        # ---
        self.buffer = Tk.Listbox(
            self,
            background="LightYellow",
            selectmode=Tk.EXTENDED,
            height=5)

        self.buffer.grid(row=1, column=0, sticky=Tk.NSEW)

        scb = Tk.Scrollbar(
            self,
            orient=Tk.VERTICAL,
            command=self.buffer.yview)

        scb.grid(row=1, column=1, sticky=Tk.NS)

        self.buffer.config(yscrollcommand=scb.set)

        tkExtra.Balloon.set(self.buffer, _("Buffered commands"))

        self.buffer.bind("<<Copy>>", self.copy)
        self.buffer.bind("<Control-Key-c>", self.copy)

        # ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


    def clear(self, event=None):
        self.terminal.delete(0, Tk.END)


    def copy(self, event):
        self.clipboard_clear()
        self.clipboard_append("\n".join(
            [event.widget.get(x) for x in event.widget.curselection()]))
        return "break"



class TerminalPage(CNCRibbon.Page):
    """Terminal Page"""
    __doc__ = _("Serial Terminal")
    _name_ = "Terminal"
    _icon_ = "terminal"


    def register(self):
        """Add a widget in the widgets list to enable disable during the run"""
        self._register(
            (CommandsGroup, TerminalGroup),
            (TerminalFrame,))
