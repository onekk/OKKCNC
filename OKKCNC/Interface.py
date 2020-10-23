# -*- coding: ascii -*-
"""Interface.py

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

# Import Tkinter
try:
    import Tkinter as Tk
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import CNCCanvas
import CNCRibbon
import Commands as cmd
# Import Here the OCV module as it contains variables used across the program
import OCV
import IniFile
import Ribbon
import tkExtra
import Utils

from ToolsPage import ToolsPage  # , Tools
from FilePage import FilePage
from ControlPage import ControlPage
from TerminalPage import TerminalPage
from ProbePage import ProbePage
from EditorPage import EditorPage


def main_interface(self):
    """Generate main interface widgets
    moved from __main__.py
    """

    # --- Ribbon ---
    OCV.RIBBON = Ribbon.TabRibbonFrame(self)
    OCV.RIBBON.pack(side=Tk.TOP, fill=Tk.X)

    # Main frame
    self.paned = Tk.PanedWindow(self, orient=Tk.HORIZONTAL)
    self.paned.pack(fill=Tk.BOTH, expand=Tk.YES)

    # Status bar
    frame = Tk.Frame(self)
    frame.pack(side=Tk.BOTTOM, fill=Tk.X)
    OCV.STATUSBAR = tkExtra.ProgressBar(
        frame,
        height=20,
        relief=Tk.SUNKEN)

    OCV.STATUSBAR.pack(
        side=Tk.LEFT,
        fill=Tk.X,
        expand=Tk.YES)

    OCV.STATUSBAR.configText(
        fill="DarkBlue",
        justify=Tk.LEFT,
        anchor=Tk.W)

    self.statusz = Tk.Label(
        frame,
        foreground="DarkRed",
        relief=Tk.SUNKEN,
        anchor=Tk.W,
        width=10)

    self.statusz.pack(side=Tk.RIGHT)

    self.statusy = Tk.Label(
        frame,
        foreground="DarkRed",
        relief=Tk.SUNKEN,
        anchor=Tk.W,
        width=10)

    self.statusy.pack(side=Tk.RIGHT)

    self.statusx = Tk.Label(
        frame,
        foreground="DarkRed",
        relief=Tk.SUNKEN,
        anchor=Tk.W,
        width=10)

    self.statusx.pack(side=Tk.RIGHT)

    # Buffer bar
    OCV.BUFFERBAR = tkExtra.ProgressBar(
        frame,
        height=20,
        width=40,
        relief=Tk.SUNKEN)

    OCV.BUFFERBAR.pack(side=Tk.RIGHT, expand=Tk.NO)

    OCV.BUFFERBAR.setLimits(0, 100)

    tkExtra.Balloon.set(OCV.BUFFERBAR, _("Controller buffer fill"))

    # --- Left side ---
    self.Lframe = Tk.Frame(self.paned)

    self.paned.add(self.Lframe)  #, minsize=340)

    self.pageframe = Tk.Frame(self.Lframe)

    self.pageframe.pack(side=Tk.TOP, expand=Tk.YES, fill=Tk.BOTH)

    OCV.RIBBON.setPageFrame(self.pageframe)

    # Command bar
    cmd_f = Tk.Frame(self.Lframe)
    cmd_f.pack(side=Tk.BOTTOM, fill=Tk.X)

    self.cmdlabel = Tk.Label(cmd_f, text=_("Command:"))
    self.cmdlabel.pack(side=Tk.LEFT)

    OCV.CMD_W = Tk.Entry(cmd_f, relief=Tk.SUNKEN, background="White")

    OCV.CMD_W.pack(side=Tk.RIGHT, fill=Tk.X, expand=Tk.YES)

    tkExtra.Balloon.set(
        OCV.CMD_W,
        _("MDI Command line: Accept g-code commands or macro " \
          "commands (RESET/HOME...) or editor commands " \
          "(move,inkscape, round...) [Space or Ctrl-Space]"))

    # --- Right side ---
    self.Rframe = Tk.Frame(self.paned)
    self.paned.add(self.Rframe)

    # --- Canvas ---
    OCV.CANVAS_F = CNCCanvas.CanvasFrame(self.Rframe, self)

    OCV.CANVAS_F.pack(side=Tk.TOP, fill=Tk.BOTH, expand=Tk.YES)

    self.linebuffer = Tk.Label(self.Rframe, background="khaki")

    self.proc_line = Tk.StringVar()

    self.linebuffer.configure(
        height=1,
        anchor=Tk.W,
        textvariable=self.proc_line)

    self.linebuffer.pack(side=Tk.BOTTOM, fill=Tk.X)

    # fist create Pages
    self.pages = {}
    for cls in (ControlPage, EditorPage, FilePage, ProbePage,
                TerminalPage, ToolsPage):

        page = cls(OCV.RIBBON, self)

        self.pages[page.name] = page

    # then add their properties (in separate loop)
    errors = []
    for name, page in self.pages.items():
        for page_name in IniFile.get_str(
                OCV.PRG_NAME, "{0}.ribbon".format(page.name)).split():
            try:
                page.addRibbonGroup(page_name)
            except KeyError:
                errors.append(page_name)

        for page_name in IniFile.get_str(
                OCV.PRG_NAME, "{0}.page".format(page.name)).split():
            last = page_name[-1]
            try:
                if last == "*":
                    page.addPageFrame(
                        page_name[:-1], fill=Tk.BOTH, expand=Tk.TRUE)
                else:
                    page.addPageFrame(page_name)
            except KeyError:
                errors.append(page_name)

    if errors:
        tkMessageBox.showwarning(
            "OKKCNC configuration",
            "The following pages \"{0}\" are found in " \
            "your <HOME>/.OKKCNC initialization file, " \
            "which are either spelled wrongly or " \
            "no longer exist in OKKCNC".format(" ".join(errors)), parent=self)


class DROFrame(CNCRibbon.PageFrame):
    """DRO Frame"""
    dro_status = ('Helvetica', 11, 'bold')
    dro_wpos = ('Helvetica', 11, 'bold')
    dro_mpos = ('Helvetica', 11)

    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "DRO", app)

        # print("DROFrame self.app", self.app)

        DROFrame.dro_status = Utils.get_font("dro.status", DROFrame.dro_status)
        DROFrame.dro_wpos = Utils.get_font("dro.wpos", DROFrame.dro_wpos)
        DROFrame.dro_mpos = Utils.get_font("dro.mpos", DROFrame.dro_mpos)

        row = 0
        col = 0
        Tk.Label(
            self,
            font=DROFrame.dro_status,
            text=_("Status:")
            ).grid(row=row, column=col, sticky=Tk.E)

        col += 1

        self.state = Tk.Button(
            self,
            text=OCV.STATE_NOT_CONN,
            font=DROFrame.dro_status,
            command=cmd.showState,
            cursor="hand1",
            background=OCV.STATECOLOR[OCV.STATE_NOT_CONN],
            activebackground="LightYellow")

        self.state.grid(row=row, column=col, columnspan=3, sticky=Tk.EW)

        tkExtra.Balloon.set(
            self.state,
            _("Show current state of the machine\n"
              "Click to see details\n"
              "Right-Click to clear alarm/errors"))
        #self.state.bind("<Button-3>", lambda e,s=self : s.event_generate("<<AlarmClear>>"))
        self.state.bind("<Button-3>", self.state_menu)

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
        self.xwork.bind('<FocusIn>', cmd.work_focus)
        self.xwork.bind('<Return>', self.set_x)
        self.xwork.bind('<KP_Enter>', self.set_x)

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
        self.ywork.bind('<FocusIn>', cmd.work_focus)
        self.ywork.bind('<Return>', self.set_y)
        self.ywork.bind('<KP_Enter>', self.set_y)

        col += 1

        self.zwork = Tk.Entry(
            self, font=DROFrame.dro_wpos,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            relief=Tk.FLAT,
            borderwidth=0,
            justify=Tk.RIGHT)
        self.zwork.grid(row=row, column=col, padx=1, sticky=Tk.EW)
        tkExtra.Balloon.set(self.zwork, _("Z work position (click to set)"))
        self.zwork.bind('<FocusIn>', cmd.work_focus)
        self.zwork.bind('<Return>', self.set_z)
        self.zwork.bind('<KP_Enter>', self.set_z)

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
       
        col = 0

        but = Tk.Button(
            self,
            text=_("SWP"),
            font=OCV.FONT_DRO_ZERO,
            image=OCV.icons["origin"],
            compound=Tk.LEFT,
            activebackground="LightYellow",
            command=lambda s=self: s.event_generate("<<SetWPOS>>"),
            padx=2, pady=1)

        but.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        #but.pack(side=Tk.LEFT, fill=Tk.X, expand=Tk.YES)

        tkExtra.Balloon.set(but, _("Set WPOS to mouse location"))

        self.addWidget(but)
        
        
        col = 1

        self.xzero = Tk.Button(
            self,
            text=_("X=0"),
            font=OCV.FONT_DRO_ZERO,
            command=cmd.set_x0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.xzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(
            self.xzero,
            _("Set X coordinate to zero (or to typed coordinate in WPos)"))

        self.addWidget(self.xzero)

        col += 1
        self.yzero = Tk.Button(
            self,
            text=_("Y=0"),
            font=OCV.FONT_DRO_ZERO,
            command=cmd.set_y0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.yzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(
            self.yzero,
            _("Set Y coordinate to zero (or to typed coordinate in WPos)"))

        self.addWidget(self.yzero)

        col += 1
        self.zzero = Tk.Button(
            self,
            text=_("Z=0"),
            font=OCV.FONT_DRO_ZERO,
            command=cmd.set_z0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.zzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(
            self.zzero,
            _("Set Z coordinate to zero (or to typed coordinate in WPos)"))

        self.addWidget(self.zzero)

        # Set buttons
        row += 1


        col = 0
        but = Tk.Button(
            self,
            text=_("MG"),
            font=OCV.FONT_DRO_ZERO,
            image=OCV.icons["gantry"],
            compound=Tk.LEFT,
            activebackground="LightYellow",
            command=lambda s=self: s.event_generate("<<MoveGantry>>"),
            padx=2, pady=1)
        but.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        #but.pack(side=Tk.RIGHT, fill=Tk.X, expand=Tk.YES)

        tkExtra.Balloon.set(but, _("Move gantry to mouse location [g]"))

        self.addWidget(but)


        
        col = 1
        self.xyzero = Tk.Button(
            self,
            text=_("XY=0"),
            font=OCV.FONT_DRO_ZERO,
            command=cmd.set_xy0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.xyzero.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(
            self.xyzero,
            _("Set XY coordinate to zero (or to typed coordinate in WPos)"))

        self.addWidget(self.xyzero)

        col += 1
        self.xyzzero = Tk.Button(
            self,
            text=_("XYZ=0"),
            font=OCV.FONT_DRO_ZERO,
            command=cmd.set_xyz0,
            activebackground="LightYellow",
            padx=2, pady=1)

        self.xyzzero.grid(
            row=row, column=col, pady=0, sticky=Tk.EW, columnspan=2)
        tkExtra.Balloon.set(
            self.xyzzero,
            _("Set XYZ coordinate to zero (or to typed coordinate in WPos)"))

        self.addWidget(self.xyzzero)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

    def state_menu(self, event=None):
        """display state menu"""
        menu = Tk.Menu(self, tearoff=0)

        menu.add_command(
            label=_("Show Info"),
            image=OCV.icons["info"],
            compound=Tk.LEFT,
            command=cmd.showState)

        menu.add_command(
            label=_("Clear Message"),
            image=OCV.icons["clear"],
            compound=Tk.LEFT,
            command=lambda s=self: s.event_generate("<<AlarmClear>>"))

        menu.add_separator()

        menu.add_command(
            label=_("Feed hold"),
            image=OCV.icons["pause"],
            compound=Tk.LEFT,
            command=lambda s=self: s.event_generate("<<FeedHold>>"))

        menu.add_command(
            label=_("Resume"),
            image=OCV.icons["start"],
            compound=Tk.LEFT,
            command=lambda s=self: s.event_generate("<<Resume>>"))

        menu.tk_popup(event.x_root, event.y_root)

    def update_state(self):
        """update State label"""
        msg = OCV.APP._msg or OCV.c_state
        if OCV.CD["pins"] is not None and OCV.CD["pins"] != "":
            msg += " ["+OCV.CD["pins"]+"]"
        self.state.config(text=msg, background=OCV.CD["color"])

    def update_coords(self):
        """Update WCS and MCS"""
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

    def set_x(self, event=None):
        """set a different wcs X"""
        if OCV.s_running:
            return

        try:
            value = round(eval(self.xwork.get(), None, OCV.CD), 3)
            OCV.MCTRL.wcs_set(value, None, None)
        except:
            pass

    def set_y(self, event=None):
        """set a different wcs Y"""
        if OCV.s_running:
            return

        try:
            value = round(eval(self.ywork.get(), None, OCV.CD), 3)
            OCV.MCTRL.wcs_set(None, value, None)
        except:
            pass

    def set_z(self, event=None):
        """set a different wcs Z"""
        if OCV.s_running:
            return

        try:
            value = round(eval(self.zwork.get(), None, OCV.CD), 3)
            OCV.MCTRL.wcs_set(None, None, value)
        except:
            pass


class UserGroup(CNCRibbon.ButtonGroup):
    """User Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "User", app)
        self.grid3rows()

        b_num = IniFile.get_int("Buttons", "n", 6)

        for idx in range(1, b_num):
            but = Utils.UserButton(
                self.frame,
                OCV.APP,
                idx,
                anchor=Tk.W,
                background=OCV.COLOR_BACKGROUND)
            col, row = divmod(idx-1, 3)

            but.grid(row=row, column=col, sticky=Tk.NSEW)

            self.addWidget(but)


