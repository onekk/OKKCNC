#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 15:21:49 2019

@author: carlo
"""

acceleration_x = 25.0    # mm/s^2
acceleration_y = 25.0    # mm/s^2
acceleration_z = 25.0    # mm/s^2
accuracy       = 0.01    # sagitta error during arc conversion
appendFeed       = False    # append feed on every G1/G2/G3 commands to be used
                # for feed override testing
                # FIXME will not be needed after Grbl v1.0

# C #
comment        = ""    # last parsed comment

# D #
developer      = False
digits         = 4
drillPolicy    = 1        # Expand Canned cycles
drozeropad     = 0

# F #
feedmax_x      = 3000
feedmax_y      = 3000
feedmax_z      = 2000

# I #
inch           = False

# L #
lasercutter    = False
laseradaptive  = False


# M #
memNum = 0

# S #
startup        = "G90"
stdexpr        = False    # standard way of defining expressions with []
step1 = 0.0
step2 = 0.0
step3 = 0.0
step4 = 0.0

# T #
toolPolicy     = 1        # Should be in sync with ProbePage
                # 0 - send to grbl
                # 1 - skip those lines
                # 2 - manual tool change (WCS)
                # 3 - manual tool change (TLO)
                # 4 - manual tool change (No Probe)
toolWaitAfterProbe = True    # wait at tool change position after probing
travel_x       = 300
travel_y       = 300
travel_z       = 60

# Z #
zstep1 = 0.0
zstep2 = 0.0
zstep3 = 0.0
zstep4 = 0.0

# W #
WK_mem = 0 # used to pass the memory number across the different program part

# dictionary containing memories data
# WK_mems[mem_name] = [mBx,mBy,mBz,set]
# where mem_name a string like mem_N with N 0 > N < 99
# mem_0 is mem_A and mem_1 is mem_B and are treated in a special way
# memories are saved in the configuration file <TODO>
WK_mems = {}
WK_bank = 0;

ACTIVE_COLOR       = "LightYellow"
BACKGROUND         = "#E6E2E0"
BACKGROUND_DISABLE = "#A6A2A0"
BACKGROUND_GROUP   = "#B6B2B0"
BACKGROUND_GROUP2  = "#B0C0C0"
BACKGROUND_GROUP3  = "#A0C0A0"
BACKGROUND_GROUP4  = "#B0C0A0"
BLOCK_COLOR   = "LightYellow"
BOX_SELECT    = "Cyan"
CAMERA_COLOR  = "Cyan"
CANVAS_COLOR  = "White"
COMMENT_COLOR = "Blue"
DISABLE_COLOR = "LightGray"
ENABLE_COLOR  = "Black"
FOREGROUND_GROUP   = "White"
GANTRY_COLOR  = "Red"
GRID_COLOR    = "Gray"
INFO_COLOR    = "Gold"
INSERT_COLOR  = "Blue"
LABEL_SELECT_COLOR = "#C0FFC0"
MARGIN_COLOR  = "Magenta"
MEM_COLOR     = "Orchid1"
MOVE_COLOR    = "DarkCyan"
PROBE_TEXT_COLOR = "Green"
PROCESS_COLOR = "Green"
RULER_COLOR   = "Green"
SELECT_COLOR  = "Blue"
SELECT2_COLOR = "DarkCyan"
TAB_COLOR     = "DarkOrange"
TABS_COLOR    = "Orange"
WORK_COLOR    = "Orange"


CD = {
    "prbx"       : 0.0,
    "prby"       : 0.0,
    "prbz"       : 0.0,
    "prbcmd"     : "G38.2",
    "prbfeed"    : 10.,
    "errline"    : "",
    "wx"         : 0.0,
    "wy"         : 0.0,
    "wz"         : 0.0,
    "mx"         : 0.0,
    "my"         : 0.0,
    "mz"         : 0.0,
    "wcox"       : 0.0,
    "wcoy"       : 0.0,
    "wcoz"       : 0.0,
    "curfeed"    : 0.0,
    "curspindle" : 0.0,
    "_camwx"     : 0.0,
    "_camwy"     : 0.0,
    "G"          : [],
    "TLO"        : 0.0,
    "motion"     : "G0",
    "WCS"        : "G54",
    "plane"      : "G17",
    "feedmode"   : "G94",
    "distance"   : "G90",
    "arc"        : "G91.1",
    "units"      : "G20",
    "cutter"     : "",
    "tlo"        : "",
    "program"    : "M0",
    "spindle"    : "M5",
    "coolant"    : "M9",

    "tool"       : 0,
    "feed"       : 0.0,
    "rpm"        : 0.0,

    "planner"    : 0,
    "rxbytes"    : 0,

    "OvFeed"     : 100,    # Override status
    "OvRapid"    : 100,
    "OvSpindle"  : 100,
    "_OvChanged" : False,
    "_OvFeed"    : 100,    # Override target values
    "_OvRapid"   : 100,
    "_OvSpindle" : 100,

    "diameter"   : 3.175,    # Tool diameter
    "cutfeed"    : 1000.,    # Material feed for cutting
    "cutfeedz"   : 500.,    # Material feed for cutting
    "safe"       : 3.,
    "state"      : "",
    "pins"       : "",
    "msg"        : "",
    "stepz"      : 1.,
    "surface"    : 0.,
    "thickness"  : 5.,
    "stepover"   : 40.,

    "PRB"        : None,
    "TLO"        : 0.,

    "version"    : "",
    "controller" : "",
    "running"    : False,
    }

