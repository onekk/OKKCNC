# -*- coding: ascii -*-
"""Utils.py

This module contains some helper functions:
    - get and set the configuration from the INI file
    - some elements of the interface


Credits:
    this module code is based on bCNC
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

import gettext
try:
    import __builtin__
except:
    import builtins as __builtin__
#    __builtin__.unicode = str        # dirty hack for python3

try:
    import serial
except:
    serial = None

import OCV

prgpath = os.path.abspath(os.path.dirname(__file__))

if getattr(sys, 'frozen', False):
    # When being bundled by pyinstaller, paths are different
    print("Running as pyinstaller bundle!", sys.argv[0])
    prgpath = os.path.abspath(os.path.dirname(sys.argv[0]))

iniSystem = os.path.join(prgpath, "{0}.ini".format(OCV.PRGNAME))
iniUser = os.path.expanduser("~/.{0}".format(OCV.PRGNAME))
hisFile = os.path.expanduser("~/.{0}.history".format(OCV.PRGNAME))

# dirty way of substituting the "_" on the builtin namespace
# __builtin__.__dict__["_"] = gettext.translation(
# 'OKKCNC',
# 'locale',
# fallback=True).ugettext

__builtin__._ = gettext.translation(
    'OKKCNC',
    os.path.join(prgpath, 'locale'),
    fallback=True).gettext

__builtin__.N_ = lambda message: message

import Ribbon
import tkExtra

__www__ = "https://github.com/onekk/OKKCNC"
__contribute__ = ""

__credits__ = \
        "bCNC Creator @vvlachoudis vvlachoudis@gmail.com\n" \
        "@effer Filippo Rivato , " \
        "@harvie Tomas Mudrunka\n\n" \
        "And all the contributors of bCNC"
__translations__ = \
        "Italian - @onekk\n" \

LANGUAGES = {
    "": "<system>",
    "en": "English",
    "it": "Italiano",
    }

icons = {}
images = {}
OCV.config = ConfigParser.ConfigParser()
# This is here to debug the fact that config is sometimes instantiated twice
print("new-config", __name__, OCV.config)
language = ""

_errorReport = True
errors = []
_maxRecent = 10

class Config(object):
    """New class to provide config for everyone"""
    def greet(self, who=__name__):
        """print on console the """
        print("Config class loaded in {0}".format(who))

def loadIcons():
    global icons
    icons = {}
    for img in glob.glob("{0}{1}icons{1}*.gif".format(prgpath, os.sep)):
        name, ext = os.path.splitext(os.path.basename(img))
        try:
            icons[name] = Tk.PhotoImage(file=img)
            if get_bool("CNC", "doublesizeicon"):
                icons[name] = icons[name].zoom(2, 2)
        except Tk.TclError:
            pass

    # Images
    global images
    images = {}
    for img in glob.glob("{0}{1}images{1}*.gif".format(prgpath, os.sep)):
        name, ext = os.path.splitext(os.path.basename(img))
        try:
            images[name] = Tk.PhotoImage(file=img)
            if get_bool("CNC", "doublesizeicon"):
                images[name] = images[name].zoom(2, 2)
        except Tk.TclError:
            pass


def delIcons():
    global icons
    if len(icons) > 0:
        for i in icons.values():
            del i
        icons = {}    # needed otherwise it complains on deleting the icons

    global images
    if len(images) > 0:
        for i in images.values():
            del i
        images = {}    # needed otherwise it complains on deleting the icons


def loadConfiguration(systemOnly=False):
    """Load configuration"""
    global _errorReport, language
    if systemOnly:
        OCV.config.read(iniSystem)
    else:
        OCV.config.read([iniSystem, iniUser])
        _errorReport = get_int("Connection", "errorreport", 1)

        language = get_str(OCV.PRGNAME, "language")
        if language:
            # replace language
            __builtin__._ = gettext.translation(
                OCV.PRGNAME,
                os.path.join(prgpath, 'locale'),
                fallback=True,
                languages=[language]).gettext


def saveConfiguration():
    """Save configuration file"""
    cleanConfiguration()
    f = open(iniUser, "w")
    OCV.config.write(f)
    f.close()
    delIcons()


def cleanConfiguration():
    """Remove items that are the same as in the default ini"""
    newconfig = OCV.config  # Remember config
    OCV.config = ConfigParser.ConfigParser()

    loadConfiguration(True)

    # Compare items
    for section in OCV.config.sections():
        for item, value in OCV.config.items(section):
            try:
                new = newconfig.get(section, item)
                if value == new:
                    newconfig.remove_option(section, item)
            except ConfigParser.NoOptionError:
                pass
    OCV.config = newconfig


def add_config_section(section):
    """add section if it doesn't exist"""
    if not OCV.config.has_section(section):
        OCV.config.add_section(section)