class RunGroup(CNCRibbon.ButtonGroup):
    """Run Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "Run", app)
        OCV.RUN_GROUP = self

        but = Ribbon.LabelButton(
            self.frame,
            self, "<<Run>>",
            image=OCV.icons["start32"],
            text=_("Start"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        but.pack(side=Tk.LEFT, fill=Tk.BOTH)

        tkExtra.Balloon.set(
            but, _("Run g-code commands from editor to controller"))

        self.addWidget(but)

        but = Ribbon.LabelButton(
            self.frame,
            self, "<<Pause>>",
            name="run_pause",
            image=OCV.icons["pause32"],
            text=_("Pause"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        but.pack(side=Tk.LEFT, fill=Tk.BOTH)

        tkExtra.Balloon.set(
            but,
            _("Pause running program. Sends either FEED_HOLD ! or CYCLE_START ~"))

        but = Ribbon.LabelButton(
            self.frame,
            self, "<<Stop>>",
            name="run_stop",
            image=OCV.icons["stop32"],
            text=_("Stop"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        but.pack(side=Tk.LEFT, fill=Tk.BOTH)

        tkExtra.Balloon.set(
            but,
            _("Pause running program and soft reset controller to empty the buffer."))


class ConnectionGroup(CNCRibbon.ButtonMenuGroup):
    """Connection Group"""

    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(
            self,
            master,
            N_("Connection"),
            app,
            [(_("Hard Reset"), "reset", OCV.MCTRL.hardReset),
             (_("Toggle Sender Dbg"), "toggle", self.toggleDbgSnd),
             (_("Toggle Com Dbg"), "toggle", self.toggleDbgCom),
             (_("View Flags"), "toggle", self.viewFlags)
            ])

        # print("ConnectionGroup app", app)

        self.grid2rows()

        col, row = 0, 0

        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["home32"],
            text=_("Home"),
            compound=Tk.TOP,
            anchor=Tk.W,
            command=lambda s=self: s.event_generate("<<Home>>"),
            background=OCV.COLOR_BACKGROUND)

        but.grid(
            row=row, column=col,
            rowspan=3,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("Perform a homing cycle [$H]"))

        self.addWidget(but)

        col, row = 1, 0

        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["unlock"],
            text=_("Unlock"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=self: s.event_generate("<<Unlock>>"),
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("Unlock controller [$X]"))

        self.addWidget(but)

        row += 1

        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["serial"],
            text=_("Connection"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=self: s.event_generate("<<Connect>>"),
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("Open/Close connection"))
        self.addWidget(but)

        row += 1
        but = Ribbon.LabelButton(
            self.frame,
            image=OCV.icons["reset"],
            text=_("Reset"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=self: s.event_generate("<<SoftReset>>"),
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("Software reset of controller [ctrl-x]"))

        self.addWidget(but)

    def viewFlags(self):
        Utils.showState()

    @staticmethod
    def toggleDbgSnd():
        if OCV.DEBUG_SER is True:
            OCV.DEBUG_SER = False
        else:
            OCV.DEBUG_SER = True

    @staticmethod
    def toggleDbgCom():
        if OCV.DEBUG_COM is True:
            OCV.DEBUG_COM = False
        else:
            OCV.DEBUG_COM = True


class MemoryGroup(CNCRibbon.ButtonMenuGroup):
    """Panel with memory buttons and some service buttons"""

    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(
            self, master, N_("Memory"), app,
            [(_("Save Memories"), "save",
              lambda a=app: a.event_generate("<<SaveMems>>")),
             (_("Toggle this Bank visibility"), "view",
              self.display_bank_mems),
             (_("Don't Show all Memories"), "view",
              self.reset_all_displayed_mem),
            ])

        col, row = 0, 0

        but = Tk.Button(
            self.frame,
            #image=OCV.icons["start32"],
            font=OCV.FONT,
            text=_("M2A"),
            background=OCV.COLOR_BACKGROUND,
            command=None)

        but.grid(row=row, column=col)# padx=0, pady=0, sticky=Tk.EW)

        tkExtra.Balloon.set(but, _("Memory to A"))

        self.addWidget(but)

        row += 1

        but = Tk.Button(
            self.frame,
            #image=OCV.icons["pause32"],
            font=OCV.FONT,
            text=_("M2B"),
            background=OCV.COLOR_BACKGROUND,
            command=None)

        but.grid(row=row, column=col, columnspan=3)

        tkExtra.Balloon.set(but, _("Memory to B"))

        self.addWidget(but)

        row += 1

        but = Tk.Button(
            self.frame,
            #image=OCV.icons["stop32"],
            font=OCV.FONT,
            text=_("C_M"),
            command=self.clr_mem,
            background=OCV.COLOR_BACKGROUND)
        but.grid(row=row, column=col, columnspan=3)

        tkExtra.Balloon.set(but, _("Cancel mem X"))

        self.addWidget(but)

        row, col = 0, 4

        lab = Tk.Label(
            self.frame,
            name="lab_bank",
            text="B {0}".format(OCV.WK_bank),
            background=OCV.COLOR_BACKGROUND_LABELS)

        lab.grid(row=row, column=col, columnspan=2)

        tkExtra.Balloon.set(
            lab, _("Bank Number \n Mem {0}".format(OCV.WK_mem_num)))

        self.addWidget(lab)

        row += 1

        but = Tk.Button(
            self.frame,
            # image=OCV.icons["pause32"],
            font=OCV.FONT,
            text=_("B +"),
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, columnspan=2)

        but.bind(
            "<1>", lambda event, obj="B+": self.on_click_bank(event, obj))

        tkExtra.Balloon.set(but, _("Upper Memory Bank"))

        self.addWidget(but)

        row += 1

        but = Tk.Button(
            self.frame,
            # image=OCV.icons["stop32"],
            font=OCV.FONT,
            text=_("B -"),
            compound=Tk.TOP,
            background=OCV.COLOR_BACKGROUND)

        but.grid(row=row, column=col, columnspan=2)

        but.bind(
            "<1>", lambda event, obj="B-": self.on_click_bank(event, obj))

        tkExtra.Balloon.set(but, _("Lower Memory Bank"))

        self.addWidget(but)

        for idx in range(0, OCV.WK_bank_mem, 3):
            col += 3
            rows = 0
            for sub_i in range(idx, idx+3):
                but_name = "but_m_{0}".format(str(sub_i))
                # print("creation", but_name)
                but = Tk.Button(
                    self.frame,
                    # image=OCV.icons["pause32"],
                    font=OCV.FONT,
                    name=but_name,
                    text="M_{0:02d}".format(sub_i + 2),
                    compound=Tk.TOP,
                    background=OCV.COLOR_BACKGROUND)

                but.grid(row=rows, column=col, columnspan=3,
                         padx=0, pady=0, sticky=Tk.NSEW)

                but.bind(
                    "<Button-1>",
                    lambda event, obj=sub_i: self.on_click_mem(event, obj))

                but.bind(
                    "<Button-3>",
                    lambda event, obj=sub_i: self.on_click_mem(event, obj))

                tkExtra.Balloon.set(but, _("Set {0}"))

                self.addWidget(but)

                rows += 1

        # print("MemoryGroup: Init end")
        self.select_bank(0)

    def on_click_mem(self, event, obj):
        """manage the click on memory buttons
        left click - go to postion in memory
        right click - memorize position in memory
        """
        if OCV.c_state == "Idle":
            # print(event.num)
            # print("Button {0} CLicked".format(obj))
            mem_clicked = (OCV.WK_bank * OCV.WK_bank_mem) + 2 + obj
            mem_key = "mem_{0}".format(mem_clicked)
            # print ("{0} clicked".format(mem_key))

            # Left Button Clicked, goto position
            if event.num == 1:
                if mem_key in OCV.WK_mems:
                    mem_data = OCV.WK_mems[mem_key]
                    if mem_data[3] == 1:
                        self.sendGCode(
                            "$J=G90 G53 {0}{1:f} {2}{3:f} F100000".format(
                                "X", mem_data[0],
                                "Y", mem_data[1]))

            # Right Button Clicked, set mem
            if event.num == 3:
                OCV.WK_mem = mem_clicked
                mem_name = Utils.ask_for_value(OCV.APP, "ME")
                # print("MG mem_name = ", mem_name)
                if mem_name is None:
                    mem_name = mem_key

                OCV.WK_mems[mem_key] = [
                    OCV.CD["mx"],
                    OCV.CD["my"],
                    OCV.CD["mz"],
                    1,
                    mem_name]

                # refresh buttons
                # force the refres of all buttons as the creation is done
                # in batch
                self.select_bank(OCV.WK_bank)

                self.event_generate("<<SetMem>>")
        else:
            return

    def on_click_bank(self, event, obj):
        """manage the click on bank buttons
        one place for two buttons depending on paramter 'obj'
        """
        # print("you clicked on", obj)
        if obj == "B+":
            mem_bank = OCV.WK_bank + 1
        elif obj == "B-":
            mem_bank = OCV.WK_bank - 1
        else:
            return

        if mem_bank < 0:
            OCV.WK_bank = 0
            mem_bank = 0
        elif mem_bank > 3:
            OCV.WK_bank = 3
            mem_bank = 3

        self.select_bank(mem_bank)

    def select_bank(self, mem_bank):
        """actions to select a memory bank"""
        # assign the proper values
        OCV.WK_bank = mem_bank
        OCV.WK_bank_start = (OCV.WK_bank * OCV.WK_bank_mem) + 2
        wdg = self.frame.nametowidget("lab_bank")
        wdg.config(text="B {0}".format(OCV.WK_bank))
        but_color = OCV.COLOR_BACKGROUND

        for idx in range(0, OCV.WK_bank_mem):
            but_name = "but_m_{0}".format(str(idx))
            label = "M_{0:02d}".format(OCV.WK_bank_start + idx)
            mem_addr = "mem_{0}".format(OCV.WK_bank_start + idx)
            mem_tt = "{0}\n\n name: {5}\n\nX: {1}\n\nY: {2}\n\nZ: {3}"
            wdg = self.frame.nametowidget(but_name)

            if mem_addr in OCV.WK_mems:
                if OCV.WK_mems[mem_addr][3] == 1:
                    but_color = "aquamarine"
                    mem_data = OCV.WK_mems[mem_addr]
                    # print("Select Bank ", md)
                    tkExtra.Balloon.set(
                        wdg, mem_tt.format(mem_addr, *mem_data))
            else:
                but_color = OCV.COLOR_BACKGROUND
                tkExtra.Balloon.set(wdg, "Empty")

            wdg.config(text=label, background=but_color)

    def clr_mem(self):
        """clear memory - asking for memory number"""
        mem_num = Utils.ask_for_value(OCV.APP, "MN")

        # print("clr_mem >", mem_num)

        if mem_num is not None:
            mem_addr = "mem_{0}".format(mem_num)
            OCV.WK_mems[mem_addr] = [0, 0, 0, 0, "Empty"]
            # clear the marker on canvas
            # and the canvas memnory shown list
            OCV.WK_mem = mem_num
            self.event_generate("<<ClrMem>>")
            # check if the button is shown
            b_check = self.check_btn_value(mem_num)

            # print ("clr_mem check > ",b_check)

            if b_check > 0:
                # reset the button state
                but_name = "but_m_{0}".format(mem_num - OCV.WK_bank_start)
                label = "M_{0}".format(mem_num)

                # print("clr_mem but_name > ", but_name)

                wdg = self.frame.nametowidget(but_name)
                but_color = OCV.COLOR_BACKGROUND
                tkExtra.Balloon.set(wdg, "Empty")
                wdg.config(text=label, background=but_color)

        # print(OCV.WK_mems)

    @staticmethod
    def check_btn_value(mem_num):
        """check if memory button is in selected bank"""
        upp_mem = OCV.WK_bank_start + OCV.WK_bank_mem
        # print ("check Button {0} in range {1} {2}".format(
        #        mem_num, OCV.WK_bank_start, upp_mem))
        if mem_num in range(OCV.WK_bank_start, upp_mem):
            return mem_num
        else:
            return -1

    @staticmethod
    def display_bank_mems():
        """display/hide all bank "active" memory on canvas"""
        # print("sBM Bank >> ", OCV.WK_bank)
        for idx in range(0, OCV.WK_bank_mem):
            mem_num = OCV.WK_bank_start + idx
            mem_addr = "mem_{0}".format(mem_num)

            # check the presence of the key in dictionary
            if mem_addr in OCV.WK_mems:
                # chek if the memory is valid
                mem_data = OCV.WK_mems[mem_addr]
                # print("sBM mem_data >> ", mem_data)
                if mem_data[3] == 1:
                    OCV.WK_mem = mem_num

                    if OCV.WK_active_mems[OCV.WK_mem] == 2:
                        OCV.APP.event_generate("<<ClrMem>>")
                    else:
                        OCV.APP.event_generate("<<SetMem>>")

    @staticmethod
    def reset_all_displayed_mem():
        """hide all "active" memory on canvas"""
        indices = [i for i, x in enumerate(OCV.WK_active_mems) if x == 2]

        for mem in indices:
            print("reset_all_displayed_mem index = ", mem)
            OCV.WK_mem = mem
            OCV.APP.event_generate("<<ClrMem>>")
