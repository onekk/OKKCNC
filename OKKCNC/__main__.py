#!/usr/bin/python
# -*- coding: ascii -*-
# $Id: OKKCNC.py $
#
# Author: carlo.dormeletti@gmail.com
# Date: 26 Oct 2019
"""
    _main__.py

    This module is the main module

"""

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import time
import getopt
import socket
import traceback
from datetime import datetime


PRGPATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PRGPATH)
sys.path.append(os.path.join(PRGPATH, 'lib'))
sys.path.append(os.path.join(PRGPATH, 'plugins'))
sys.path.append(os.path.join(PRGPATH, 'controllers'))

# Import Here the OCV module as it contains variables used across the program
import OCV

# Check if pyserial is installed
try:
    import serial
    OCV.HAS_SERIAL = True
except ImportError:
    OCV.HAS_SERIAL = None

# Import Tkinter
try:
    import Tkinter as Tk
    from Queue import *
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox
    from queue import *

import webbrowser


# Load configuration before anything else
# and if needed replace the  translate function _()
# before any string is initialized
import Utils
Utils.loadConfiguration()

import rexx
import tkExtra
import bFileDialog
import tkDialogs

import Commands as cmd

from CNC import WAIT, CNC, GCode
import Ribbon
import Pendant
from Sender import Sender, NOT_CONNECTED, STATECOLOR, STATECOLORDEF

import CNCCanvas


from CNCRibbon    import Page
from ToolsPage    import Tools, ToolsPage
from FilePage     import FilePage
from ControlPage  import ControlPage
from TerminalPage import TerminalPage
from ProbePage    import ProbePage
from EditorPage   import EditorPage

import MemoryPanel

_openserial = True # override ini parameters
_device = None
_baud = None

MONITOR_AFTER = 200 # ms
DRAW_AFTER = 300 # ms

RX_BUFFER_SIZE = 128

MAX_HISTORY = 500

#ZERO = ["G28", "G30", "G92"]

FILETYPES = [
    (_("All accepted"),
     ("*.ngc", "*.cnc", "*.nc", "*.tap", "*.gcode", "*.probe",
      "*.orient")),
    (_("G-Code"), ("*.ngc", "*.cnc", "*.nc", "*.tap", "*.gcode")),
    (_("G-Code clean"), ("*.txt")),
    (_("Probe"), ("*.probe", "*.xyz")),
    (_("Orient"), "*.orient"),
    (_("All"), "*")]

