# -*- coding: ascii -*-
"""__main__.py

OKKCNC main module

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

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
#import webbrowser

PRGPATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PRGPATH)
sys.path.append(os.path.join(PRGPATH, 'lib'))
sys.path.append(os.path.join(PRGPATH, 'plugins'))
sys.path.append(os.path.join(PRGPATH, 'controllers'))

# Import Here the OCV module as it contains variables used across the program
import OCV

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

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

# Load configuration before anything else
OCV.config = ConfigParser.ConfigParser()
# This is here to debug the fact that config is sometimes instantiated twice
#print("new-config", __name__, OCV.config)

import IniFile
IniFile.conf_file_load()

import rexx
import tkExtra
import bFileDialog
import tkDialogs
import CAMGen
import CNCCanvas
import Commands as cmd
import GCode
import Heuristic
import Interface

from CNC import CNC

# import Ribbon
import Pendant
from Sender import Sender
import Utils
import Bindings
from CNCRibbon import Page
from ToolsPage import Tools
#from ControlPage import ControlPage, ControlFrame

_openserial = True # override ini parameters
_device = None
_baud = None

MONITOR_AFTER = 200 # ms
DRAW_AFTER = 300 # ms

RX_BUFFER_SIZE = 128

MAX_HISTORY = 500

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

        # Set OCV.TK_MAIN to hold the Tk Object reference to reuse through
        # all interface, quick and dirty method to add clarity
        OCV.TK_MAIN = self

        #print("Application > ", self)

        # Initialisation of Sender loaded also some variables and methods
        # as OCV.TK_MAIN (this class as defined above) is declared also
        # as self in Sender.__init__.
        # all variables and methods of Sender defined as self.VARNAME or
        # self.METHOD are accessible through OCV.TK_MAIN across all the modules.

        Sender.__init__(OCV.TK_MAIN)

        if sys.platform == "win32":
            self.iconbitmap("{0}\\OKKCNC.ico".format(OCV.PRG_PATH))
        else:
            self.iconbitmap("@{0}/OKKCNC.xbm".format(OCV.PRG_PATH))

        self.title("{0} {1} {2} {3}".format(
                OCV.PRG_NAME, OCV.PRG_VER, OCV.PLATFORM, OCV.TITLE_MSG))
        OCV.iface_widgets = []

        #--- GLOBAL VARIABLES

        self.tools = Tools(self.gcode)
        self.controller = None
        self.load_main_config()
        
        #Load main_interface where some code has been moved
        # self.pages, OCV.TK_RIBBON, OCV.TK_CMD_W and many widget
        # are defined in Interface.py
        Interface.main_interface(OCV.TK_MAIN)

        ctl = OCV.CD["controller"]
        if ctl in ("GRBL1", "GRBL0"):
            cmd.get_errors(ctl)
            cmd.get_settings(ctl)
        else:
            OCV.CTL_ERRORS = []
            OCV.CTL_SHELP = []

        OCV.iface_widgets.append(OCV.TK_CMD_W)

        # remember some widgets
        self.dro = Page.frames["DRO"]
        self.gstate = Page.frames["State"]
        self.control = Page.frames["Control"]

        # Left side
        for name in IniFile.get_str(OCV.PRG_NAME, "ribbon").split():
            last = name[-1]
            if last == '>':
                name = name[:-1]
                side = Tk.RIGHT
            else:
                side = Tk.LEFT
                
            OCV.TK_RIBBON.addPage(self.pages[name], side)

        # Restore last page
        # Select "Probe:Probe" tab to show the dialogs!
        self.pages["Probe"].tabChange()
        OCV.TK_RIBBON.changePage(IniFile.get_str(OCV.PRG_NAME, "page", "File"))

        tkExtra.bindEventData(
            self, "<<OrientSelect>>",
            lambda e,
            f=Page.frames["Probe:Probe"]: f.selectMarker(int(e.data)))

        tkExtra.bindEventData(
            self, '<<OrientChange>>',
            lambda e, s=self: OCV.TK_CANVAS.orientChange(int(e.data)))

        self.bind('<<OrientUpdate>>', Page.frames["Probe:Probe"].orientUpdate)

        #--- Bindings
        # most of assignements are done in Bindings.
        # Some are here due to the way they are defined
        
        Bindings.Bindings()

        for i_wdg in OCV.iface_widgets:
            if isinstance(i_wdg, Tk.Entry):
                i_wdg.bind("<Escape>", self.canvasFocus)

        self.bind('<<TerminalClear>>', Page.frames["Terminal"].clear)

        #--- Probe Bindings
        frame = Page.frames["Probe:Tool"]

        self.bind('<<ToolCalibrate>>', frame.calibrate)
        self.bind('<<ToolChange>>', frame.change)

        alevel = Page.frames["Probe:Autolevel"]

        self.bind('<<AutolevelMargins>>', alevel.getMargins)
        self.bind('<<AutolevelZero>>', alevel.setZero)
        self.bind('<<AutolevelClear>>', alevel.clear)
        self.bind('<<AutolevelScan>>', alevel.scan)
        self.bind('<<AutolevelScanMargins>>', alevel.scanMargins)

        # END Bindings

        OCV.TK_CANVAS_F.canvas.focus_set()

        OCV.c_state = OCV.STATE_NOT_CONN
        OCV.CD["color"] = OCV.STATECOLOR[OCV.STATE_NOT_CONN]
        self._pendantFileUploaded = None
        self._drawAfter = None  # after handle for modification
        self._inFocus = False
        #  END - insertCount lines where ok was applied to for $xxx commands
        self._insertCount = 0
        self._selectI = 0
        self.monitorSerial()

        OCV.TK_CANVAS_F.toggleDrawFlag()

        self.paned.sash_place(0, IniFile.get_int(OCV.PRG_NAME, "sash", 340), 0)

        # Auto start pendant and serial
        if IniFile.get_bool("Connection", "pendant"):
            self.startPendant(False)

        Interface.set_debug_flags()

        if _openserial and IniFile.get_bool("Connection", "openserial"):
            self.openClose()

        # Filedialog Load history
        for i in range(OCV.maxRecent):
            filename = IniFile.get_recent_file(i)

            if filename is None:
                break

            bFileDialog.append2History(os.path.dirname(filename))

    #--- CTRL COMMANDS HERE to make them work

    def ctrl_home(self, event=None):
        """Send HOME signal to controller"""
        OCV.TK_MCTRL.home()

    def ctrl_feedhold(self, event=None):
        """Send FEED_HOLD signal to controller"""
        OCV.TK_MCTRL.feedHold(None)

    def ctrl_softreset(self, event=None):
        """Send SoftReset signal to controller"""
        OCV.TK_MCTRL.softReset(True)

    def ctrl_unlock(self, event=None):
        """Send Unlock signal to controller"""
        OCV.TK_MCTRL.unlock(True)

    #--- JOGGING

    def jog_x_up(self, event=None):
        """jog X axis up by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog("{0}{1:f}".format("X", float(OCV.stepxy)))

    def jog_x_down(self, event=None):
        """jog X axis down by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog("{0}{1:f}".format("X-", float(OCV.stepxy)))

    def jog_y_up(self, event=None):
        """jog Y axis up by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog("{0}{1:f}".format("Y", float(OCV.stepxy)))

    def jog_y_down(self, event=None):
        """jog Y axis down by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog("{0}{1:f}".format("Y-", float(OCV.stepxy)))

    def jog_x_down_y_up(self, event=None):
        """jog X axis down and Y axis up by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog(
            "{0}{1:f} {2}{3:f}".format(
                "X-", float(OCV.stepxy),
                "Y", float(OCV.stepxy)))

    def jog_x_up_y_up(self, event=None):
        """jog X axis up and Y axis up by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog(
            "{0}{1:f} {2}{3:f}".format(
                "X", float(OCV.stepxy),
                "Y", float(OCV.stepxy)))

    def jog_x_down_y_down(self, event=None):
        """jog X axis down and Y axis down by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog(
            "{0}{1:f} {2}{3:f}".format(
                "X-", float(OCV.stepxy),
                "Y-", float(OCV.stepxy)))

    def jog_x_up_y_down(self, event=None):
        """jog X axis up and Y axis down by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog(
            "{0}{1:f} {2}{3:f}".format(
                "X", float(OCV.stepxy),
                "Y-", float(OCV.stepxy)))

    def jog_z_up(self, event=None):
        """jog Z axis up by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog("{0}{1:f}".format("Z", float(OCV.stepz)))

    def jog_z_down(self, event=None):
        """jog Z axis down by defined step"""
        if event is not None and not self.acceptKey():
            return
        OCV.TK_MCTRL.jog("{0}{1:f}".format("Z-", float(OCV.stepz)))

    #--- STEP CONTROL

    def cycle_up_step_xy(self, event=None):
        """Increase predefined XY_Step"""
        if event is not None and not self.acceptKey():
            return

        OCV.pstep_xy += 1

        if OCV.pstep_xy > len(OCV.pslist_xy) - 1:
            OCV.pstep_xy = 0

        OCV.stepxy = OCV.pslist_xy[OCV.pstep_xy]
        print("csxy = {0:.4f}".format(OCV.stepxy))
        self.control.set_step_view(OCV.stepxy, OCV.stepz)


    def cycle_dw_step_xy(self, event=None):
        """Decrease predefined XY_Step"""
        if event is not None and not self.acceptKey():
            return

        OCV.pstep_xy -= 1

        if OCV.pstep_xy < 0:
            OCV.pstep_xy = len(OCV.pslist_xy) - 1

        OCV.stepxy = OCV.pslist_xy[OCV.pstep_xy]
        print("csxy = {0:.4f}".format(OCV.stepxy))
        self.control.set_step_view(OCV.stepxy, OCV.stepz)

    def cycle_up_step_z(self, event=None):
        """Increase predefined Z_Step"""
        if event is not None and not self.acceptKey():
            return

        OCV.pstep_z += 1

        if OCV.pstep_z > len(OCV.pslist_z) - 1:
            OCV.pstep_z = 0

        OCV.stepz = OCV.pslist_z[OCV.pstep_z]
        self.control.set_step_view(OCV.stepxy, OCV.stepz)

    def cycle_dw_step_z(self, event=None):
        """Decrease predefined Z_Step"""
        if event is not None and not self.acceptKey():
            return

        OCV.pstep_z -= 1

        if OCV.pstep_z < 0:
            OCV.pstep_z = len(OCV.pslist_z) - 1

        OCV.stepz = OCV.pslist_z[OCV.pstep_z]
        self.control.set_step_view(OCV.stepxy, OCV.stepz)

    #--- CAM COMMANDS

    def mop_ok(self, event=None):
        """Execute CAM Commands
        Validation checks are done in Utils.MOPWindow"""

        CAMGen.mop(self, OCV.TK_MAIN, "mem_0", "mem_1", OCV.mop_vars["type"])
 
    #---

    def setStatus(self, msg, force_update=False):
        """Update Text in StatusBar"""
        OCV.TK_STATUSBAR.configText(text=msg, fill="DarkBlue")
        if force_update:
            OCV.TK_STATUSBAR.update_idletasks()
            OCV.TK_BUFFERBAR.update_idletasks()

    def updateStatus(self, event):
        """Set status message from an event"""
        self.setStatus(_(event.data))

    #--- Memory Actions

    def setMem(self, event=None):
        """Set memory position"""
        OCV.TK_CANVAS_F.canvas.memDraw(OCV.WK_mem)
        OCV.WK_active_mems[OCV.WK_mem] = 2

    def clrMem(self, event=None):
        """Clear Memory marker"""
        OCV.TK_CANVAS_F.canvas.memDelete(OCV.WK_mem)
        OCV.WK_active_mems[OCV.WK_mem] = 1

    def saveMems(self, event=None):
        """Save memories in Ini file"""
        IniFile.save_memories()

    def ToggleMems(self):
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
                        OCV.TK_MAIN.event_generate("<<ClrMem>>")
                    else:
                        OCV.TK_MAIN.event_generate("<<SetMem>>")        

    #--- Canvas Actions

    def updateCanvasCoords(self, event):
        """Update canvas coordinates"""
        x, y, z = event.data.split()
        self.statusx["text"] = "X: "+x
        self.statusy["text"] = "Y: "+y
        self.statusz["text"] = "Z: "+z

    def viewChange(self, event=None):
        """Redraw Canvas"""
        if OCV.s_running:
            self._selectI = 0    # last selection pointer in items
        self.draw()

    def refresh(self, event=None):
        """Refresh Canvas"""
        OCV.TK_EDITOR.fill()
        self.draw()

    def draw(self):
        """Draw Canvas"""
        view = CNCCanvas.VIEWS.index(OCV.TK_CANVAS_F.view.get())
        OCV.TK_CANVAS_F.canvas.draw(view)
        self.selectionChange()

    def drawAfter(self, event=None):
        """Redraw with a small delay"""
        if self._drawAfter is not None:
            self.after_cancel(self._drawAfter)

        self._drawAfter = self.after(DRAW_AFTER, self.draw)
        return "break"

    def canvasFocus(self, event=None):
        """Set Focus on Canvas"""
        OCV.TK_CANVAS_F.canvas.focus_set()
        return "break"


    def entry(self, message="Enter value", title="", prompt="", type_="str",
              from_=None, to_=None):
        """Show popup dialog asking for value entry
           usefull in g-code scripts"""
        d = tkDialogs.InputDialog(
            self, title, message, prompt, type_, from_, to_)

        v = d.show()

        if isinstance(v, basestring):
            v = v.strip()
        print("entered "+str(type(v))+": "+str(v))
        return v

    def acceptKey(self, skipRun=False):
        """Accept the user key if not editing any text"""
        if not skipRun and OCV.s_running:
            return False
        focus = self.focus_get()
        if isinstance(focus, Tk.Entry) or isinstance(focus, Tk.Spinbox) or \
           isinstance(focus, Tk.Listbox) or isinstance(focus, Tk.Text):
            return False

        return True

    def configWidgets(self, var, value):
        """Configure Interface Widgets"""
        for w in OCV.iface_widgets:
            if isinstance(w, tuple):
                try:
                    w[0].entryconfig(w[1], state=value)
                except Tk.TclError:
                    pass
            elif isinstance(w, tkExtra.Combobox):
                w.configure(state=value)
            else:
                w[var] = value

    def busy(self):
        """"Set cursor to Busy"""
        try:
            self.config(cursor="watch")
            self.update_idletasks()
        except Tk.TclError:
            pass

    def notBusy(self):
        """"Set cursor Not Busy"""
        try:
            self.config(cursor="")
        except Tk.TclError:
            pass

    def enable(self):
        """Enable Widget"""
        self.configWidgets("state", Tk.NORMAL)
        OCV.TK_STATUSBAR.clear()
        OCV.TK_STATUSBAR.config(background="LightGray")
        OCV.TK_BUFFERBAR.clear()
        OCV.TK_BUFFERBAR.config(background="LightGray")
        OCV.TK_BUFFERBAR.setText("")

    def disable(self):
        """Disable Widget"""
        self.configWidgets("state", Tk.DISABLED)

    #--- Editor Actions

    def cut(self, event=None):
        """Editor cut"""
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_EDITOR.cut()
            return "break"

    def copy(self, event=None):
        """Editor copy"""
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_EDITOR.copy()
            return "break"

    def paste(self, event=None):
        """Editor paste"""
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_EDITOR.paste()
            return "break"

    def undo(self, event=None):
        """Editor undo"""
        if not OCV.s_running and self.gcode.canUndo():
            self.gcode.undo()
            OCV.TK_EDITOR.fill()
            self.drawAfter()
        return "break"

    def redo(self, event=None):
        """Editor redo"""
        if not OCV.s_running and self.gcode.canRedo():
            self.gcode.redo()
            OCV.TK_EDITOR.fill()
            self.drawAfter()
        return "break"

    def ClearEditor(self, event=None):
        """Clear Editor"""
        self.clear_editor()

    def addUndo(self, undoinfo):
        """Add Undoinfo to gcode"""
        self.gcode.addUndo(undoinfo)

    def about_box(self, event=None, timer=None):
        """About Window"""
        Utils.about_win(timer)

    def help_box(self, event=None):
        """Show an help box as an Html Window
            using the content in OKKCBC,help file"""
        h_win = Utils.TEditorWindow(OCV.TK_MAIN,0)
        h_win.open_file(OCV.HELP_FILE)
        h_win.set_title("Help")
        h_win.fileName['text'] = ""        

    def closeFunc(self, event=None):
        """Calls destroy in Main Window"""
        OCV.TK_MAIN.destroy()

    def quit(self, event=None):
        """Exit from Program"""
        if OCV.s_running and self._quit < 1:
            tkMessageBox.showinfo(
                _("Running"),
                _("CNC is currently running, please stop it before."),
                parent=self)
            self._quit += 1
            return
        del OCV.iface_widgets[:]

        if self.fileModified():
            return

        OCV.TK_CANVAS_F.canvas.cameraOff()
        Sender.quit(self)
        self.saveConfig()
        self.destroy()

        if OCV.errors and OCV.error_report:
            # Don't send report dialog
            # Infrastructure not (yet) created
            # Utils.ReportDialog.sendErrorReport()
            pass

        OCV.TK_ROOT.destroy()

    def alarmClear(self, event=None):
        """Clear OCV.s_alarm"""
        OCV.s_alarm = False

    def showInfo(self, event=None):
        """Display information on selected blocks"""
        OCV.TK_CANVAS_F.canvas.showInfo(OCV.TK_EDITOR.getSelectedBlocks())
        return "break"

    def showStats(self, event=None):
        """Display statistics on enabled blocks"""
        Interface.show_stats()

    def show_error_panel(self, event=None):
        """Show controller error panel"""
        Interface.show_error_panel()

    def show_settings_panel(self, event=None):
        """Show settings panel"""
        Interface.show_settings_panel()
        
    def selectAll(self, event=None):
        """Editor Select All"""
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_EDITOR.copy()
            OCV.TK_RIBBON.changePage("Editor")
            OCV.TK_EDITOR.selectAll()
            self.selectionChange()
            return "break"

    def unselectAll(self, event=None):
        """Editor Unselect All"""
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_RIBBON.changePage("Editor")
            OCV.TK_EDITOR.selectClear()
            self.selectionChange()
            return "break"

    def selectInvert(self, event=None):
        """EditorIvert  selection"""        
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_RIBBON.changePage("Editor")
            OCV.TK_EDITOR.selectInvert()
            self.selectionChange()
            return "break"

    def selectLayer(self, event=None):
        """Editor Select Layer"""        
        focus = self.focus_get()
        if focus in (OCV.TK_CANVAS_F.canvas, OCV.TK_EDITOR):
            OCV.TK_RIBBON.changePage("Editor")
            OCV.TK_EDITOR.selectLayer()
            self.selectionChange()
            return "break"

    def find(self, event=None):
        """Editor Find TO BE DONE"""        
        OCV.TK_RIBBON.changePage("Editor")
