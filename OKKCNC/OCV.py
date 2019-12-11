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

PRGNAME = "OKKCNC"
PRG_PATH = os.path.abspath(os.path.dirname(__file__))

if getattr(sys, 'frozen', False):
    # When being bundled by pyinstaller, paths are different
    print("Running as pyinstaller bundle!", sys.argv[0])
    PRG_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

SYS_CONFIG = os.path.join(PRG_PATH, "{0}.ini".format(PRGNAME))
USER_CONFIG = os.path.expanduser("~/.{0}".format(PRGNAME))
COMMAND_HISTORY = os.path.expanduser("~/.{0}.history".format(PRGNAME))

"""version and date"""
PG_VER = "0.2.0-dev"
PG_DATE = "26 Dec 2019"

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


DEBUG = False
GRAP_DEBUG = True
INT_DEBUG = False
COM_DEBUG = True

HAS_SERIAL = None
IS_PY3 = False

FONT = ("Sans", "-10")
EXE_FONT = ("Helvetica", 12, "bold")
RIBBON_TABFONT = ("Sans", "-14", "bold")
RIBBON_FONT = ("Sans", "-11")

DRO_ZERO_FONT = ("Sans", "-11")

STATE_WCS_FONT = ("Helvetica", "-14")
STATE_BUT_FONT = ("Sans", "-11")

FONT_SECTION = "Font"

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

IDPAT = re.compile(r".*\bid:\s*(.*?)\)")
PARENPAT = re.compile(r"(\(.*?\))")
SEMIPAT = re.compile(r"(;.*)")
OPPAT = re.compile(r"(.*)\[(.*)\]")
CMDPAT = re.compile(r"([A-Za-z]+)")
BLOCKPAT = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
AUXPAT = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")

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

""" used to simplify mosto of the coordinates in Gcode and text strings"""
sh_coord = "X: {0:0.{3}f} \nY: {1:0.{3}f} \nZ: {2:0.{3}f}"
gc_coord = "X: {0:.{3}f} Y: {1:.{3}f} Z: {2:.{3}f}"

"""Other variables in alphabetical order"""

# A #
acceleration_x = 25.0  # mm/s^2
acceleration_y = 25.0  # mm/s^2
acceleration_z = 25.0  # mm/s^2
accuracy = 0.01  # sagitta error during arc conversion
appendFeed = False  # append feed on every G1/G2/G3 commands to be used
                    # for feed override testing
                    # FIXME will not be needed after Grbl v1.0

# C #
comment = ""  # last parsed comment
config = None
c_state = ""  # controller state to determine the state

# D #
DRAW_TIME = 5  # Maximum draw time permitted
developer = False
digits = 3
drillPolicy = 1  # Expand Canned cycles
drozeropad = 0

# F #
feedmax_x = 3000
feedmax_y = 3000
feedmax_z = 2000

# G #
geometry = None

# H #
history = []

# I #
icons = {}
# This holds the interface widgets
iface_widgets = []
images = {}
inch = False

# L #
language = ""
lasercutter = False
laseradaptive = False

# M #
maxRecent = 10
memNum = 0

# S #
serial_open = False
startup = "G90"
stdexpr = False  # standard way of defining expressions with []
step1 = 0.0
step2 = 0.0
step3 = 0.0
step4 = 0.0
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

WK_mem = 0 # pass memory number across the different program part
WK_mem_name = "" # pass memory name across the different program part

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
    "TLO": 0.,

    "version": "",
    "controller": "",
    "running": False,
    }

# INTERFACE COLORS #
ACTIVE_COLOR = "LightYellow"
BACKGROUND = "#E6E2E0"
BACKGROUND_LABELS = "pale green"
BACKGROUND_DISABLE = "#A6A2A0"
BACKGROUND_GROUP = "#B6B2B0"
BACKGROUND_GROUP2 = "#B0C0C0"
BACKGROUND_GROUP3 = "#A0C0A0"
BACKGROUND_GROUP4 = "#B0C0A0"
BLOCK_COLOR = "LightYellow"
BOX_SELECT = "Cyan"
CAMERA_COLOR = "Cyan"
CANVAS_COLOR = "White"
COMMENT_COLOR = "Blue"
DISABLE_COLOR = "LightGray"
ENABLE_COLOR = "Black"
FOREGROUND_GROUP = "White"
GANTRY_COLOR = "Red"
GRID_COLOR = "Gray"
INFO_COLOR = "Gold"
INSERT_COLOR = "Blue"
LABEL_SELECT_COLOR = "#C0FFC0"
LISTBOX_NUMBER = "khaki1"
LISTBOX_SEP = "aquamarine"
LISTBOX_TEXT = "azure"
LISTBOX_VAL = "AntiqueWhite1"
MARGIN_COLOR = "Magenta"
MEM_COLOR = "Orchid1"
MOVE_COLOR = "DarkCyan"
PROBE_TEXT_COLOR = "Green"
PROCESS_COLOR = "Green"
RULER_COLOR = "Green"
SELECT_COLOR = "Blue"
SELECT2_COLOR = "DarkCyan"
TAB_COLOR = "DarkOrange"
TABS_COLOR = "Orange"
WORK_COLOR = "Orange"

def showC(X, Y, Z):
    return sh_coord.format(X, Y, Z, digits)

def gcodeCC(X, Y, Z):
    return gc_coord.format(X, Y, Z, digits)
