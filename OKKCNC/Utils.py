# -*- coding: ascii -*-
# $Id$
#
# Author:    carlo.dormeletti@gmail.com
# Date: 26 Oct 2019

from __future__ import absolute_import
from __future__ import print_function

__author__  = "Carlo Dormeletti (onekk)"
__email__   = "carlo.dormeletti@gmail.com"

import os
import glob
import traceback
from lib.log import say
try:
    from Tkinter import *
    import tkFont
    import tkMessageBox
    import ConfigParser
except ImportError:
    from tkinter import *
    import tkinter.font as tkFont
    import tkinter.messagebox as tkMessageBox
    import configparser as ConfigParser

import gettext
try:
    import __builtin__
except:
    import builtins as __builtin__
    #__builtin__.unicode = str        # dirty hack for python3

try:
    import serial
except:
    serial = None

__prg__     = "OKKCNC"
prgpath   = os.path.abspath(os.path.dirname(__file__))
if getattr( sys, 'frozen', False ):
    #When being bundled by pyinstaller, paths are different
    print("Running as pyinstaller bundle!", sys.argv[0])
    prgpath   = os.path.abspath(os.path.dirname(sys.argv[0]))
iniSystem = os.path.join(prgpath,"%s.ini"%(__prg__))
iniUser   = os.path.expanduser("~/.%s" % (__prg__))
hisFile   = os.path.expanduser("~/.%s.history" % (__prg__))

# dirty way of substituting the "_" on the builtin namespace
#__builtin__.__dict__["_"] = gettext.translation('bCNC', 'locale', fallback=True).ugettext
__builtin__._ = gettext.translation('bCNC', os.path.join(prgpath,'locale'), fallback=True).gettext
__builtin__.N_ = lambda message: message

import Ribbon
import tkExtra

__www__     = "https://github.com/onekk/OKKCNC"
__contribute__ = ""

__credits__ = \
        "@vvlachoudis vvlachoudis@gmail.com" \
        "@effer Filippo Rivato\n" \
        "@carlosgs Carlos Garcia Saura\n" \
        "@dguerizec\n" \
        "@buschhardt\n" \
        "@MARIOBASZ\n" \
        "@harvie Tomas Mudrunka" \
        "@1bigpig\n" \
        "@chamnit Sonny Jeon\n" \
        "@harvie Tomas Mudrunka\n" \
        "@onekk Carlo\n" \
        "@SteveMoto\n" \
        "@willadams William Adams"
__translations__ = \
        "Dutch - @hypothermic\n" \
        "French - @ThierryM\n" \
        "German - @feistus, @SteveMoto\n" \
        "Italian - @onekk\n" \
        "Japanese - @stm32f1\n" \
        "Korean - @jjayd\n" \
        "Portuguese - @moacirbmn \n" \
        "Russian - @minithc\n" \
        "Simplified Chinese - @Bluermen\n" \
        "Spanish - @carlosgs\n" \
        "Traditional Chinese - @Engineer2Designer\n"

LANGUAGES = {
        ""      : "<system>",
        "en"    : "English",
        "it"    : "Italiano",
    }

icons     = {}
images     = {}
config    = ConfigParser.ConfigParser()
print("new-config", __name__, config) #This is here to debug the fact that config is sometimes instantiated twice
language  = ""

_errorReport = True
errors       = []
_maxRecent   = 10

_FONT_SECTION = "Font"


#New class to provide config for everyone
#FIXME: create single instance of this and pass it to all parts of application
class Config():
    def greet(self, who=__name__):
        print("Config class loaded in %s"%(who))


#------------------------------------------------------------------------------
def loadIcons():
    global icons
    icons = {}
    for img in glob.glob("%s%sicons%s*.gif"%(prgpath,os.sep,os.sep)):
        name,ext = os.path.splitext(os.path.basename(img))
        try:
            icons[name] = PhotoImage(file=img)
            if getBool("CNC", "doublesizeicon"):
                icons[name] = icons[name].zoom(2,2)
        except TclError:
            pass

    #Images
    global images
    images = {}
    for img in glob.glob("%s%simages%s*.gif"%(prgpath,os.sep,os.sep)):
        name,ext = os.path.splitext(os.path.basename(img))
        try:
            images[name] = PhotoImage(file=img)
            if getBool("CNC", "doublesizeicon"):
                images[name] = images[name].zoom(2,2)
        except TclError:
            pass


