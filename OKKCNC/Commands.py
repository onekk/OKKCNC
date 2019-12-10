# -*- coding: ascii -*-
"""Commands.py

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""


try:
    import Tkinter as Tk
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import OCV
from _GenericGRBL import ERROR_CODES


def set_x0():
    OCV.MCTRL.wcs_set("0", None, None)
    RefreshMemories()


def set_y0():
    OCV.MCTRL.wcs_set(None, "0", None)
    RefreshMemories()


def set_z0():
    OCV.MCTRL.wcs_set(None, None, "0")
    RefreshMemories()


def set_xy0():
    OCV.MCTRL.wcs_set("0", "0", None)
    RefreshMemories()


def set_xyz0():
    OCV.MCTRL.wcs_set("0", "0", "0")
    RefreshMemories()


def work_focus():
    """Do not give the focus while we are running"""
    if OCV.s_running:
        OCV.APP.focus_set()


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
                          msg, parent=OCV.APP)

def RefreshMemories():
    for i in range(2, OCV.WK_mem_num):
        if OCV.WK_active_mems[i] == 2:
            OCV.CANVAS.memDraw(i)


def get_errors():
    err_list = [value for key, value in ERROR_CODES.items() if 'error:' in key.lower()]
    return err_list
#
# Misc functions
#

def padFloat(decimals, value):
    if decimals > 0:
        return "{0:0.{1}f".format(value, decimals)
    else:
        return value
