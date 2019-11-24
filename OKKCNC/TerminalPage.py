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
except ImportError:
    from tkinter import *

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

        b = Ribbon.LabelButton(self.frame, self, "<<TerminalClear>>",
                image=Utils.icons["clean32"],
                text=_("Clear"),
                compound=TOP,
                background=OCV.BACKGROUND)
        b.pack(fill=BOTH, expand=YES)
        tkExtra.Balloon.set(b, _("Clear terminal"))


#===============================================================================
# Commands Group
#===============================================================================
class CommandsGroup(CNCRibbon.ButtonMenuGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(self, master, N_("Commands"), app,
            [(_("Restore Settings"),  "grbl_settings",  OCV.application.grblRestoreSettings),
             (_("Restore Workspace"), "grbl_params",    OCV.application.grblRestoreWCS),
             (_("Restore All"),      "reset",        OCV.application.grblRestoreAll),
            ])
        self.grid3rows()

        # Disable state for some SMOOTHIE commands
        state=OCV.application.controller in ("GRBL0", "GRBL1") and NORMAL or DISABLED,

        # ---
        col,row=0,0
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_settings"],
                text=_("Settings"),
                compound=LEFT,
                anchor=W,
                state=state,
                command=OCV.application.viewSettings,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$$ Display settings of Grbl"))
        if state == NORMAL: self.addWidget(b)

        row += 1
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_params"],
                text=_("Parameters"),
                compound=LEFT,
                anchor=W,
                command=OCV.application.viewParameters,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$# Display parameters of Grbl"))
        self.addWidget(b)

        row += 1
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_state"],
                text=_("State"),
                compound=LEFT,
                anchor=W,
                command=OCV.application.viewState,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$G Display state of Grbl"))
        self.addWidget(b)

        # ---
        col += 1
        row  = 0
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_build"],
                text=_("Build"),
                compound=LEFT,
                anchor=W,
                command=OCV.application.viewBuild,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$I Display build information of Grbl"))
        self.addWidget(b)

        row += 1
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_startup"],
                text=_("Startup"),
                compound=LEFT,
                anchor=W,
                state=state,
                command=OCV.application.viewStartup,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$N Display startup configuration of Grbl"))
        if state == NORMAL: self.addWidget(b)

        row += 1
        # FIXME Checkbutton!!!!!
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_check"],
                text=_("Check gcode"),
                compound=LEFT,
                anchor=W,
                state=state,
                command=OCV.application.checkGcode,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$C Enable/Disable checking of gcode"))
        if state == NORMAL: self.addWidget(b)

        # ---
        col += 1
        row  = 1
        b = Ribbon.LabelButton(self.frame,
                image=Utils.icons["grbl_help"],
                text=_("Help"),
                compound=LEFT,
                anchor=W,
                command=OCV.application.grblHelp,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("$ Display build information of Grbl"))
        self.addWidget(b)


#===============================================================================
class TerminalFrame(CNCRibbon.PageFrame):
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, N_("Terminal"), app)

        # ---
        self.terminal = Listbox(self,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    selectmode=EXTENDED,
                    height=5)
        self.terminal.grid(row=0, column=0, sticky=NSEW)
        sb = Scrollbar(self, orient=VERTICAL, command=self.terminal.yview)
        sb.grid(row=0, column=1, sticky=NS)
        self.terminal.config(yscrollcommand=sb.set)
        self.terminal.bind("<<Copy>>",        self.copy)
        self.terminal.bind("<Control-Key-c>",    self.copy)
        tkExtra.Balloon.set(self.terminal, _("Terminal communication with controller"))

        # ---
        self.buffer = Listbox(self,
                    background="LightYellow",
                    selectmode=EXTENDED,
                    height=5)
        self.buffer.grid(row=1, column=0, sticky=NSEW)
        sb = Scrollbar(self, orient=VERTICAL, command=self.buffer.yview)
        sb.grid(row=1, column=1, sticky=NS)
        self.buffer.config(yscrollcommand=sb.set)
        tkExtra.Balloon.set(self.buffer, _("Buffered commands"))
        self.buffer.bind("<<Copy>>",        self.copy)
        self.buffer.bind("<Control-Key-c>",    self.copy)

        # ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    #----------------------------------------------------------------------
    def clear(self, event=None):
        self.terminal.delete(0,END)

    #----------------------------------------------------------------------
    def copy(self, event):
        self.clipboard_clear()
        self.clipboard_append("\n".join(
            [event.widget.get(x)
                for x in event.widget.curselection()]))
        return "break"


#===============================================================================
# Terminal Page
#===============================================================================
class TerminalPage(CNCRibbon.Page):
    __doc__ = _("Serial Terminal")
    _name_    = "Terminal"
    _icon_    = "terminal"

    #----------------------------------------------------------------------
    # Add a widget in the widgets list to enable disable during the run
    #----------------------------------------------------------------------
    def register(self):
        self._register((CommandsGroup,TerminalGroup),
                (TerminalFrame,))