#------------------------------------------------------------------------------
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


#------------------------------------------------------------------------------
# Load configuration
#------------------------------------------------------------------------------
def loadConfiguration(systemOnly=False):
    global config, _errorReport, language
    if systemOnly:
        config.read(iniSystem)
    else:
        config.read([iniSystem, iniUser])
        _errorReport = getInt("Connection","errorreport",1)

        language = getStr(__prg__, "language")
        if language:
            # replace language
            __builtin__._ = gettext.translation('OKKCNC', os.path.join(prgpath,'locale'),
                    fallback=True, languages=[language]).gettext


#------------------------------------------------------------------------------
# Save configuration file
#------------------------------------------------------------------------------
def saveConfiguration():
    global config
    cleanConfiguration()
    f = open(iniUser,"w")
    config.write(f)
    f.close()
    delIcons()


#----------------------------------------------------------------------
# Remove items that are the same as in the default ini
#----------------------------------------------------------------------
def cleanConfiguration():
    global config
    newconfig = config    # Remember config
    config = ConfigParser.ConfigParser()

    loadConfiguration(True)

    # Compare items
    for section in config.sections():
        for item, value in config.items(section):
            try:
                new = newconfig.get(section, item)
                if value==new:
                    newconfig.remove_option(section, item)
            except ConfigParser.NoOptionError:
                pass
    config = newconfig


#------------------------------------------------------------------------------
# add section if it doesn't exist
#------------------------------------------------------------------------------
def addSection(section):
    global config
    if not config.has_section(section):
        config.add_section(section)


#------------------------------------------------------------------------------
def getStr(section, name, default=""):
    global config
    try:
        return config.get(section, name)
    except:
        return default


#------------------------------------------------------------------------------
def getUtf(section, name, default=""):
    global config
    try:
        return config.get(section, name).decode("utf8")
    except:
        return default


#------------------------------------------------------------------------------
def getInt(section, name, default=0):
    global config
    try: return int(config.get(section, name))
    except: return default


#------------------------------------------------------------------------------
def getFloat(section, name, default=0.0):
    global config
    try: return float(config.get(section, name))
    except: return default


#------------------------------------------------------------------------------
def getBool(section, name, default=False):
    global config
    try: return bool(int(config.get(section, name)))
    except: return default


#-------------------------------------------------------------------------------
# Return a font from a string
#-------------------------------------------------------------------------------
def makeFont(name, value=None):
    try:
        font = tkFont.Font(name=name, exists=True)
    except TclError:
        font = tkFont.Font(name=name)
        font.delete_font = False
    except AttributeError:
        return None

    if value is None: return font

    if isinstance(value, tuple):
        font.configure(family=value[0])
        try:    font.configure(size=value[1])
        except: pass
        try:    font.configure(weight=value[2])
        except: pass
        try:    font.configure(slant=value[3])
        except: pass
    return font


#-------------------------------------------------------------------------------
# Create a font string
#-------------------------------------------------------------------------------
def fontString(font):
    name  = str(font[0])
    size  = str(font[1])
    if name.find(' ')>=0:
        s = '"%s" %s'%(name,size)
    else:
        s = '%s %s'%(name,size)

    try:
        if font[2] == tkFont.BOLD: s += " bold"
    except: pass
    try:
        if font[3] == tkFont.ITALIC: s += " italic"
    except: pass
    return s


#-------------------------------------------------------------------------------
# Get font from configuration
#-------------------------------------------------------------------------------
def getFont(name, default=None):
    try:
        value = config.get(_FONT_SECTION, name)
    except:
        value = None

    if not value:
        font = makeFont(name, default)
        setFont(name, font)
        return font

    if isinstance(value, str):
        value = tuple(value.split(','))

    if isinstance(value, tuple):
        font = makeFont(name, value)
        if font is not None: return font
    return value


#-------------------------------------------------------------------------------
# Set font in configuration
#-------------------------------------------------------------------------------
def setFont(name, font):
    if font is None: return
    if isinstance(font,str):
        config.set(_FONT_SECTION, name, font)
    elif isinstance(font,tuple):
        config.set(_FONT_SECTION, name, ",".join(map(str,font)))
    else:
        config.set(_FONT_SECTION, name, "%s,%s,%s" % \
            (font.cget("family"),font.cget("size"),font.cget("weight")))