class Application(Tk.Toplevel, Sender):
    """Main Application window"""
    def __init__(self, master, **kw):
        Tk.Toplevel.__init__(self, master, **kw)

        OCV.application = self

        print("Application > ", self)

        #Tk.Toplevel.__init__(OCV.application, master, **kw)

        Sender.__init__(OCV.application)

        if sys.platform == "win32":
            self.iconbitmap("{0}\\OKKCNC.ico".format(Utils.prgpath))
        else:
            self.iconbitmap("@{0}/OKKCNC.xbm".format(Utils.prgpath))
        self.title("{0} {1}".format(Utils.__prg__, OCV._version))
        self.widgets = []

        # Global variables
        self.tools = Tools(self.gcode)
        self.controller = None
        self.loadConfig()

        # --- Ribbon ---
        self.ribbon = Ribbon.TabRibbonFrame(self)
        self.ribbon.pack(side=Tk.TOP, fill=Tk.X)

        # Main frame
        self.paned = Tk.PanedWindow(self, orient=Tk.HORIZONTAL)
        self.paned.pack(fill=Tk.BOTH, expand=Tk.YES)

        # Status bar
        frame = Tk.Frame(self)
        frame.pack(side=Tk.BOTTOM, fill=Tk.X)
        self.statusbar = tkExtra.ProgressBar(
            frame,
            height=20,
            relief=Tk.SUNKEN)

        self.statusbar.pack(
            side=Tk.LEFT,
            fill=Tk.X,
            expand=Tk.YES)

        self.statusbar.configText(
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
        self.bufferbar = tkExtra.ProgressBar(
            frame,
            height=20,
            width=40,
            relief=Tk.SUNKEN)

        self.bufferbar.pack(side=Tk.RIGHT, expand=Tk.NO)

        self.bufferbar.setLimits(0, 100)

        tkExtra.Balloon.set(self.bufferbar, _("Controller buffer fill"))

        # --- Left side ---
        frame = Tk.Frame(self.paned)

        self.paned.add(frame) #, minsize=340)

        pageframe = Tk.Frame(frame)

        pageframe.pack(side=Tk.TOP, expand=Tk.YES, fill=Tk.BOTH)

        self.ribbon.setPageFrame(pageframe)

        # Command bar
        cmd_f = Tk.Frame(frame)
        cmd_f.pack(side=Tk.BOTTOM, fill=Tk.X)
        self.cmdlabel = Tk.Label(cmd_f, text=_("Command:"))
        self.cmdlabel.pack(side=Tk.LEFT)

        self.command = Tk.Entry(cmd_f, relief=Tk.SUNKEN, background="White")

        self.command.pack(side=Tk.RIGHT, fill=Tk.X, expand=Tk.YES)

        self.command.bind("<Return>", self.cmdExecute)
        self.command.bind("<Up>", self.commandHistoryUp)
        self.command.bind("<Down>", self.commandHistoryDown)
        self.command.bind("<FocusIn>", self.commandFocusIn)
        self.command.bind("<FocusOut>", self.commandFocusOut)
        self.command.bind("<Key>", self.commandKey)
        self.command.bind("<Control-Key-z>", self.undo)
        self.command.bind("<Control-Key-Z>", self.redo)
        self.command.bind("<Control-Key-y>", self.redo)

        tkExtra.Balloon.set(
            self.command,
            _("MDI Command line: Accept g-code commands or macro " \
              "commands (RESET/HOME...) or editor commands " \
              "(move,inkscape, round...) [Space or Ctrl-Space]"))

        self.widgets.append(self.command)

        # --- Right side ---
        frame = Tk.Frame(self.paned)
        self.paned.add(frame)

        # --- Canvas ---
        self.canvasFrame = CNCCanvas.CanvasFrame(frame, self)

        self.canvasFrame.pack(side=Tk.TOP, fill=Tk.BOTH, expand=Tk.YES)

        self.linebuffer = Tk.Label(frame, background="khaki")

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

            page = cls(self.ribbon, self)

            self.pages[page.name] = page

        # then add their properties (in separate loop)
        errors = []
        for name, page in self.pages.items():
            for n in Utils.getStr(Utils.__prg__, "{0}.ribbon".format(page.name)).split():
                try:
                    page.addRibbonGroup(n)
                except KeyError:
                    errors.append(n)

            for n in Utils.getStr(Utils.__prg__, "{0}.page".format(page.name)).split():
                last = n[-1]
                try:
                    if last == "*":
                        page.addPageFrame(n[:-1], fill=Tk.BOTH, expand=Tk.TRUE)
                    else:
                        page.addPageFrame(n)
                except KeyError:
                    errors.append(n)

        if errors:
            tkMessageBox.showwarning(
                "OKKCNC configuration",
                "The following pages \"{0}\" are found in " \
                "your ${HOME}/.OKKCNC initialization file, " \
                "which are either spelled wrongly or " \
                "no longer exist in OKKCNC".format(" ".join(errors)), parent=self)

        # remember the editor list widget
        self.dro = Page.frames["DRO"]
        self.gstate = Page.frames["State"]
        self.control = Page.frames["Control"]
        self.editor = Page.frames["Editor"].editor
        self.terminal = Page.frames["Terminal"].terminal
        self.buffer = Page.frames["Terminal"].buffer

        # Left side
        for name in Utils.getStr(Utils.__prg__, "ribbon").split():
            last = name[-1]
            if last == '>':
                name = name[:-1]
                side = Tk.RIGHT
            else:
                side = Tk.LEFT
            self.ribbon.addPage(self.pages[name], side)

        # Restore last page
        self.pages["Probe"].tabChange()    # Select "Probe:Probe" tab to show the dialogs!
        self.ribbon.changePage(Utils.getStr(Utils.__prg__, "page", "File"))

        probe = Page.frames["Probe:Probe"]

        tkExtra.bindEventData(self, "<<OrientSelect>>",
                              lambda e, f=probe: f.selectMarker(int(e.data)))

        tkExtra.bindEventData(self, '<<OrientChange>>',
                              lambda e, s=self: s.canvas.orientChange(int(e.data)))

        self.bind('<<OrientUpdate>>', probe.orientUpdate)

        # Global bindings
        self.bind('<<Undo>>', self.undo)
        self.bind('<<Redo>>', self.redo)
        self.bind('<<Copy>>', self.copy)
        self.bind('<<Cut>>', self.cut)
        self.bind('<<Paste>>', self.paste)

        self.bind('<<Connect>>', self.openClose)

        self.bind('<<New>>', self.newFile)
        self.bind('<<Open>>', self.loadDialog)
        self.bind('<<Import>>', lambda x, s=self: s.importFile())
        self.bind('<<Save>>', self.saveAll)
        self.bind('<<SaveAs>>', self.saveDialog)
        self.bind('<<Reload>>', self.reload)

        self.bind('<<Recent0>>', self._loadRecent0)
        self.bind('<<Recent1>>', self._loadRecent1)
        self.bind('<<Recent2>>', self._loadRecent2)
        self.bind('<<Recent3>>', self._loadRecent3)
        self.bind('<<Recent4>>', self._loadRecent4)
        self.bind('<<Recent5>>', self._loadRecent5)
        self.bind('<<Recent6>>', self._loadRecent6)
        self.bind('<<Recent7>>', self._loadRecent7)
        self.bind('<<Recent8>>', self._loadRecent8)
        self.bind('<<Recent9>>', self._loadRecent9)
        self.bind('<<AlarmClear>>', self.alarmClear)
        self.bind('<<Help>>', self.help)
        # Do not send the event otherwise it will skip the feedHold/resume
        self.bind('<<FeedHold>>', lambda e, s=self: s.feedHold())
        self.bind('<<Resume>>', lambda e, s=self: s.resume())
        self.bind('<<Run>>', lambda e, s=self: s.run())
        self.bind('<<Stop>>', self.stopRun)
        self.bind('<<Pause>>', self.pause)
#        self.bind('<<TabAdded>>',    self.tabAdded)
        self.bind('<<SetMem>>', self.setMem)
        self.bind('<<ClrMem>>', self.clrMem)
        self.bind('<<SaveMems>>', self.saveMems)
        self.bind("<<ListboxSelect>>", self.selectionChange)
        self.bind("<<Modified>>", self.drawAfter)

        self.bind('<Control-Key-a>', self.selectAll)
        self.bind('<Control-Key-A>', self.unselectAll)
        self.bind('<Escape>', self.unselectAll)
        self.bind('<Control-Key-i>', self.selectInvert)

        self.bind('<<SelectAll>>', self.selectAll)
        self.bind('<<SelectNone>>', self.unselectAll)
        self.bind('<<SelectInvert>>', self.selectInvert)
        self.bind('<<SelectLayer>>', self.selectLayer)

        self.bind('<<ZmoveUp>>', self.control.moveZup)
        self.bind('<<ZmoveDown>>', self.control.moveZdown)



        self.bind('<<TerminalClear>>', Page.frames["Terminal"].clear)

        tkExtra.bindEventData(self, "<<Status>>", self.updateStatus)
        tkExtra.bindEventData(self, "<<Coords>>", self.updateCanvasCoords)

        # Editor bindings
        self.bind("<<Add>>", self.editor.insertItem)
        self.bind("<<AddBlock>>", self.editor.insertBlock)
        self.bind("<<AddLine>>", self.editor.insertLine)
        self.bind("<<Clone>>", self.editor.clone)
        self.bind("<<ClearEditor>>", self.ClearEditor)
        self.bind("<<Delete>>", self.editor.deleteBlock)

        # CanvasFrame see if is == OCV.canvas
        self.canvasFrame.canvas.bind("<Control-Key-Prior>", self.editor.orderUp)
        self.canvasFrame.canvas.bind("<Control-Key-Next>", self.editor.orderDown)
        self.canvasFrame.canvas.bind('<Control-Key-d>', self.editor.clone)
        self.canvasFrame.canvas.bind('<Control-Key-c>', self.copy)
        self.canvasFrame.canvas.bind('<Control-Key-x>', self.cut)
        self.canvasFrame.canvas.bind('<Control-Key-v>', self.paste)
        self.canvasFrame.canvas.bind("<Delete>", self.editor.deleteBlock)
        self.canvasFrame.canvas.bind("<BackSpace>", self.editor.deleteBlock)

        try:
            self.canvasFrame.canvas.bind("<KP_Delete>", self.editor.deleteBlock)
        except:
            pass

        self.bind('<<Invert>>', self.editor.invertBlocks)
        self.bind('<<Expand>>', self.editor.toggleExpand)
        self.bind('<<EnableToggle>>', self.editor.toggleEnable)
        self.bind('<<Enable>>', self.editor.enable)
        self.bind('<<Disable>>', self.editor.disable)
        self.bind('<<ChangeColor>>', self.editor.changeColor)
        self.bind('<<Comment>>', self.editor.commentRow)
        self.bind('<<Join>>', self.editor.joinBlocks)
        self.bind('<<Split>>', self.editor.splitBlocks)

        # Canvas X-bindings
        self.bind("<<ViewChange>>", self.viewChange)
        self.bind("<<AddMarker>>", self.canvasFrame.canvas.setActionAddMarker)
        self.bind('<<MoveGantry>>', self.canvasFrame.canvas.setActionGantry)
        self.bind('<<SetWPOS>>', self.canvasFrame.canvas.setActionWPOS)

        frame = Page.frames["Probe:Tool"]

        self.bind('<<ToolCalibrate>>', frame.calibrate)
        self.bind('<<ToolChange>>', frame.change)

        self.bind('<<AutolevelMargins>>', Page.frames["Probe:Autolevel"].getMargins)
        self.bind('<<AutolevelZero>>', Page.frames["Probe:Autolevel"].setZero)
        self.bind('<<AutolevelClear>>', Page.frames["Probe:Autolevel"].clear)
        self.bind('<<AutolevelScan>>', Page.frames["Probe:Autolevel"].scan)
        self.bind('<<AutolevelScanMargins>>', Page.frames["Probe:Autolevel"].scanMargins)

        self.bind('<<CameraOn>>', self.canvasFrame.canvas.cameraOn)
        self.bind('<<CameraOff>>', self.canvasFrame.canvas.cameraOff)

        self.bind('<<CanvasFocus>>', self.canvasFocus)
        self.bind('<<Draw>>', self.draw)
        self.bind('<<DrawProbe>>', lambda e, c=self.canvasFrame: c.drawProbe(True))
        self.bind('<<DrawOrient>>', self.canvasFrame.canvas.drawOrient)


        #self.bind('<Control-Key-f>',    self.find)
        #self.bind('<Control-Key-g>',    self.findNext)
        #self.bind('<Control-Key-h>',    self.replace)
        self.bind('<Control-Key-e>', self.editor.toggleExpand)
        self.bind('<Control-Key-n>', self.showInfo)
        self.bind('<<ShowInfo>>', self.showInfo)
        self.bind('<Control-Key-l>', self.editor.toggleEnable)
        self.bind('<Control-Key-q>', self.quit)
        self.bind('<Control-Key-o>', self.loadDialog)
        self.bind('<Control-Key-r>', self.drawAfter)
        self.bind("<Control-Key-s>", self.saveAll)
        self.bind('<Control-Key-y>', self.redo)
        self.bind('<Control-Key-z>', self.undo)
        self.bind('<Control-Key-Z>', self.redo)
        self.canvasFrame.canvas.bind('<Key-space>', self.commandFocus)
        self.bind('<Control-Key-space>', self.commandFocus)
        self.bind('<<CommandFocus>>', self.commandFocus)

        tools = self.pages["CAM"]
        self.bind('<<ToolAdd>>', tools.add)
        self.bind('<<ToolDelete>>', tools.delete)
        self.bind('<<ToolClone>>', tools.clone)
        self.bind('<<ToolRename>>', tools.rename)

        self.bind('<Prior>', self.control.moveZup)
        self.bind('<Next>', self.control.moveZdown)

        if self._swapKeyboard == 1:
            self.bind('<Right>', self.control.moveYup)
            self.bind('<Left>', self.control.moveYdown)
            self.bind('<Up>', self.control.moveXdown)
            self.bind('<Down>', self.control.moveXup)
        elif self._swapKeyboard == -1:
            self.bind('<Right>', self.control.moveYdown)
            self.bind('<Left>', self.control.moveYup)
            self.bind('<Up>', self.control.moveXup)
            self.bind('<Down>', self.control.moveXdown)
        else:
            self.bind('<Right>', self.control.moveXup)
            self.bind('<Left>', self.control.moveXdown)
            self.bind('<Up>', self.control.moveYup)
            self.bind('<Down>', self.control.moveYdown)

        try:
            self.bind('<KP_Prior>', self.control.moveZup)
            self.bind('<KP_Next>', self.control.moveZdown)

            if self._swapKeyboard == 1:
                self.bind('<KP_Right>', self.control.moveYup)
                self.bind('<KP_Left>', self.control.moveYdown)
                self.bind('<KP_Up>', self.control.moveXdown)
                self.bind('<KP_Down>', self.control.moveXup)
            elif self._swapKeyboard == -1:
                self.bind('<KP_Right>', self.control.moveYdown)
                self.bind('<KP_Left>', self.control.moveYup)
                self.bind('<KP_Up>', self.control.moveXup)
                self.bind('<KP_Down>', self.control.moveXdown)
            else:
                self.bind('<KP_Right>', self.control.moveXup)
                self.bind('<KP_Left>', self.control.moveXdown)
                self.bind('<KP_Up>', self.control.moveYup)
                self.bind('<KP_Down>', self.control.moveYdown)
        except Tk.TclError:
            pass

        self.bind('<Key-plus>', self.control.incStep)
        self.bind('<Key-equal>', self.control.incStep)
        self.bind('<KP_Add>', self.control.incStep)
        self.bind('<Key-minus>', self.control.decStep)
        self.bind('<Key-underscore>', self.control.decStep)
        self.bind('<KP_Subtract>', self.control.decStep)

        self.bind('<Key-asterisk>', self.control.mulStep)
        self.bind('<KP_Multiply>', self.control.mulStep)
        self.bind('<Key-slash>', self.control.divStep)
        self.bind('<KP_Divide>', self.control.divStep)

        self.bind('<Key-1>', self.control.setStep1)
        self.bind('<Key-2>', self.control.setStep2)
        self.bind('<Key-3>', self.control.setStep3)

        self.bind('<Key-exclam>', self.feedHold)
        self.bind('<Key-asciitilde>', self.resume)

        for x in self.widgets:
            if isinstance(x, Tk.Entry):
                x.bind("<Escape>", self.canvasFocus)

        self.bind('<FocusIn>', self.focus_in)
        self.protocol("WM_DELETE_WINDOW", self.quit)

        self.canvasFrame.canvas.focus_set()

        OCV.CD["state"] = NOT_CONNECTED
        OCV.CD["color"] = STATECOLOR[NOT_CONNECTED]
        self._pendantFileUploaded = None
        self._drawAfter = None # after handle for modification
        self._inFocus = False
        self._insertCount = 0 # END - insertCount lines where ok was applied to for $xxx commands
        self._selectI = 0
        self.monitorSerial()
        self.canvasFrame.toggleDrawFlag()

        self.paned.sash_place(0, Utils.getInt(Utils.__prg__, "sash", 340), 0)

        # Auto start pendant and serial
        if Utils.getBool("Connection", "pendant"):
            self.startPendant(False)

        if _openserial and Utils.getBool("Connection", "openserial"):
            self.openClose()

        # Filedialog Load history
        for i in range(Utils._maxRecent):
            filename = Utils.getRecent(i)

            if filename is None:
                break

            bFileDialog.append2History(os.path.dirname(filename))


    def setStatus(self, msg, force_update=False):
        self.statusbar.configText(text=msg, fill="DarkBlue")
        if force_update:
            self.statusbar.update_idletasks()
            self.bufferbar.update_idletasks()


    def updateStatus(self, event):
        """Set a status message from an event"""
        self.setStatus(_(event.data))

    def setMem(self, event=None):
        self.canvasFrame.canvas.memDraw(OCV.WK_mem)
        OCV.WK_active_mems[OCV.WK_mem] = 2

    def clrMem(self, event=None):
        # delete the marker
        self.canvasFrame.canvas.memDelete(OCV.WK_mem)
        OCV.WK_active_mems[OCV.WK_mem] = 1

    def saveMems(self, event=None):
        MemoryPanel.Config.saveMemory()


    def entry(self, message="Enter value", title="", prompt="", type_="str",
              from_=None, to_=None):
        """Show popup dialog asking for value entry, usefull in g-code scripts"""
        d = tkDialogs.InputDialog(self, title, message, prompt, type_, from_, to_)
        v = d.show()

        if isinstance(v, basestring):
            v = v.strip()
        print("entered "+str(type(v))+": "+str(v))
        return v


    def updateCanvasCoords(self, event):
        """Update canvas coordinates"""
        x, y, z = event.data.split()
        self.statusx["text"] = "X: "+x
        self.statusy["text"] = "Y: "+y
        self.statusz["text"] = "Z: "+z


    def acceptKey(self, skipRun=False):
        """Accept the user key if not editing any text"""
        if not skipRun and self.running:
            return False
        focus = self.focus_get()
        if isinstance(focus, Tk.Entry) or isinstance(focus, Tk.Spinbox) or \
           isinstance(focus, Tk.Listbox) or isinstance(focus, Tk.Text):
            return False

        return True


    def quit(self, event=None):
        if self.running and self._quit < 1:
            tkMessageBox.showinfo(
                _("Running"),
                _("CNC is currently running, please stop it before."),
                parent=self)
            self._quit += 1
            return
        del self.widgets[:]

        if self.fileModified():
            return

        self.canvasFrame.canvas.cameraOff()
        Sender.quit(self)
        self.saveConfig()
        self.destroy()

        if Utils.errors and Utils._errorReport:
            # Don't send report dialog
            #    Utils.ReportDialog.sendErrorReport()
            pass

        OCV.root.destroy()

    # ---------------------------------------------------------------------
    def configWidgets(self, var, value):
        for w in self.widgets:
            if isinstance(w, tuple):
                try:
                    w[0].entryconfig(w[1], state=value)
                except Tk.TclError:
                    pass
            elif isinstance(w, tkExtra.Combobox):
                w.configure(state=value)
            else:
                w[var] = value

    # ---------------------------------------------------------------------
    def busy(self):
        try:
            self.config(cursor="watch")
            self.update_idletasks()
        except Tk.TclError:
            pass

    # ----------------------------------------------------------------------
    def notBusy(self):
        try:
            self.config(cursor="")
        except Tk.TclError:
            pass

    # ---------------------------------------------------------------------
    def enable(self):
        self.configWidgets("state", Tk.NORMAL)
        self.statusbar.clear()
        self.statusbar.config(background="LightGray")
        self.bufferbar.clear()
        self.bufferbar.config(background="LightGray")
        self.bufferbar.setText("")

    # ---------------------------------------------------------------------
    def disable(self):
        self.configWidgets("state", Tk.DISABLED)

    # ----------------------------------------------------------------------
    # Check for updates
    # ----------------------------------------------------------------------
    def checkUpdates(self):
        # Find OKKCNC version
        #Updates.CheckUpdateDialog(self, OCV._version)
        pass


    def loadShortcuts(self):
        for name, value in Utils.config.items("Shortcut"):
            # Convert to uppercase
            key = name.title()
            self.unbind("<{0}>".format(key))    # unbind any possible old value
            if value:
                self.bind("<{0}>".format(key), lambda e, s=self, c=value: s.execute(c))

    @staticmethod
    def showUserFile(self):
        webbrowser.open(Utils.iniUser)
        #os.startfile(Utils.iniUser)


    def loadConfig(self):

        if OCV.geometry is None:
            OCV.geometry = "{0:d}x{1:d}".format(
                Utils.getInt(Utils.__prg__, "width", 900),
                Utils.getInt(Utils.__prg__, "height", 650))
        try:
            self.geometry(OCV.geometry)
        except:
            pass

        #restore windowsState
        try:
            self.wm_state(Utils.getStr(Utils.__prg__, "windowstate", "normal"))
        except:
            pass

        # read Tk fonts to initialize them
        font = Utils.getFont("TkDefaultFont")
        font = Utils.getFont("TkFixedFont")
        font = Utils.getFont("TkMenuFont")
        font = Utils.getFont("TkTextFont")

        print("Font: >", font)

        self._swapKeyboard = Utils.getInt("Control", "swap", 0)

        self._onStart = Utils.getStr("Events", "onstart", "")
        self._onStop = Utils.getStr("Events", "onstop", "")

        tkExtra.Balloon.font = Utils.getFont("balloon", tkExtra.Balloon.font)

        OCV.RIBBON_FONT = Utils.getFont("ribbon.label", OCV.RIBBON_FONT)
        OCV.RIBBON_TABFONT = Utils.getFont("ribbon.tab", OCV.RIBBON_TABFONT)

        OCV.ACTIVE_COLOR = Utils.getStr("Color", "ribbon.active", OCV.ACTIVE_COLOR)
        OCV.LABEL_SELECT_COLOR = Utils.getStr("Color", "ribbon.select", OCV.LABEL_SELECT_COLOR)
        OCV.INSERT_COLOR = Utils.getStr("Color", "canvas.insert", OCV.INSERT_COLOR)
        OCV.GANTRY_COLOR = Utils.getStr("Color", "canvas.gantry", OCV.GANTRY_COLOR)
        OCV.MARGIN_COLOR = Utils.getStr("Color", "canvas.margin", OCV.MARGIN_COLOR)
        OCV.GRID_COLOR = Utils.getStr("Color", "canvas.grid", OCV.GRID_COLOR)
        OCV.BOX_SELECT = Utils.getStr("Color", "canvas.selectbox", OCV.BOX_SELECT)
        OCV.ENABLE_COLOR = Utils.getStr("Color", "canvas.enable", OCV.ENABLE_COLOR)
        OCV.DISABLE_COLOR = Utils.getStr("Color", "canvas.disable", OCV.DISABLE_COLOR)
        OCV.SELECT_COLOR = Utils.getStr("Color", "canvas.select", OCV.SELECT_COLOR)
        OCV.SELECT2_COLOR = Utils.getStr("Color", "canvas.select2", OCV.SELECT2_COLOR)
        OCV.PROCESS_COLOR = Utils.getStr("Color", "canvas.process", OCV.PROCESS_COLOR)
        OCV.MOVE_COLOR = Utils.getStr("Color", "canvas.move", OCV.MOVE_COLOR)
        OCV.RULER_COLOR = Utils.getStr("Color", "canvas.ruler", OCV.RULER_COLOR)
        OCV.CAMERA_COLOR = Utils.getStr("Color", "canvas.camera", OCV.CAMERA_COLOR)
        OCV.PROBE_TEXT_COLOR = Utils.getStr("Color", "canvas.probetext", OCV.PROBE_TEXT_COLOR)
        OCV.CANVAS_COLOR = Utils.getStr("Color", "canvas.background", OCV.CANVAS_COLOR)

        self.tools.loadConfig()
        Sender.loadConfig(self)
        self.loadShortcuts()
        MemoryPanel.Config.loadMemory()


    def saveConfig(self):
        # Program
        Utils.setInt(Utils.__prg__, "width", str(self.winfo_width()))
        Utils.setInt(Utils.__prg__, "height", str(self.winfo_height()))
        #Utils.setInt(Utils.__prg__,  "x", str(self.winfo_rootx()))
        #Utils.setInt(Utils.__prg__,  "y", str(self.winfo_rooty()))
        Utils.setInt(Utils.__prg__, "sash", str(self.paned.sash_coord(0)[0]))

        #save windowState
        Utils.setStr(Utils.__prg__, "windowstate", str(self.wm_state()))
        Utils.setStr(Utils.__prg__, "page", str(self.ribbon.getActivePage().name))

        # Connection
        Page.saveConfig()
        Sender.saveConfig(self)
        self.tools.saveConfig()
        self.canvasFrame.saveConfig()
        MemoryPanel.Config.saveMemory()


    def loadHistory(self):
        try:
            f = open(Utils.hisFile, "r")
        except:
            return
        self.history = [x.strip() for x in f]
        self._historySearch = None
        f.close()


    def saveHistory(self):
        try:
            f = open(Utils.hisFile, "w")
        except:
            return
        f.write("\n".join(self.history))
        f.close()


    def cut(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.editor.cut()
            return "break"


    def copy(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.editor.copy()
            return "break"


    def paste(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.editor.paste()
            return "break"


    def undo(self, event=None):
        if not self.running and self.gcode.canUndo():
            self.gcode.undo()
            self.editor.fill()
            self.drawAfter()
        return "break"


    def redo(self, event=None):
        if not self.running and self.gcode.canRedo():
            self.gcode.redo()
            self.editor.fill()
            self.drawAfter()
        return "break"


    def ClearEditor(self, event=None):
        self.editor.selectClear()
        self.editor.selectAll()
        self.editor.deleteBlock()


    def addUndo(self, undoinfo):
        self.gcode.addUndo(undoinfo)


    def about(self, event=None, timer=None):
        toplevel = Tk.Toplevel(self)
        toplevel.transient(self)
        toplevel.title(_("About {0} v{1}").format(Utils.__prg__, OCV._version))
        if sys.platform == "win32":
            self.iconbitmap("OKKCNC.ico")
        else:
            self.iconbitmap("@{0}/OKKCNC.xbm".format(Utils.prgpath))

        bg = "#707070"
        fg = "#ffffff"

        font1 = 'Helvetica -32 bold'
        font2 = 'Helvetica -12'
        font3 = 'Helvetica -10'

        frame = Tk.Frame(
            toplevel,
            borderwidth=2,
            relief=Tk.SUNKEN,
            background=bg)

        frame.pack(side=Tk.TOP, expand=Tk.TRUE, fill=Tk.BOTH, padx=5, pady=5)

        # -----
        row = 0
        lab = Tk.Label(
            frame,
            image=Utils.icons["OKKCNC"],
            foreground=fg,
            background=bg,
            relief=Tk.RAISED,
            padx=0, pady=0)

        lab.grid(row=row, column=0, columnspan=2, padx=5, pady=5)

        row += 1

        lab = Tk.Label(
            frame,
            text=_("OKKCNC/\tAn advanced fully featured\n" \
                  "\t\tg-code sender for GRBL. \n\n"\
                  "\t\tForked from bCNC"),
            font=font3,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=0, columnspan=2, sticky=Tk.W, padx=10, pady=1)

        # -----
        row += 1
        frm = Tk.Frame(
            frame,
            borderwidth=1,
            relief=Tk.SUNKEN,
            height=2,
            background=bg)

        frm.grid(row=row, column=0, columnspan=2, sticky=Tk.EW, padx=5, pady=5)

        row += 1

        lab = Tk.Label(
            frame,
            text='www:',
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=0, sticky=Tk.E, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=Utils.__www__,
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            activeforeground="Blue",
            cursor="hand1")

        lab.grid(row=row, column=1, sticky=Tk.W, padx=2, pady=2)

        lab.bind('<Button-1>', lambda e: webbrowser.open(Utils.__www__))

        row += 1

        lab = Tk.Label(
            frame,
            text='email:',
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=0, sticky=Tk.E, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=__email__,
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=1, sticky=Tk.W, padx=2, pady=2)

        row += 1

        lab = Tk.Label(
            frame,
            text='author:',
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=0, sticky=Tk.NE, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=OCV.author,
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=1, sticky=Tk.NW, padx=2, pady=2)

        row += 1

        lab = Tk.Label(
            frame,
            text='contributors:',
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=0, sticky=Tk.NE, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=Utils.__contribute__,
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=1, sticky=Tk.NW, padx=2, pady=2)

        row += 1

        lab = Tk.Label(
            frame,
            text='translations:',
            font=font2,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT)

        lab.grid(row=row, column=0, sticky=Tk.NE, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=Utils.__translations__,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=1, sticky=Tk.NW, padx=2, pady=2)

        row += 1

        lab = Tk.Label(
            frame,
            text='credits:',
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=0, sticky=Tk.NE, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=Utils.__credits__,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=1, sticky=Tk.NW, padx=2, pady=2)

        row += 1

        lab = Tk.Label(
            frame,
            text='version:',
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=0, sticky=Tk.E, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=OCV._version,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=1, sticky=Tk.NW, padx=2, pady=2)

        row += 1

        lab = Tk.Label(
            frame,
            text='last change:',
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=0, sticky=Tk.E, padx=10, pady=2)

        lab = Tk.Label(
            frame,
            text=OCV._date,
            foreground=fg,
            background=bg,
            justify=Tk.LEFT,
            font=font2)

        lab.grid(row=row, column=1, sticky=Tk.NW, padx=2, pady=2)

        closeFunc = lambda e=None, t=toplevel: t.destroy()

        but = Tk.Button(toplevel, text=_("Close"), command=closeFunc)
        but.pack(pady=5)

        frame.grid_columnconfigure(1, weight=1)

        toplevel.bind('<Escape>', closeFunc)
        toplevel.bind('<Return>', closeFunc)
        toplevel.bind('<KP_Enter>', closeFunc)

        toplevel.deiconify()
        toplevel.wait_visibility()
        toplevel.resizable(False, False)

        try:
            toplevel.grab_set()
        except:
            pass

        but.focus_set()
        toplevel.lift()

        if timer:
            toplevel.after(timer, closeFunc)

        toplevel.wait_window()


    def alarmClear(self, event=None):
        self._alarm = False


    def showInfo(self, event=None):
        """Display information on selected blocks"""
        self.canvasFrame.canvas.showInfo(self.editor.getSelectedBlocks())
        return "break"


    def showStats(self, event=None):
        toplevel = Tk.Toplevel(self)
        toplevel.transient(self)
        toplevel.title(_("Statistics"))

        if OCV.inch:
            unit = "in"
        else:
            unit = "mm"

        # count enabled blocks
        e = 0
        l = 0
        r = 0
        t = 0
        for block in self.gcode.blocks:
            if block.enable:
                e += 1
                l += block.length
                r += block.rapid
                t += block.time

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
            text="{0:.f} .. {1:.f} [{2:.f}] {3}".format(
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
            text="{0:.f} .. {1:.f} [{2:.f}] {3}".format(
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
            text="{0:.f} .. {1:.f} [{2:.f}] {3}".format(
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
            text="{0:.f} {1}".format(l, unit),
            foreground="DarkBlue")

        lab.grid(row=row, column=col, sticky=Tk.W)

        row += 1
        col = 0

        lab = Tk.Label(frame, text=_("Rapid:"))

        lab.grid(row=row, column=col, sticky=Tk.E)

        col += 1

        lab = Tk.Label(
            frame,
            text="{0:.f} {1}".format(r, unit),
            foreground="DarkBlue")

        lab.grid(row=row, column=col, sticky=Tk.W)

        row += 1
        col = 0

        lab = Tk.Label(frame, text=_("Time:"))

        lab.grid(row=row, column=col, sticky=Tk.E)

        col += 1

        h, m = divmod(t, 60)  # t in min
        s = (m-int(m))*60

        lab = Tk.Label(
            frame,
            text="{0:d}{1:02d}{2:02d}".format(int(h), int(m), int(s)),
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
            text="{0:.f} .. {1:.f} [{2:.f}] {3}".format(
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
            text="{0:.f} .. {1:.f} [{2:.f}] {3}".format(
                OCV.CD["aymin"], OCV.CD["aymax"],
                OCV.CD["aymax"] -OCV.CD["aymin"],
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
            text="{0:.f} .. {1:.f} [{2:.f}] {3}".format(
                OCV.CD["azmin"], OCV.CD["azmax"],
                OCV.CD["azmax"] -OCV.CD["azmin"],
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
            text=str(len(self.gcode.blocks)),
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
            text="{0:.f} {1}".format(self.cnc.totalLength, unit),
            foreground="DarkBlue")

        lab.grid(row=row, column=col, sticky=Tk.W)

        row += 1
        col = 0

        lab = Tk.Label(frame, text=_("Time:"))

        lab.grid(row=row, column=col, sticky=Tk.E)

        col += 1

        h, m = divmod(self.cnc.totalTime, 60) # t in min
        s = (m-int(m))*60

        lab = Tk.Label(
            frame,
            text="{0:d}{1:02d}{2:02d}".format(int(h), int(m), int(s)),
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


    #def reportDialog(self, event=None):
    #    Utils.ReportDialog(self)


    def viewChange(self, event=None):
        if self.running:
            self._selectI = 0    # last selection pointer in items
        self.draw()


    def refresh(self, event=None):
        self.editor.fill()
        self.draw()


    def draw(self):
        view = CNCCanvas.VIEWS.index(self.canvasFrame.view.get())
        self.canvasFrame.canvas.draw(view)
        self.selectionChange()

    def drawAfter(self, event=None):
        """Redraw with a small delay"""
        if self._drawAfter is not None:
            self.after_cancel(self._drawAfter)

        self._drawAfter = self.after(DRAW_AFTER, self.draw)
        return "break"


    def canvasFocus(self, event=None):
        self.canvasFrame.canvas.focus_set()
        return "break"


    def selectAll(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.editor.copy()
            self.ribbon.changePage("Editor")
            self.editor.selectAll()
            self.selectionChange()
            return "break"


    def unselectAll(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.ribbon.changePage("Editor")
            self.editor.selectClear()
            self.selectionChange()
            return "break"


    def selectInvert(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.ribbon.changePage("Editor")
            self.editor.selectInvert()
            self.selectionChange()
            return "break"


    def selectLayer(self, event=None):
        focus = self.focus_get()
        if focus in (self.canvasFrame.canvas, self.editor):
            self.ribbon.changePage("Editor")
            self.editor.selectLayer()
            self.selectionChange()
            return "break"


    def find(self, event=None):
        self.ribbon.changePage("Editor")
        #self.editor.findDialog()
        #return "break"


    def findNext(self, event=None):
        self.ribbon.changePage("Editor")
        #self.editor.findNext()
        #return "break"


    def replace(self, event=None):
        self.ribbon.changePage("Editor")
        #self.editor.replaceDialog()
        #return "break"


    def activeBlock(self):
        return self.editor.activeBlock()


    def cmdExecute(self, event):
        """
        Keyboard binding to <Return>
        """
        self.commandExecute()


    def insertCommand(self, cmd, execute=False):
        self.command.delete(0, Tk.END)
        self.command.insert(0, cmd)

        if execute:
            self.commandExecute(False)


    def commandExecute(self, addHistory=True):
        """
        Execute command from command line
        """
        self._historyPos = None
        self._historySearch = None

        line = self.command.get().strip()
        if not line:
            return

        if self._historyPos is not None:
            if self.history[self._historyPos] != line:
                self.history.append(line)
        elif not self.history or self.history[-1] != line:
            self.history.append(line)

        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
        self.command.delete(0, Tk.END)
        self.execute(line)


    def execute(self, line):
        """
        Execute a single command
        """
        try:
            line = self.evaluate(line)
        except:
            tkMessageBox.showerror(
                _("Evaluation error"),
                sys.exc_info()[1], parent=self)
            return "break"
        #print ">>>",line

        if line is None:
            return "break"

        if self.executeGcode(line):
            return "break"

        oline = line.strip()
        line = oline.replace(",", " ").split()
        cmd = line[0].upper()

        # ABO*UT: About dialog
        if rexx.abbrev("ABOUT", cmd, 3):
            self.about()

        elif rexx.abbrev("AUTOLEVEL", cmd, 4):
            self.executeOnSelection("AUTOLEVEL", True)

        # CAM*ERA: camera actions
        elif rexx.abbrev("CAMERA", cmd, 3):
            # FIXME will make crazy the button state
            if rexx.abbrev("SWITCH", line[1].upper(), 1):
                Page.groups["Probe:Camera"].switchCamera()

            elif rexx.abbrev("SPINDLE", line[1].upper(), 2):
                Page.frames["Probe:Camera"].registerSpindle()

            elif rexx.abbrev("CAMERA", line[1].upper(), 1):
                Page.frames["Probe:Camera"].registerCamera()

        # CLE*AR: clear terminal
        elif rexx.abbrev("CLEAR", cmd, 3) or cmd == "CLS":
            self.ribbon.changePage("Terminal")
            Page.frames["Terminal"].clear()

        # CLOSE: close path - join end with start with a line segment
        elif rexx.abbrev("CLOSE", cmd, 4):
            self.executeOnSelection("CLOSE", True)

        # CONT*ROL: switch to control tab
        elif rexx.abbrev("CONTROL", cmd, 4):
            self.ribbon.changePage("Control")

        # default values are taken from the active material
        elif cmd == "CUT":
            try:
                depth = float(line[1])
            except:
                depth = None

            try:
                step = float(line[2])
            except:
                step = None

            try:
                surface = float(line[3])
            except:
                surface = None

            try:
                feed = float(line[4])
            except:
                feed = None

            try:
                feedz = float(line[5])
            except:
                feedz = None

            self.executeOnSelection("CUT", True, depth, step, surface, feed, feedz)

        # DOWN: move downward in cutting order the selected blocks
        # UP: move upwards in cutting order the selected blocks
        elif cmd == "DOWN":
            self.editor.orderDown()
        elif cmd == "UP":
            self.editor.orderUp()

        # DIR*ECTION
        elif rexx.abbrev("DIRECTION", cmd, 3):
            if rexx.abbrev("CLIMB", line[1].upper(), 2):
                direction = -2
            elif rexx.abbrev("CONVENTIONAL", line[1].upper(), 2):
                direction = 2
            elif rexx.abbrev("CW", line[1].upper(), 2):
                direction = 1
            elif rexx.abbrev("CCW", line[1].upper(), 2):
                direction = -1
            else:
                tkMessageBox.showerror(
                    _("Direction command error"),
                    _("Invalid direction {0} specified".format(line[1])),
                    parent=self)
                return "break"
            self.executeOnSelection("DIRECTION", True, direction)

        # DRI*LL [depth] [peck]: perform drilling at all penetrations points
        elif rexx.abbrev("DRILL", cmd, 3):
            try:
                h = float(line[1])
            except:
                h = None
            try:
                p = float(line[2])
            except:
                p = None

            self.executeOnSelection("DRILL", True, h, p)

        # ECHO <msg>: echo message
        elif cmd == "ECHO":
            self.setStatus(oline[5:].strip())

        # FEED on/off: append feed commands on every motion line for feed override testing
        elif cmd == "FEED":
            try:
                OCV.appendFeed = (line[1].upper() == "ON")
            except:
                OCV.appendFeed = True
            self.setStatus(OCV.appendFeed and \
                "Feed appending turned on" or \
                "Feed appending turned off")

        # INV*ERT: invert selected blocks
        elif rexx.abbrev("INVERT", cmd, 3):
            self.editor.invertBlocks()

        # MSG|MESSAGE <msg>: echo message
        elif cmd in ("MSG", "MESSAGE"):
            tkMessageBox.showinfo("Message", oline[oline.find(" ")+1:].strip(), parent=self)

        # FIL*TER: filter editor blocks with text
        elif rexx.abbrev("FILTER", cmd, 3) or cmd == "ALL":
            try:
                self.editor.filter = line[1]
            except:
                self.editor.filter = None
            self.editor.fill()

        # ED*IT: edit current line or item
        elif rexx.abbrev("EDIT", cmd, 2):
            self.edit()

        # IM*PORT <filename>: import filename with gcode or dxf at cursor location
        # or at the end of the file
        elif rexx.abbrev("IMPORT", cmd, 2):
            try:
                self.importFile(line[1])
            except:
                self.importFile()

        # INK*SCAPE: remove uneccessary Z motion as a result of inkscape gcodetools
        elif rexx.abbrev("INKSCAPE", cmd, 3):
            if len(line) > 1 and rexx.abbrev("ALL", line[1].upper()):
                self.editor.selectAll()
            self.executeOnSelection("INKSCAPE", True)

        # ISLAND set or toggle island tag
        elif rexx.abbrev("ISLAND", cmd, 3):
            if len(line) > 1:
                if line[1].upper() == "1":
                    isl = True
                else:
                    isl = False
            else:
                isl = None
            self.executeOnSelection("ISLAND", True, isl)

        # ISO1: switch to ISO1 projection
        elif cmd == "ISO1":
            self.canvasFrame.viewISO1()
        # ISO2: switch to ISO2 projection
        elif cmd == "ISO2":
            self.canvasFrame.viewISO2()
        # ISO3: switch to ISO3 projection
        elif cmd == "ISO3":
            self.canvasFrame.viewISO3()

        # LO*AD [filename]: load filename containing g-code
        elif rexx.abbrev("LOAD", cmd, 2) and len(line) == 1:
            self.loadDialog()

        elif rexx.abbrev("MIRROR", cmd, 3):

            if len(line) == 1:
                return "break"

            line1 = line[1].upper()
            #if nothing is selected:
            if not self.editor.curselection():
                self.editor.selectAll()
            if rexx.abbrev("HORIZONTAL", line1):
                self.executeOnSelection("MIRRORH", False)
            elif rexx.abbrev("VERTICAL", line1):
                self.executeOnSelection("MIRRORV", False)

        elif rexx.abbrev("ORDER", cmd, 2):
            if line[1].upper() == "UP":
                self.editor.orderUp()
            elif line[1].upper() == "DOWN":
                self.editor.orderDown()

        # MO*VE [|CE*NTER|BL|BR|TL|TR|UP|DOWN|x] [[y [z]]]:
        # move selected objects either by mouse or by coordinates
        elif rexx.abbrev("MOVE", cmd, 2):
            if len(line) == 1:
                self.canvasFrame.canvas.setActionMove()
                return "break"
            line1 = line[1].upper()
            dz = 0.0
            if rexx.abbrev("CENTER", line1, 2):
                dx = -(OCV.CD["xmin"] + OCV.CD["xmax"])/2.0
                dy = -(OCV.CD["ymin"] + OCV.CD["ymax"])/2.0
                self.editor.selectAll()
            elif line1 == "BL":
                dx = -OCV.CD["xmin"]
                dy = -OCV.CD["ymin"]
                self.editor.selectAll()
            elif line1 == "BC":
                dx = -(OCV.CD["xmin"] + OCV.CD["xmax"])/2.0
                dy = -OCV.CD["ymin"]
                self.editor.selectAll()
            elif line1 == "BR":
                dx = -OCV.CD["xmax"]
                dy = -OCV.CD["ymin"]
                self.editor.selectAll()
            elif line1 == "TL":
                dx = -OCV.CD["xmin"]
                dy = -OCV.CD["ymax"]
                self.editor.selectAll()
            elif line1 == "TC":
                dx = -(OCV.CD["xmin"] + OCV.CD["xmax"])/2.0
                dy = -OCV.CD["ymax"]
                self.editor.selectAll()
            elif line1 == "TR":
                dx = -OCV.CD["xmax"]
                dy = -OCV.CD["ymax"]
                self.editor.selectAll()
            elif line1 == "LC":
                dx = -OCV.CD["xmin"]
                dy = -(OCV.CD["ymin"] + OCV.CD["ymax"])/2.0
                self.editor.selectAll()
            elif line1 == "RC":
                dx = -OCV.CD["xmax"]
                dy = -(OCV.CD["ymin"] + OCV.CD["ymax"])/2.0
                self.editor.selectAll()
            elif line1 in ("UP", "DOWN"):
                dx = line1
                dy = dz = line1
            else:
                try:
                    dx = float(line[1])
                except:
                    dx = 0.0
                try:
                    dy = float(line[2])
                except:
                    dy = 0.0
                try:
                    dz = float(line[3])
                except:
                    dz = 0.0

            self.executeOnSelection("MOVE", False, dx, dy, dz)

        # OPT*IMIZE: reorder selected blocks to minimize rapid motions
        elif rexx.abbrev("OPTIMIZE", cmd, 3):
            if not self.editor.curselection():
                tkMessageBox.showinfo(
                    _("Optimize"),
                    _("Please select the blocks of gcode you want to optimize."),
                    parent=self)
            else:
                self.executeOnSelection("OPTIMIZE", True)

        # OPT*IMIZE: reorder selected blocks to minimize rapid motions
        elif rexx.abbrev("ORIENT", cmd, 4):
            if not self.editor.curselection():
                self.editor.selectAll()
            self.executeOnSelection("ORIENT", False)

        # ORI*GIN x y z: move origin to x,y,z by moving all to -x -y -z
        elif rexx.abbrev("ORIGIN", cmd, 3):
            try:
                dx = -float(line[1])
            except:
                dx = 0.0
            try:
                dy = -float(line[2])
            except:
                dy = 0.0
            try:
                dz = -float(line[3])
            except:
                dz = 0.0

            self.editor.selectAll()
            self.executeOnSelection("MOVE", False, dx, dy, dz)

        # REV*ERSE: reverse path direction
        elif rexx.abbrev("REVERSE", cmd, 3):
            self.executeOnSelection("REVERSE", True)

        # ROT*ATE [CCW|CW|FLIP|ang] [x0 [y0]]: rotate selected blocks
        # counter-clockwise(90) / clockwise(-90) / flip(180)
        # 90deg or by a specific angle and a pivot point
        elif rexx.abbrev("ROTATE", cmd, 3):
            line1 = line[1].upper()
            x0 = y0 = 0.0
            if line1 == "CCW":
                ang = 90.0
                #self.editor.selectAll()
            elif line1 == "CW":
                ang = -90.0
                #self.editor.selectAll()
            elif line1 == "FLIP":
                ang = 180.0
                #self.editor.selectAll()
            else:
                try:
                    ang = float(line[1])
                except:
                    pass
                try:
                    x0 = float(line[2])
                except:
                    pass
                try:
                    y0 = float(line[3])
                except:
                    pass

            self.executeOnSelection("ROTATE", False, ang, x0, y0)

        # ROU*ND [n]: round all digits to n fractional digits
        elif rexx.abbrev("ROUND", cmd, 3):
            acc = None
            if len(line) > 1:
                if rexx.abbrev("ALL", line[1].upper()):
                    self.editor.selectAll()
                else:
                    try:
                        acc = int(line[1])
                    except:
                        pass
            self.executeOnSelection("ROUND", False, acc)

        # RU*LER: measure distances with mouse ruler
        elif rexx.abbrev("RULER", cmd, 2):
            self.canvasFrame.canvas.setActionRuler()

        # STAT*ISTICS: show statistics of current job
        elif rexx.abbrev("STATISTICS", cmd, 4):
            self.showStats()

        # STEP [s]: set motion step size to s
        elif cmd == "STEP":
            try:
                self.control.setStep(float(line[1]))
            except:
                pass

        # SPI*NDLE [ON|OFF|speed]: turn on/off spindle
        elif rexx.abbrev("SPINDLE", cmd, 3):
            if len(line) > 1:
                if line[1].upper() == "OFF":
                    self.spindle.set(False)
                elif line[1].upper() == "ON":
                    self.spindle.set(True)
                else:
                    try:
                        rpm = int(line[1])
                        if rpm == 0:
                            self.spindleSpeed.set(0)
                            self.spindle.set(False)
                        else:
                            self.spindleSpeed.set(rpm)
                            self.spindle.set(True)
                    except:
                        pass
            else:
                # toggle spindle
                self.spindle.set(not self.spindle.get())
            self.spindleControl()

        # STOP: stop current run
        elif cmd == "STOP":
            self.stopRun()

        # TERM*INAL: switch to terminal tab
        elif rexx.abbrev("TERMINAL", cmd, 4):
            self.ribbon.changePage("Terminal")

        # TOOL [diameter]: set diameter of cutting tool
        elif cmd in ("BIT", "TOOL", "MILL"):
            try:
                diam = float(line[1])
            except:
                tool = self.tools["EndMill"]
                diam = self.tools.fromMm(tool["diameter"])
            self.setStatus(_("EndMill: %s %g")%(tool["name"], diam))

        # TOOLS
        elif cmd == "TOOLS":
            self.ribbon.changePage("CAM")

        # UNL*OCK: unlock grbl
        elif rexx.abbrev("UNLOCK", cmd, 3):
            self.mcontrol.unlock(True)

        # US*ER cmd: execute user command, cmd=number or name
        elif rexx.abbrev("USER", cmd, 2):
            n = Utils.getInt("Buttons", "n", 6)
            try:
                idx = int(line[1])
            except:
                try:
                    name = line[1].upper()
                    for i in range(n):
                        if name == Utils.getStr("Buttons", "name. {0:d}".format(i), "").upper():
                            idx = i
                            break
                except:
                    return "break"
            if idx < 0 or idx >= n:
                self.setStatus(_("Invalid user command {0}").format(line[1]))
                return "break"
            cmd = Utils.getStr("Buttons", "command. {0:d}".format(idx), "")
            for line in cmd.splitlines():
                self.execute(line)

        # RR*APID:
        elif rexx.abbrev("RRAPID", cmd, 2):
            Page.frames["Probe:Probe"].recordRapid()

        # RF*EED:
        elif rexx.abbrev("RFEED", cmd, 2):
            Page.frames["Probe:Probe"].recordFeed()

        # RP*OINT:
        elif rexx.abbrev("RPOINT", cmd, 2):
            Page.frames["Probe:Probe"].recordPoint()

        # RC*IRCLE:
        elif rexx.abbrev("RCIRCLE", cmd, 2):
            Page.frames["Probe:Probe"].recordCircle()

        # RFI*NISH:
        elif rexx.abbrev("RFINISH", cmd, 3):
            Page.frames["Probe:Probe"].recordFinishAll()

        # XY: switch to XY view
        # YX: switch to XY view
        elif cmd in ("XY", "YX"):
            self.canvasFrame.viewXY()

        # XZ: switch to XZ view
        # ZX: switch to XZ view
        elif cmd in ("XZ", "ZX"):
            self.canvasFrame.viewXZ()

        # YZ: switch to YZ view
        # ZY: switch to YZ view
        elif cmd in ("YZ", "ZY"):
            self.canvasFrame.viewYZ()

        else:
            rc = self.executeCommand(oline)
            if rc:
                tkMessageBox.showerror(rc[0], rc[1], parent=self)
            return "break"


    def executeOnSelection(self, cmd, blocksonly, *args):
        """Execute a command over the selected lines"""
        if blocksonly:
            items = self.editor.getSelectedBlocks()
        else:
            items = self.editor.getCleanSelection()
        if not items:
            tkMessageBox.showwarning(
                _("Nothing to do"),
                _("Operation %s requires some gcode to be selected")%(cmd),
                parent=self)
            return

        self.busy()
        sel = None
        undoinfo = None    # all operations should return undo information
        if   cmd == "AUTOLEVEL":
            sel = self.gcode.autolevel(items)
        elif cmd == "CUT":
            sel = self.gcode.cut(items, *args)
        elif cmd == "CLOSE":
            sel = self.gcode.close(items)
        elif cmd == "DIRECTION":
            sel = self.gcode.cutDirection(items, *args)
        elif cmd == "DRILL":
            sel = self.gcode.drill(items, *args)
        elif cmd == "ORDER":
            self.gcode.orderLines(items, *args)
        elif cmd == "INKSCAPE":
            self.gcode.inkscapeLines()
        elif cmd == "ISLAND":
            self.gcode.island(items, *args)
        elif cmd == "MIRRORH":
            self.gcode.mirrorHLines(items)
        elif cmd == "MIRRORV":
            self.gcode.mirrorVLines(items)
        elif cmd == "MOVE":
            self.gcode.moveLines(items, *args)
        elif cmd == "OPTIMIZE":
            self.gcode.optimize(items)
        elif cmd == "ORIENT":
            self.gcode.orientLines(items)
        elif cmd == "REVERSE":
            self.gcode.reverse(items, *args)
        elif cmd == "ROUND":
            self.gcode.roundLines(items, *args)
        elif cmd == "ROTATE":
            self.gcode.rotateLines(items, *args)

        # Fill listbox and update selection
        self.editor.fill()
        if sel is not None:
            if isinstance(sel, str):
                tkMessageBox.showerror(_("Operation error"), sel, parent=self)
            else:
                self.editor.select(sel, clear=True)
        self.drawAfter()
        self.notBusy()
        self.setStatus("{0} {1}".format(cmd, " ".join([str(a) for a in args if a is not None])))


    def edit(self, event=None):
        page = self.ribbon.getActivePage()
        if page.name == "Editor":
            self.editor.edit()
        elif page.name == "CAM":
            page.edit()


    def commandFocus(self, event=None):
        self.command.focus_set()


    def commandFocusIn(self, event=None):
        self.cmdlabel["foreground"] = "Blue"


    def commandFocusOut(self, event=None):
        self.cmdlabel["foreground"] = "Black"


    def commandKey(self, event):
        # FIXME why it is not called?
        if event.char or event.keysym in ("BackSpace"):
            self._historyPos = None
            self._historySearch = None


    def commandHistoryUp(self, event=None):
        if self._historyPos is None:
            s = self.command.get()
            if self.history:
                self._historyPos = len(self.history)-1
            else:
                self._historySearch = None
                return
            if s and self._historySearch is None:
                self._historySearch = s.strip().upper()
        else:
            self._historyPos = max(0, self._historyPos-1)

        if self._historySearch:
            for i in range(self._historyPos, -1, -1):
                h = self.history[i]
                if h.upper().startswith(self._historySearch):
                    self._historyPos = i
                    break

        self.command.delete(0, Tk.END)
        self.command.insert(0, self.history[self._historyPos])


    def commandHistoryDown(self, event=None):
        if self._historyPos is None:
            self._historySearch = None
            return
        else:
            self._historyPos += 1
            if self._historyPos >= len(self.history):
                self._historyPos = None
                self._historySearch = None

        if self._historySearch:
            for i in range(self._historyPos, len(self.history)):
                h = self.history[i]
                if h.upper().startswith(self._historySearch):
                    self._historyPos = i
                    break

        self.command.delete(0, Tk.END)
        if self._historyPos is not None:
            self.command.insert(0, self.history[self._historyPos])


    def select(self, items, double, clear, toggle=True):
        self.editor.select(items, double, clear, toggle)
        self.selectionChange()


    def selectionChange(self, event=None):
        """Selection has changed highlight the canvas"""
        items = self.editor.getSelection()
        self.canvasFrame.canvas.clearSelection()

        if not items:
            return

        self.canvasFrame.canvas.select(items)
        self.canvasFrame.canvas.activeMarker(self.editor.getActive())


    def newFile(self, event=None):
        """Create a new file"""
        if self.running:
            return

        if self.fileModified():
            return

        self.gcode.init()
        self.gcode.headerFooter()
        self.editor.fill()
        self.draw()
        self.title("{0}{1}".format(Utils.__prg__, OCV._version))


    def loadDialog(self, event=None):
        """load dialog"""
        if self.running:
            return

        filename = bFileDialog.askopenfilename(
            master=self,
            title=_("Open file"),
            initialfile=os.path.join(
                Utils.getUtf("File", "dir"),
                Utils.getUtf("File", "file")),
            filetypes=FILETYPES)

        if filename:
            self.load(filename)

        return "break"


    def saveDialog(self, event=None):
        """save dialog"""
        if self.running:
            return

        fn, ext = os.path.splitext(Utils.getUtf("File", "file"))

        if ext in (".dxf", ".DXF"):
            ext = ".ngc"
        filename = bFileDialog.asksaveasfilename(
            master=self,
            title=_("Save file"),
            initialfile=os.path.join(Utils.getUtf("File", "dir"), fn+ext),
            filetypes=FILETYPES)

        if filename:
            self.save(filename)

        return "break"


    def fileModified(self):
        if self.gcode.isModified():
            ans = tkMessageBox.askquestion(
                _("File modified"),
                _("Gcode was modified do you want to save it first?"),
                type=tkMessageBox.YESNOCANCEL,
                parent=self)
            if ans == tkMessageBox.CANCEL:
                return True
            if ans == tkMessageBox.YES or ans is True:
                self.saveAll()

        if not self.gcode.probe.isEmpty() and not self.gcode.probe.saved:
            ans = tkMessageBox.askquestion(
                _("Probe File modified"),
                _("Probe was modified do you want to save it first?"),
                type=tkMessageBox.YESNOCANCEL,
                parent=self)
            if ans == tkMessageBox.CANCEL:
                return True
            if ans == tkMessageBox.YES or ans is True:
                if self.gcode.probe.filename == "":
                    self.saveDialog()
                else:
                    self.gcode.probe.save()
        return False


    def load(self, filename, autoloaded=False):
        """Load a file into editor"""
        fn, ext = os.path.splitext(filename)
        if ext == ".probe":
            pass
        else:
            if self.fileModified():
                return

            if not self.gcode.probe.isEmpty():
                ans = tkMessageBox.askquestion(
                    _("Existing Autolevel"),
                    _("Autolevel/probe information already exists.\nDelete it?"),
                    parent=self)

                if ans == tkMessageBox.YES or ans is True:
                    self.gcode.probe.init()

        self.setStatus(_("Loading: {0} ...").format(filename), True)
        Sender.load(self, filename)

        if ext == ".probe":
            Page.frames["Probe:Autolevel"].setValues()
            self.event_generate("<<DrawProbe>>")

        elif ext == ".orient":
            self.event_generate("<<DrawOrient>>")
            self.event_generate("<<OrientSelect>>", data=0)
            self.event_generate("<<OrientUpdate>>")

        else:
            self.editor.selectClear()
            self.editor.fill()
            self.canvasFrame.canvas.reset()
            self.draw()
            self.canvasFrame.canvas.fit2Screen()
            Page.frames["CAM"].populate()

        if autoloaded:
            self.setStatus(
                _("'{0}' reloaded at '{1}'").format(
                    filename,
                    str(datetime.now())))
        else:
            self.setStatus(_("'{0}' loaded").format(filename))

        self.title("{0}{1}: {2}".format(Utils.__prg__, OCV._version, self.gcode.filename))


    def save(self, filename):
        Sender.save(self, filename)

        self.setStatus(_("'{0}' saved").decode("utf8").format(filename))

        self.title("{0}{1}: {2}".format(Utils.__prg__, OCV._version, self.gcode.filename))


    def saveAll(self, event=None):
        if self.gcode.filename:
            Sender.saveAll(self)
        else:
            self.saveDialog()
        return "break"


    def reload(self, event=None):
        self.load(self.gcode.filename)


    def importFile(self, filename=None):
        if filename is None:
            filename = bFileDialog.askopenfilename(
                master=self,
                title=_("Import Gcode/DXF file"),
                initialfile=os.path.join(
                    Utils.getUtf("File", "dir"),
                    Utils.getUtf("File", "file")),
                filetypes=[
                    (_("G-Code"), ("*.ngc", "*.nc", "*.gcode")),
                    ("DXF", "*.dxf"),
                    ("All", "*")])
        if filename:
            fn, ext = os.path.splitext(filename)
            ext = ext.lower()
            gcode = GCode()
            gcode.load(filename)
            sel = self.editor.getSelectedBlocks()
            if not sel:
                pos = None
            else:
                pos = sel[-1]
            self.addUndo(self.gcode.insBlocksUndo(pos, gcode.blocks))
            del gcode
            self.editor.fill()
            self.draw()
            self.canvasFrame.canvas.fit2Screen()


    def focus_in(self, event):
        if self._inFocus:
            return
        # FocusIn is generated for all sub-windows, handle only the main window
        if self is not event.widget:
            return

        self._inFocus = True
        if self.gcode.checkFile():
            if self.gcode.isModified():
                ans = tkMessageBox.askquestion(
                    _("Warning"),
                    _("Gcode file {0} was changed since editing started\n" \
                      "Reload new version?").format(self.gcode.filename),
                    parent=self)
                if ans == tkMessageBox.YES or ans is True:
                    self.gcode.resetModified()
                    self.load(self.gcode.filename)
            else:
                self.load(self.gcode.filename, True)
        self._inFocus = False
        self.gcode.syncFileTime()


    def openClose(self, event=None):
        serialPage = Page.frames["Serial"]
        print("OpenClose Reached")
        if OCV.serial_open is True:
            self.close()
            serialPage.connectBtn.config(
                text=_("Open"),
                background="Salmon",
                activebackground="Salmon")
            OCV.serial_open = False
        else:
            serialPage = Page.frames["Serial"]
            device = _device or serialPage.portCombo.get() #.split("\t")[0]
            baudrate = _baud   or serialPage.baudCombo.get()
            if self.open(device, baudrate):
                OCV.serial_open = True
                serialPage.connectBtn.config(
                    text=_("Close"),
                    background="LightGreen",
                    activebackground="LightGreen")
                self.enable()


    def open(self, device, baudrate):
        try:
            return Sender.open(self, device, baudrate)
        except:
            OCV.serial_open = False
            self.thread = None
            tkMessageBox.showerror(
                _("Error opening serial"),
                sys.exc_info()[1],
                parent=self)
        return False


    def close(self):
        Sender.close(self)
        try:
            self.dro.updateState()
        except Tk.TclError:
            pass


    def checkStop(self):
        """
        An entry function should be called periodically during compiling
        to check if the Pause or Stop buttons are pressed
        @return true if the compile has to abort
        """

        try:
            self.update()    # very tricky function of Tk
        except Tk.TclError:
            pass
        return self._stop


    def run(self, lines=None):
        """
        Send enabled gcode file to the CNC machine
        """
        self.cleanAfter = True    #Clean when this operation stops
        print("Will clean after this operation")

        if OCV.HAS_SERIAL is False and not OCV.developer:
            tkMessageBox.showerror(
                _("Serial Error"),
                _("Serial is not connected"),
                parent=self)
            return

        if self.running:
            if self._pause:
                self.resume()
                return
            tkMessageBox.showerror(
                _("Already running"),
                _("Please stop before"),
                parent=self)
            return

        self.editor.selectClear()
        self.selectionChange()
        OCV.CD["errline"] = ""

        # the buffer of the machine should be empty?
        self.initRun()
        self.canvasFrame.canvas.clearSelection()
        self._runLines = sys.maxsize    # temporary WARNING this value is used
                        # by Sender._serialIO to check if we
                        # are still sending or we finished
        self._gcount = 0 # count executed lines
        self._selectI = 0 # last selection pointer in items
        self._paths = None # temporary
        OCV.CD["running"] = True # enable running status
        OCV.CD["_OvChanged"] = True # force a feed change if any
        if self._onStart:
            try:
                os.system(self._onStart)
            except:
                pass

        if lines is None:
            #if not self.gcode.probe.isEmpty() and not self.gcode.probe.zeroed:
            #    tkMessageBox.showerror(_("Probe is not zeroed"),
            #        _("Please ZERO any location of the probe before starting a run"),
            #        parent=self)
            #    return
            self.statusbar.setLimits(0, 9999)
            self.statusbar.setProgress(0, 0)

            self._paths = self.gcode.compile(self.queue, self.checkStop)
            if self._paths is None:
                self.emptyQueue()
                self.purgeController()
                return
            elif not self._paths:
                self.runEnded()
                tkMessageBox.showerror(
                    _("Empty gcode"),
                    _("Not gcode file was loaded"),
                    parent=self)
                return

            # reset colors
            before = time.time()
            for ij in self._paths:  # Slow loop

                if not ij:
                    continue

                path = self.gcode[ij[0]].path(ij[1])
                if path:
                    color = self.canvasFrame.canvas.itemcget(path, "fill")
                    if color != OCV.ENABLE_COLOR:
                        self.canvasFrame.canvas.itemconfig(
                            path,
                            width=1,
                            fill=OCV.ENABLE_COLOR)
                    # Force a periodic update since this loop can take time
                    if time.time() - before > 0.25:
                        self.update()
                        before = time.time()

            # the buffer of the machine should be empty?
            self._runLines = len(self._paths) + 1  # plus the wait
        else:
            n = 1        # including one wait command
            for line in CNC.compile(lines):
                if line is not None:
                    if isinstance(line, str):
                        self.queue.put(line+"\n")
                    else:
                        self.queue.put(line)
                    n += 1
            self._runLines = n    # set it at the end to be sure that all lines are queued
        self.queue.put((WAIT,))        # wait at the end to become idle

        self.setStatus(_("Running..."))
        self.statusbar.setLimits(0, self._runLines)
        self.statusbar.configText(fill="White")
        self.statusbar.config(background="DarkGray")

        self.bufferbar.configText(fill="White")
        self.bufferbar.config(background="DarkGray")
        self.bufferbar.setText("")


    def startPendant(self, showInfo=True):
        """
        Start the web pendant
        """

        started = Pendant.start(self)
        if showInfo:
            hostName = "http://{0}:{1:d}".format(socket.gethostname(), Pendant.port)
            if started:
                tkMessageBox.showinfo(
                    _("Pendant"),
                    _("Pendant started:\n")+hostName,
                    parent=self)
            else:
                dr = tkMessageBox.askquestion(
                    _("Pendant"),
                    _("Pendant already started:\n") \
                    + hostName + \
                    _("\nWould you like open it locally?"),
                    parent=self)
                if dr == "yes":
                    webbrowser.open(hostName, new=2)


    def stopPendant(self):
        """
        Stop the web pendant
        """
        if Pendant.stop():
            tkMessageBox.showinfo(
                _("Pendant"),
                _("Pendant stopped"),
                parent=self)


    def _monitorSerial(self):
        """
        Inner loop to catch any generic exception
        """

        # Check serial output
        t = time.time()

        # dump in the terminal what ever you can in less than 0.1s
        inserted = False
        while self.log.qsize() > 0 and time.time()-t < 0.1:
            try:
                msg, line = self.log.get_nowait()
                #line = line.rstrip("\n")
                line = str(line).rstrip("\n")
                inserted = True
                #print "<<<",msg,line,"\n" in line

                if msg == Sender.MSG_BUFFER:
                    self.buffer.insert(Tk.END, line)

                elif msg == Sender.MSG_SEND:
                    self.terminal.insert(Tk.END, line)
                    self.terminal.itemconfig(Tk.END, foreground="Blue")

                elif msg == Sender.MSG_RECEIVE:
                    self.terminal.insert(Tk.END, line)
                    if self._insertCount:
                        # when counting is started, then continue
                        self._insertCount += 1
                    elif line and line[0] in ("[", "$"):
                        # start the counting on the first line received
                        # starting with $ or [
                        self._insertCount = 1

                elif msg == Sender.MSG_OK:
                    if self.terminal.size() > 0:
                        if self._insertCount:
                            pos = self.terminal.size()-self._insertCount
                            self._insertCount = 0
                        else:
                            pos = Tk.END
                        self.terminal.insert(pos, self.buffer.get(0))
                        self.terminal.itemconfig(pos, foreground="Blue")
                        self.buffer.delete(0)
                    self.terminal.insert(Tk.END, line)

                elif msg == Sender.MSG_ERROR:
                    if self.terminal.size() > 0:
                        if self._insertCount:
                            pos = self.terminal.size()-self._insertCount
                            self._insertCount = 0
                        else:
                            pos = Tk.END
                        self.terminal.insert(pos, self.buffer.get(0))
                        self.terminal.itemconfig(pos, foreground="Blue")
                        self.buffer.delete(0)
                    self.terminal.insert(Tk.END, line)
                    self.terminal.itemconfig(Tk.END, foreground="Red")

                elif msg == Sender.MSG_RUNEND:
                    self.terminal.insert(Tk.END, line)
                    self.terminal.itemconfig(Tk.END, foreground="Magenta")
                    self.setStatus(line)
                    self.enable()

                elif msg == Sender.MSG_CLEAR:
                    self.buffer.delete(0, Tk.END)

                else:
                    # Unknown?
                    self.buffer.insert(Tk.END, line)
                    self.terminal.itemconfig(Tk.END, foreground="Magenta")

                if self.terminal.size() > 1000:
                    self.terminal.delete(0, 500)
            except Empty:
                break

        if inserted:
            self.terminal.see(Tk.END)

        # Check pendant
        try:
            cmd = self.pendant.get_nowait()
            self.execute(cmd)
        except Empty:
            pass

        # Load file from pendant
        if self._pendantFileUploaded != None:
            self.load(self._pendantFileUploaded)
            self._pendantFileUploaded = None

        # Update position if needed
        if self._posUpdate:
            state = OCV.CD["state"]
            #print Sender.ERROR_CODES[state]
            try:
                OCV.CD["color"] = STATECOLOR[state]
            except KeyError:
                if self._alarm:
                    OCV.CD["color"] = STATECOLOR["Alarm"]
                else:
                    OCV.CD["color"] = STATECOLORDEF
            self._pause = ("Hold" in state)
            self.dro.updateState()
            self.dro.updateCoords()
            self.canvasFrame.canvas.gantry(
                OCV.CD["wx"],
                OCV.CD["wy"],
                OCV.CD["wz"],
                OCV.CD["mx"],
                OCV.CD["my"],
                OCV.CD["mz"])
            if state == "Run":
                self.gstate.updateFeed()
                #self.xxx.updateSpindle()
            self._posUpdate = False

        # Update status string
        if self._gUpdate:
            self.gstate.updateG()
            self._gUpdate = False

        # Update probe and draw point
        if self._probeUpdate:
            Page.frames["Probe:Probe"].updateProbe()
            Page.frames["ProbeCommon"].updateTlo()
            self.canvasFrame.canvas.drawProbe()
            self._probeUpdate = False

        # Update any possible variable?
        if self._update:
            if self._update == "toolheight":
                Page.frames["Probe:Tool"].updateTool()
            elif self._update == "TLO":
                Page.frames["ProbeCommon"].updateTlo()
            self._update = None

        if self.running:
            self.proc_line_n = self._runLines - self.queue.qsize()
            #print(self.proc_line_n)
            self.statusbar.setProgress(
                self.proc_line_n,
                self._gcount)

            OCV.CD["msg"] = self.statusbar.msg

            b_fill = Sender.getBufferFill(self)
            #print ("Buffer = ", b_fill)
            self.bufferbar.setProgress(b_fill)
            self.bufferbar.setText("{0:02.2f}".format(b_fill))
            #print("Queue > ", self.queue.queue)

            if self.proc_line_n > 0 and \
                self.proc_line_n < len(self.gcode.gcodelines):

                displ_line = "{0} > {1} ".format(
                    self.proc_line_n,
                    self.gcode.gcodelines[self.proc_line_n])

                self.proc_line.set(displ_line)

            if self._selectI >= 0 and self._paths:
                while self._selectI <= self._gcount and self._selectI < len(self._paths):
                    if self._paths[self._selectI]:
                        i, j = self._paths[self._selectI]
                        path = self.gcode[i].path(j)
                        if path:
                            self.canvasFrame.canvas.itemconfig(
                                path,
                                width=2,
                                fill=OCV.PROCESS_COLOR)
                    self._selectI += 1

            if self._gcount >= self._runLines:
                self.runEnded()


    def monitorSerial(self):
        """
        "thread" timed function looking for messages in the serial thread
        and reporting back in the terminal
        """
        try:
            self._monitorSerial()
        except:
            typ, val, tb = sys.exc_info()
            traceback.print_exception(typ, val, tb)
        self.after(MONITOR_AFTER, self.monitorSerial)

    @staticmethod
    def get(self, section, item):
        return Utils.config.get(section, item)

    @staticmethod
    def set(self, section, item, value):
        return Utils.config.set(section, item, value)


def usage(rc):
    sys.stdout.write("{0} V{1} [{2}]\n".format(Utils.__prg__, OCV._version, OCV._date))
    sys.stdout.write("{0} <{1}>\n\n".format(OCV.author, OCV.email))
    sys.stdout.write("Usage: [options] [filename...]\n\n")
    sys.stdout.write("Options:\n")
    sys.stdout.write("\t-b # | --baud #\t\tSet the baud rate\n")
    sys.stdout.write("\t-d\t\t\tEnable developer features\n")
    sys.stdout.write("\t-D\t\t\tDisable developer features\n")
    sys.stdout.write("\t-f | --fullscreen\tEnable fullscreen mode\n")
    sys.stdout.write("\t-g #\t\t\tSet the default geometry\n")
    sys.stdout.write("\t-h | -? | --help\tThis help page\n")
    sys.stdout.write("\t-i # | --ini #\t\tAlternative ini file for testing\n")
    sys.stdout.write("\t-l | --list\t\tList all recently opened files\n")
    sys.stdout.write("\t-p # | --pendant #\tOpen pendant to specified port\n")
    sys.stdout.write("\t-P\t\t\tDo not start pendant\n")
    sys.stdout.write("\t-r | --recent\t\tLoad the most recent file opened\n")
    sys.stdout.write("\t-R #\t\t\tLoad the recent file matching the argument\n")
    sys.stdout.write("\t-s # | --serial #\tOpen serial port specified\n")
    sys.stdout.write("\t-S\t\t\tDo not open serial port\n")
    sys.stdout.write("\t--run\t\t\tDirectly run the file once loaded\n")
    sys.stdout.write("\n")
    sys.exit(rc)

def main(args=None):

    OCV.root = Tk.Tk()
    OCV.root.withdraw()

    if sys.version_info[0] != 2:
        sys.stdout.write("="*80+"\n")
        sys.stdout.write(
                "WARNING: OKKCNC is tested for running on python v2.x for now\n")
        sys.stdout.write("="*80+"\n")

        tkMessageBox.showwarning(
                "OKKCNC: Unsupported Python version",
                "Only Python 2 is currently supported by bCNC.\
                \nContinue on your own risk!")
        OCV.IS_PY3 = True

    Tk.CallWrapper = Utils.CallWrapper

    tkExtra.bindClasses(OCV.root)
    Utils.loadIcons()

    # Parse arguments
    try:
        optlist, args = getopt.getopt(
            sys.argv[1:],
            '?b:dDfhi:g:rlpPSs:',
            ['help', 'ini=', 'fullscreen', 'recent', 'list', 'pendant=',
             'serial=', 'baud=', 'run'])
    except getopt.GetoptError:
        usage(1)

    recent = None
    run = False
    fullscreen = False
    for opt, val in optlist:
        print("Opt, val ", opt, val)
        if opt in ("-h", "-?", "--help"):
            usage(0)
        elif opt in ("-i", "--ini"):
            Utils.iniUser = val
            Utils.loadConfiguration()
        elif opt == "-d":
            OCV.developer = True
        elif opt == "-D":
            OCV.developer = False
        elif opt == "-g":
            OCV.geometry = val
        elif opt in ("-r", "-R", "--recent", "-l", "--list"):
            if opt in ("-r", "--recent"):
                r = 0
            elif opt in ("--list", "-l"):
                r = -1
            else:
                try:
                    r = int(val)-1
                except:
                    # Scan in names
                    for r in range(Utils._maxRecent):
                        filename = Utils.getRecent(r)

                        if filename is None:
                            break

                        fn, ext = os.path.splitext(os.path.basename(filename))
                        if fn == val:
                            break
                    else:
                        r = 0
            if r < 0:
                # display list of recent files
                maxlen = 10
                for i in range(Utils._maxRecent):

                    try:
                        filename = Utils.getRecent(i)
                        #print ("Recent = ", i, maxlen, filename)
                    except:
                        continue

                    if (filename is not None):
                        maxlen = max(maxlen, len(os.path.basename(filename)))

                sys.stdout.write("Recent files:\n")
                for i in range(Utils._maxRecent):
                    filename = Utils.getRecent(i)

                    if filename is None:
                        break

                    d = os.path.dirname(filename)
                    fn = os.path.basename(filename)
                    sys.stdout.write(
                        "  {0:2d}: {1:d} {3}{2}\n".format(i+1, maxlen, fn, d))

                try:
                    sys.stdout.write("Select one: ")
                    r = int(sys.stdin.readline())-1
                except:
                    pass
            try:
                recent = Utils.getRecent(r)
            except:
                pass

        elif opt in ("-f", "--fullscreen"):
            fullscreen = True

        elif opt == "-S":
            _openserial = False

        elif opt in ("-s", "--serial"):
            _openserial = True
            _device = val

        elif opt in ("-b", "--baud"):
            _baud = val

        elif opt == "-p":
            pass #startPendant()

        elif opt == "-P":
            pass #stopPendant()

        elif opt == "--pendant":
            pass #startPendant on port

        elif opt == "--run":
            run = True

    palette = {"background": OCV.root.cget("background")}

    color_count = 0
    custom_color_count = 0

    for color_name in ("background", "foreground", "activeBackground",
                       "activeForeground", "disabledForeground",
                       "highlightBackground", "highlightColor",
                       "selectBackground", "selectForeground"):

        color2 = Utils.getStr("Color", "global." + color_name.lower(), None)
        color_count += 1

        if (color2 is not None) and (color2.strip() != ""):
            palette[color_name] = color2.strip()
            custom_color_count += 1

            if color_count == 0:
                tkExtra.GLOBAL_CONTROL_BACKGROUND = color2
            elif color_count == 1:
                tkExtra.GLOBAL_FONT_COLOR = color2

    if custom_color_count > 0:
        print("Changing palette")
        OCV.root.tk_setPalette(**palette)

    # Start application
    _application = Application(OCV.root)

    if fullscreen:
        _application.attributes("-fullscreen", True)

    # Parse remaining arguments except files
    if recent:
        args.append(recent)

    for fn in args:
        _application.load(fn)

    if OCV.HAS_SERIAL is False:
        tkMessageBox.showerror(
            _("python serial missing"),
            _("ERROR: Please install the python pyserial module\n" \
              "Windows:\n\tC:\\PythonXX\\Scripts\\easy_install pyserial\n" \
              "Mac:\tpip install pyserial\n" \
              "Linux:\tsudo apt-get install python-serial\n" \
              "\tor yum install python-serial\n" \
              "\tor dnf install python-pyserial"),
            parent=_application)

    if run:
        _application.run()

    try:
        _application.mainloop()
    except KeyboardInterrupt:
        _application.quit()

    _application.close()
    Utils.saveConfiguration()

if __name__ == "__main__":
    main()

 #vim:ts=8:sw=8:sts=8:noet
