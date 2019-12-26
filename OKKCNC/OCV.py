# -*- coding: ascii -*-
"""OCV.py

This module contains the variables used in OKKCNC, it is imported
almost in every module as it provide an "elegant" way to provide
"globals" across the program

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import re
import os
import sys

author = "Carlo Dormeletti (onekk)"
email = "carlo.dormeletti@gmail.com"

PRG_NAME = "OKKCNC"
"""version and date"""

PRG_VER = "0.2.10-dev"
PRG_DATE = "26 Dec 2019"

PRG_PATH = os.path.abspath(os.path.dirname(__file__))

if getattr(sys, 'frozen', False):
    # When being bundled by pyinstaller, paths are different
    print("Running as pyinstaller bundle!", sys.argv[0])
    PRG_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

HOME_DIR = os.path.expanduser("~/")
SYS_CONFIG = os.path.join(PRG_PATH, "{0}.ini".format(PRG_NAME))
USER_CONFIG = os.path.expanduser("~/.{0}".format(PRG_NAME))
COM_HIST_FILE = os.path.expanduser("~/.{0}.history".format(PRG_NAME))

"""Debug flags. used across the interface to print debug info on terminal
    the debug comment
    # DEBUG_INFO
    denote a place where a DEBUG info are relevant, in some methods
    or functions there are a "dual level" mechanism, after DEBUG_INFO line
    there is an assignement of INT_DEBUG "local" variable to one of the
    DEBUG_XXX "flags" below, to have the relevant information shown only when
    needed to debug the code in the development process, searching for
    DEBUG_INFO in the code permit to decomment the line to show the relevant
    code, this for not having to define too many DEBUG_XXX "flags"