#------------------------------------------------------------------------------
def setBool(section, name, value):
    global config
    config.set(section, name, str(int(value)))


#------------------------------------------------------------------------------
def setStr(section, name, value):
    global config
    config.set(section, name, str(value))


#------------------------------------------------------------------------------
def setUtf(section, name, value):
    global config
    try:
        s = str(value.encode("utf8"))
    except:
        s = str(value)
    config.set(section, name, s)

setInt   = setStr
setFloat = setStr


#-------------------------------------------------------------------------------
# Add Recent
#-------------------------------------------------------------------------------
def addRecent(filename):
    try:
        sfn = str(os.path.abspath(filename))
    except UnicodeEncodeError:
        sfn = filename.encode("utf8")

    last = _maxRecent-1
    for i in range(_maxRecent):
        rfn = getRecent(i)
        if rfn is None:
            last = i-1
            break
        if rfn == sfn:
            if i==0: return
            last = i-1
            break

    # Shift everything by one
    for i in range(last, -1, -1):
        config.set("File", "recent.%d"%(i+1), getRecent(i))
    config.set("File", "recent.0", sfn)


#-------------------------------------------------------------------------------
def getRecent(recent):
    try:
        return config.get("File","recent.%d"%(recent))
    except ConfigParser.NoOptionError:
        return None


#------------------------------------------------------------------------------
# Return all comports when serial.tools.list_ports is not available!
#------------------------------------------------------------------------------
def comports(include_links=True):
    locations=[    '/dev/ttyACM',
            '/dev/ttyUSB',
            '/dev/ttyS',
            'com']

    comports = []
    for prefix in locations:
        for i in range(32):
            device = "%s%d"%(prefix,i)
            try:
                os.stat(device)
                comports.append((device,None,None))
            except OSError:
                pass

            # Detects windows XP serial ports
            try:
                s = serial.Serial(device)
                s.close()
                comports.append((device,None,None))
            except:
                pass
    return comports


#===============================================================================
def addException():
    global errors
    #self.widget._report_exception()
    try:
        typ, val, tb = sys.exc_info()
        traceback.print_exception(typ, val, tb)
        if errors: errors.append("")
        exception = traceback.format_exception(typ, val, tb)
        errors.extend(exception)
        if len(errors) > 100:
            # do nothing for now
            print (errors)
    except:
        say(str(sys.exc_info()))


#===============================================================================
class CallWrapper:
    """Replaces the Tkinter.CallWrapper with extra functionality"""
    def __init__(self, func, subst, widget):
        """Store FUNC, SUBST and WIDGET as members."""
        self.func   = func
        self.subst  = subst
        self.widget = widget

    # ----------------------------------------------------------------------
    def __call__(self, *args):
        """Apply first function SUBST to arguments, than FUNC."""
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        # One possible fix is to make an external file for the wrapper
        # and import depending the version
        #except SystemExit, msg:    # python2.4 syntax
        #except SystemExit as msg:    # python3 syntax
        #    raise SystemExit(msg)
        except SystemExit:        # both
            raise SystemExit(sys.exc_info()[1])
        except KeyboardInterrupt:
            pass
        except:
            addException()


#===============================================================================
# User Button
#===============================================================================
class UserButton(Ribbon.LabelButton):
    TOOLTIP  = "User configurable button.\n<RightClick> to configure"

    def __init__(self, master, cnc, button, *args, **kwargs):
        if button == 0:
            Button.__init__(self, master, *args, **kwargs)
        else:
            Ribbon.LabelButton.__init__(self, master, *args, **kwargs)
        self.cnc = cnc
        self.button = button
        self.get()
        #self.bind("<Control-Button-1>", self.edit)
        self.bind("<Button-3>",         self.edit)
        self.bind("<Control-Button-1>", self.edit)
        self["command"] = self.execute

    # ----------------------------------------------------------------------
    # get information from configuration
    # ----------------------------------------------------------------------
    def get(self):
        if self.button == 0: return
        name = self.name()
        self["text"] = name
        #if icon == "":
        #    icon = icons.get("empty","")
        self["image"] = icons.get(self.icon(),icons["material"])
        self["compound"] = LEFT
        tooltip = self.tooltip()
        if not tooltip: tooltip = UserButton.TOOLTIP
        tkExtra.Balloon.set(self, tooltip)

    # ----------------------------------------------------------------------
    def name(self):
        try:
            return config.get("Buttons","name.%d"%(self.button))
        except:
            return str(self.button)

    # ----------------------------------------------------------------------
    def icon(self):
        try:
            return config.get("Buttons","icon.%d"%(self.button))
        except:
            return None

    # ----------------------------------------------------------------------
    def tooltip(self):
        try:
            return config.get("Buttons","tooltip.%d"%(self.button))
        except:
            return ""

    # ----------------------------------------------------------------------
    def command(self):
        try:
            return config.get("Buttons","command.%d"%(self.button))
        except:
            return ""

    # ----------------------------------------------------------------------
    # Edit button
    # ----------------------------------------------------------------------
    def edit(self, event=None):
        UserButtonDialog(self, self)
        self.get()

    # ----------------------------------------------------------------------
    # Execute command
    # ----------------------------------------------------------------------
    def execute(self):
        cmd = self.command()
        if not cmd:
            self.edit()
            return
        for line in cmd.splitlines():
            self.cnc.pendant.put(line)


