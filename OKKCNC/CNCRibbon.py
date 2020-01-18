# -*- coding: ascii -*-
"""CNCRibbon.py


Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
import Ribbon
import tkExtra


class _LinkApp:
    """Link to main app"""
    def __init__(self, app):
        self.app = app

    def addWidget(self, widget):
        """Add a widget in the widgets list
        to enable disable during the run
        """
        OCV.iface_widgets.append(widget)

    def sendGCode(self, cmd):
        """Send a command to Grbl"""
        self.app.sendGCode(cmd)

    def acceptKey(self, skipRun=False):
        """Accept the user key if not editing any text"""
        self.app.acceptKey(skipRun)

    def saveConfig(self):
        pass

    def loadConfig(self):
        pass


class ButtonGroup(Ribbon.LabelGroup, _LinkApp):
    """Button Group, a group of widgets that will be placed in the ribbon"""
    def __init__(self, master, name, app):
        Ribbon.LabelGroup.__init__(self, master, name)
        _LinkApp.__init__(self, app)
        if ":" in name:
            self.label["text"] = name.split(":")[1]


class ButtonMenuGroup(Ribbon.MenuGroup, _LinkApp):
    """Button Group, a group of widgets that will be placed in the ribbon"""
    def __init__(self, master, name, app, menulist=None):
        Ribbon.MenuGroup.__init__(self, master, name, menulist)
        _LinkApp.__init__(self, app)


class PageFrame(Tk.Frame, _LinkApp):
    """Page, Frame"""
    def __init__(self, master, name, app):
        Tk.Frame.__init__(self, master)
        _LinkApp.__init__(self, app)
        self.name = name


class PageLabelFrame(Tk.LabelFrame, _LinkApp):
    """Page, LabelFrame"""
    def __init__(self, master, name, name_alias_lng, app):
        Tk.LabelFrame.__init__(
            self, master, text=name_alias_lng, foreground="DarkBlue")
        _LinkApp.__init__(self, app)
        self.name = name


class PageExLabelFrame(tkExtra.ExLabelFrame, _LinkApp):
    """Page, ExLabelFrame"""
    def __init__(self, master, name, name_alias_lng, app):
        tkExtra.ExLabelFrame.__init__(
            self, master, text=name_alias_lng, foreground="DarkBlue")
        _LinkApp.__init__(self, app)
        self.name = name


class Page(Ribbon.Page):
    """CNC Page interface between the basic Page class and the OKKCNC class"""
    groups = {}
    frames = {}

    def __init__(self, master, app, **kw):
        self.app = app
        Ribbon.Page.__init__(self, master, **kw)
        self.register()

        # print("Page self.app> ", self.app)
        # print("Page master > ", master)

    def register(self):
        """Should be overridden with the groups and frames to register"""
        pass

    def _register(self, groups, frames):
        """Register groups"""
        if groups:
            for g in groups:
                w = g(self.master._ribbonFrame, self.app)
                Page.groups[w.name] = w

        if frames:
            for f in frames:
                w = f(self.master._pageFrame, self.app)
                Page.frames[w.name] = w

    def addWidget(self, widget):
        """Add a widget in the widgets list to enable disable during the run"""
        OCV.iface_widgets.append(widget)

    def sendGCode(self, cmd):
        """Send a command to Grbl"""
        self.app.sendGCode(cmd)

    def addRibbonGroup(self, name, **args):
        if not args:
            args = {"side": Tk.LEFT, "fill": Tk.BOTH}
        self.ribbons.append((Page.groups[name], args))

    def addPageFrame(self, name, **args):
        if not args:
            args = {"side": Tk.TOP, "fill": Tk.BOTH}
        if isinstance(name, str):
            self.frames.append((Page.frames[name], args))
        else:
            self.frames.append((name, args))

    @staticmethod
    def saveConfig():
        for frame in Page.frames.values():
            frame.saveConfig()

    @staticmethod
    def loadConfig():
        for frame in Page.frames.values():
            frame.loadConfig()