"""
# General unspecified debug flag
DEBUG = False
# Debug graphical part
DEBUG_GRAPH = False
# Debug Interface
DEBUG_INT = False
# Debug Comunications
DEBUG_COM = False
# debug GCode parsing
DEBUG_PAR = True

# String related to About window
PRG_CREDITS = \
    "bCNC Creator @vvlachoudis vvlachoudis@gmail.com\n" \
    "@effer Filippo Rivato , " \
    "@harvie Tomas Mudrunka\n\n" \
    "And all the contributors of bCNC"

PRG_CONTRIB = ""

PRG_LANGUAGES = {
    "": "<system>",
    "en": "English",
    "it": "Italiano",
    }

PRG_SITE = "https://github.com/onekk/OKKCNC"

PRG_TRANS = \
    "Italian - @onekk\n" \

# Some flags to make choices based on init values, used across different files
HAS_SERIAL = None
IS_PY3 = False

# INTERFACE COLORS
"""See Inifile.py/load_colors()
values with comments Above are the corresponding item names in IniFile
"""
# "ribbon.active"
COLOR_ACTIVE = "LightYellow"
COLOR_BACKGROUND = "#E6E2E0"
COLOR_BACKGROUND_LABELS = "pale green"
COLOR_BACKGROUND_DISABLE = "#A6A2A0"

COLOR_BLOCK = "LightYellow"
# "canvas.camera"
COLOR_CAMERA = "Cyan"
# "canvas.background"
COLOR_CANVAS = "White"

COLOR_COMMENT = "Blue"
# "canvas.disable"
COLOR_DISABLE = "LightGray"
# "canvas.enable"
COLOR_ENABLE = "Black"
# "canvas.gantry"
COLOR_GANTRY = "Red"
# "canvas.grid"
COLOR_GRID = "Gray"
COLOR_GROUP_BACKGROUND = "#B6B2B0"
COLOR_GROUP_BACKGROUND2 = "#B0C0C0"
# COLOR_GROUP_BACKGROUND3 = "#A0C0A0"
# COLOR_GROUP_BACKGROUND4 = "#B0C0A0"
COLOR_GROUP_FOREGROUND = "White"
COLOR_INFO = "Gold"
COLOR_INSERT = "Blue"  # CHECK set but unused
COLOR_LSTB_NUMBER = "khaki1"
COLOR_LSTB_SEP = "aquamarine"
COLOR_LSTB_TEXT = "azure"
COLOR_LSTB_VAL = "AntiqueWhite1"
# "canvas.margin"
COLOR_MARGIN = "Magenta"
COLOR_MEM = "Orchid1"
# "canvas.move"
COLOR_MOVE = "DarkCyan"
# "canvas.probetext"
COLOR_PROBE_TEXT = "Green"
# "canvas.process"
COLOR_PROCESS = "Green"
# "canvas.ruler"
COLOR_RULER = "Green"
# "canvas.select"
COLOR_SELECT = "Blue"
# "canvas.select2"
COLOR_SELECT2 = "DarkCyan"
# "canvas.selectbox"
COLOR_SELECT_BOX = "Cyan"
# "ribbon.select"
COLOR_SELECT_LABEL = "#C0FFC0"
COLOR_TAB = "DarkOrange"
# TODO we need this color?
COLOR_TABS = "Orange"
COLOR_WORK = "Orange"

# INTERFACE FONTS
FONT = ("Sans", "-10")
FONT_DRO_ZERO = ("Sans", "-11")
FONT_EXE = ("Helvetica", 12, "bold")
FONT_RIBBON_TAB = ("Sans", "-14", "bold")
FONT_RIBBON = ("Sans", "-11")
FONT_STATE_WCS = ("Helvetica", "-14")
FONT_STATE_BUT = ("Sans", "-11")

# Font section name in Config file.
FONT_SEC_NAME = "Font"

#
WCS = ["G54", "G55", "G56", "G57", "G58", "G59"]

DISTANCE_MODE = {
    "G90": "Absolute",
    "G91": "Incremental"}

FEED_MODE = {
    "G93": "1/Time",
    "G94": "unit/min",
    "G95": "unit/rev"}

UNITS = {
    "G20": "inch",
    "G21": "mm"}

PLANE = {
    "G17": "XY",
    "G18": "XZ",
    "G19": "YZ"}

STATE_CONN = "Connected"
STATE_NOT_CONN = "Not connected"

STATECOLOR = {
    "Idle": "Yellow",
    "Run": "LightGreen",
    "Alarm": "Red",
    "Jog": "Green",
    "Home": "Green",
    "Check": "Magenta2",
    "Sleep": "LightBlue",
    "Hold": "Orange",
    "Hold:0": "Orange",
    "Hold:1": "OrangeRed",
    "Queue": "OrangeRed",
    "Door": "Red",
    "Door:0": "OrangeRed",
    "Door:1": "Red",
    "Door:2": "Red",
    "Door:3": "OrangeRed",
    STATE_CONN: "Yellow",
    STATE_NOT_CONN: "OrangeRed",
    "Default": "LightYellow"
    }


"""these group of variable holds Tk references to various object
across the program, mainly:
    OCV.APP >