def get_str(section, name, default=""):
    try:
        return OCV.config.get(section, name)
    except Exception:
        return default


def set_str(section, name, value):
    OCV.config.set(section, name, str(value))


set_int = set_str
set_float = set_str


def set_utf(section, name, value):
    try:
        s = str(value)
    except:
        s = str(value)
    OCV.config.set(section, name, s)


def get_int(section, name, default=0):
    try:
        return int(OCV.config.get(section, name))
    except Exception:
        return default


def get_float(section, name, default=0.0):
    try:
        return float(OCV.config.get(section, name))
    except Exception:
        return default


def get_bool(section, name, default=False):
    try:
        return bool(int(OCV.config.get(section, name)))
    except Exception:
        return default


def set_bool(section, name, value):
    OCV.config.set(section, name, str(int(value)))

def remove_config_item(section, name):
    if OCV.config.has_option(section, name):
        OCV.config.remove_option(section, name)


def do_nothing():
    pass


def makeFont(name, value=None):
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


def fontString(font):
    """Create a font string"""
    name = str(font[0])
    size = str(font[1])

    if name.find(' ') >= 0:
        s = '"{0}" {1}'.format(name, size)
    else:
        s = '{0}, {1}'.format(name, size)

    try:
        if font[2] == tkFont.BOLD:
            s += " bold"
    except:
        pass
    try:
        if font[3] == tkFont.ITALIC:
            s += " italic"
    except:
        pass
    return s


def get_font( name, default=None):
    """Get font from configuration"""
    try:
        value = OCV.config.get(OCV.FONT_SECTION, name)
    except:
        value = None

    if not value:
        font = makeFont(name, default)
        set_font(name, font)
        return font

    if isinstance(value, str):
        value = tuple(value.split(','))

    if isinstance(value, tuple):
        font = makeFont(name, value)

        if font is not None:
            return font
    return value


def set_font(name, font):
    """Set font in configuration"""
    if font is None:
        return

    if isinstance(font, str):
        OCV.config.set(OCV.FONT_SECTION, name, font)
    elif isinstance(font, tuple):
        OCV.config.set(OCV.FONT_SECTION, name, ",".join(map(str, font)))
    else:
        OCV.config.set(OCV.FONT_SECTION, name, "{0},{1},{2}".format(
            font.cget("family"),
            font.cget("size"),
            font.cget("weight")))


def add_recent_file(filename):
    """Add recent file"""
    try:
        sfn = str(os.path.abspath(filename))
    except UnicodeEncodeError:
        sfn = filename

    last = OCV.maxRecent - 1
    for i in range(OCV.maxRecent):
        rfn = get_recent_file(i)
        if rfn is None:
            last = i - 1
            break
        if rfn == sfn:
            if i == 0:
                return
            last = i - 1
            break

    # Shift everything by one
    for i in range(last, -1, -1):
        OCV.config.set("File", "recent.{0}".format(i + 1), get_recent_file(i))
    OCV.config.set("File", "recent.0", sfn)


def get_recent_file(recent):
    try:
        return OCV.config.get("File", "recent.{0}".format(recent))
    except ConfigParser.NoOptionError:
        return None


def set_predefined_steps():
    """set pre defined steps used in ControlPage"""
    # Predefined XY steppings
    try:
        OCV.step1 = get_float("Control", "step1")
    except Exception:
        OCV.step1 = 1.0

    try:
        OCV.step2 = get_float("Control", "step2")
    except Exception:
        OCV.step2 = 1.0

    try:
        OCV.step3 = get_float("Control", "step3")
    except Exception:
        OCV.step3 = 10.0

    # Predefined Z steppings
    try:
        OCV.zstep1 = get_float("Control", "zstep1")
    except Exception:
        OCV.zstep1 = 0.1

    try:
        OCV.zstep2 = get_float("Control", "zstep2")
    except Exception:
        OCV.zstep2 = 1.0

    try:
        OCV.zstep3 = get_float("Control", "zstep3")
    except Exception:
        OCV.zstep3 = 5.0

    try:
        OCV.zstep4 = get_float("Control", "zstep4")
    except Exception:
        OCV.zstep4 = 10.0