#        OCV.TK_EDITOR.findDialog()
#        return "break"

    def findNext(self, event=None):
        """Editor Find Next TO BE DONE"""                
        OCV.TK_RIBBON.changePage("Editor")
#        OCV.TK_EDITOR.findNext()
#        return "break"

    def replace(self, event=None):
        """Editor Replace TO BE DONE"""                
        OCV.TK_RIBBON.changePage("Editor")
#        OCV.TK_EDITOR.replaceDialog()
#        return "break"

    def activeBlock(self):
        """Return editor active Block
        Used in CAMGen"""                
        return OCV.TK_EDITOR.activeBlock()

    def cmdExecute(self, event):
        """Keyboard binding to <Return> in Command Window"""
        self.commandExecute()

    def insertCommand(self, cmd, execute=False):
        """Insert command in Command Window"""        
        OCV.TK_CMD_W.delete(0, Tk.END)
        OCV.TK_CMD_W.insert(0, cmd)

        if execute:
            self.commandExecute(False)

    def commandExecute(self, addHistory=True):
        """Execute command from Command Window"""
        self._historyPos = None
        self._historySearch = None

        line = OCV.TK_CMD_W.get().strip()
        if not line:
            return

        if self._historyPos is not None:
            if OCV.history[self._historyPos] != line:
                OCV.history.append(line)
        elif not OCV.history or OCV.history[-1] != line:
            OCV.history.append(line)

        if len(OCV.history) > MAX_HISTORY:
            OCV.history.pop(0)
        OCV.TK_CMD_W.delete(0, Tk.END)
        self.execute(line)

    def execute(self, line):
        """Execute a single command"""
        try:
            line = self.evaluate(line)
        except:
            tkMessageBox.showerror(
                _("Evaluation error"),
                sys.exc_info()[1], parent=self)
            return "break"