"""
TOLERANCE = 1e-7
# python3 doesn't have maxint it has sys.maxsize
# but i think setting a mximun value here is enough
MAXINT = 1000000000

# -- Regular expressions
AUXPAT = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")
BLOCKPAT = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
CMDPAT = re.compile(r"([A-Za-z]+)")
FEEDPAT = re.compile(r"^(.*)[fF](\d+\.?\d+)(.*)$")
GPAT = re.compile(r"[A-Za-z]\s*[-+]?\d+.*")
IDPAT = re.compile(r".*\bid:\s*(.*?)\)")
OPPAT = re.compile(r"(.*)\[(.*)\]")
PARENPAT = re.compile(r"(\(.*?\))")
# [\+\-]?[\d\.]+)\D?
POSPAT = re.compile(r"([XYZ]+):\s*([\+\-]?[\d\.]+)\D")
SEMIPAT = re.compile(r"(;.*)")

# -- GRBL States
STOP = 0
SKIP = 1
ASK = 2
MSG = 3
WAIT = 4
UPDATE = 5

XY = 0
XZ = 1
YZ = 2

CW = 2
CCW = 3

ERROR_HANDLING = {}

# These vars are to simplify and make clear the code around
# One name for one entity not var or self var or Module.var
# if used across many modules
root = None
# Main window
APP = None
# Bufferbar
BUFFERBAR = None
# Canvas
CANVAS = None
# CanvaFrame
CANVAS_F = None
# Command Entry
CMD_W = None
# Machine controller instance
MCTRL = None
# Main interface Ribbon
RIBBON = None
RUN_GROUP = None
# Statusbar
STATUSBAR = None

""" used to unify most of coordinates printout in Gcode and text strings
note the {3} parameter holding decimal precision """
sh_coord = "X: {0:0.{3}f} \nY: {1:0.{3}f} \nZ: {2:0.{3}f}"
gc_coord = "X: {0:.{3}f} Y: {1:.{3}f} Z: {2:.{3}f}"

"""Other variables in alphabetical order"""

# A #
acceleration_x = 25.0  # mm/s^2
acceleration_y = 25.0  # mm/s^2
acceleration_z = 25.0  # mm/s^2
accuracy = 0.01  # sagitta error during arc conversion
"""append feed on every G1/G2/G3 commands to be used
for feed override testing
will not be needed after Grbl v1.0
"""
appendFeed = False

# B #
blocks = []  # Gcode blocks, here to be shared
# b_mdata_xx variables holds Block metedata used in heuristic analisys
# ':' is used to quiclky separate string from values
b_mdata_sp = "(B_MD SP: X{0} Y{1} Z{2})"
b_mdata_ep = "(B_MD EP: X{0} Y{1} Z{2})"
b_mdata_zp = "(B_MD ZP: X{0} Y{1} Z{2})"
b_mdata_pz = "(B_MD PZ: Z{0})"

# C #
comment = ""  # last parsed comment
config = None
c_state = ""  # controller state to determine the state

# D #
DRAW_TIME = 5  # Maximum draw time permitted
developer = False
digits = 4
drillPolicy = 1  # Expand Canned cycles
drozeropad = 0

# E #
# theese command are parsed as a block end command after a G0 Z_max
end_cmds = ("M9", "M5", "M2", "M30")
errors = []
error_report = True

# F #
feedmax_x = 3000
feedmax_y = 3000
feedmax_z = 2000
first_move_detect = False

# G #
# gcodelines holds "plain" lines, readed from file, used by heuristic and
# other parts
gcodelines = ["(-)",]
# gcp_ vars are used in GCode.pre_process_gcode to signal some detection
gcp_mop_s = False  # 'MOP Start:' detection
gcp_mop_e = False  # 'MOP End:' detection
gcp_mop_name = ""

geometry = None
g_code_precision = 4
# holds the value of the detected post processor that generate the GCode file
# used in heuristic module to rearrange GCode in a proper manner
# values are "Generic" and "CamBam" to use the custom GRBL.cbpp present in
# OKKCNC/controllers dir that is taylored to supply some relevant metadata
g_code_pp = "Generic"


# H #
history = []

# I #
icons = {}
# This holds the interface widgets
iface_widgets = []
images = {}
inch = False
# hold infos used to display values
infos = []

# L #
language = ""
lasercutter = False
laseradaptive = False

# M #
memNum = 0
min_z = 0
max_z = 0
maxRecent = 10

# N #

# O #

# P #
post_proc = False
post_temp_fname = ""

# S #
serial_open = False
# hold the set commands that probably follow
set_cmds = ("G17", "G18", "G19", "G20", "G21")
startup = "G90"
stdexpr = False  # standard way of defining expressions with []
step1 = 0.0
step2 = 0.0
step3 = 0.0
step4 = 0.0
str_sep = "-"*78
str_pad = "-" + " "*76 + "-"
s_alarm = None
s_pause = None
s_running = None
s_runningPrev = None
s_stop = None
s_stop_req = None

# T #
toolPolicy = 1
"""
Should be in sync with ProbePage
0 > send to grbl
1 > skip those lines
2 > manual tool change (WCS)
3 > manual tool change (TLO)
4 > manual tool change (No Probe)
"""

toolWaitAfterProbe = True  # wait at tool change position after probing
travel_x = 300
travel_y = 300
travel_z = 60


# U #

unit = 1.0

# Z #
zstep1 = 0.0
zstep2 = 0.0
zstep3 = 0.0
zstep4 = 0.0

# W #
wcsvar = object

WK_active_mems = []
"""
    List containing the active mems
    one position for each mem
    hold the mem status
     0 empty
     1 set but not shown
     2 set and shown
