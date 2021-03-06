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

AUTHOR = "Carlo Dormeletti (onekk)"
AUT_EMAIL = "carlo.dormeletti@gmail.com"

PLATFORM = "({0} py{1}.{2}.{3})".format(
        sys.platform, sys.version_info.major, sys.version_info.minor,
        sys.version_info.micro)

PRG_NAME = "OKKCNC"
"""version and date"""
PRG_VER = "0.3.38-t2"
PRG_DATE = "23 nov 2020"
CONF_VER = "1.1"
PRG_DEV_HOME = "https://github.com/onekk/OKKCNC"

PRG_PATH = os.path.abspath(os.path.dirname(__file__))

if getattr(sys, 'frozen', False):
    # When being bundled by pyinstaller, paths are different
    print("Running as pyinstaller bundle!", sys.argv[0])
    PRG_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

init_msg = []

if sys.version_info[0] == 3:
    IS_PY3 = True
    init_msg.append("OKKCNC Python v3.x version.\n")
    init_msg.append(
        "Please report any error through github page {0}\n".format(
            PRG_DEV_HOME))

    warn_msg = "".join(init_msg)

    sys.stdout.write("="*80+"\n")
    sys.stdout.write(warn_msg)
    sys.stdout.write("="*80+"\n")

    TITLE_MSG = ""

else:
    IS_PY3 = False
    init_msg.append("END OF LIFE WARNING!!!\n")
    init_msg.append("OKKCNC Python v2.x version ")
    init_msg.append("is at his end of life.\n")
    init_msg.append("As python 2.x is offcially")
    init_msg.append("no longer mantained.\n")
    init_msg.append("see: \n{0} \nfor more info \n".format(PRG_DEV_HOME))

    warn_msg = "".join(init_msg)

    sys.stdout.write("="*80+"\n")
    sys.stdout.write(warn_msg)
    sys.stdout.write("="*80+"\n")

    TITLE_MSG = "end of life"

HOME_DIR = os.path.expanduser("~/")
CONF_DIR = os.path.expanduser("~/.config/{0}".format(PRG_NAME))

if os.path.isdir(CONF_DIR):
    U_CONF_NAME = "config.ini"
    U_HIST_NAME = "history"
else:
    CONF_DIR = HOME_DIR
    U_CONF_NAME = ".{0}".format(PRG_NAME)
    U_HIST_NAME = ".{0}.history".format(PRG_NAME)

SYS_CONFIG = os.path.join(PRG_PATH, "{0}.ini".format(PRG_NAME))
USER_CONFIG = os.path.join(CONF_DIR, U_CONF_NAME)
COM_HIST_FILE = os.path.join(CONF_DIR, U_HIST_NAME)
HELP_FILE = os.path.join(PRG_PATH, "OKKCNC.help")


if os.path.isfile(USER_CONFIG):
    print("User configuration file: {}".format(USER_CONFIG))
else:
    print("Creating User configuration File: {}".format(USER_CONFIG))
    orig = open(SYS_CONFIG, 'r')
    dest = open(USER_CONFIG, 'w')
    
    for line in orig:
        dest.writelines(line)

    orig.close()
    dest.close()    

#--- Direction seems not needed anymore
#CW = 2
#CCW = 3

""" used to unify most of coordinates printout in Gcode and text strings
note the {3} parameter holding decimal precision """
sh_coord = "X: {0:0.{3}f} \nY: {1:0.{3}f} \nZ: {2:0.{3}f}"
gc_coord = "X: {0:.{3}f} Y: {1:.{3}f} Z: {2:.{3}f}"

"""Other variables in alphabetical order"""

#--- A #
acceleration_x = 25.0  # mm/s^2
acceleration_y = 25.0  # mm/s^2
acceleration_z = 25.0  # mm/s^2
accuracy = 0.01  # sagitta error during arc conversion
"""append feed on every G1/G2/G3 commands to be used
for feed override testing
will not be needed after Grbl v1.0
"""
appendFeed = False

#--- B #
blocks = []  # Gcode blocks, here to be shared
""" blocks_info is used in GCode.process_block indes is given by block_pos
    list items:
    0 > block start line (the line in OCV.gcodlines)
    1 > number of added lines to keep in sync with OCV.gcodelines
"""
blocks_ev = []  # blocks events, used by pre_process_gcode
blocks_info = []
#  to keep tracks on which block we are working
blocks_pos = 0
# to keep tracks of adde line in the block during event processing
block_add_l = 0
# #

