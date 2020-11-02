# -*- coding: ascii -*-
"""FilePage.py


Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import os

try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
import CNCRibbon
import IniFile
import Ribbon
import tkExtra

try:
    from serial.tools.list_ports import comports
except:
    print("Using fallback Utils.comports()!")
    from Utils import comports

BAUDS = [2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400]

class _RecentMenuButton(Ribbon.MenuButton):
    """Recent Menu button"""
    def createMenu(self):
        menu = Tk.Menu(self, tearoff=0, activebackground=OCV.COLOR_ACTIVE)
        for i in range(OCV.maxRecent):
            filename = IniFile.get_recent_file(i)

            if filename is None:
                break

            path = os.path.dirname(filename)
            fn = os.path.basename(filename)

            menu.add_command(
                label="{0:d} {1}".format(i+1, fn),
                compound=Tk.LEFT,
                image=OCV.icons["new"],
                accelerator=path,  # Show as accelerator in order to be aligned
                command=lambda s=self, i=i: s.event_generate(
                        "<<Recent{0:d}>>".format(i)))

        if i == 0:  # no entry
            self.event_generate("<<Open>>")
            return None
        return menu


class FileGroup(CNCRibbon.ButtonGroup):
    """File Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(
            self,
            master,
            N_("File"),
            app)

        self.grid3rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame, self, "<<New>>",
            image=OCV.icons["new32"],
            text=_("New"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("New gcode file"))

        self.addWidget(b)


        col, row = 1, 0

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Open>>",
            image=OCV.icons["open32"],
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, rowspan=2, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Open existing gcode file [Ctrl-O]"))

        self.addWidget(b)

        col, row = 1, 2

        b = _RecentMenuButton(
            self.frame,
            None,
            text=_("Open"),
            image=OCV.icons["triangle_down"],
            compound=Tk.RIGHT,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Open recent file"))

        self.addWidget(b)

        col, row = 2, 0

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Import>>",
            image=OCV.icons["import32"],
            text=_("Import"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Import gcode file"))

        self.addWidget(b)

        col, row = 3, 0

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Save>>",
            image=OCV.icons["save32"],
            command=OCV.TK_APP.save,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, rowspan=2, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Save gcode file [Ctrl-S]"))

        self.addWidget(b)

        col, row = 3, 2

        b = Ribbon.LabelButton(
                self.frame,
                self,
                "<<SaveAs>>",
                text=_("Save"),
                image=OCV.icons["triangle_down"],
                compound=Tk.RIGHT,
                background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Save gcode as..."))

        self.addWidget(b)


class OptionsGroup(CNCRibbon.ButtonGroup):
    """Options Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(
                self,
                master,
                N_("Options"),
                app)

        self.grid3rows()


#        col,row=0,0
#        b = Ribbon.LabelButton(self.frame, #self.page, "<<Config>>",
#                text=_("Config"),
#                image=OCV.icons["config32"],
#                command=OCV.TK_APP.preferences,
#                state=DISABLED,
#                compound=TOP,
#                anchor=W,
#                background=OCV.COLOR_BACKGROUND)
#        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=NS)
#        tkExtra.Balloon.set(b, _("Open configuration dialog"))

#        # ===
#        col,row=1,0
#        b = Ribbon.LabelButton(self.frame,
#                text=_("Report"),
#                image=OCV.icons["debug"],
#                compound=LEFT,
#                command=Utils.ReportDialog.sendErrorReport,
#                anchor=W,
#                background=OCV.COLOR_BACKGROUND)
#        b.grid(row=row, column=col, padx=0, pady=0, sticky=EW)
#        tkExtra.Balloon.set(b, _("Send Error Report"))
#
#        # ---
#        col,row=1,1
#        b = Ribbon.LabelButton(self.frame,
#                text=_("Updates"),
#                image=OCV.icons["global"],
#                compound=LEFT,
#                command=OCV.TK_APP.checkUpdates,
#                anchor=W,
#                background=OCV.COLOR_BACKGROUND)
#        b.grid(row=row, column=col, padx=0, pady=0, sticky=EW)
#        tkExtra.Balloon.set(b, _("Check Updates"))

        col, row = 1, 2

        b = Ribbon.LabelButton(
            self.frame,
            text=_("About"),
            image=OCV.icons["about"],
            compound=Tk.LEFT,
            command=OCV.TK_APP.about,
            anchor=Tk.W,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.EW)

        tkExtra.Balloon.set(b, _("About the program"))


class PendantGroup(CNCRibbon.ButtonGroup):
    """Pendant Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(
                self,
                master,
                N_("Pendant"),
                app)

        self.grid3rows()

        col, row = 0, 0
        b = Ribbon.LabelButton(
            self.frame,
            text=_("Start"),
            image=OCV.icons["start_pendant"],
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.TK_APP.startPendant,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Start pendant"))

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            text=_("Stop"),
            image=OCV.icons["stop_pendant"],
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.TK_APP.stopPendant,
            background=OCV.COLOR_BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Stop pendant"))


class CloseGroup(CNCRibbon.ButtonGroup):
    """Close Group"""
    def __init__(self, master, app):

        CNCRibbon.ButtonGroup.__init__(
                self,
                master,
                N_("Close"),
                app)

        b = Ribbon.LabelButton(
            self.frame,
            text=_("Exit"),
            image=OCV.icons["exit32"],
            compound=Tk.TOP,
            command=OCV.TK_APP.quit,
            anchor=Tk.W,
            background=OCV.COLOR_BACKGROUND)

        b.pack(fill=Tk.BOTH, expand=Tk.YES)

        tkExtra.Balloon.set(b, _("Close program [Ctrl-Q]"))


class SerialFrame(CNCRibbon.PageLabelFrame):
    """Serial Frame"""
    def __init__(self, master, app):
        CNCRibbon.PageLabelFrame.__init__(
            self,
            master,
            "Serial",
            _("Serial"), app)

        self.autostart = Tk.BooleanVar()

        col, row = 0, 0

        b = Tk.Label(self, text=_("Port:"))

        b.grid(row=row, column=col, sticky=Tk.E)

        self.addWidget(b)

        self.portCombo = tkExtra.Combobox(
            self,
            False,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            width=16,
            command=self.comportClean)

        self.portCombo.grid(row=row, column=col+1, sticky=Tk.EW)

        tkExtra.Balloon.set(
                self.portCombo,
                _("Select (or manual enter) port to connect"))

        self.portCombo.set(IniFile.get_str("Connection","port"))

        self.addWidget(self.portCombo)

        self.comportRefresh()

        row += 1

        b = Tk.Label(self, text=_("Baud:"))

        b.grid(row=row, column=col, sticky=Tk.E)

        self.baudCombo = tkExtra.Combobox(
            self,
            True,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.baudCombo.grid(row=row, column=col+1, sticky=Tk.EW)

        tkExtra.Balloon.set(self.baudCombo, _("Select connection baud rate"))

        self.baudCombo.fill(BAUDS)

        self.baudCombo.set(IniFile.get_str("Connection","baud","115200"))

        self.addWidget(self.baudCombo)

        row += 1

        b = Tk.Label(self, text=_("Controller:"))

        b.grid(row=row, column=col, sticky=Tk.E)

        self.ctrlCombo = tkExtra.Combobox(
            self,
            True,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            command=self.ctrlChange)

        self.ctrlCombo.grid(row=row, column=col+1, sticky=Tk.EW)

        tkExtra.Balloon.set(self.ctrlCombo, _("Select controller board"))

        self.ctrlCombo.fill(OCV.TK_APP.controllerList())

        self.ctrlCombo.set(OCV.TK_APP.controller)

        self.addWidget(self.ctrlCombo)

        row += 1

        b = Tk.Checkbutton(
                self,
                text=_("Connect on startup"),
                variable=self.autostart)

        b.grid(row=row, column=col, columnspan=2, sticky=Tk.W)

        tkExtra.Balloon.set(
            b,
            _("Connect to serial on startup of the program"))

        self.autostart.set(IniFile.get_bool("Connection","openserial"))

        self.addWidget(b)

        col += 2

        self.comrefBtn = Ribbon.LabelButton(
            self,
            image=OCV.icons["refresh"],
            text=_("Refresh"),
            compound=Tk.TOP,
            command=lambda s=self: s.comportRefresh(True),
            background=OCV.COLOR_BACKGROUND)

        self.comrefBtn.grid(
            row=row,
            column=col,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(self.comrefBtn, _("Refresh list of serial ports"))

        #col += 2
        row = 0

        self.connectBtn = Ribbon.LabelButton(
            self,
            image=OCV.icons["serial48"],
            text=_("Open"),
            compound=Tk.TOP,
            command=lambda s=self: s.event_generate("<<Connect>>"),
            background=OCV.COLOR_BACKGROUND)

        self.connectBtn.grid(
            row=row,
            column=col,
            rowspan=3,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(self.connectBtn, _("Open/Close serial port"))

        self.grid_columnconfigure(1, weight=1)

    def ctrlChange(self):
#        OCV.TK_APP.controller = Utils.CONTROLLER.get(self.ctrlCombo.get(), 0)
#        print("selected",self.ctrlCombo.get())
        OCV.TK_APP.controllerSet(self.ctrlCombo.get())

    def comportClean(self, event=None):
        clean = self.portCombo.get().split("\t")[0]
        if(self.portCombo.get() != clean):
#            print("comport fix")
            self.portCombo.set(clean)

    def comportsGet(self):
        try:
            return comports(include_links=True)
        except TypeError:
            print("Using old style comports()!")
            return comports()

    def comportRefresh(self, dbg=False):
        # Detect devices
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

            if i[2] is not None:

                for hw in i[2].split(' '):
                    hwgrep += ["hwgrep://{0}\t{1}".format(hw, i[1])]

        # Populate combobox
        devices = sorted(["{0}\t {1}".format(*x) for x in com_ports])
        devices += ['']
        devices += sorted(set(hwgrep))
        devices += ['']

        if OCV.IS_PY3 is True:
            s_string = "spy://{0}?color\t(Debug) {1}"
        else:
            s_string = "spy://{0}?raw&color\t(Debug) {1}"

        devices += sorted([s_string.format(*x) for x in com_ports])

        devices += ['', 'socket://localhost:23', 'rfc2217://localhost:2217']

        # Clean neighbour duplicates
        devices_clean = []
        devprev = ''

        for i in devices:
            if i.split("\t")[0] != devprev:
                devices_clean += [i]

            devprev = i.split("\t")[0]

        self.portCombo.fill(devices_clean)

    def saveConfig(self):
        # Connection
        IniFile.set_value("Connection", "controller", OCV.TK_APP.controller)
        IniFile.set_value("Connection", "port", self.portCombo.get().split("\t")[0])
        IniFile.set_value("Connection", "baud", self.baudCombo.get())
        IniFile.set_value("Connection", "openserial", self.autostart.get())


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
