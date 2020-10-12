# -*- coding: ascii -*-
"""TerminalPage.py


Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
import Ribbon
import tkExtra

import CNCRibbon


class TerminalGroup(CNCRibbon.ButtonGroup):
    """Terminal Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Terminal"), app)

        but = Ribbon.LabelButton(
            self.frame,
            self, "<<TerminalClear>>",
            image=OCV.icons["clean32"],
            text=_("Clear"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        but.pack(fill=Tk.BOTH, expand=Tk.YES)

        tkExtra.Balloon.set(but, _("Clear terminal"))


class CommandsGroup(CNCRibbon.ButtonMenuGroup):
    """Commands Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(
            self, master,
            N_("Commands"), app,
            [(_("Restore Settings"), "grbl_settings", OCV.MCTRL.grblRestoreSettings),
             (_("Restore Workspace"), "grbl_params", OCV.MCTRL.grblRestoreWCS),
             (_("Restore All"), "reset", OCV.MCTRL.grblRestoreAll),
            ])

        self.grid3rows()

        # Disable state for some SMOOTHIE commands
        state = OCV.APP.controller in ("GRBL0", "GRBL1") and Tk.NORMAL or Tk.DISABLED,

        # ---
        col, row = 0, 0
        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_settings"],
            text=_("Settings"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            state=state,
            command=OCV.MCTRL.viewSettings,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)
        tkExtra.Balloon.set(but, _("$$ Display settings of Grbl"))

        if state == Tk.NORMAL:
            self.addWidget(but)

        row += 1
        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_params"],
            text=_("Parameters"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.MCTRL.viewParameters,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$# Display parameters of Grbl"))
        self.addWidget(but)

        row += 1
        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_state"],
            text=_("State"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.MCTRL.viewState,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$G Display state of Grbl"))

        self.addWidget(but)

        # ---
        col += 1
        row = 0

        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_build"],
            text=_("Build"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.MCTRL.viewBuild,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$I Display build information of Grbl"))

        self.addWidget(but)

        row += 1

        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_startup"],
            text=_("Startup"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            state=state,
            command=OCV.MCTRL.viewStartup,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$N Display startup configuration of Grbl"))

        if state == Tk.NORMAL:
            self.addWidget(but)

        row += 1
        # FIXME Checkbutton!!!!!
        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_check"],
            text=_("Check gcode"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            state=state,
            command=OCV.MCTRL.checkGcode,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$C Enable/Disable checking of gcode"))

        if state == Tk.NORMAL:
            self.addWidget(but)

        # ---
        col += 1

        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["grbl_help"],
            text=_("Help"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.MCTRL.grblHelp,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=0, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("$ Display build information of Grbl"))

        self.addWidget(but)


        but = Ribbon.LabelButton(
            self.frame,
            self,
            "<<ERR_HELP>>",
            text=_("Error Help"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=1, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        but = Ribbon.LabelButton(
            self.frame,
            self,
            "<<SET_HELP>>",
            text=_("Settings Help"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=2, column=col, padx=0, pady=0, sticky=Tk.NSEW)

class TerminalFrame(CNCRibbon.PageFrame):
    """TerminalFrame class"""
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, N_("Terminal"), app)

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
