# -*- coding: ascii -*-
"""FilePage.py


Credits:
    this module code is based on bCNC
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import os

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

import OCV

import tkExtra
import Utils
#import Sender
import Ribbon
import CNCRibbon

try:
    from serial.tools.list_ports import comports
except:
    print("Using fallback Utils.comports()!")
    from Utils import comports

BAUDS = [2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400]

#===============================================================================
# Recent Menu button
#===============================================================================
class _RecentMenuButton(Ribbon.MenuButton):
    #----------------------------------------------------------------------
    def createMenu(self):
        menu = Menu(self, tearoff=0, activebackground=OCV.ACTIVE_COLOR)
        for i in range(Utils._maxRecent):
            filename = Utils.getRecent(i)
            if filename is None: break
            path = os.path.dirname(filename)
            fn   = os.path.basename(filename)
            menu.add_command(label="{0:d} {1}".format(i+1, fn),
                compound=LEFT,
                image=Utils.icons["new"],
                accelerator=path, # Show as accelerator in order to be aligned
                command=lambda s=self,i=i: s.event_generate("<<Recent{0:d}>>".format(i)))
        if i==0: # no entry
            self.event_generate("<<Open>>")
            return None
        return menu


#===============================================================================
# File Group
#===============================================================================
class FileGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("File"), app)
        self.grid3rows()

        # ---
        col,row=0,0
        b = Ribbon.LabelButton(self.frame, self, "<<New>>",
                image=Utils.icons["new32"],
                text=_("New"),
                compound=TOP,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("New gcode/dxf file"))
        self.addWidget(b)

        # ---
        col,row=1,0
        b = Ribbon.LabelButton(self.frame, self, "<<Open>>",
                image=Utils.icons["open32"],
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, rowspan=2, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Open existing gcode/dxf file [Ctrl-O]"))
        self.addWidget(b)

        col,row=1,2
        b = _RecentMenuButton(self.frame, None,
                text=_("Open"),
                image=Utils.icons["triangle_down"],
                compound=RIGHT,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Open recent file"))
        self.addWidget(b)

        # ---
        col,row=2,0
        b = Ribbon.LabelButton(self.frame, self, "<<Import>>",
                image=Utils.icons["import32"],
                text=_("Import"),
                compound=TOP,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Import gcode/dxf file"))
        self.addWidget(b)

        # ---
        col,row=3,0
        b = Ribbon.LabelButton(self.frame, self, "<<Save>>",
                image=Utils.icons["save32"],
                command=OCV.APP.save,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, rowspan=2, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Save gcode/dxf file [Ctrl-S]"))
        self.addWidget(b)

        col,row=3,2
        b = Ribbon.LabelButton(self.frame, self, "<<SaveAs>>",
                text=_("Save"),
                image=Utils.icons["triangle_down"],
                compound=RIGHT,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Save gcode/dxf AS"))
        self.addWidget(b)


#===============================================================================
# Options Group
#===============================================================================
class OptionsGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Options"), app)
        self.grid3rows()

#        # ---
#        col,row=0,0
#        b = Ribbon.LabelButton(self.frame, #self.page, "<<Config>>",
#                text=_("Config"),
#                image=Utils.icons["config32"],
##                command=OCV.APP.preferences,
#                state=DISABLED,
#                compound=TOP,
#                anchor=W,
#                background=OCV.BACKGROUND)
#        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NS)
#        tkExtra.Balloon.set(b, _("Open configuration dialog"))

#        # ===
#        col,row=1,0
#        b = Ribbon.LabelButton(self.frame,
#                text=_("Report"),
#                image=Utils.icons["debug"],
#                compound=LEFT,
#                command=Utils.ReportDialog.sendErrorReport,
#                anchor=W,
#                background=OCV.BACKGROUND)
#        b.grid(row=row, column=col, padx=0, pady=0, sticky=EW)
#        tkExtra.Balloon.set(b, _("Send Error Report"))
#
#        # ---
#        col,row=1,1
#        b = Ribbon.LabelButton(self.frame,
#                text=_("Updates"),
#                image=Utils.icons["global"],
#                compound=LEFT,
#                command=OCV.APP.checkUpdates,
#                anchor=W,
#                background=OCV.BACKGROUND)
#        b.grid(row=row, column=col, padx=0, pady=0, sticky=EW)
#        tkExtra.Balloon.set(b, _("Check Updates"))

        col,row=1,2
        b = Ribbon.LabelButton(self.frame,
                text=_("About"),
                image=Utils.icons["about"],
                compound=LEFT,
                command=OCV.APP.about,
                anchor=W,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=EW)
        tkExtra.Balloon.set(b, _("About the program"))


#===============================================================================
# Pendant Group
#===============================================================================
class PendantGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Pendant"), app)
        self.grid3rows()

        col,row=0,0
        b = Ribbon.LabelButton(self.frame,
                text=_("Start"),
                image=Utils.icons["start_pendant"],
                compound=LEFT,
                anchor=W,
                command=OCV.APP.startPendant,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Start pendant"))

        row += 1
        b = Ribbon.LabelButton(self.frame,
                text=_("Stop"),
                image=Utils.icons["stop_pendant"],
                compound=LEFT,
                anchor=W,
                command=OCV.APP.stopPendant,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(b, _("Stop pendant"))


#===============================================================================
# Close Group
#===============================================================================
class CloseGroup(CNCRibbon.ButtonGroup):
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Close"), app)

        # ---
        b = Ribbon.LabelButton(self.frame,
                text=_("Exit"),
                image=Utils.icons["exit32"],
                compound=TOP,
                command=OCV.APP.quit,
                anchor=W,
                background=OCV.BACKGROUND)
        b.pack(fill=BOTH, expand=YES)
        tkExtra.Balloon.set(b, _("Close program [Ctrl-Q]"))


#===============================================================================
# Serial Frame
#===============================================================================
class SerialFrame(CNCRibbon.PageLabelFrame):
    def __init__(self, master, app):
        CNCRibbon.PageLabelFrame.__init__(self, master, "Serial", _("Serial"), app)
        self.autostart = BooleanVar()

        # ---
        col,row=0,0
        b = Label(self, text=_("Port:"))
        b.grid(row=row,column=col,sticky=E)
        self.addWidget(b)

        self.portCombo = tkExtra.Combobox(self, False, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=16, command=self.comportClean)
        self.portCombo.grid(row=row, column=col+1, sticky=EW)
        tkExtra.Balloon.set(self.portCombo, _("Select (or manual enter) port to connect"))
        self.portCombo.set(Utils.getStr("Connection","port"))
        self.addWidget(self.portCombo)

        self.comportRefresh()


        # ---
        row += 1
        b = Label(self, text=_("Baud:"))
        b.grid(row=row,column=col,sticky=E)

        self.baudCombo = tkExtra.Combobox(self, True, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.baudCombo.grid(row=row, column=col+1, sticky=EW)
        tkExtra.Balloon.set(self.baudCombo, _("Select connection baud rate"))
        self.baudCombo.fill(BAUDS)
        self.baudCombo.set(Utils.getStr("Connection","baud","115200"))
        self.addWidget(self.baudCombo)

        # ---
        row += 1
        b = Label(self, text=_("Controller:"))
        b.grid(row=row,column=col,sticky=E)

        self.ctrlCombo = tkExtra.Combobox(self, True,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
                    command=self.ctrlChange)
        self.ctrlCombo.grid(row=row, column=col+1, sticky=EW)
        tkExtra.Balloon.set(self.ctrlCombo, _("Select controller board"))
        #self.ctrlCombo.fill(sorted(Utils.CONTROLLER.keys()))
        self.ctrlCombo.fill(OCV.APP.controllerList())
        self.ctrlCombo.set(OCV.APP.controller)
        self.addWidget(self.ctrlCombo)

        # ---
        row += 1
        b= Checkbutton(self, text=_("Connect on startup"),
                    variable=self.autostart)
        b.grid(row=row, column=col, columnspan=2, sticky=W)
        tkExtra.Balloon.set(b, _("Connect to serial on startup of the program"))
        self.autostart.set(Utils.getBool("Connection","openserial"))
        self.addWidget(b)

        # ---
        col += 2
        self.comrefBtn = Ribbon.LabelButton(self,
                image=Utils.icons["refresh"],
                text=_("Refresh"),
                compound=TOP,
                command=lambda s=self : s.comportRefresh(True),
                background=OCV.BACKGROUND)
        self.comrefBtn.grid(row=row, column=col, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(self.comrefBtn, _("Refresh list of serial ports"))

        # ---
        #col += 2
        row  = 0

        self.connectBtn = Ribbon.LabelButton(self,
                image=Utils.icons["serial48"],
                text=_("Open"),
                compound=TOP,
                command=lambda s=self : s.event_generate("<<Connect>>"),
                background=OCV.BACKGROUND)
        self.connectBtn.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NSEW)
        tkExtra.Balloon.set(self.connectBtn, _("Open/Close serial port"))
        self.grid_columnconfigure(1, weight=1)

    #-----------------------------------------------------------------------
    def ctrlChange(self):
        #OCV.APP.controller = Utils.CONTROLLER.get(self.ctrlCombo.get(), 0)
        #print("selected",self.ctrlCombo.get())
        OCV.APP.controllerSet(self.ctrlCombo.get())

    #-----------------------------------------------------------------------
    def comportClean(self, event=None):
        clean = self.portCombo.get().split("\t")[0]
        if(self.portCombo.get() != clean):
            print("comport fix")
            self.portCombo.set(clean)

    #-----------------------------------------------------------------------
    def comportsGet(self):
        try:
            return comports(include_links=True)
        except TypeError:
            print("Using old style comports()!")
            return comports()

    def comportRefresh(self, dbg=False):
        #Detect devices
        hwgrep = []
        com_ports = self.comportsGet()

        print("comportRefresh scg > ", com_ports)

        for i in com_ports:
            if dbg:
                # Print list to console if requested
                comport = ''
                for j in i:
                    comport += j + "\t"
                print(comport)

            for hw in i[2].split(' '):
                hwgrep += ["hwgrep://{0}\t{1}".format(hw, i[1])]

        #Populate combobox
        devices = sorted(["{0}\t {1}".format(*x) for x in com_ports])
        devices += ['']
        devices += sorted(set(hwgrep))
        devices += ['']
        devices += sorted(["spy://{0} ?raw&color\t(Debug) {1}".format(*x) for x in com_ports])
        devices += ['', 'socket://localhost:23', 'rfc2217://localhost:2217']

        #Clean neighbour duplicates
        devices_clean = []
        devprev = ''

        for i in devices:
            if i.split("\t")[0] != devprev:
                devices_clean += [i]

            devprev = i.split("\t")[0]

        self.portCombo.fill(devices_clean)

    def saveConfig(self):
        # Connection
        Utils.setStr("Connection", "controller", OCV.APP.controller)
        Utils.setStr("Connection", "port", self.portCombo.get().split("\t")[0])
        Utils.setStr("Connection", "baud", self.baudCombo.get())
        Utils.setBool("Connection", "openserial", self.autostart.get())


class FilePage(CNCRibbon.Page):
    """File Page"""
    __doc__ = _("File I/O and configuration")
    _name_ = N_("File")
    _icon_ = "new"

    def register(self):
        """Add a widget in the widgets list to enable disable during the run"""
        self._register(
                (FileGroup,
                 PendantGroup,
                 OptionsGroup,
                 CloseGroup),
                 (SerialFrame,))