"""

"""variables to manage the memory bank"""
WK_bank = 0
WK_bank_max = 3
WK_bank_start = 0
"""number of memories in Bank"""
WK_bank_mem = 9
"""Toggle used to whow the memory bank"""
WK_bank_show = []

WK_mem = 0  # pass memory number across the different program part
WK_mem_name = ""  # pass memory name across the different program part

"""
    dictionary containing memories data
    WK_mems[mem_name] = [mx,my,mz, set, desc]
    where mem_name a string like mem_N with N 0 > N < 49
    set is a flag 0 mem non set (used to inactivate a memory)
    desc is the memory name in tooltips (button and canvas)
    mem_0 is mem_A and mem_1 is mem_B and are treated in a special way
    they are working memories and not saved in the user file
    memories are saved in the configuration file <TODO>
"""
WK_mems = {}
WK_mem_num = 0

CD = {
    "prbx": 0.0,
    "prby": 0.0,
    "prbz": 0.0,
    "prbcmd": "G38.2",
    "prbfeed": 10.,
    "errline": "",
    "wx": 0.0,
    "wy": 0.0,
    "wz": 0.0,
    "mx": 0.0,
    "my": 0.0,
    "mz": 0.0,
    "wcox": 0.0,
    "wcoy": 0.0,
    "wcoz": 0.0,
    "curfeed": 0.0,
    "curspindle": 0.0,
    "_camwx": 0.0,
    "_camwy": 0.0,
    "G": [],
    "TLO": 0.0,
    "motion": "G0",
    "WCS": "G54",
    "plane": "G17",
    "feedmode": "G94",
    "distance": "G90",
    "arc": "G91.1",
    "units": "G20",
    "cutter": "",
    "tlo": "",
    "program": "M0",
    "spindle": "M5",
    "coolant": "M9",

    "tool": 0,
    "feed": 0.0,
    "rpm": 0.0,

    "planner": 0,
    "rxbytes": 0,

    "OvFeed": 100,    # Override status
    "OvRapid": 100,
    "OvSpindle": 100,
    "_OvChanged": False,
    "_OvFeed": 100,    # Override target values
    "_OvRapid": 100,
    "_OvSpindle": 100,

    "diameter": 3.175,    # Tool diameter
    "cutfeed": 1000.,    # Material feed for cutting
    "cutfeedz": 500.,    # Material feed for cutting
    "safe": 3.,
    "state": "",
    "pins": "",
    "msg": "",
    "stepz": 1.,
    "surface": 0.,
    "thickness": 5.,
    "stepover": 40.,

    "PRB": None,

    "version": "",
    "controller": "",
    "running": False,
    }


def printout_header(message, content):
    """printout a padded text using message with a {0} for the content"""
    # str_sep is 78 chr long as 80 chr is the conventional terminal line length
    # compensate using 80 for the {} in the message
    msg_length = len(message) + len(str(content))
    pad_str = "-" + " "*((80 - msg_length)//2)
    pad2_str = " "*(80 - len(pad_str) - msg_length) + "-"
    info_str = pad_str + message + pad2_str
    print(str_sep)
    print(str_pad)
    print(info_str.format(content))
    print(str_pad)
    print(str_sep)


def printout_infos(messages):
    """printout a padded text using formatted string in a list"""
    # str_sep is 78 chr long as 80 chr is the conventional terminal line length
    print(str_sep)
    print(str_pad)

    for message in messages:
        msg_length = len(message)
        pad_str = "-" + " "*((77 - msg_length)//2)
        pad2_str = " "*(77 - len(pad_str) - msg_length) + "-"
        info_str = pad_str + message + pad2_str
        print(info_str)
        print(str_pad)

    print(str_sep)


def showC(x_val, y_val, z_val):
    return sh_coord.format(x_val, y_val, z_val, digits)

# TODO uniform the metadata in CAMGen with those used by heuristic
# gcodeCC is used only in CAMGen
def gcodeCC(x_val, y_val, z_val):
    return gc_coord.format(x_val, y_val, z_val, g_code_precision)


def fmt(c, val, precision=None):
    """Number formating"""
    if precision is None:
        precision = digits
    # Don't know why, but in some cases floats are not truncated
    # by format string unless rounded
    # I guess it's vital idea to round them rather than truncate anyway!
    r_val = round(val, precision)
    # return ("{0}{2:0.{1}f}".format(c,d,v)).rstrip("0").rstrip(".")
    return "{0}{2:0.{1}f}".format(c, precision, r_val)