#        print ">>>",line

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
            OCV.TK_RIBBON.changePage("Terminal")
            Page.frames["Terminal"].clear()

        # CLOSE: close path - join end with start with a line segment
        elif rexx.abbrev("CLOSE", cmd, 4):
            self.executeOnSelection("CLOSE", True)

        # CONT*ROL: switch to control tab
        elif rexx.abbrev("CONTROL", cmd, 4):
            OCV.TK_RIBBON.changePage("Control")

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

            self.executeOnSelection(
                "CUT", True, depth, step, surface, feed, feedz)

        # DOWN: move downward in cutting order the selected blocks
        # UP: move upwards in cutting order the selected blocks
        elif cmd == "DOWN":
            OCV.TK_EDITOR.orderDown()
        elif cmd == "UP":
            OCV.TK_EDITOR.orderUp()

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

        elif cmd == "ECHO":
            """ECHO <msg>: echo message"""
            self.setStatus(oline[5:].strip())

        elif cmd == "FEED":
            """
            FEED on/off:
            append feed commands on every motion line for feed override testing
            """

            try:
                OCV.appendFeed = (line[1].upper() == "ON")
            except:
                OCV.appendFeed = True
            self.setStatus(OCV.appendFeed and
                           "Feed appending turned on" or
                           "Feed appending turned off")

        # INV*ERT: invert selected blocks
        elif rexx.abbrev("INVERT", cmd, 3):
            OCV.TK_EDITOR.invertBlocks()

        # MSG|MESSAGE <msg>: echo message
        elif cmd in ("MSG", "MESSAGE"):
            tkMessageBox.showinfo(
                "Message",
                oline[oline.find(" ")+1:].strip(),
                parent=self)

        # FIL*TER: filter editor blocks with text
        elif rexx.abbrev("FILTER", cmd, 3) or cmd == "ALL":
            try:
                OCV.TK_EDITOR.filter = line[1]
            except:
                OCV.TK_EDITOR.filter = None
            OCV.TK_EDITOR.fill()

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
                OCV.TK_EDITOR.selectAll()
            self.executeOnSelection("INKSCAPE", True)

        # ISO1: switch to ISO1 projection
        elif cmd == "ISO1":
            OCV.TK_CANVAS_F.viewISO1()
        # ISO2: switch to ISO2 projection
        elif cmd == "ISO2":
            OCV.TK_CANVAS_F.viewISO2()
        # ISO3: switch to ISO3 projection
        elif cmd == "ISO3":
            OCV.TK_CANVAS_F.viewISO3()

        # LO*AD [filename]: load filename containing g-code
        elif rexx.abbrev("LOAD", cmd, 2) and len(line) == 1:
            self.loadDialog()

        elif rexx.abbrev("MIRROR", cmd, 3):

            if len(line) == 1:
                return "break"

            line1 = line[1].upper()
            # if nothing is selected:
            if not OCV.TK_EDITOR.curselection():
                OCV.TK_EDITOR.selectAll()
            if rexx.abbrev("HORIZONTAL", line1):
                self.executeOnSelection("MIRRORH", False)
            elif rexx.abbrev("VERTICAL", line1):
                self.executeOnSelection("MIRRORV", False)

        elif rexx.abbrev("ORDER", cmd, 2):
            if line[1].upper() == "UP":
                OCV.TK_EDITOR.orderUp()
            elif line[1].upper() == "DOWN":
                OCV.TK_EDITOR.orderDown()

        # MO*VE [|CE*NTER|BL|BR|TL|TR|UP|DOWN|x] [[y [z]]]:
        # move selected objects either by mouse or by coordinates
        elif rexx.abbrev("MOVE", cmd, 2):
            if len(line) == 1:
                OCV.TK_CANVAS_F.canvas.setActionMove()
                return "break"
            line1 = line[1].upper()
            dz = 0.0
            if rexx.abbrev("CENTER", line1, 2):
                dx = -(OCV.CD["xmin"] + OCV.CD["xmax"])/2.0
                dy = -(OCV.CD["ymin"] + OCV.CD["ymax"])/2.0
                OCV.TK_EDITOR.selectAll()
            elif line1 == "BL":
                dx = -OCV.CD["xmin"]
                dy = -OCV.CD["ymin"]
                OCV.TK_EDITOR.selectAll()
            elif line1 == "BC":
                dx = -(OCV.CD["xmin"] + OCV.CD["xmax"])/2.0
                dy = -OCV.CD["ymin"]
                OCV.TK_EDITOR.selectAll()
            elif line1 == "BR":
                dx = -OCV.CD["xmax"]
                dy = -OCV.CD["ymin"]
                OCV.TK_EDITOR.selectAll()
            elif line1 == "TL":
                dx = -OCV.CD["xmin"]
                dy = -OCV.CD["ymax"]
                OCV.TK_EDITOR.selectAll()
            elif line1 == "TC":
                dx = -(OCV.CD["xmin"] + OCV.CD["xmax"])/2.0
                dy = -OCV.CD["ymax"]
                OCV.TK_EDITOR.selectAll()
            elif line1 == "TR":
                dx = -OCV.CD["xmax"]
                dy = -OCV.CD["ymax"]
                OCV.TK_EDITOR.selectAll()
            elif line1 == "LC":
                dx = -OCV.CD["xmin"]
                dy = -(OCV.CD["ymin"] + OCV.CD["ymax"])/2.0
                OCV.TK_EDITOR.selectAll()
            elif line1 == "RC":
                dx = -OCV.CD["xmax"]
                dy = -(OCV.CD["ymin"] + OCV.CD["ymax"])/2.0
                OCV.TK_EDITOR.selectAll()
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
            if not OCV.TK_EDITOR.curselection():
                tkMessageBox.showinfo(
                    _("Optimize"),
                    _("Please select the blocks of gcode you want to optimize."),
                    parent=self)
            else:
                self.executeOnSelection("OPTIMIZE", True)

        # OPT*IMIZE: reorder selected blocks to minimize rapid motions
        elif rexx.abbrev("ORIENT", cmd, 4):
            if not OCV.TK_EDITOR.curselection():
                OCV.TK_EDITOR.selectAll()
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

            OCV.TK_EDITOR.selectAll()
            self.executeOnSelection("MOVE", False, dx, dy, dz)

        # ROT*ATE [CCW|CW|FLIP|ang] [x0 [y0]]: rotate selected blocks
        # counter-clockwise(90) / clockwise(-90) / flip(180)
        # 90deg or by a specific angle and a pivot point
        elif rexx.abbrev("ROTATE", cmd, 3):
            line1 = line[1].upper()
            x0 = y0 = 0.0
            if line1 == "CCW":
                ang = 90.0
                # OCV.TK_EDITOR.selectAll()
            elif line1 == "CW":
                ang = -90.0
                # OCV.TK_EDITOR.selectAll()
            elif line1 == "FLIP":
                ang = 180.0
                # OCV.TK_EDITOR.selectAll()
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
                    OCV.TK_EDITOR.selectAll()
                else:
                    try:
                        acc = int(line[1])
                    except:
                        pass
            self.executeOnSelection("ROUND", False, acc)

        # RU*LER: measure distances with mouse ruler
        elif rexx.abbrev("RULER", cmd, 2):
            OCV.TK_CANVAS_F.canvas.setActionRuler()

        # STAT*ISTICS: show statistics of current job
        elif rexx.abbrev("STATISTICS", cmd, 4):
            self.showStats()

        # STEP [s]: set motion step size to s
        elif cmd == "STEP":
            try:
                self.control.set_step_view(float(line[1]))
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
            OCV.TK_RIBBON.changePage("Terminal")

        # TOOL [diameter]: set diameter of cutting tool
        elif cmd in ("BIT", "TOOL", "MILL"):
            try:
                diam = float(line[1])
            except:
                tool = self.tools["EndMill"]
                diam = self.tools.fromMm(tool["diameter"])
            self.setStatus(_("EndMill: {0} {1}").format(tool["name"], diam))

        # TOOLS
        elif cmd == "TOOLS":
            OCV.TK_RIBBON.changePage("Tools")

        # UNL*OCK: unlock grbl
        elif rexx.abbrev("UNLOCK", cmd, 3):
            OCV.TK_MCTRL.unlock(True)

        # US*ER cmd: execute user command, cmd=number or name
        elif rexx.abbrev("USER", cmd, 2):
            n = IniFile.get_int("Buttons", "n", 6)
            try:
                idx = int(line[1])
            except:
                try:
                    name = line[1].upper()
                    for i in range(n):
                        if name == IniFile.get_str(
                                "Buttons",
                                "name. {0:d}".format(i), "").upper():
                            idx = i
                            break
                except:
                    return "break"
            if idx < 0 or idx >= n:
                self.setStatus(_("Invalid user command {0}").format(line[1]))
                return "break"
            cmd = IniFile.get_str("Buttons", "command. {0:d}".format(idx), "")
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
            OCV.TK_CANVAS_F.viewXY()

        # XZ: switch to XZ view
        # ZX: switch to XZ view
        elif cmd in ("XZ", "ZX"):
            OCV.TK_CANVAS_F.viewXZ()

        # YZ: switch to YZ view
        # ZY: switch to YZ view
        elif cmd in ("YZ", "ZY"):
            OCV.TK_CANVAS_F.viewYZ()

        else:
            rc = self.executeCommand(oline)
            if rc:
                tkMessageBox.showerror(rc[0], rc[1], parent=self)
            return "break"

    def executeOnSelection(self, cmd, blocksonly, *args):
        """Execute a command over the selected lines"""
        if blocksonly:
            items = OCV.TK_EDITOR.getSelectedBlocks()
        else:
            items = OCV.TK_EDITOR.getCleanSelection()
        if not items:
            tkMessageBox.showwarning(
                _("Nothing to do"),
                _("Operation %s requires some gcode to be selected")%(cmd),
                parent=self)
            return

        self.busy()
        sel = None

        undoinfo = None  # all operations should return undo information

        if cmd == "AUTOLEVEL":
            sel = self.gcode.autolevel(items)
        elif cmd == "CUT":
            sel = self.gcode.cut(items, *args)
        elif cmd == "CLOSE":
            sel = self.gcode.close(items)
        elif cmd == "DRILL":
            sel = self.gcode.drill(items, *args)
        elif cmd == "ORDER":
            self.gcode.orderLines(items, *args)
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
        elif cmd == "ROUND":
            self.gcode.roundLines(items, *args)
        elif cmd == "ROTATE":
            self.gcode.rotateLines(items, *args)

        # Fill listbox and update selection
        OCV.TK_EDITOR.fill()
        if sel is not None:
            if isinstance(sel, str):
                tkMessageBox.showerror(_("Operation error"), sel, parent=self)
            else:
                OCV.TK_EDITOR.select(sel, clear=True)
        self.drawAfter()
        self.notBusy()
        self.setStatus("{0} {1}".format(cmd, " ".join(
            [str(a) for a in args if a is not None])))

    def edit(self, event=None):
        """Edit event for "Editor" and "Tools"  Pages """
        page = OCV.TK_RIBBON.getActivePage()
        if page.name == "Editor":
            OCV.TK_EDITOR.edit()
        elif page.name == "Tools":
            page.edit()

    def commandFocus(self, event=None):
        """Set focus on Command Window"""
        OCV.TK_CMD_W.focus_set()

    def commandFocusIn(self, event=None):
        """Set active color on Command Window"""
        self.cmdlabel["foreground"] = "Blue"

    def commandFocusOut(self, event=None):
        """Set inactive color on Command Window"""        
        self.cmdlabel["foreground"] = "Black"

    def commandKey(self, event):
        """Command Window Keypress"""        
        # FIXME: why it is not called?
        if event.char or event.keysym in ("BackSpace",):
            self._historyPos = None
            self._historySearch = None

    def commandHistoryUp(self, event=None):
        """Command Window History Up"""
        if self._historyPos is None:
            s = OCV.TK_CMD_W.get()
            if OCV.history:
                self._historyPos = len(OCV.history)-1
            else:
                self._historySearch = None
                return
            if s and self._historySearch is None:
                self._historySearch = s.strip().upper()
        else:
            self._historyPos = max(0, self._historyPos-1)

        if self._historySearch:
            for i in range(self._historyPos, -1, -1):
                h = OCV.history[i]
                if h.upper().startswith(self._historySearch):
                    self._historyPos = i
                    break

        OCV.TK_CMD_W.delete(0, Tk.END)
        OCV.TK_CMD_W.insert(0, OCV.history[self._historyPos])

    def commandHistoryDown(self, event=None):
        """Command Window History Down"""        
        if self._historyPos is None:
            self._historySearch = None
            return
        else:
            self._historyPos += 1
            if self._historyPos >= len(OCV.history):
                self._historyPos = None
                self._historySearch = None

        if self._historySearch:
            for i in range(self._historyPos, len(OCV.history)):
                h = OCV.history[i]
                if h.upper().startswith(self._historySearch):
                    self._historyPos = i
                    break

        OCV.TK_CMD_W.delete(0, Tk.END)
        if self._historyPos is not None:
            OCV.TK_CMD_W.insert(0, OCV.history[self._historyPos])

    def select(self, items, double, clear, toggle=True):
        """Editor Selection"""
        OCV.TK_EDITOR.select(items, double, clear, toggle)
        self.selectionChange()

    def selectionChange(self, event=None):
        """Selection has changed highlight the canvas"""
        items = OCV.TK_EDITOR.getSelection()
        OCV.TK_CANVAS_F.canvas.clearSelection()

        if not items:
            return

        OCV.TK_CANVAS_F.canvas.select(items)
        OCV.TK_CANVAS_F.canvas.activeMarker(OCV.TK_EDITOR.getActive())

    def newFile(self, event=None):
        """Create a new file"""
        if OCV.s_running:
            return

        if self.fileModified():
            return

        self.gcode.init()
        self.gcode.headerFooter()
        OCV.TK_EDITOR.fill()
        self.draw()
        self.title("{0}{1}".format(OCV.PRG_NAME, OCV.PRG_VER))

    def loadDialog(self, event=None):
        """Load dialog"""
        if OCV.s_running:
            return

        inipos = os.path.join(
                IniFile.get_str("File", "dir"),
                IniFile.get_str("File", "file"))

        # DEBUG info do not remove
        # print(inipos)

        filename = bFileDialog.askopenfilename(
            master=self,
            title=_("Open file"),
            initialfile=inipos,
            filetypes=FILETYPES)

        if filename:
            self.load(filename)
            IniFile.save_lastfile(filename)

        return "break"

    def saveDialog(self, event=None):
        """Save dialog"""
        if OCV.s_running:
            return

        fn, ext = os.path.splitext(IniFile.get_str("File", "file"))

        filename = bFileDialog.asksaveasfilename(
            master=self,
            title=_("Save file"),
            initialfile=os.path.join(IniFile.get_str("File", "dir"), fn+ext),
            filetypes=FILETYPES)

        if filename:
            self.save(filename)

        return "break"

    def fileModified(self):
        """Ask to save the file if Gcode is modified after loaded"""
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
            # Page.frames["Probe:Autolevel"] = alevel
            alevel.setValues()
            self.event_generate("<<DrawProbe>>")

        elif ext == ".orient":
            self.event_generate("<<DrawOrient>>")
            self.event_generate("<<OrientSelect>>", data=0)
            self.event_generate("<<OrientUpdate>>")

        else:
            OCV.TK_EDITOR.selectClear()
            self.reset_canvas()
            Page.frames["Tools"].populate()

        if autoloaded:
            self.setStatus(
                _("'{0}' reloaded at '{1}'").format(
                    filename,
                    str(datetime.now())))
        else:
            self.setStatus(_("'{0}' loaded").format(filename))

        self.title("{0}{1}: {2}".format(
            OCV.PRG_NAME, OCV.PRG_VER, self.gcode.filename))

    def save(self, filename):
        """Save file"""
        Sender.save(self, filename)

        self.setStatus(_("'{0}' saved").format(filename))

        self.title("{0}{1}: {2}".format(
            OCV.PRG_NAME, OCV.PRG_VER, self.gcode.filename))

    def saveAll(self, event=None):
        """Save all open files"""
        if self.gcode.filename:
            Sender.saveAll(self)
        else:
            self.saveDialog()
        return "break"

    def reload(self, event=None):
        """Reload gcode file in editor"""
        self.load(self.gcode.filename)

    def importFile(self, filename=None):
        """Import a file in Program"""
        if filename is None:
            filename = bFileDialog.askopenfilename(
                master=self,
                title=_("Import Gcode file"),
                initialfile=os.path.join(
                    IniFile.get_str("File", "dir"),
                    IniFile.get_str("File", "file")),
                filetypes=[
                    (_("G-Code"), ("*.ngc", "*.nc", "*.gcode")),
                    ("All", "*")])
        if filename:
            fn, ext = os.path.splitext(filename)
            ext = ext.lower()
            gcode = GCode.GCode()
            gcode.load(filename)
            sel = OCV.TK_EDITOR.getSelectedBlocks()

            if not sel:
                pos = None
            else:
                pos = sel[-1]

            self.addUndo(self.gcode.insBlocksUndo(pos, gcode.blocks))
            del gcode
            self.reset_canvas()

    def clear_gcode(self):
        """Clear GCode lines stored after parsing a filename.
        mainly used to avoid importing GCode in CAMGen
        """

        self.gcode = GCode.GCode()

    def reset_canvas(self):
        """Reset Canvas
        used here and in CAMGen"""
        OCV.TK_EDITOR.fill()
        OCV.TK_CANVAS_F.canvas.reset()
        self.draw()
        OCV.TK_CANVAS_F.canvas.fit2Screen()

    def clear_editor(self):
        OCV.TK_EDITOR.selectClear()
        OCV.TK_EDITOR.selectAll()
        if len(OCV.blocks) > 0:
            OCV.TK_EDITOR.deleteBlock()

    def focus_in(self, event):
        """manage focus in..."""

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

    #--- Run GCode

    def checkStop(self):
        """An entry function should be called periodically during compiling
        to check if the Pause or Stop buttons are pressed
        @return true if the compile has to abort
        """

        try:
            self.update()  # very tricky function of Tk
        except Tk.TclError:
            pass
        
        return OCV.s_stop

    def run(self, lines=None):
        """Send enabled gcode file to CNC machine """

        if OCV.HAS_SERIAL is False and not OCV.developer:
            tkMessageBox.showerror(
                _("Serial Error"),
                _("Serial is not connected"),
                parent=self)
            return

        if OCV.s_running:
            if OCV.s_pause:
                self.resume()
                return
            tkMessageBox.showerror(
                _("Already running"),
                _("Please stop before"),
                parent=self)
            return

        # probably is better to assign cleanAfter here, as there are changes
        # that the two conditiong above reject the run request
        self.cleanAfter = True  # Clean when this operation stops
        print("RUN: Will clean after this operation")

        OCV.TK_EDITOR.selectClear()
        self.selectionChange()

        # the buffer of the machine should be empty?
        self.initRun()
        OCV.TK_CANVAS_F.canvas.clearSelection()
        # WARNING _runLines is used by Sender._serialIO
        # to check if we are still sending lines
        self._runLines = sys.maxsize
        self._gcount = 0  # count executed lines
        self.disp_line = -1 # reset display line counter
        self._selectI = 0  # last selection pointer in items
        self._paths = None  # temporary

        OCV.CD["errline"] = ""
        OCV.CD["running"] = True  # enable running status
        OCV.CD["_OvChanged"] = True  # force a feed change if any

        if self._onStart:
            try:
                os.system(self._onStart)
            except:
                pass

        if lines is None:
            OCV.TK_STATUSBAR.setLimits(0, 9999)
            OCV.TK_STATUSBAR.setProgress(0, 0)

            self._paths = self.gcode.comp_level(self.queue, self.checkStop)

            if self._paths is None:
                self.emptyQueue()
                self.jobDone("R")
                return
            elif not self._paths:
                self.runEnded("run No GCode Loaded")
                tkMessageBox.showerror(
                    _("Empty gcode"),
                    _("No gcode file was loaded"),
                    parent=self)
                return

            # reset colors
            before = time.time()
            for ij in self._paths:  # Slow loop

                if not ij:
                    continue

                path = self.gcode[ij[0]].path(ij[1])

                if path:
                    color = OCV.TK_CANVAS_F.canvas.itemcget(path, "fill")
                    if color != OCV.COLOR_ENABLE:
                        OCV.TK_CANVAS_F.canvas.itemconfig(
                            path,
                            width=1,
                            fill=OCV.COLOR_ENABLE)
                    # Force a periodic update since this loop can take time
                    if time.time() - before > 0.25:
                        self.update()
                        before = time.time()

            # the buffer of the machine should be empty?
            self._runLines = len(self._paths) + 1  # plus the wait
            #print("DBG: runlines assigned by path")
        else:
            # empty the gctos value
            OCV.gctos = []
            n = 1        # including one wait command
            for line in CNC.compile_pgm(lines):
                if line is not None:
                    if isinstance(line, str):
                        self.queue.put(line + "\n")
                        OCV.gctos.append(line)
                    else:
                        self.queue.put(line)
                        OCV.gctos.append(line)
                    n += 1
            self._runLines = n  # set it at the end to be sure that all lines are queued

        self.queue.put((OCV.GSTATE_WAIT,))  # wait at the end to become idle

        self.setStatus(_("Running..."))

        OCV.TK_STATUSBAR.setLimits(0, self._runLines)
        OCV.TK_STATUSBAR.configText(fill="White")
        OCV.TK_STATUSBAR.config(background="DarkGray")

        OCV.TK_BUFFERBAR.configText(fill="White")
        OCV.TK_BUFFERBAR.config(background="DarkGray")
        OCV.TK_BUFFERBAR.setText("")

    #--- Web Pendant

    def startPendant(self, showInfo=True):
        """Start web pendant"""

        started = Pendant.start(self)
        if showInfo:
            hostName = "http://{0}:{1:d}".format(
                socket.gethostname(), Pendant.port)

            if started:
                tkMessageBox.showinfo(
                    _("Pendant"),
                    _("Pendant started:\n")+hostName,
                    parent=self)
            else:
                ret_val = tkMessageBox.askquestion(
                    _("Pendant"),
                    _("Pendant already started:\n") \
                    + hostName + \
                    _("\nWould you like open it locally?"),
                    parent=self)
                if ret_val == "yes":
                    webbrowser.open(hostName, new=2)

    def stopPendant(self):
        """Stop web pendant"""
        if Pendant.stop():
            tkMessageBox.showinfo(
                _("Pendant"),
                _("Pendant stopped"),
                parent=self)

    #--- Serial Management

    def openClose(self, event=None):
        """Open/Close action called by button"""

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
            if self.device_open(device, baudrate):
                OCV.serial_open = True
                serialPage.connectBtn.config(
                    text=_("Close"),
                    background="LightGreen",
                    activebackground="LightGreen")
                self.enable()

    def device_open(self, device, baudrate):
        """Open serial device"""

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
        """Close Sender"""
        Sender.close(self)
        try:
            self.dro.update_state()
        except Tk.TclError:
            pass

    def _monitorSerial(self):
        """Inner loop to catch any generic exception """

        # Check serial output
        t = time.time()

        # dump in the terminal what ever you can in less than 0.1s
        inserted = False
        _last_sent = ""

        while self.log.qsize() > 0 and time.time()-t < 0.1:
            try:
                msg, line = self.log.get_nowait()
                line = str(line).rstrip("\n")
                inserted = True
                #print("msg >> ", msg)

                if msg == Sender.MSG_BUFFER:
                    OCV.TK_TERMBUF.insert(Tk.END, line)

                elif msg == Sender.MSG_SEND:
                    OCV.TK_TERMINAL.insert(Tk.END, line)
                    OCV.TK_TERMINAL.itemconfig(Tk.END, foreground="Blue")

                elif msg == Sender.MSG_RECEIVE:
                    OCV.TK_TERMINAL.insert(Tk.END, line)
                    if self._insertCount:
                        # when counting is started, then continue
                        self._insertCount += 1
                    elif line and line[0] in ("[", "$"):
                        # start the counting on the first line received
                        # starting with $ or [
                        self._insertCount = 1

                elif msg == Sender.MSG_OK:
                    if OCV.TK_TERMINAL.size() > 0:
                        if self._insertCount:
                            pos = OCV.TK_TERMINAL.size() - self._insertCount
                            self._insertCount = 0
                        else:
                            pos = Tk.END
                            
                        _last_sent = OCV.TK_TERMBUF.get(0)
                        print("MSG_OK >> {} gc > {}".format(
                            _last_sent, self._gcount))
                        OCV.TK_TERMINAL.insert(pos, _last_sent)
                        OCV.TK_TERMINAL.itemconfig(pos, foreground="Blue")
                        OCV.TK_TERMBUF.delete(0)

                    OCV.TK_TERMINAL.insert(Tk.END, line)

                elif msg == Sender.MSG_ERROR:
                    if OCV.TK_TERMINAL.size() > 0:
                        if self._insertCount:
                            pos = OCV.TK_TERMINAL.size() - self._insertCount
                            self._insertCount = 0
                        else:
                            pos = Tk.END
                            
                        _last_sent = OCV.TK_TERMBUF.get(0)
                        print("MSG_ERR >> ", _last_sent)
                        OCV.TK_TERMINAL.insert(pos, _last_sent)
                        OCV.TK_TERMINAL.itemconfig(pos, foreground="Blue")
                        OCV.TK_TERMBUF.delete(0)
                        
                    OCV.TK_TERMINAL.insert(Tk.END, line)
                    OCV.TK_TERMINAL.itemconfig(Tk.END, foreground="Red")

                elif msg == Sender.MSG_RUNEND:
                    OCV.TK_TERMINAL.insert(Tk.END, line)
                    OCV.TK_TERMINAL.itemconfig(Tk.END, foreground="Magenta")
                    self.setStatus(line)
                    self.enable()

                elif msg == Sender.MSG_CLEAR:
                    OCV.TK_TERMBUF.delete(0, Tk.END)

                else:
                    # Unknown?
                    OCV.TK_TERMBUF.insert(Tk.END, line)
                    OCV.TK_TERMINAL.itemconfig(Tk.END, foreground="Magenta")

                if OCV.TK_TERMINAL.size() > 1000:
                    OCV.TK_TERMINAL.delete(0, 500)
                    
            except Empty:
                break

        if inserted:
            OCV.TK_TERMINAL.see(Tk.END)

        # Check pendant/buttons queue
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
            try:
                OCV.CD["color"] = OCV.STATECOLOR[OCV.c_state]
            except KeyError:

                if OCV.s_alarm == True:
                    OCV.CD["color"] = OCV.STATECOLOR["Alarm"]
                else:
                    OCV.CD["color"] = OCV.STATECOLOR["Default"]

            OCV.s_pause = ("Hold" in OCV.c_state)

            self.dro.update_state()
            self.dro.update_coords()

            OCV.TK_CANVAS_F.canvas.gantry(
                OCV.CD["wx"],
                OCV.CD["wy"],
                OCV.CD["wz"],
                OCV.CD["mx"],
                OCV.CD["my"],
                OCV.CD["mz"])

            if OCV.c_state == "Run":
                self.gstate.updateFeed()

            self._posUpdate = False

        # Update status string
        if self._gUpdate:
            self.gstate.updateG()
            self._gUpdate = False

        # Update probe and draw point
        if self._probeUpdate:
            Page.frames["Probe:Probe"].updateProbe()
            Page.frames["ProbeCommon"].updateTlo()
            OCV.TK_CANVAS_F.canvas.drawProbe()
            self._probeUpdate = False

        # Update any possible variable?
        if self._update:
            if self._update == "toolheight":
                Page.frames["Probe:Tool"].updateTool()
            elif self._update == "TLO":
                Page.frames["ProbeCommon"].updateTlo()
            self._update = None

        if OCV.s_running:
            self.proc_line_n = self._runLines - self.queue.qsize()
            OCV.TK_STATUSBAR.setProgress(self.proc_line_n, self._gcount)
            OCV.CD["msg"] = OCV.TK_STATUSBAR.msg
            b_fill = Sender.getBufferFill(self)
            OCV.TK_BUFFERBAR.setProgress(b_fill)
            OCV.TK_BUFFERBAR.setText("{0:02.2f}".format(b_fill))

            if self.disp_line != self._gcount and self._gcount < len(OCV.gctos):
                show_line = "{0} > {1} ".format(
                    self._gcount, OCV.gctos[self._gcount - 1])
                self.proc_line.set(show_line)
                self.disp_line = self._gcount
                print("match ", _last_sent, show_line)

            if self._selectI >= 0 and self._paths:
                while self._selectI <= self._gcount and\
                        self._selectI < len(self._paths):

                    if self._paths[self._selectI]:
                        i, j = self._paths[self._selectI]
                        path = self.gcode[i].path(j)
                        if path:
                            OCV.TK_CANVAS_F.canvas.itemconfig(
                                path,
                                width=2,
                                fill=OCV.COLOR_PROCESS)

                    self._selectI += 1

            if self._gcount >= self._runLines:
                self.runEnded("_SM")
                self.jobDone("_SM")

            if OCV.c_pgm_end is True:
                OCV.c_pg_end = False
                self.runEnded("_PE")
                self.jobDone("_PE")

    def monitorSerial(self):
        """'thread' timed function looking for messages in the serial thread
        and reporting back in the terminal
        """
        try:
            self._monitorSerial()
        except:
            typ, val, trace_back = sys.exc_info()
            traceback.print_exception(typ, val, trace_back)
        self.after(MONITOR_AFTER, self.monitorSerial)

    #--- Configuration Management

    def loadShortcuts(self):
        """Load Shortcuts from config"""
        for name, value in OCV.config.items("Shortcut"):
            # Convert to uppercase
            key = name.title()
            self.unbind("<{0}>".format(key))    # unbind any possible old value
            if value:
                self.bind("<{0}>".format(key),
                          lambda e, s=self, c=value: s.execute(c))

    def load_main_config(self):
        """Load initial config parameters from ini file"""

        # Check version of inifile
        if IniFile.get_str(OCV.PRG_NAME,"conf_ver","") != OCV.CONF_VER:
            print("Warning!!! Configuration file mismatch")
        else:
            print("Configuration File Version OK")

        if OCV.geometry is None:
            OCV.geometry = "{0:d}x{1:d}".format(
                IniFile.get_int(OCV.PRG_NAME, "width", 900),
                IniFile.get_int(OCV.PRG_NAME, "height", 650))
        try:
            self.geometry(OCV.geometry)
        except:
            pass

        # restore windowsState
        try:
            self.wm_state(IniFile.get_str(OCV.PRG_NAME, "windowstate", "normal"))
        except:
            pass

        # read Tk fonts to initialize them
        font = Utils.get_font("TkDefaultFont")
        font = Utils.get_font("TkFixedFont")
        font = Utils.get_font("TkMenuFont")
        font = Utils.get_font("TkTextFont")

        print("Font: >", font)

        self._swapKeyboard = IniFile.get_int("Control", "swap", 0)

        self._onStart = IniFile.get_str("Events", "onstart", "")
        self._onStop = IniFile.get_str("Events", "onstop", "")

        tkExtra.Balloon.font = Utils.get_font("balloon", tkExtra.Balloon.font)

        OCV.FONT_RIBBON = Utils.get_font("ribbon.label", OCV.FONT_RIBBON)
        OCV.FONT_RIBBON_TAB = Utils.get_font("ribbon.tab", OCV.FONT_RIBBON_TAB)

        IniFile.load_colors()

        self.tools.loadConfig()
        Sender.load_sender_config(self)
        self.loadShortcuts()
        IniFile.load_memories()

    def saveConfig(self):
        """Save config values in Ini file"""
        # Program
        IniFile.set_value(OCV.PRG_NAME, "width", str(self.winfo_width()))
        IniFile.set_value(OCV.PRG_NAME, "height", str(self.winfo_height()))
        # IniFile.set_value(OCV.PRG_NAME,  "x", str(self.winfo_rootx()))
        # IniFile.set_value(OCV.PRG_NAME,  "y", str(self.winfo_rooty()))
        IniFile.set_value(
            OCV.PRG_NAME, "sash", str(self.paned.sash_coord(0)[0]))

        # WindowState
        IniFile.set_value(OCV.PRG_NAME, "windowstate", str(self.wm_state()))
        IniFile.set_value(
            OCV.PRG_NAME, "page", str(OCV.TK_RIBBON.getActivePage().name))

        # Connection
        Page.saveConfig()

        # Others

        self.tools.saveConfig()
        OCV.TK_CANVAS_F.saveConfig()
        OCV.TK_CONTROL.saveConfig()
        IniFile.save_command_history()
        IniFile.save_memories()

    @staticmethod
    def get(self, section, item):
        """get section item in configuration file"""
        return OCV.config.get(section, item)

    @staticmethod
    def set(self, section, item, value):
        """set section item in configuration file"""
        return OCV.config.set(section, item, value)

