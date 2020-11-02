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

import re

import OCV
from _GenericGRBL import ERROR_CODES, SETTINGS_CODES

def set_x0():
    OCV.TK_MCTRL.wcs_set("0", None, None)
    RefreshMemories()


def set_y0():
    OCV.TK_MCTRL.wcs_set(None, "0", None)
    RefreshMemories()


def set_z0():
    OCV.TK_MCTRL.wcs_set(None, None, "0")
    RefreshMemories()


def set_xy0():
    OCV.TK_MCTRL.wcs_set("0", "0", None)
    RefreshMemories()


def set_xyz0():
    OCV.TK_MCTRL.wcs_set("0", "0", "0")
    RefreshMemories()


def work_focus():
    """Do not give the focus while we are running"""
    if OCV.s_running:
        OCV.TK_APP.focus_set()


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
                          msg, parent=OCV.TK_APP)

def RefreshMemories():
    for i in range(2, OCV.WK_mem_num):
        if OCV.WK_active_mems[i] == 2:
            OCV.TK_CANVAS.memDraw(i)

#
# Misc functions
#

def padFloat(decimals, value):
    if decimals > 0:
        return "{0:0.{1}f".format(value, decimals)
    else:
        return value


def get_errors(ctl):
    err_list = []
    
    # debug code not to delete
    #print(ctl, ERROR_CODES)

    if ctl in ("GRBL0", "GRBL1"):
        pat_err = r'\b' + re.escape("error:") + r'\b'
        pat_alm = r'\b' + re.escape("ALARM:") + r'\b'
        int_list = [
            "error:{0:02d} >> {1}".format(int(key[6:]), value)
            for key, value in ERROR_CODES.items()
            if re.search(pat_err, key)]
        alm_list = [
            "ALARM:{0:02d} >> {1}".format(int(key[6:]), value)
            for key, value in ERROR_CODES.items()
            if re.search(pat_alm, key)]
        int_list.extend(alm_list)
    else:
        # I don't know other controllers behaviour
        # Maybe Wrong
        pattern = r'\b' + re.escape("error:") + r'\b'
        int_list = [
            "{0} > {1}".format(key, value)
            for key, value in ERROR_CODES.items()
            if re.search(pattern, key)]

    err_list = sorted(int_list)
    
    # debug code not to delete
    #print(int_list)

    OCV.CTL_ERRORS = err_list

def get_settings(ctl):
    settings_list = []
    
    # debug code not to delete
    #print(ctl, ERROR_CODES)

    if ctl in ("GRBL0", "GRBL1"):
        int_list = [
            "Setting: {0:03d} >> {1}".format(int(key), value)
            for key, value in SETTINGS_CODES.items()]
    else:
        pass

    setting_list = sorted(int_list)
    
    # debug code not to delete
    #print(int_list)

    OCV.CTL_SHELP = setting_list
