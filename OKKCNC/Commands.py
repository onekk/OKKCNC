#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:59:17 2019

@author: carlo
"""

try:
    import Tkinter as Tk
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import OCV
from _GenericGRBL import ERROR_CODES

#from Sender import ERROR_CODES

#----------------------------------------------------------------------
def setX0():
    OCV.mcontrol.wcs_set("0", None, None)
    RefreshMemories()


def setY0():
    OCV.mcontrol.wcs_set(None, "0", None)
    RefreshMemories()


def setZ0():
    OCV.mcontrol.wcs_set(None, None, "0")
    RefreshMemories()


def setXY0():
    OCV.mcontrol.wcs_set("0", "0", None)
    RefreshMemories()


def setXYZ0():
    OCV.mcontrol.wcs_set("0", "0", "0")
    RefreshMemories()


def workFocus():
    """Do not give the focus while we are running"""
    if OCV.application.running:
        OCV.application.focus_set()


def showState():
    err = OCV.CD["errline"]

    if err:
        msg = _("Last error: {0}\n").format(OCV.CD["errline"])
    else:
        msg = ""

    msg += ERROR_CODES.get(
        OCV.c_state,
        _("No info available.\nPlease contact the author."))

    tkMessageBox.showinfo(_("State: {0}").format(OCV.c_state),
                          msg, parent=OCV.application)


def RefreshMemories():
    for i in range(2, OCV.WK_mem_num):
        if OCV.WK_active_mems[i] == 2:
            OCV.canvas.memDraw(i)

#
# Misc functions
#

def padFloat(decimals, value):
    if decimals > 0:
        return "{0:0.{1}f".format(value, decimals)
    else:
        return value