#--- App initialisation

def usage(ret_code):
    """Print on console the usage message"""
    sys.stdout.write(
        "{0} V{1} [{2}]\n".format(OCV.PRG_NAME, OCV.PRG_VER, OCV.PRG_DATE))
    sys.stdout.write("{0} <{1}>\n\n".format(OCV.AUTHOR, OCV.AUT_EMAIL))
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
    sys.stdout.write(
        "\t-R #\t\t\tLoad the recent file matching the argument\n")
    sys.stdout.write("\t-s # | --serial #\tOpen serial port specified\n")
    sys.stdout.write("\t-S\t\t\tDo not open serial port\n")
    sys.stdout.write("\t--run\t\t\tDirectly run the file once loaded\n")
    sys.stdout.write("\n")
    sys.exit(ret_code)


def main(args=None):
    """main method"""

    OCV.TK_ROOT = Tk.Tk()
    OCV.TK_ROOT.withdraw()

    Tk.CallWrapper = Utils.CallWrapper

    tkExtra.bindClasses(OCV.TK_ROOT)
    Utils.load_icons()

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
            OCV.USER_CONFIG = val
            IniFile.conf_file_load()
        elif opt == "-d":
            OCV.developer = True
        elif opt == "-D":
            OCV.developer = False
        elif opt == "-g":
            OCV.geometry = val
        elif opt in ("-r", "-R", "--recent", "-l", "--list"):
            if opt in ("-r", "--recent"):
                rec_file = 0
            elif opt in ("--list", "-l"):
                rec_file = -1
            else:
                try:
                    rec_file = int(val)-1
                except:
                    # Scan in names
                    for rec_file in range(OCV.maxRecent):
                        filename = IniFile.get_recent_file(rec_file)

                        if filename is None:
                            break

                        file_name, ext = os.path.splitext(
                            os.path.basename(filename))
                        if file_name == val:
                            break
                    else:
                        rec_file = 0
            if rec_file < 0:
                # display list of recent files
                maxlen = 10
                for idx in range(OCV.maxRecent):

                    try:
                        filename = IniFile.get_recent_file(idx)
                        # print ("Recent = ", i, maxlen, filename)
                    except:
                        continue

                    if filename is not None:
                        maxlen = max(maxlen, len(os.path.basename(filename)))

                sys.stdout.write("Recent files:\n")
                for i in range(OCV.maxRecent):
                    filename = IniFile.get_recent_file(i)

                    if filename is None:
                        break

                    dir_name = os.path.dirname(filename)
                    file_name = os.path.basename(filename)
                    sys.stdout.write(
                        "  {0:2d}: {1:d} {3}{2}\n".format(
                            i + 1, maxlen, file_name, dir_name))

                try:
                    sys.stdout.write("Select one: ")
                    rec_file = int(sys.stdin.readline())-1
                except:
                    pass
            try:
                recent = IniFile.get_recent_file(rec_file)
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
            pass # startPendant()

        elif opt == "-P":
            pass # stopPendant()

        elif opt == "--pendant":
            pass # startPendant on port

        elif opt == "--run":
            run = True

    palette = {"background": OCV.TK_ROOT.cget("background")}

    color_count = 0
    custom_color_count = 0

    for color_name in ("background", "foreground", "activeBackground",
                       "activeForeground", "disabledForeground",
                       "highlightBackground", "highlightColor",
                       "selectBackground", "selectForeground"):

        color2 = IniFile.get_str("Color", "global." + color_name.lower(), None)
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
        OCV.TK_ROOT.tk_setPalette(**palette)

    # Start application
    _application = Application(OCV.TK_ROOT)

    if fullscreen:
        _application.attributes("-fullscreen", True)

    if OCV.TITLE_MSG != "":
        # need two end of line to make the messagebox readable
        warn_msg = "\n".join(OCV.init_msg)
        tkMessageBox.showwarning("WARNING !", warn_msg)

    # Parse remaining arguments except files
    if recent:
        args.append(recent)

    for file_names in args:
        _application.load(file_names)

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
    IniFile.save_user_conf_file()


if __name__ == "__main__":
    main()

 #vim:ts=8:sw=8:sts=8:noet