# b_mdata_xx variables holds Block metedata used in heuristic analisys
# ':' is used to quiclky separate string from values
b_mdata_h = "(BMD:"
b_mdata_mc = "CUTMOV from"
b_mdata_mczf = "CUTZF from"
b_mdata_mcz = "Z_PASS: at"
b_mdata_mcfz = "FZ_PASS: at"
b_mdata_mcxy = "CUTXY at"
b_mdata_mr = "RAPMOV from"
b_mdata_ss = "[{0}][{1}]"


#--- C #
cb_dig = 3  # number of decimal displayed in the controlframe comboboxes
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

#--- Planes
CNC_XY = 0
CNC_XZ = 1
CNC_YZ = 2


# INTERFACE COLORS
"""See Inifile.py/load_colors()
values with comments Above are the corresponding item names in IniFile
"""
COLOR_ACTION_GANTRY = "seashell"
COLOR_ACTION_WPOS = "ivory"
# "ribbon.active"
COLOR_ACTIVE = "LightYellow"
COLOR_BG = "#E6E2E0"
COLOR_BG_DISABLE = "#A6A2A0"
# used in some label, entry and window background
COLOR_BG1 = "white"
COLOR_BG2 = "khaki"
COLOR_BG3 = "pale green"
COLOR_BG_RUN = "DarkGray"
COLOR_BG_SAFE = "lightgreen"
COLOR_BG_WRN = "salmon"

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
# "canvas.mems"
COLOR_MEM = "Orchid1"
COLOR_MEM_SET = "Aquamarine"
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


comment = ""  # last parsed comment
config = None
c_pgm_end = False
# controller state to determine the state
c_state = ""
# controllers errors (only for GBRL for now)
CTL_ERRORS = []
# controllers errors (only for GBRL for now)
CTL_SHELP = []

#--- D #
"""Debug flags. used across the interface to print debug info on terminal
    the debug comment
    Debug Flags are set in config.ini and read at program start
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
# Debug SerialIO
DEBUG_SER = False
# debug GCode parsing
DEBUG_PAR = False
# set level of info displayed in Heuristic, 0 - 4
DEBUG_HEUR = 3
#
DRAW_TIME = 5  # Maximum draw time permitted
developer = False
digits = 4
DISTANCE_MODE = {
    "G90": "Absolute",
    "G91": "Incremental"}
drillPolicy = 1  # Expand Canned cycles
drozeropad = 0

#--- E #
# theese command are parsed as a block end command after a G0 Z_max
end_cmds = ("M9", "M5", "M2", "M30")
errors = []
ERROR_HANDLING = {}
error_report = True

#--- F #
feedmax_x = 3000
feedmax_y = 3000
feedmax_z = 2000
FEED_MODE = {
    "G93": "1/Time",
    "G94": "unit/min",
    "G95": "unit/rev"}
first_move_detect = False
# INTERFACE FONTS
FONT = ("Sans", "-10")
# About text font
FONT_ABOUT_DESC = ('Helvetica', '-15', 'bold')
FONT_ABOUT_TEXT = ('Helvetica', '-12', 'normal')
FONT_ABOUT_TITLE = ('Helvetica', '-17', 'bold')
# ---
FONT_DRO_ZERO = ("Sans", "-11")
FONT_EXE = ("Helvetica", 12, "bold")
FONT_RIBBON_TAB = ("Sans", "-14", "bold")
FONT_RIBBON = ("Sans", "-11")
FONT_STATE_WCS = ("Helvetica", "-14")
FONT_STATE_BUT = ("Sans", "-11")
# Font section name in Config file.
FONT_SEC_NAME = "Font"

#--- G #
# gcodelines holds "plain" lines, readed from file, used by heuristic and
# other parts
gcodelines = ["(-)",]
# gcp_ vars are used in GCode.pre_process_gcode to signal some detection
gcp_mop_s = False  # 'MOP Start:' detection
gcp_mop_e = False  # 'MOP End:' detection
gcp_mop_name = ""

# gctos hold the lines added to the queue to track the executed lines during
# a program run
gctos = []

geometry = None
g_code_precision = 4
# holds the value of the detected post processor that generate the GCode file
# used in heuristic module to rearrange GCode in a proper manner
# values are "Generic" and "CamBam" to use the custom GRBL.cbpp present in
# OKKCNC/controllers dir that is taylored to supply some relevant metadata
g_code_pp = "Generic"

#--- GRBL States some seems not needed
#GSTATE_STOP = 0
GSTATE_SKIP = 1
#GSTATE_ASK = 2
GSTATE_MSG = 3
GSTATE_WAIT = 4
GSTATE_UPDATE = 5

#--- H #
HAS_SERIAL = None  # flag
history = []

#--- I #
icons = {}
# This holds the interface widgets
iface_widgets = []
images = {}
inch = False
# hold infos used to display values
infos = []

#--- L #
language = ""
lasercutter = False
laseradaptive = False

#--- M #
# python3 doesn't have maxint it has sys.maxsize
MAXINT = 1000000000
maxRecent = 10
memNum = 0
min_z = 0
max_z = 0

mop_vars = {}
# N #

# O #

#--- P #
PLANE = {
    "G17": "XY",
    "G18": "XZ",
    "G19": "YZ"}
post_proc = False
post_temp_fname = ""
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
    "Italian - @onekk\n" # \ for continuation


pslist_xy = []
pslist_z= []
# positional index for the step cycling xy
pstep_xy = 0
# positional index for the step cycling z
pstep_z = 0
# Z predefined steps
psz1 = 0.0
psz2 = 0.0
psz3 = 0.0
psz4 = 0.0
# XY predefined steps
psxy1 = 0.0
psxy2 = 0.0
psxy3 = 0.0
psxy4 = 0.0


#--- R #
#--- Regular expressions
RE_AUX = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")
RE_BLOCK = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
RE_CMD = re.compile(r"([A-Za-z]+)")
RE_FEED = re.compile(r"^(.*)[fF](\d+\.?\d+)(.*)$")
RE_GCODE = re.compile(r"[A-Za-z]\s*[-+]?\d+.*")
RE_ID = re.compile(r".*\bid:\s*(.*?)\)")
RE_OP = re.compile(r"(.*)\[(.*)\]")
RE_PAREN = re.compile(r"(\(.*?\))")
# [\+\-]?[\d\.]+)\D?
RE_POS = re.compile(r"([XYZ]+):\s*([\+\-]?[\d\.]+)\D")
RE_SEMI = re.compile(r"(;.*)")

#--- S #
serial_open = False
# hold the set commands that probably follow
set_cmds = ("G17", "G18", "G19", "G20", "G21")
startup = "G90"
STATE_CONN = "Connected"
STATE_NOT_CONN = "Not connected"
# not following the alphabetic order as it contains the two variables above
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
    "Default": "LightYellow"}
stdexpr = False  # standard way of defining expressions with []
stepxy = 0.0
stepz = 0.0

#
str_sep = "-"*78
str_pad = "-" + " "*76 + "-"
s_alarm = None
s_pause = None
s_running = None
s_runningPrev = None
# used in SIO it signal a request to stop sending lines see Sender code
s_stop = None
# used by Sender.stopRun to signal a stop request
s_stop_req = None

#--- T #
"""these group of variable holds Tk references to various object
across the program, to simplify and make clear the code:
    One name for one entity not var or self var or Module.var
