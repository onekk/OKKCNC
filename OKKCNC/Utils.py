# -*- coding: ascii -*-
"""Utils.py

This module contains some helper functions:
    - get and set the configuration from the INI file
    - some elements of the interface


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
import glob
import traceback
import gettext
import re

try:
    import __builtin__
except:
    import builtins as __builtin__

from lib.log import say

try:
    import Tkinter as Tk
    import tkFont
    import tkMessageBox
    import tkSimpleDialog
    import ConfigParser
except ImportError:
    import tkinter as Tk
    import tkinter.font as tkFont
    import tkinter.simpledialog as tkSimpleDialog
    import tkinter.messagebox as tkMessageBox
    import tkinter.ttk as ttk
    import configparser as ConfigParser
    from tkinter.filedialog import askopenfilename, asksaveasfilename

try:
    import serial
except:
    serial = None

import OCV

__builtin__._ = gettext.translation(
    'OKKCNC',
    os.path.join(OCV.PRG_PATH, 'locale'),
    fallback=True).gettext

__builtin__.N_ = lambda message: message

import IniFile
import Ribbon
import tkExtra


'''
class Config(object):
    """New class to provide config for everyone"""
    def greet(self, who=__name__):
        """print on console the """
        print("Config class loaded in {0}".format(who))
'''


def load_icons():
    """load icons and images in internal dictionaries"""
    OCV.icons = {}
    for img in glob.glob("{0}{1}icons{1}*.gif".format(OCV.PRG_PATH, os.sep)):
        name, ext = os.path.splitext(os.path.basename(img))
        try:
            OCV.icons[name] = Tk.PhotoImage(file=img)
            if IniFile.get_bool("CNC", "doublesizeicon"):
                OCV.icons[name] = OCV.icons[name].zoom(2, 2)
        except Tk.TclError:
            pass

    # Images
    OCV.images = {}
    for img in glob.glob("{0}{1}images{1}*.gif".format(OCV.PRG_PATH, os.sep)):
        name, ext = os.path.splitext(os.path.basename(img))
        try:
            OCV.images[name] = Tk.PhotoImage(file=img)
            if IniFile.get_bool("CNC", "doublesizeicon"):
                OCV.images[name] = OCV.images[name].zoom(2, 2)
        except Tk.TclError:
            pass


def del_icons():
    """empty icons and images dictionaries"""
    if len(OCV.icons) > 0:
        for i in OCV.icons.values():
            del i
        # needed otherwise it complains on deleting the icons
        OCV.icons = {}

    if len(OCV.images) > 0:
        for i in OCV.images.values():
            del i
        # needed otherwise it complains on deleting the icons
        OCV.images = {}


def font_from_string(name, value=None):
    """Return a proper tkFont from a string"""
    try:
        font = tkFont.Font(name=name, exists=True)
    except Tk.TclError:
        font = tkFont.Font(name=name)
        font.delete_font = False
    except AttributeError:
        return None

    if value is None:
        return font

    if isinstance(value, tuple):
        font.configure(family=value[0])
        try:
            font.configure(size=value[1])
        except:
            pass

        try:
            font.configure(weight=value[2])
        except:
            pass

        try:
            font.configure(slant=value[3])
        except:
            pass

    return font


def string_from_font(font):
    """Create a font string front tKFont"""
    name = str(font[0])
    size = str(font[1])

    if name.find(' ') >= 0:
        font_string = '"{0}" {1}'.format(name, size)
    else:
        font_string = '{0}, {1}'.format(name, size)

    try:
        if font[2] == tkFont.BOLD:
            font_string += " bold"
    except:
        pass
    try:
        if font[3] == tkFont.ITALIC:
            font_string += " italic"
    except:
        pass
    return font_string


def get_font(name, default=None):
    """Get font from configuration"""
    try:
        value = OCV.config.get(OCV.FONT_SEC_NAME, name)
    except:
        value = None

    if not value:
        font = font_from_string(name, default)
        set_font(name, font)
        return font

    if isinstance(value, str):
        value = tuple(value.split(','))

    if isinstance(value, tuple):
        font = font_from_string(name, value)

        if font is not None:
            return font
    return value


def set_font(name, font):
    """Set font in configuration"""
    if font is None:
        return

    if isinstance(font, str):
        OCV.config.set(OCV.FONT_SEC_NAME, name, font)
    elif isinstance(font, tuple):
        OCV.config.set(OCV.FONT_SEC_NAME, name, ",".join(map(str, font)))
    else:
        OCV.config.set(OCV.FONT_SEC_NAME, name, "{0},{1},{2}".format(
            font.cget("family"),
            font.cget("size"),
            font.cget("weight")))


def set_predefined_steps():
    """set pre defined steps used in ControlPage"""
    # Predefined XY steppings
    try:
        OCV.psxy1 = IniFile.get_float("Control", "psxy1")
    except Exception:
        OCV.psxy1 = 1.0

    try:
        OCV.psxy2 = IniFile.get_float("Control", "psxy2")
    except Exception:
        OCV.psxy2 = 1.0

    try:
        OCV.psxy3 = IniFile.get_float("Control", "psxy3")
    except Exception:
        OCV.psxy3 = 10.0

    try:
        OCV.psxy4 = IniFile.get_float("Control", "psxy4")
    except Exception:
        OCV.psxy4 = 90.0

    # Predefined Z steppings
    try:
        OCV.psz1 = IniFile.get_float("Control", "psz1")
    except Exception:
        OCV.psz1 = 0.1

    try:
        OCV.psz2 = IniFile.get_float("Control", "psz2")
    except Exception:
        OCV.psz2 = 1.0

    try:
        OCV.psz3 = IniFile.get_float("Control", "psz3")
    except Exception:
        OCV.psz3 = 5.0

    try:
        OCV.psz4 = IniFile.get_float("Control", "psz4")
    except Exception:
        OCV.psz4 = 10.0


def populate_cyclelist():
    """populate steplists with OCV.step(n) values"""
    # Predefined XY steppings
    OCV.pslist_xy = [OCV.psxy1, OCV.psxy2, OCV.psxy3, OCV.psxy4]
    OCV.pslist_z = [OCV.psz1, OCV.psz2, OCV.psz3, OCV.psz4]


def set_steps():
    """Set steps and predefined steps"""
    set_predefined_steps()
    populate_cyclelist()
    # retrieve step from config file.
    OCV.stepxy = float(OCV.config.get("Control", "xystep"))
    OCV.stepz = float(OCV.config.get("Control", "zstep"))
    
    OCV.pstep_xy = int(OCV.config.get("Control", "xystep_idx"))
    OCV.pstep_z = int(OCV.config.get("Control", "zstep_idx"))
 
def populate_tooltable():
    """Popultae tooltable list for use with CAM Buttons
    It reuse the existing EndMill data saved in inifile"""
    n_tools = IniFile.get_int("EndMill", "n", 0)
    for idx in range(0, n_tools):
        t_index = IniFile.get_int("EndMill", "number.{}".format(idx), 0)
        t_dia = IniFile.get_float("EndMill", "diameter.{}".format(idx) , 0)
        #print("Tool number: {} diameter: {}".format(t_index, t_dia))
        OCV.tooltable.append((t_index, t_dia))

    print(OCV.tooltable)

def ask_for_value(app, caller):
    """Show an input windows asking for a value
    uses tkSimpleDialog
    """
    title_d = _("Enter A Value")
    switch = {
        "S1": ("Step1", "step", 0.001, 100.0),
        "S2": ("Step2", "step", 0.001, 100.0),
        "S3": ("Step3", "step", 0.001, 100.0),
        "S4": ("Step4", "step", 0.001, 100.0),
        "ZS1": ("Z Step1", "step", 0.001, 25.0),
        "ZS2": ("Z Step2", "step", 0.001, 25.0),
        "ZS3": ("Z Step3", "step", 0.001, 25.0),
        "ZS4": ("Z Step4", "step", 0.001, 25.0),
        "ZS4": ("Z Step4", "step", 0.001, 25.0),
        "TD": (_("Enter Target Depth :"), "depth", -35.0, 0.0),
        "MN": (_("Enter Memory Number :"), "mem_num", 2, OCV.WK_mem_num),
        "ME": (_("Enter Memory {0} Description :"), "mem_desc", 0, 0),
        }

    choiche = switch.get(
        caller, (_("Enter a float Value :"), "gen_float", 0.001, 100.0))

    if choiche[1] in ("step", "depth", "gen_float"):
        if choiche[1] == "step":
            title_c = _("Enter Value for {0} :").format(choiche[0])
        else:
            title_c = choiche[0]

        prompt = "{0}\n (min: {1:.04f} max: {2:.04f})".format(
            title_c,
            choiche[2],
            choiche[3])

        retval = tkSimpleDialog.askfloat(
            title_d, prompt, parent=app,
            minvalue=choiche[2],
            maxvalue=choiche[3])

    elif choiche[1] == "mem_num":
        prompt = "{0}\n (min: {1:d} max: {2:d})".format(
            choiche[0],
            choiche[2],
            choiche[3])

        retval = tkSimpleDialog.askinteger(
            title_d, prompt, parent=app,
            minvalue=choiche[2],
            maxvalue=choiche[3])

    elif choiche[1] == "mem_desc":
        prompt = choiche[0].format(OCV.WK_mem)
        retval = tkSimpleDialog.askstring(title_d, prompt, parent=app)

    else:
        retval = None

    if retval is None:
        return None
    else:
        return retval


def comports(include_links=True):
    """Return all comports when serial.tools.list_ports is not available!"""
    locations = [
        '/dev/ttyACM',
        '/dev/ttyUSB',
        '/dev/ttyS',
        'com']

    comports = []

    for prefix in locations:
        for i in range(32):
            device = "{0}{1}".format(prefix, i)
            try:
                os.stat(device)
                comports.append((device, None, None))
            except OSError:
                pass

            # Detects windows XP serial ports
            try:
                ser_dev = serial.Serial(device)
                ser_dev.close()
                comports.append((device, None, None))
            except:
                pass
    return comports


def q_round(value, prec=2, base=.05):
    """round a number specifing the decimal digits
    and a quantization factor
    """
    return round(base * round(float(value)/base), prec)


def showState():
    print("DEBUG: Controller state: {}".format(OCV.c_state))
    print("DEBUG: stop: {} -- stop_req: {} -- running: {}".format(
        OCV.s_stop, OCV.s_stop_req,OCV.s_running))
    print("DEBUG: alarm: {} -- pause: {}".format(
        OCV.s_alarm, OCV.s_pause))


def addException():
    """collect and report exceptions"""
    # self.widget._report_exception()
    try:
        typ, val, tb = sys.exc_info()
        traceback.print_exception(typ, val, tb)

        if OCV.errors:
            OCV.errors.append("")

        exception = traceback.format_exception(typ, val, tb)
        OCV.errors.extend(exception)

        if len(OCV.errors) > 100:
            # do nothing for now
            print(OCV.errors)
    except:
        say(str(sys.exc_info()))


def about_win(timer = None):
    OCV.TK_ABOUT = Tk.Toplevel(OCV.TK_MAIN)
    OCV.TK_ABOUT.transient(OCV.TK_MAIN)
    OCV.TK_ABOUT.title(_("About {0}").format(OCV.PRG_NAME))
    if sys.platform == "win32":
        OCV.TK_MAIN.iconbitmap("OKKCNC.ico")
    else:
        OCV.TK_MAIN.iconbitmap("@{0}/OKKCNC.xbm".format(OCV.PRG_PATH))

    bg = "#707070"
    fg = "#ffffff"

    text_items = [
        ("", _("An advanced fully featured g-code sender for GRBL. \n"\
                   "Forked from bCNC")),
        ("www: ", OCV.PRG_SITE),
        ("author: ", OCV.AUTHOR),
        ("e-mail: ", OCV.AUT_EMAIL),
        ("contributors: ", OCV.PRG_CONTRIB),
        ("translations: ", OCV.PRG_TRANS),
        ("credits: ", OCV.PRG_CREDITS),
        ("version: ", OCV.PRG_VER),
        ("last change: ", OCV.PRG_DATE)
        ]

    frame = Tk.Frame(
        OCV.TK_ABOUT,
        borderwidth=2,
        relief=Tk.SUNKEN,
        background=bg)


    frame.pack(side=Tk.TOP, expand=Tk.TRUE, fill=Tk.BOTH, padx=5, pady=5)

    # -----
    row = 0

    lab = Tk.Label(
        frame,
        image=OCV.icons["OKKCNC"],
        foreground=fg,
        background=bg,
        relief=Tk.SUNKEN,
        padx=0, pady=0)

    lab.grid(row=row, column=0, columnspan=2, padx=5, pady=5)

    row += 1

    m_txt = Tk.Text(frame, wrap=Tk.WORD, font=OCV.FONT_ABOUT_TEXT)

    m_txt.tag_config(
        "title",
        font=OCV.FONT_ABOUT_TITLE,
        background="white",
        foreground="black")

    m_txt.tag_config(
        "desc",
        font=OCV.FONT_ABOUT_DESC)

    m_txt.tag_config(
        "text",
        lmargin1=20,
        lmargin2=20,
        font=OCV.FONT_ABOUT_TEXT)

    # reset the text fields
    m_txt.configure(state=Tk.NORMAL)
    m_txt.delete(1.0, Tk.END)
    
    m_txt.insert(Tk.END, "{0}".format(OCV.PRG_NAME), ('title'))

    for val in text_items:
        m_txt.insert(Tk.END, "{0} \n".format(val[0]), ('desc'))
        m_txt.insert(Tk.END, "{0} \n\n".format(val[1]) , ('text'))

    # we need to disable the text field to make it not editable
    m_txt.configure(state=Tk.DISABLED)

    m_txt.grid(row=row, column=0, columnspan=3, padx=0, pady=2)

    scrollb = Tk.Scrollbar(frame, orient=Tk.VERTICAL, command=m_txt.yview)
    scrollb.grid(row=row, column=3, sticky= Tk.NSEW, padx=0, pady=0)
    m_txt['yscrollcommand'] = scrollb.set

    closeAbout = lambda e=None, t=OCV.TK_ABOUT: t.destroy()

    row += 1

    but = Tk.Button(frame, text=_("Close"), command=closeAbout)
    but.grid(row=row, column=1, sticky= Tk.NS, padx=5, pady=5)

    frame.grid_columnconfigure(0, weight=1)

    OCV.TK_ABOUT.bind('<Escape>', closeAbout)
    OCV.TK_ABOUT.bind('<Return>', closeAbout)
    OCV.TK_ABOUT.bind('<KP_Enter>', closeAbout)

    OCV.TK_ABOUT.deiconify()
    OCV.TK_ABOUT.wait_visibility()
    OCV.TK_ABOUT.resizable(False, False)

    try:
        OCV.TK_ABOUT.grab_set()
    except:
        pass

    but.focus_set()
    OCV.TK_ABOUT.lift()

    if timer:
        OCV.TK_ABOUT.after(timer, closeAbout)

    OCV.TK_ABOUT.wait_window()


class CallWrapper(object):
    """Replaces the Tkinter.CallWrapper with extra functionality"""
    def __init__(self, func, subst, widget):
        """Store FUNC, SUBST and WIDGET as members."""
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        """Apply first function SUBST to arguments, than FUNC."""
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        # One possible fix is to make an external file for the wrapper
        # and import depending the version
#        except SystemExit, msg:    # python2.4 syntax
#        except SystemExit as msg:    # python3 syntax
        #    raise SystemExit(msg)
        except SystemExit:        # both
            raise SystemExit(sys.exc_info()[1])
        except KeyboardInterrupt:
            pass
        except:
            addException()


class UserButton(Ribbon.LabelButton):
    """User Button"""
    TOOLTIP = "User configurable button.\n<RightClick> to configure"

    def __init__(self, master, cnc, button, *args, **kwargs):
        if button == 0:
            Tk.Button.__init__(self, master, *args, **kwargs)
        else:
            Ribbon.LabelButton.__init__(self, master, *args, **kwargs)
        self.cnc = cnc
        self.button = button
        self.get()
        self.bind("<Button-3>", self.edit)
        self.bind("<Control-Button-1>", self.edit)
        self["command"] = self.execute

    def get(self):
        """get information from configuration"""

        if self.button == 0:
            return
        name = self.name()
        self["text"] = name
        self["image"] = OCV.icons.get(self.icon(), OCV.icons["material"])
        self["compound"] = Tk.LEFT
        tooltip = self.tooltip()

        if not tooltip:
            tooltip = UserButton.TOOLTIP

        tkExtra.Balloon.set(self, tooltip)

    def name(self):
        try:
            return OCV.config.get("Buttons", "name.{0}".format(self.button))
        except:
            return str(self.button)

    def icon(self):
        try:
            return OCV.config.get("Buttons", "icon.{0}".format(self.button))
        except:
            return None

    def tooltip(self):
        try:
            return OCV.config.get("Buttons", "tooltip.{0}".format(self.button))
        except:
            return ""

    def command(self):
        try:
            return OCV.config.get("Buttons", "command.{0}".format(self.button))
        except:
            return ""

    def edit(self, event=None):
        """Edit button"""
        UserButtonDialog(self, self)
        self.get()

    def execute(self):
        """Execute command"""
        cmd = self.command()
        if not cmd:
            self.edit()
            return
        for line in cmd.splitlines():
            # put the lines in pendant/buttons queue
            self.cnc.pendant.put(line)


class UserButtonDialog(Tk.Toplevel):
    """User Configurable Buttons"""
    NONE = "<none>"

    def __init__(self, master, button):
        Tk.Toplevel.__init__(self, master)
        self.title(_("User configurable button"))
        self.transient(master)
        self.button = button

        # Name
        row, col = 0, 0
        Tk.Label(self, text=_("Name:")).grid(row=row, column=col, sticky=Tk.E)
        col += 1
        self.name = Tk.Entry(
            self,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.name.grid(row=row, column=col, columnspan=2, sticky=Tk.EW)

        tkExtra.Balloon.set(self.name, _("Name to appear on button"))

        # Icon
        row, col = row + 1, 0
        Tk.Label(self, text=_("Icon:")).grid(row=row, column=col, sticky=Tk.E)

        col += 1
        self.icon = Tk.Label(self, relief=Tk.RAISED)
        self.icon.grid(row=row, column=col, sticky=Tk.EW)

        col += 1
        self.iconCombo = tkExtra.Combobox(
            self,
            True,
            width=5,
            command=self.iconChange)

        lst = list(sorted(OCV.icons.keys()))

        lst.insert(0, UserButtonDialog.NONE)

        self.iconCombo.fill(lst)
        self.iconCombo.grid(row=row, column=col, sticky=Tk.EW)

        tkExtra.Balloon.set(self.iconCombo, _("Icon to appear on button"))

        # Tooltip
        row, col = row + 1, 0
        lab = Tk.Label(self, text=_("Tool Tip:"))

        lab.grid(row=row, column=col, sticky=Tk.E)

        col += 1

        self.tooltip = Tk.Entry(
            self,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.tooltip.grid(row=row, column=col, columnspan=2, sticky=Tk.EW)

        tkExtra.Balloon.set(self.tooltip, _("Tooltip for button"))

        # Tooltip
        row, col = row + 1, 0

        lab = Tk.Label(self, text=_("Command:"))
        lab.grid(row=row, column=col, sticky=Tk.NE)

        col += 1

        self.command = Tk.Text(
            self,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            width=40,
            height=10)

        self.command.grid(row=row, column=col, columnspan=2, sticky=Tk.EW)

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(row, weight=1)

        # Actions
        row += 1

        f = Tk.Frame(self)
        f.grid(row=row, column=0, columnspan=3, sticky=Tk.EW)
        Tk.Button(f, text=_("Cancel"), command=self.cancel).pack(side=Tk.RIGHT)
        Tk.Button(f, text=_("Ok"), command=self.ok).pack(side=Tk.RIGHT)

        # Set variables
        self.name.insert(0, self.button.name())
        self.tooltip.insert(0, self.button.tooltip())
        icon = self.button.icon()
        if icon is None:
            self.iconCombo.set(UserButtonDialog.NONE)
        else:
            self.iconCombo.set(icon)
        self.icon["image"] = OCV.icons.get(icon, "")
        self.command.insert("1.0", self.button.command())

        # Wait action
        self.wait_visibility()
        self.grab_set()
        self.focus_set()
        self.wait_window()

    def ok(self, event=None):
        n = self.button.button
        OCV.config.set(
            "Buttons",
            "name.{0}".format(n),
            self.name.get().strip())

        icon = self.iconCombo.get()

        if icon == UserButtonDialog.NONE:
            icon = ""

        OCV.config.set("Buttons", "icon.{0}".format(n), icon)
        OCV.config.set(
            "Buttons", "tooltip.{0}".format(n),
            self.tooltip.get().strip())

        OCV.config.set(
            "Buttons", "command.{0}".format(n),
            self.command.get("1.0", Tk.END).strip())

        self.destroy()

    def cancel(self):
        self.destroy()

    def iconChange(self):
        self.icon["image"] = OCV.icons.get(self.iconCombo.get(), "")


class ErrorWindow(Tk.Toplevel):

    def __init__(self, master, title="Error_panel"):
        super().__init__(master)
        super().minsize(100,100)
        super().title(title)
        self.transient(master)
        frame = Tk.Frame(self)
        self.m_txt = Tk.Text(frame, width=80, height=5, wrap=Tk.WORD)
        frame.pack(fill=Tk.BOTH, expand=1)

    def show_message(self, msg):
        self.m_txt.configure(state=Tk.NORMAL)
        self.m_txt.delete(1.0, Tk.END)
        self.m_txt.insert(Tk.END, msg)
        self.m_txt['state'] = Tk.DISABLED
        self.m_txt.pack()
        
class MOPWindow(Tk.Toplevel):

    def __init__(self, master, tipo, title):
        super().__init__(master)
        super().minsize(350,150)
        super().title(title)
        self.transient(master)
        self.fr1 = Tk.Frame(self)
        self.fr1.pack(fill=Tk.BOTH, expand=True)

        butKO = Tk.Button(self, text=_("Cancel"))
        butKO.bind("<Button-1>",
                   lambda event, obj=tipo: self.exit_mop(event, obj))
        butKO.pack(side=Tk.RIGHT, padx=10, pady=5) 

        butOK = Tk.Button(self, text=_("OK"))
        butOK.bind("<Button-1>",
                   lambda event, obj=tipo: self.validate_mop(event, obj))
        butOK.pack(side=Tk.RIGHT, padx=10, pady=5) 
    
        self.f_row = 0
        self.values = []
        
    def create_form(self, tipo):
        if tipo == "PK":
            OCV.mop_vars["type"] = "PK"
            self.populate_form((
                ("ToolsDb", "db", "tt"),
                ("Diameter", "en", "fl", "tdi"),
                ("StepOver", "en", "pc", "mso"),
                ("StepDown", "en", "fl", "msd"),
                ("Target Depth", "en", "fl", "tdp"),
                ("Start internally", "cb", "bl", "sin"),
                ("Spiral Pocket", "cb", "bl", "pks")
                ))
        elif tipo == "LN":
            OCV.mop_vars["type"] = "LN"
            self.populate_form((
                ("ToolsDb", "db", "tt"),
                ("Diameter", "en", "fl", "tdi"),
                ("StepOver", "en", "pc", "mso"),
                ("StepDown", "en", "fl", "msd"),
                ("Target Depth", "en", "fl", "tdp")
                ))
        else:
            return
 
    def populate_form(self, data):
        print("Create Form")
        for field in data:
            if field[1] == "db":
                self.create_db_field(field[0], field[2])
            elif field[1] == "en":
                self.create_en_field(field[0], field[2], field[3])
            elif field[1] == "cb":
                self.create_cb_field(field[0], field[2], field[3])
        
        # Add a blank line to the form 
        label = Tk.Label(self.fr1, text="")
        label.grid(row=self.f_row, column=0, sticky=Tk.EW)
        
        # set frame resize priorities
        self.fr1.columnconfigure(0, weight=2)
        self.fr1.columnconfigure(1, weight=1)
                
                
    def create_db_field(self, name, db_name):
        """Create Database Field"""
        label = Tk.Label(self.fr1, text=name)
        label.grid(row=self.f_row, column=0, sticky="w", padx=5, pady=3)

        if db_name == "tt":
            self.tcb = ttk.Combobox(self.fr1)
            cbitems = []

            for item in OCV.tooltable:
                cbitems.append("n: {} dia: {}".format(item[0], item[1]))

            self.tcb['values'] = cbitems     
            self.tcb.grid(row=self.f_row, column=1, sticky="ew")
       
            self.tcb.bind("<<ComboboxSelected>>", self.fill_dia)

        self.f_row +=1

    def create_cb_field(self, name, var_type, var_name):
        """Create CheckBox Field"""

        ret_val = Tk.BooleanVar()
        cb = Tk.Checkbutton(
            self.fr1,
            text=name,
            variable=ret_val,
            onvalue=1, offvalue=0)
        cb.grid(row=self.f_row, column=0, pady=3, sticky="w")

        self.values.append((var_name, var_type, ret_val))
        self.f_row +=1

    def create_en_field(self, name, var_type, var_name):
        """Create value Field"""

        if var_type == "pc":
            lab_name = name + " (0-100)"
            f_width = 5
        else:
            lab_name = name
            f_width = 10
            
        label = Tk.Label(self.fr1, text=lab_name)
        label.grid(row=self.f_row, column=0, padx=5, pady=3, sticky="w")

        ret_val = Tk.StringVar()
        value = Tk.Entry(self.fr1, name=var_name, width=f_width,
                         textvariable=ret_val, justify="right")
        value.grid(row=self.f_row, column=1, sticky="e")

        self.values.append((var_name, var_type, ret_val))
         
        self.f_row +=1

    def fill_dia(self, event):
        """Auto fill Endmill diameter field with values from ListBox"""
        #print(self.tcb.get())
        ret_val = self.tcb.get()
        s_pat = re.search("dia: ", ret_val)
        value = ret_val[s_pat.span()[1]:] 

        wdg = [value[2] for value in self.values if value[0] == "tdi"]
        wdg[0].set(value)

    def validate_mop(self, event, tipo):
        """Validate MOP data"""
        #print("MOP validate")
        tdia =  self.get_value("tdi")

        if tdia > 0 and tdia < 100:
            OCV.mop_vars["tdia"] = tdia        
        else:
             e_win = ErrorWindow(self, _("Tool Diameter Invalid"))
             e_win.show_message(_("Tool Diameter must be > 0 or < 100"))    
             return
         
        mult = self.get_value("mso")
        ret_val = [value for value in self.values if value[0] == "mso"]
 
        if ret_val[0][1] == "pc":
            if mult > 0 and mult < 100:
                stepover = tdia * mult / 100
            else:
                 e_win = ErrorWindow(self, _("Step Over Invalid"))
                 e_win.show_message(_("Step Over must be > 0 and < 100"))    
                 return
        else:
            if mult > 0 and mult <= tdia:
                stepover = mult
            else:
                 e_win = ErrorWindow(self, _("Step Over Invalid"))
                 e_win.show_message(_("Step Over must be > 0 and < tdia"))    
                 return            

        OCV.mop_vars["mso"] = stepover

        stepdown = self.get_value("msd")

        if stepdown > 0 and stepdown < tdia * 0.5:
            OCV.mop_vars["msd"] = stepdown
        else:
             e_win = ErrorWindow(self, _("Step Down Invalid"))
             e_win.show_message(_("Step Down must be > 0 and < tdia * 0.5"))    
             return

        t_depth = self.get_value("tdp")
        
        if t_depth < 0:
            OCV.mop_vars["tdp"] = t_depth            
        else:
             e_win = ErrorWindow(self, _("Data Invalid"))
             e_win.show_message(_("Target Depth has to be negative"))
             return
        
        if tipo == "PK":
            pocket_type = self.get_value("pks", "bl")
            OCV.mop_vars["pks"] = pocket_type
            pocket_int = self.get_value("sin", "bl")
            OCV.mop_vars["sin"] = pocket_int
            
        elif tipo == "LN":
            pass
        else:
            pass
        
        OCV.TK_MAIN.event_generate("<<MOP_OK>>")    
        self.destroy()    
  
    def get_value(self, var_name, var_type="fl"):
        ret_val = [value for value in self.values if value[0] == var_name]
        value = ret_val[0][2].get()
        
        try:
            if var_type == "fl":
                return float(value)
            elif var_type == "bl":
                return value
            else:
                return value
        except ValueError:
            return 0
            
    def exit_mop(self, event, tipo):
        self.destroy()

class TEditorWindow(Tk.Toplevel):
    """Simple Editor Window"""

    def __init__(self, master, buttons=0):
        super().__init__(master)
        super().minsize(300,100)
        super().title("Text Editor Window")
        self.transient(master)
        
        self.columnconfigure(0, weight=1, minsize=180)
        self.rowconfigure(0, weight=1)
        
        self.frame = Tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky="nsew")
        # button area column 0
        self.frame.columnconfigure(0, weight=0)
        # text frame area column 1
        self.frame.columnconfigure(1, weight=1, minsize=190)
        # filename area row 0
        self.frame.rowconfigure(0, weight=0)
        # 3 row fpr buttons not expanding
        self.frame.rowconfigure(1, weight=0)
        self.frame.rowconfigure(2, weight=0)
        self.frame.rowconfigure(3, weight=0)
        # weight of the remaining area could span
        self.frame.rowconfigure(4, weight=1)

        self.txt_edit = Tk.Text(self.frame)
        
        self.txt_edit.grid(
            row=1, column=1, rowspan=5,
            padx=5, pady=5, sticky="nsew")

        ys = Tk.ttk.Scrollbar(
            self.frame, orient = 'vertical', command = self.txt_edit.yview)
        ys.grid(row=1, column=2, rowspan=5, padx=5, pady=5, sticky='ns')

        self.txt_edit['yscrollcommand'] = ys.set

        if buttons != 0:
            # buttons number as follows:
            # 0 = display windows only
            # 1 means "Save As.." i.e. the file could be edited
            # 2 means "Open File" button for a "normal editor" 
            if buttons == 2:
                self.btn_open = Tk.Button(
                    self.frame, text="Open File", command=self.open_file)
                self.btn_open.grid(
                    row=1, column=0, sticky="ew", padx=5, pady=5) 
            elif buttons in (1,2):    
                self.btn_save = Tk.Button(self.frame, text="Save As...", command=self.save_file)
                self.btn_save.grid(row=2, column=0, sticky="ew", padx=5)
            else:
                pass
        else:
             pass
        
        self.fileName = Tk.Label(self.frame)
        self.fileName.grid(row=0, column=1, sticky="ew")

    def set_title(self, title):
        super().title(title)
    
    def open_file(self, filename=""):
        """Open a file for editing."""

        if filename == "":
            filepath = askopenfilename(
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if not filepath:
                return
            
            self.txt_edit.delete(1.0, Tk.END)
        else:
            filepath = filename

        with open(filepath, "r") as input_file:
            text = input_file.read()
            self.txt_edit.insert(Tk.END, text)
        
        self.fileName['text'] = f"File: {filepath}"


    def parse_ini(self,filename):
        """Parse the ini file here for syntax highlighting

        Parameters
        ----------
        filename : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        filepath = filename
            
        with open(filepath, "r") as input_file:
            for line in input_file:
                self.txt_edit.insert(Tk.END, line)
        
        self.fileName['text'] = f"File: {filepath}"
    
    def save_file(self):
        """Save the current file as a new file."""
        filepath = asksaveasfilename(
            defaultextension="txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        
        with open(filepath, "w") as output_file:
            text = self.txt_edit.get(1.0, Tk.END)
            output_file.write(text)
        self.FileName['text'] = f"File: {filepath} Saved"