def InputValue(app, caller):
    title_d = _("Enter A Value")
    title_p = _("Enter Value for {0} :")
    title_c = ""
    c_t = 0
    if caller in ("S1", "S2", "S3"):
        if caller == "S1":
            title_c = title_p.format("Step1")
        elif caller == "S2":
            title_c = title_p.format("Step2")
        elif caller == "S3":
            title_c = title_p.format("Step3")
        else:
            return
        min_value = 0.001
        max_value = 100.0

    elif caller in ("ZS1", "ZS2", "ZS3", "ZS4"):
        if caller == "ZS1":
            title_c = title_p.format("Z Step1")
        elif caller == "ZS2":
            title_c = title_p.format("Z Step2")
        elif caller == "ZS3":
            title_c = title_p.format("Z Step3")
        elif caller == "ZS4":
            title_c = title_p.format("Z Step3")
        else:
            return
        min_value = 0.001
        max_value = 10.0

    elif caller == "TD":
        title_c = _("Enter Target Depth :")
        min_value = -35.0
        max_value = 0.0

    elif caller == "MN":
        title_c = _("Enter Memory Number :")
        min_value = 2
        max_value = OCV.WK_mem_num
        c_t = 1

    elif caller == "ME":
        title_p = _("Enter Memory {0} Description :")
        title_c = title_p.format(OCV.WK_mem)
        c_t = 2

    else:
        title_c = _("Enter a float Value :")
        min_value = 0.001
        max_value = 100.0

    if c_t == 0:
        prompt = "{0}\n (min: {1:.04f} max: {2:.04f})".format(
            title_c,
            min_value,
            max_value)

        retval = tkSimpleDialog.askfloat(
            title_d, prompt, parent=app,
            minvalue=min_value,
            maxvalue=max_value)
    elif c_t == 1:
        prompt = "{0}\n (min: {1:d} max: {2:d})".format(
            title_c,
            min_value,
            max_value)

        retval = tkSimpleDialog.askinteger(
            title_d, prompt, parent=app,
            minvalue=min_value,
            maxvalue=max_value)
    elif c_t == 2:
        prompt = title_c
        retval = tkSimpleDialog.askstring(title_d, prompt, parent=app)

    # early check for null value

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
                s = serial.Serial(device)
                s.close()
                comports.append((device, None, None))
            except:
                pass
    return comports


def q_round(x, prec=2, base=.05):
    """round a number specifing the decimal digits
    and a quantization factor"""
    return round(base * round(float(x)/base), prec)


def addException():
    global errors
#    self.widget._report_exception()
    try:
        typ, val, tb = sys.exc_info()
        traceback.print_exception(typ, val, tb)

        if errors:
            errors.append("")

        exception = traceback.format_exception(typ, val, tb)
        errors.extend(exception)

        if len(errors) > 100:
            # do nothing for now
            print(errors)
    except:
        say(str(sys.exc_info()))


class CallWrapper:
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
#        self.bind("<Control-Button-1>", self.edit)
        self.bind("<Button-3>", self.edit)
        self.bind("<Control-Button-1>", self.edit)
        self["command"] = self.execute

    def get(self):
        """get information from configuration"""

        if self.button == 0:
            return
        name = self.name()
        self["text"] = name
        self["image"] = icons.get(self.icon(), icons["material"])
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

        lst = list(sorted(icons.keys()))

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
        self.icon["image"] = icons.get(icon, "")
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
        self.icon["image"] = icons.get(self.iconCombo.get(), "")


class ErrorWindow(Tk.Toplevel):

    def __init__(self, master):
        Tk.Toplevel.__init__(self, master, name="error_panel")
        self.title(_("User configurable Dialog"))
        self.transient(master)
        self.msg = "message"

    def show_message(self):
        print(self.winfo_name)