"""

TK_ROOT = None
# Main window
TK_MAIN = None
# About window, needed to have a reference for the close function
TK_ABOUT = None
# Bufferbar
TK_BUFFERBAR = None
# Canvas
TK_CANVAS = None
# CanvasFrame
TK_CANVAS_F = None
# Command Entry
TK_CMD_W = None
# ControlPanel used for memory events
TK_CONTROL = None
# EditorFrame.editor 
TK_EDITOR = None
# Machine controller instance
TK_MCTRL = None
# MOP window
TK_MOP = None
# Main interface Ribbon
TK_RIBBON = None
TK_RUN_GROUP = None
# Statusbar
TK_STATUSBAR = None
# TerminalFrame.buffer
TK_TERMBUF = None
# TerminalFrame.terminal
TK_TERMINAL = None

TOLERANCE = 1e-7

"""
Should be in sync with ProbePage
0 > send to grbl
1 > skip those lines
2 > manual tool change (WCS)
3 > manual tool change (TLO)
4 > manual tool change (No Probe)
"""
toolPolicy = 1
# wait at tool change position after probing
toolWaitAfterProbe = True
tooltable = []
travel_x = 300
travel_y = 300
travel_z = 60

#--- U #
unit = 1.0
UNITS = {
    "G20": "inch",
    "G21": "mm"}

#--- Z #


#--- W #
WCS = ["G54", "G55", "G56", "G57", "G58", "G59"]
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
    WK_mems[mem_name] = [mx,my,mz, set, desc]
    dictionary containing memories data
      mem_name = dictionary key defined as string
                 mem_N with N 0 > N < [(Wk_bank_max + 1) * Wk_bank_mem] + 1
                 so with bank_max = 3 and bank_mem = 9 is [4 * 9] + 1 = 37 
      set    = flag 0 mem non set (used to inactivate a memory)
      desc   = memory description shown in tooltips (button and canvas)
   
    memory positions are kept in MCS (Machine Coordinates)
    
    mem_0 is mem_A and mem_1 is mem_B these memories are special ones
    position values are kept in WCS (Working coordinates, 
    as they are used to calculate GCode commands in WCS plane
"""
WK_mems = {}
WK_mem_num = 0

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