#===============================================================================
# User Configurable Buttons
#===============================================================================
class UserButtonDialog(Toplevel):
    NONE = "<none>"

    def __init__(self, master, button):
        Toplevel.__init__(self, master)
        self.title(_("User configurable button"))
        self.transient(master)
        self.button = button

        # Name
        row,col = 0,0
        Label(self, text=_("Name:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.name = Entry(self, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.name.grid(row=row, column=col, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(self.name, _("Name to appear on button"))

        # Icon
        row,col = row+1,0
        Label(self, text=_("Icon:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.icon = Label(self, relief=RAISED)
        self.icon.grid(row=row, column=col, sticky=EW)
        col += 1
        self.iconCombo = tkExtra.Combobox(self, True,
                    width=5,
                    command=self.iconChange)
        lst = list(sorted(icons.keys()))
        lst.insert(0,UserButtonDialog.NONE)
        self.iconCombo.fill(lst)
        self.iconCombo.grid(row=row, column=col, sticky=EW)
        tkExtra.Balloon.set(self.iconCombo, _("Icon to appear on button"))

        # Tooltip
        row,col = row+1,0
        Label(self, text=_("Tool Tip:")).grid(row=row, column=col, sticky=E)
        col += 1
        self.tooltip = Entry(self, background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.tooltip.grid(row=row, column=col, columnspan=2, sticky=EW)
        tkExtra.Balloon.set(self.tooltip, _("Tooltip for button"))

        # Tooltip
        row,col = row+1,0
        Label(self, text=_("Command:")).grid(row=row, column=col, sticky=N+E)
        col += 1
        self.command = Text(self, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=40, height=10)
        self.command.grid(row=row, column=col, columnspan=2, sticky=EW)

        self.grid_columnconfigure(2,weight=1)
        self.grid_rowconfigure(row,weight=1)

        # Actions
        row += 1
        f = Frame(self)
        f.grid(row=row, column=0, columnspan=3, sticky=EW)
        Button(f, text=_("Cancel"), command=self.cancel).pack(side=RIGHT)
        Button(f, text=_("Ok"),     command=self.ok).pack(side=RIGHT)

        # Set variables
        self.name.insert(0,self.button.name())
        self.tooltip.insert(0,self.button.tooltip())
        icon = self.button.icon()
        if icon is None:
            self.iconCombo.set(UserButtonDialog.NONE)
        else:
            self.iconCombo.set(icon)
        self.icon["image"] = icons.get(icon,"")
        self.command.insert("1.0", self.button.command())

        # Wait action
        self.wait_visibility()
        self.grab_set()
        self.focus_set()
        self.wait_window()

    # ----------------------------------------------------------------------
    def ok(self, event=None):
        n = self.button.button
        config.set("Buttons", "name.%d"%(n), self.name.get().strip())
        icon = self.iconCombo.get()
        if icon == UserButtonDialog.NONE: icon = ""
        config.set("Buttons", "icon.%d"%(n), icon)
        config.set("Buttons", "tooltip.%d"%(n), self.tooltip.get().strip())
        config.set("Buttons", "command.%d"%(n), self.command.get("1.0",END).strip())
        self.destroy()

    # ----------------------------------------------------------------------
    def cancel(self):
        self.destroy()

    # ----------------------------------------------------------------------
    def iconChange(self):
        self.icon["image"] = icons.get(self.iconCombo.get(),"")
