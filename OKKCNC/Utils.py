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
    import tkinter.messagebox as tkMessageBox
    import configparser as ConfigParser

# import webbrowser

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
        OCV.step1 = IniFile.get_float("Control", "step1")
    except Exception:
        OCV.step1 = 1.0

    try:
        OCV.step2 = IniFile.get_float("Control", "step2")
    except Exception:
        OCV.step2 = 1.0

    try:
        OCV.step3 = IniFile.get_float("Control", "step3")
    except Exception:
        OCV.step3 = 10.0

    # Predefined Z steppings
    try:
        OCV.zstep1 = IniFile.get_float("Control", "zstep1")
    except Exception:
        OCV.zstep1 = 0.1

    try:
        OCV.zstep2 = IniFile.get_float("Control", "zstep2")
    except Exception:
        OCV.zstep2 = 1.0

    try:
        OCV.zstep3 = IniFile.get_float("Control", "zstep3")
    except Exception:
        OCV.zstep3 = 5.0

    try:
        OCV.zstep4 = IniFile.get_float("Control", "zstep4")
    except Exception:
        OCV.zstep4 = 10.0


def ask_for_value(app, caller):
    """Show an input windows asking for a value
    uses tkSimpleDialog
    """
    title_d = _("Enter A Value")
    switch = {
        "S1": ("Step1", "step", 0.001, 100.0),
        "S2": ("Step2", "step", 0.001, 100.0),
        "S3": ("Step3", "step", 0.001, 100.0),
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
    OCV.ABOUT = Tk.Toplevel(OCV.APP)
    OCV.ABOUT.transient(OCV.APP)
    OCV.ABOUT.title(_("About {0}").format(OCV.PRG_NAME))
    if sys.platform == "win32":
        OCV.APP.iconbitmap("OKKCNC.ico")
    else:
        OCV.APP.iconbitmap("@{0}/OKKCNC.xbm".format(OCV.PRG_PATH))

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
        OCV.ABOUT,
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

    closeAbout = lambda e=None, t=OCV.ABOUT: t.destroy()

    row += 1

    but = Tk.Button(frame, text=_("Close"), command=closeAbout)
    but.grid(row=row, column=1, sticky= Tk.NS, padx=5, pady=5)

    frame.grid_columnconfigure(0, weight=1)

    OCV.ABOUT.bind('<Escape>', closeAbout)
    OCV.ABOUT.bind('<Return>', closeAbout)
    OCV.ABOUT.bind('<KP_Enter>', closeAbout)

    OCV.ABOUT.deiconify()
    OCV.ABOUT.wait_visibility()
    OCV.ABOUT.resizable(False, False)

    try:
        OCV.ABOUT.grab_set()
    except:
        pass

    but.focus_set()
    OCV.ABOUT.lift()

    if timer:
        OCV.ABOUT.after(timer, closeAbout)

    OCV.ABOUT.wait_window()


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

    def __init__(self, master):
        Tk.Toplevel.__init__(self, master, name="error_panel")
        self.title(_("Error Dialog"))
        self.transient(master)
        frame = Tk.Frame(self, width=100, height=100)
        self.m_txt = Tk.Text(frame, wrap=Tk.WORD)
        frame.pack(fill=Tk.BOTH, expand=1)

    def show_message(self, msg):
        self.m_txt.configure(state=Tk.NORMAL)
        self.m_txt.delete(1.0, Tk.END)
        self.m_txt.insert(Tk.END, msg)
        self.m_txt.configure(state=Tk.DISABLED)
        self.m_txt.pack()
