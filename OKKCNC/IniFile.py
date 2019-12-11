# -*- coding: ascii -*-
"""Interface.py

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import os
import gettext

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

try:
    import __builtin__
except:
    import builtins as __builtin__
#    __builtin__.unicode = str        # dirty hack for python3

import OCV
import Utils

__builtin__._ = gettext.translation(
    'OKKCNC',
    os.path.join(OCV.PRG_PATH, 'locale'),
    fallback=True).gettext

__builtin__.N_ = lambda message: message

_errorReport = True


def conf_file_load(only_from_system_ini=False):
    """Load configuration"""
    global _errorReport

    if only_from_system_ini is True:
        OCV.config.read(OCV.SYS_CONFIG)
    else:
        OCV.config.read([OCV.SYS_CONFIG, OCV.USER_CONFIG])
        _errorReport = get_int("Connection", "errorreport", 1)

        OCV.language = get_str(OCV.PRGNAME, "language")
        if OCV.language:
            # replace language
            __builtin__._ = gettext.translation(
                OCV.PRGNAME,
                os.path.join(OCV.PRG_PATH, 'locale'),
                fallback=True,
                languages=[OCV.language]).gettext


def set_value(section, name, value):
    """write value to configuration"""
    if isinstance(value, bool):
        OCV.config.set(section, name, str(int(value)))
    else:
        OCV.config.set(section, name, str(value))


def get_str(section, name, default=""):
    """retrieve a string from configuration"""
    try:
        return OCV.config.get(section, name)
    except Exception:
        return default


def get_int(section, name, default=0):
    """retrieve an integer from configuration"""
    try:
        return int(OCV.config.get(section, name))
    except Exception:
        return default


def get_float(section, name, default=0.0):
    """retrieve a float from configuration"""
    try:
        return float(OCV.config.get(section, name))
    except Exception:
        return default


def get_bool(section, name, default=False):
    """retrieve a boolean from configuration"""
    try:
        return bool(int(OCV.config.get(section, name)))
    except Exception:
        return default


def remove_config_item(section, name):
    """remove unused item from configuration"""
    if OCV.config.has_option(section, name):
        OCV.config.remove_option(section, name)


def get_recent_file(recent):
    try:
        return OCV.config.get("File", "recent.{0}".format(recent))
    except ConfigParser.NoOptionError:
        return None


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


def user_conf_file_save():
    """Save configuration file to disk"""
    clean_configuration()
    file_handler = open(OCV.USER_CONFIG, "w")
    OCV.config.write(file_handler)
    file_handler.close()
    Utils.del_icons()


def clean_configuration():
    """Remove items in user configuration file
    that are present with the same value in the default ini
    prior to save the userc onfiguration file to disk
    """
    # Remember config
    newconfig = OCV.config
    OCV.config = ConfigParser.ConfigParser()

    # load configuration items from system ini file
    conf_file_load(True)

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


def loadHistory():
    try:
        f = open(OCV.COMMAND_HISTORY, "r")
    except Exception:
        return
    OCV.history = [x.strip() for x in f]
    OCV.APP._historySearch = None
    f.close()


def save_command_history():
    try:
        f = open(OCV.COMMAND_HISTORY, "w")
    except Exception:
        return
    f.write("\n".join(OCV.history))
    f.close()


def load_colors():
    """Load Interface Colors"""
    OCV.ACTIVE_COLOR = get_str(
        "Color", "ribbon.active", OCV.ACTIVE_COLOR)

    OCV.LABEL_SELECT_COLOR = get_str(
        "Color", "ribbon.select", OCV.LABEL_SELECT_COLOR)

    OCV.INSERT_COLOR = get_str(
        "Color", "canvas.insert", OCV.INSERT_COLOR)

    OCV.GANTRY_COLOR = get_str(
        "Color", "canvas.gantry", OCV.GANTRY_COLOR)

    OCV.MARGIN_COLOR = get_str(
        "Color", "canvas.margin", OCV.MARGIN_COLOR)

    OCV.GRID_COLOR = get_str(
        "Color", "canvas.grid",  OCV.GRID_COLOR)

    OCV.BOX_SELECT = get_str(
        "Color", "canvas.selectbox", OCV.BOX_SELECT)

    OCV.ENABLE_COLOR = get_str(
        "Color", "canvas.enable", OCV.ENABLE_COLOR)

    OCV.DISABLE_COLOR = get_str(
        "Color", "canvas.disable", OCV.DISABLE_COLOR)

    OCV.SELECT_COLOR = get_str(
        "Color", "canvas.select", OCV.SELECT_COLOR)

    OCV.SELECT2_COLOR = get_str(
        "Color", "canvas.select2", OCV.SELECT2_COLOR)

    OCV.PROCESS_COLOR = get_str(
        "Color", "canvas.process", OCV.PROCESS_COLOR)

    OCV.MOVE_COLOR = get_str(
        "Color", "canvas.move", OCV.MOVE_COLOR)

    OCV.RULER_COLOR = get_str(
        "Color", "canvas.ruler", OCV.RULER_COLOR)
    OCV.CAMERA_COLOR = get_str(
        "Color", "canvas.camera",  OCV.CAMERA_COLOR)

    OCV.PROBE_TEXT_COLOR = get_str(
        "Color", "canvas.probetext", OCV.PROBE_TEXT_COLOR)

    OCV.CANVAS_COLOR = get_str(
        "Color", "canvas.background", OCV.CANVAS_COLOR)


def load_memories():
    """ load saved WK_bank_max and WK_bank_num values from config file,
    fill and init memory variables and saved memory data
    """
    OCV.WK_mem_num = ((OCV.WK_bank_max + 1) * OCV.WK_bank_mem) + 1
    OCV.WK_active_mems = []

    for idx in range(0, OCV.WK_mem_num + 1):
        OCV.WK_active_mems.append(0)

    OCV.WK_bank_show = []

    for idx in range(0, OCV.WK_bank_max + 1):
        OCV.WK_bank_show.append(0)

    for name, value in OCV.config.items("Memory"):
        content = value.split(",")
        # print("Key: {0}  Name: {1} Value: X{2} Y{3} Z{4}".format(
        #     name, *content ))
        OCV.WK_mems[name] = [
            float(content[1]),
            float(content[2]),
            float(content[3]),
            1,
            content[0]]
    # print("Load Memory ended")


def save_memories():
    """save memories values in config file"""
    for mem_name in OCV.WK_mems:
        mem_data = OCV.WK_mems[mem_name]
        # Test the indicator and delete the memory from config if
        # indicator = 0
        if mem_data[3] is not 0:
            mem_value = "{0}, {1:.4f}, {2:.4f}, {3:.4f}, {4:d}".format(
                mem_data[4], mem_data[0], mem_data[1], mem_data[2],
                mem_data[3])
            set_value("Memory", mem_name, mem_value)
        else:
            remove_config_item("Memory", mem_name)
