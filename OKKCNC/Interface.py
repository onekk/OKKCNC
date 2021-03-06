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
    OCV.TK_RIBBON = Ribbon.TabRibbonFrame(self)
    OCV.TK_RIBBON.pack(side=Tk.TOP, fill=Tk.X)

    # Main frame
    self.paned = Tk.PanedWindow(self, orient=Tk.HORIZONTAL)
    self.paned.pack(fill=Tk.BOTH, expand=Tk.YES)

    # Status bar
    frame = Tk.Frame(self)
    frame.pack(side=Tk.BOTTOM, fill=Tk.X)
    OCV.TK_STATUSBAR = tkExtra.ProgressBar(
        frame,
        height=20,
        relief=Tk.SUNKEN)

    OCV.TK_STATUSBAR.pack(
        side=Tk.LEFT,
        fill=Tk.X,
        expand=Tk.YES)

    OCV.TK_STATUSBAR.configText(
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
    OCV.TK_BUFFERBAR = tkExtra.ProgressBar(
        frame,
        height=20,
        width=40,
        relief=Tk.SUNKEN)

    OCV.TK_BUFFERBAR.pack(side=Tk.RIGHT, expand=Tk.NO)

    OCV.TK_BUFFERBAR.setLimits(0, 100)

    tkExtra.Balloon.set(OCV.TK_BUFFERBAR, _("Controller buffer fill"))

    # --- Left side ---
    self.Lframe = Tk.Frame(self.paned)

    self.paned.add(self.Lframe)  #, minsize=340)

    self.pageframe = Tk.Frame(self.Lframe)

    self.pageframe.pack(side=Tk.TOP, expand=Tk.YES, fill=Tk.BOTH)

    OCV.TK_RIBBON.setPageFrame(self.pageframe)

    # Command bar
    cmd_f = Tk.Frame(self.Lframe)
    cmd_f.pack(side=Tk.BOTTOM, fill=Tk.X)

    self.cmdlabel = Tk.Label(cmd_f, text=_("Command:"))
    self.cmdlabel.pack(side=Tk.LEFT)

    OCV.TK_CMD_W = Tk.Entry(
        cmd_f, relief=Tk.SUNKEN, background=OCV.COLOR_BG1)

    OCV.TK_CMD_W.pack(side=Tk.RIGHT, fill=Tk.X, expand=Tk.YES)

    tkExtra.Balloon.set(
        OCV.TK_CMD_W,
        _("MDI Command line: Accept g-code commands or macro " \
          "commands (RESET/HOME...) or editor commands " \
          "(move,inkscape, round...) [Space or Ctrl-Space]"))

    # --- Right side ---
    self.Rframe = Tk.Frame(self.paned)
    self.paned.add(self.Rframe)

    # --- Canvas ---
    OCV.TK_CANVAS_F = CNCCanvas.CanvasFrame(self.Rframe, self)

    OCV.TK_CANVAS_F.pack(side=Tk.TOP, fill=Tk.BOTH, expand=Tk.YES)

    self.linebuffer = Tk.Label(self.Rframe, background=OCV.COLOR_BG2)

    self.proc_line = Tk.StringVar()

    self.linebuffer.configure(
        height=1,
        anchor=Tk.W,
        textvariable=self.proc_line)

    self.linebuffer.pack(side=Tk.BOTTOM, fill=Tk.X)

    # first create Pages
    self.pages = {}
    for cls in (ControlPage, EditorPage, FilePage, ProbePage,
                TerminalPage, ToolsPage):

        page = cls(OCV.TK_RIBBON, self)

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

def set_debug_flags():
    
        if IniFile.get_bool("Debug", "generic"):
             OCV.DEBUG = True

        if IniFile.get_bool("Debug", "graph"):
             OCV.DEBUG_GRAPH = True

        if IniFile.get_bool("Debug", "interface"):
             OCV.DEBUG_INT = True

        if IniFile.get_bool("Debug", "coms"):
             OCV.DEBUG_COM = True

        if IniFile.get_bool("Debug", "sio"):
             OCV.DEBUG_SER = True

        if IniFile.get_bool("Debug", "gpar"):
             OCV.DEBUG_PAR = True
             OCV.DEBUG_HEUR = IniFile.get_bool("Debug", "heur")    


def show_stats():
    """Display statistics on enabled blocks"""    
    toplevel = Tk.Toplevel(OCV.TK_MAIN)
    toplevel.transient(OCV.TK_MAIN)
    toplevel.title(_("Statistics"))

    if OCV.inch:
        unit = "in"
    else:
        unit = "mm"

    infostr = "{0:.3f} .. {1:.3f} [{2:.3f}] {3}"
    infostr1 = "{0:.3f} {1}"
    time_str = "H:{0:d} M:{1:02d} S:{2:02d}"

    # count enabled blocks
    e = 0
    b_l = 0
    b_r = 0
    b_t = 0

    for block in OCV.blocks:
        if block.enable:
            e += 1
            b_l += block.length
            b_r += block.rapid
            b_t += block.time

    frame = Tk.LabelFrame(
        toplevel,
        text=_("Enabled GCode"),
        foreground="DarkRed")

    frame.pack(fill=Tk.BOTH)

    row, col = 0, 0

    lab = Tk.Label(
        frame,
        text=_("Margins X:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr.format(
            OCV.CD["xmin"], OCV.CD["xmax"],
            OCV.CD["xmax"] -OCV.CD["xmin"],
            unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text="... Y:")

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr.format(
            OCV.CD["ymin"], OCV.CD["ymax"],
            OCV.CD["ymax"] -OCV.CD["ymin"],
            unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text="... Z:")

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr.format(
            OCV.CD["zmin"], OCV.CD["zmax"],
            OCV.CD["zmax"] -OCV.CD["zmin"],
            unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(
        frame,
        text=_("# Blocks:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame, text=str(e),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text=_("Length:"))

    lab.grid(row=row, column=col, sticky=Tk.E)


    col += 1

    lab = Tk.Label(
        frame,
        text=infostr1.format(b_l, unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text=_("Rapid:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr1.format(b_r, unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text=_("Time:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    bt_h, bt_m = divmod(b_t, 60)  # t in min
    bt_s = (bt_m-int(bt_m))*60

    lab = Tk.Label(
        frame,
        text=time_str.format(int(bt_h), int(bt_m), int(bt_s)),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    frame.grid_columnconfigure(1, weight=1)


    frame = Tk.LabelFrame(
        toplevel,
        text=_("All GCode"),
        foreground="DarkRed")

    frame.pack(fill=Tk.BOTH)

    row, col = 0, 0

    lab = Tk.Label(frame, text=_("Margins X:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr.format(
            OCV.CD["axmin"], OCV.CD["axmax"],
            OCV.CD["axmax"] -OCV.CD["axmin"],
            unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text="... Y:")

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr.format(
            OCV.CD["aymin"], OCV.CD["aymax"],
            OCV.CD["aymax"] - OCV.CD["aymin"],
            unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text="... Z:")

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr.format(
            OCV.CD["azmin"], OCV.CD["azmax"],
            OCV.CD["azmax"] - OCV.CD["azmin"],
            unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(
        frame,
        text=_("# Blocks:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=str(len(OCV.blocks)),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(
        frame,
        text=_("Length:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    lab = Tk.Label(
        frame,
        text=infostr1.format(OCV.TK_MAIN.cnc.totalLength, unit),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    row += 1
    col = 0

    lab = Tk.Label(frame, text=_("Time:"))

    lab.grid(row=row, column=col, sticky=Tk.E)

    col += 1

    tt_h, tt_m = divmod(OCV.TK_MAIN.cnc.totalTime, 60) # t in min
    tt_s = (tt_m-int(tt_m))*60

    lab = Tk.Label(
        frame,
        text=time_str.format(int(tt_h), int(tt_m), int(tt_s)),
        foreground="DarkBlue")

    lab.grid(row=row, column=col, sticky=Tk.W)

    frame.grid_columnconfigure(1, weight=1)

    frame = Tk.Frame(toplevel)
    frame.pack(fill=Tk.X)

    closeFunc = lambda e=None, t=toplevel: t.destroy()

    but = Tk.Button(frame, text=_("Close"), command=closeFunc)
    but.pack(pady=5)

    frame.grid_columnconfigure(1, weight=1)

    toplevel.bind("<Escape>", closeFunc)
    toplevel.bind("<Return>", closeFunc)
    toplevel.bind("<KP_Enter>", closeFunc)

    toplevel.deiconify()
    toplevel.wait_visibility()
    toplevel.resizable(False, False)

    try:
        toplevel.grab_set()
    except:
        pass

    but.focus_set()
    toplevel.lift()
    toplevel.wait_window()    

def show_error_panel():
    """Show controller error panel"""
    msg = "Messages"
    if len(OCV.CTL_ERRORS) > 1:
        msg = " \n\n".join(OCV.CTL_ERRORS)
    else:
        msg = "This controller has no error list"

    panel = Utils.ErrorWindow(OCV.TK_MAIN, _("Error Help"))
    panel.m_txt["height"] = 30
    panel.show_message(msg)

def show_settings_panel():
    """Show settings panel"""
    msg = "Messages"
    if len(OCV.CTL_SHELP) > 1:
        msg = " \n\n".join(OCV.CTL_SHELP)
    else:
        msg = "This controller has no setting list yet"

    panel = Utils.ErrorWindow(OCV.TK_MAIN, _("Settings Help"))
    panel.m_txt["height"] = 30
    panel.show_message(msg)

def showUserFile():
    """Show user file"""
    TEditor = Utils.TEditorWindow(OCV.TK_MAIN, 0)
    TEditor.parse_ini(OCV.USER_CONFIG)
    TEditor.txt_edit['state'] = 'disabled' # or 'normal'

def checkUpdates():
    """Check for updates"""
    # Find OKKCNC version
    # Updates.CheckUpdateDialog(self, OCV.PRG_VER)
    pass

def write_memAB(mem_name, pos_x, pos_y, pos_z):
            
    if mem_name == "memA":
        OCV.WK_mem = 0  # 0 = memA
        mem_idx = "mem_0"
        mem_desc = "mem A"        
    elif mem_name == "memB":
        OCV.WK_mem = 1  # 1 = memB        
        mem_idx = "mem_1"
        mem_desc = "mem B"
    else:
        return
    
    OCV.WK_mems[mem_idx] = [pos_x, pos_y, pos_z, 1, mem_desc]
    wid = OCV.TK_CONTROL.nametowidget(mem_name)

    wdata = "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(
        mem_name, pos_x, pos_y, pos_z)

    tkExtra.Balloon.set(wid, wdata)
    wid.configure(background=OCV.COLOR_MEM_SET)
            
    OCV.TK_MAIN.event_generate("<<SetMem>>")

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
            activebackground=OCV.COLOR_ACTIVE)

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
            activebackground=OCV.COLOR_ACTIVE,
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
            activebackground=OCV.COLOR_ACTIVE,
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
            activebackground=OCV.COLOR_ACTIVE,
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
            activebackground=OCV.COLOR_ACTIVE,
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
            activebackground=OCV.COLOR_ACTIVE,
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
            activebackground=OCV.COLOR_ACTIVE,
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
            activebackground=OCV.COLOR_ACTIVE,
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
        msg = OCV.TK_MAIN._msg or OCV.c_state
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
            OCV.TK_MCTRL.wcs_set(value, None, None)
        except:
            pass

    def set_y(self, event=None):
        """set a different wcs Y"""
        if OCV.s_running:
            return

        try:
            value = round(eval(self.ywork.get(), None, OCV.CD), 3)
            OCV.TK_MCTRL.wcs_set(None, value, None)
        except:
            pass

    def set_z(self, event=None):
        """set a different wcs Z"""
        if OCV.s_running:
            return

        try:
            value = round(eval(self.zwork.get(), None, OCV.CD), 3)
            OCV.TK_MCTRL.wcs_set(None, None, value)
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
                OCV.TK_MAIN,
                idx,
                anchor=Tk.W,
                background=OCV.COLOR_BG)
            col, row = divmod(idx-1, 3)

            but.grid(row=row, column=col, sticky=Tk.NSEW)

            self.addWidget(but)


class RunGroup(CNCRibbon.ButtonGroup):
    """Run Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, "Run", app)
        OCV.TK_RUN_GROUP = self

        but = Ribbon.LabelButton(
            self.frame,
            self, "<<Run>>",
            image=OCV.icons["start32"],
            text=_("Start"),
            compound=Tk.TOP,
            background=OCV.COLOR_BG)

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
            background=OCV.COLOR_BG)

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
            background=OCV.COLOR_BG)

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
            [(_("Hard Reset"), "reset", OCV.TK_MCTRL.hardReset),
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
            background=OCV.COLOR_BG)

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
            background=OCV.COLOR_BG)

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
            background=OCV.COLOR_BG)

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
            background=OCV.COLOR_BG)

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
            name="m2a",
            text=_("M2A"),
            font=OCV.FONT,
            background=OCV.COLOR_BG,
            activebackground=OCV.COLOR_ACTIVE,
            command=lambda: self.move_to_mem("MA"))

        but.grid(row=row, column=col, columnspan=3)

        tkExtra.Balloon.set(but, _("Memory to A"))

        self.addWidget(but)

        row += 1

        but = Tk.Button(
            self.frame,
            name="m2b",
            text=_("M2B"),
            font=OCV.FONT,
            background=OCV.COLOR_BG,
            activebackground=OCV.COLOR_ACTIVE,
            command=lambda: self.move_to_mem("MB"))

        but.grid(row=row, column=col, columnspan=3)


        tkExtra.Balloon.set(but, _("Memory to B"))

        self.addWidget(but)

        row += 1

        but = Tk.Button(
            self.frame,
            font=OCV.FONT,
            text=_("C_M"),
            command=self.clr_mem,
            background=OCV.COLOR_BG,
            activebackground=OCV.COLOR_ACTIVE)

        but.grid(row=row, column=col, columnspan=3)

        tkExtra.Balloon.set(but, _("Cancel mem X"))

        self.addWidget(but)

        row, col = 0, 4

        lab = Tk.Label(
            self.frame,
            name="lab_bank",
            text="B {0}".format(OCV.WK_bank),
            background=OCV.COLOR_BG3)

        lab.grid(row=row, column=col, columnspan=2, sticky="nsew")

        tkExtra.Balloon.set(
            lab, _("Bank Number \n Mem {0}".format(OCV.WK_mem_num)))

        self.addWidget(lab)

        row += 1

        but = Tk.Button(
            self.frame,
            font=OCV.FONT,
            text=_("B +"),
            background=OCV.COLOR_BG,
            activebackground=OCV.COLOR_ACTIVE)

        but.grid(row=row, column=col, columnspan=2)

        but.bind(
            "<1>", lambda event, obj="B+": self.on_click_bank(event, obj))

        tkExtra.Balloon.set(but, _("Upper Memory Bank"))

        self.addWidget(but)

        row += 1

        but = Tk.Button(
            self.frame,
            font=OCV.FONT,
            text=_("B -"),
            compound=Tk.TOP,
            background=OCV.COLOR_BG,
            activebackground=OCV.COLOR_ACTIVE)

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
                    font=OCV.FONT,
                    name=but_name,
                    text="M_{0:02d}".format(sub_i + 2),
                    compound=Tk.TOP,
                    background=OCV.COLOR_BG,
                    activebackground=OCV.COLOR_ACTIVE)

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
                mem_name = Utils.ask_for_value(OCV.TK_MAIN, "ME")
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

    def move_to_mem(self, obj):
        """manage the click on "M2A" and "M2B" buttons
        """
        mem_num = Utils.ask_for_value(OCV.TK_MAIN, "MN")
        mem_key = "mem_{0}".format(mem_num)

        mpos_x = OCV.WK_mems[mem_key][0]
        mpos_y = OCV.WK_mems[mem_key][1]
        mpos_z = OCV.WK_mems[mem_key][2]

        wcs_ox = OCV.CD["wcox"]
        wcs_oy = OCV.CD["wcoy"]
        wcs_oz = OCV.CD["wcoz"]
                
        trpos_x = mpos_x - wcs_ox
        trpos_y = mpos_y - wcs_oy
        trpos_z = mpos_z - wcs_oz

        print("Mem number = ", mem_num)
        print("mem pos = {} {} {}".format(mpos_x, mpos_y, mpos_z))
        print("Zero Offset = {} {} {}".format(wcs_ox, wcs_oy, wcs_oz))
        print("Dest pos = {} {} {}".format(trpos_x, trpos_y, trpos_z))
            
        if obj == "MA":
            write_memAB("memA", trpos_x, trpos_y, trpos_z)
        elif obj == "MB":
            write_memAB("memB", trpos_x, trpos_y, trpos_z)
        else:
           return

    def select_bank(self, mem_bank):
        """actions to select a memory bank"""
        # assign the proper values
        OCV.WK_bank = mem_bank
        OCV.WK_bank_start = (OCV.WK_bank * OCV.WK_bank_mem) + 2
        wdg = self.frame.nametowidget("lab_bank")
        wdg.config(text="B {0}".format(OCV.WK_bank))
        but_color = OCV.COLOR_BG

        for idx in range(0, OCV.WK_bank_mem):
            but_name = "but_m_{0}".format(str(idx))
            label = "M_{0:02d}".format(OCV.WK_bank_start + idx)
            mem_addr = "mem_{0}".format(OCV.WK_bank_start + idx)
            mem_tt = "{0}\n\n name: {5}\n\nX: {1}\n\nY: {2}\n\nZ: {3}"
            wdg = self.frame.nametowidget(but_name)

            if mem_addr in OCV.WK_mems:
                if OCV.WK_mems[mem_addr][3] == 1:
                    but_color = OCV.COLOR_MEM_SET
                    mem_data = OCV.WK_mems[mem_addr]
                    # print("Select Bank ", md)
                    tkExtra.Balloon.set(
                        wdg, mem_tt.format(mem_addr, *mem_data))
            else:
                but_color = OCV.COLOR_BG
                tkExtra.Balloon.set(wdg, "Empty")

            wdg.config(text=label, background=but_color)

    def clr_mem(self):
        """clear memory - asking for memory number"""
        mem_num = Utils.ask_for_value(OCV.TK_MAIN, "MN")

        # print("clr_mem >", mem_num)

        if mem_num is None:
            return
    
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
            label = "M_{0:02d}".format(mem_num)

            # print("clr_mem but_name > ", but_name)

            wdg = self.frame.nametowidget(but_name)
            but_color = OCV.COLOR_BG
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
        OCV.TK_MAIN.ToggleMems()

    @staticmethod
    def reset_all_displayed_mem():
        """hide all "active" memory on canvas"""
        indices = [i for i, x in enumerate(OCV.WK_active_mems) if x == 2]

        for mem in indices:
            print("reset_all_displayed_mem index = ", mem)
            OCV.WK_mem = mem
            OCV.TK_MAIN.event_generate("<<ClrMem>>")
