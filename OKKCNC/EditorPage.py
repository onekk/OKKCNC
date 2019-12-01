# -*- coding: ascii -*-
"""EditorPage.py


Credits:
    this module code is based on bCNC
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
import tkExtra
import Utils
import Ribbon
import CNCList
import CNCRibbon

from CNCCanvas import ACTION_MOVE, ACTION_ORIGIN


class ClipboardGroup(CNCRibbon.ButtonGroup):
    """Clipboard Group"""

    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Clipboard"), app)
        self.grid2rows()

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Paste>>",
            image=Utils.icons["paste32"],
            text=_("Paste"),
            compound=Tk.TOP,
            takefocus=Tk.FALSE,
            background=OCV.BACKGROUND)

        b.grid(row=0, column=0, rowspan=2, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Paste [Ctrl-V]"))

        self.addWidget(b)

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Cut>>",
            image=Utils.icons["cut"],
            text=_("Cut"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            takefocus=Tk.FALSE,
            background=OCV.BACKGROUND)

        tkExtra.Balloon.set(b, _("Cut [Ctrl-X]"))

        b.grid(row=0, column=1, padx=0, pady=1, sticky=Tk.NSEW)

        self.addWidget(b)

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Copy>>",
            image=Utils.icons["copy"],
            text=_("Copy"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            takefocus=Tk.FALSE,
            background=OCV.BACKGROUND)

        tkExtra.Balloon.set(b, _("Copy [Ctrl-C]"))

        b.grid(row=1, column=1, padx=0, pady=1, sticky=Tk.NSEW)

        self.addWidget(b)


class SelectGroup(CNCRibbon.ButtonGroup):
    """Select Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Select"), app)
        self.grid3rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame,
            app,
            "<<SelectAll>>",
            image=Utils.icons["select_all"],
            text=_("All"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Select all blocks [Ctrl-A]"))

        self.addWidget(b)

        col += 1
        b = Ribbon.LabelButton(
            self.frame,
            app,
            "<<SelectNone>>",
            image=Utils.icons["select_none"],
            text=_("None"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Unselect all blocks [Ctrl-Shift-A]"))

        self.addWidget(b)

        col, row = 0, 1

        b = Ribbon.LabelButton(
            self.frame,
            app,
            "<<SelectInvert>>",
            image=Utils.icons["select_invert"],
            text=_("Invert"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Invert selection [Ctrl-I]"))

        self.addWidget(b)

        col += 1
        b = Ribbon.LabelButton(
            self.frame,
            app,
            "<<SelectLayer>>",
            image=Utils.icons["select_layer"],
            text=_("Layer"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Select all blocks from current layer"))

        self.addWidget(b)

        col, row = 0, 2
        self.filterString = tkExtra.LabelEntry(
            self.frame,
            _("Filter"),
            "DarkGray",
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            width=16)

        self.filterString.grid(
            row=row,
            column=col,
            columnspan=2,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(self.filterString, _("Filter blocks"))

        self.addWidget(self.filterString)

        self.filterString.bind("<Return>", self.filter)
        self.filterString.bind("<KP_Enter>", self.filter)

    def filter(self, event=None):
        txt = self.filterString.get()
        OCV.APP.insertCommand("FILTER {0}".format(txt), True)


class EditGroup(CNCRibbon.ButtonMenuGroup):
    """Edit Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(
            self, master,
            N_("Edit"),
            app,
            [(_("Autolevel"), "level",
              lambda a=app: a.insertCommand("AUTOLEVEL", True)),
             (_("Color"), "color",
              lambda a=app: a.event_generate("<<ChangeColor>>")),
             (_("Import"), "load",
              lambda a=app: a.insertCommand("IMPORT", True)),
             (_("Postprocess Inkscape g-code"), "inkscape",
              lambda a=app: a.insertCommand("INKSCAPE all", True)),
             (_("Round"), "digits",
              lambda s=app: s.insertCommand("ROUND", True))
            ])
        self.grid3rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<Add>>",
            image=Utils.icons["add"],
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Insert a new block or line of code [Ins or Ctrl-Enter]"))

        self.addWidget(b)

        menulist = [
            (_("Line"),
             "add",
             lambda a=OCV.APP: a.event_generate("<<AddLine>>")),
            (_("Block"),
             "add",
             lambda a=OCV.APP: a.event_generate("<<AddBlock>>"))]

        b = Ribbon.MenuButton(
            self.frame,
            menulist,
            text=_("Add"),
            image=Utils.icons["triangle_down"],
            compound=Tk.RIGHT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)
        b.grid(row=row, column=col+1, padx=0, pady=0, sticky=Tk.NSEW)
        tkExtra.Balloon.set(
            b,
            _("Insert a new block or line of code [Ins or Ctrl-Enter]"))

        row += 1
        b = Ribbon.LabelButton(
            self.frame,
            app,
            "<<Clone>>",
            image=Utils.icons["clone"],
            text=_("Clone"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(
            row=row,
            column=col,
            columnspan=2,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Clone selected lines or blocks [Ctrl-D]"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            app,
            "<<Delete>>",
            image=Utils.icons["x"],
            text=_("Delete"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(
            row=row,
            column=col,
            columnspan=2,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Delete selected lines or blocks [Del]"))

        self.addWidget(b)

        col, row = 2, 0

        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<EnableToggle>>",
            image=Utils.icons["toggle"],
            # text=_("Toggle"),
            # compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Toggle enable/disable block of g-code [Ctrl-L]"))

        self.addWidget(b)

        menulist = [
            (_("Enable"), "enable",
             lambda a=OCV.APP: a.event_generate("<<Enable>>")),
            (_("Disable"), "disable",
             lambda a=OCV.APP: a.event_generate("<<Disable>>"))]

        b = Ribbon.MenuButton(
            self.frame,
            menulist,
            text=_("Active"),
            image=Utils.icons["triangle_down"],
            compound=Tk.RIGHT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col+1, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Enable or disable blocks of gcode"))

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<Expand>>",
            image=Utils.icons["expand"],
            text=_("Expand"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(
            row=row,
            column=col,
            columnspan=2,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Toggle expand/collapse blocks of gcode [Ctrl-E]"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<Comment>>",
            image=Utils.icons["comment"],
            text=_("Comment"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, columnspan=2, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("(Un)Comment selected lines"))

        self.addWidget(b)
        # ---
        col += 2
        row = 0
        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<Join>>",
            image=Utils.icons["union"],
            text=_("Join"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, columnspan=2, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Join selected blocks"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<Split>>",
            image=Utils.icons["cut"],
            text=_("Split"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, columnspan=2, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Split selected blocks"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            OCV.APP,
            "<<ClearEditor>>",
            image=Utils.icons["clear"],
            text=_("Clear All"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(
            row=row,
            column=col,
            columnspan=2,
            padx=0, pady=0,
            sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Clear Editor Window"))

        self.addWidget(b)


class MoveGroup(CNCRibbon.ButtonMenuGroup):
    """Move Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(self, master, N_("Move"), app)
        self.grid3rows()

        col, row = 0, 0

        b = Ribbon.LabelRadiobutton(
            self.frame,
            image=Utils.icons["move32"],
            text=_("Move"),
            compound=Tk.TOP,
            anchor=Tk.W,
            variable=OCV.APP.canvasFrame.canvas.actionVar,
            value=ACTION_MOVE,
            command=OCV.APP.canvasFrame.canvas.setActionMove,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Move objects [M]"))

        self.addWidget(b)

        col += 1

        b = Ribbon.LabelRadiobutton(
            self.frame,
            image=Utils.icons["origin32"],
            text=_("Origin"),
            compound=Tk.TOP,
            anchor=Tk.W,
            variable=OCV.APP.canvasFrame.canvas.actionVar,
            value=ACTION_ORIGIN,
            command=OCV.APP.canvasFrame.canvas.setActionOrigin,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Move all gcode such as origin is on mouse location [O]"))

        self.addWidget(b)

    def createMenu(self):
        menu = Tk.Menu(self, tearoff=0)
        for i, n, c in (
                ("tl", _("Top-Left"), "MOVE TL"),
                ("lc", _("Left"), "MOVE LC"),
                ("bl", _("Bottom-Left"), "MOVE BL"),
                ("tc", _("Top"), "MOVE TC"),
                ("center", _("Center"), "MOVE CENTER"),
                ("bc", _("Bottom"), "MOVE BC"),
                ("tr", _("Top-Right"), "MOVE TR"),
                ("rc", _("Right"), "MOVE RC"),
                ("br", _("Bottom-Right"), "MOVE BR")):

            menu.add_command(
                label=n,
                image=Utils.icons[i],
                compound=Tk.LEFT,
                command=lambda a=OCV.APP, c=c: a.insertCommand(c, True))

        return menu


class OrderGroup(CNCRibbon.ButtonMenuGroup):
    """ Order Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(
            self,
            master,
            N_("Order"),
            app,
            [(_("Optimize"),
              "optimize",
              lambda a=app: a.insertCommand("OPTIMIZE", True)),
            ])

        self.grid2rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<Control-Key-Prior>",
            image=Utils.icons["up"],
            text=_("Up"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Move selected g-code up [Ctrl-Up, Ctrl-PgUp]"))

        self.addWidget(b)

        # ---
        row += 1
        b = Ribbon.LabelButton(
            self.frame, self, "<Control-Key-Next>",
            image=Utils.icons["down"],
            text=_("Down"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Move selected g-code down [Ctrl-Down, Ctrl-PgDn]"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            self,
            "<<Invert>>",
            image=Utils.icons["swap"],
            text=_("Invert"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Invert cutting order of selected blocks"))

        self.addWidget(b)


class TransformGroup(CNCRibbon.ButtonGroup):
    """Transform Group"""
    def __init__(self, master, app):
        CNCRibbon.ButtonGroup.__init__(self, master, N_("Transform"), app)

        self.grid3rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["rotate_90"],
            text=_("CW"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("ROTATE CW", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Rotate selected gcode clock-wise (-90deg)"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["rotate_180"],
            text=_("Flip"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("ROTATE FLIP", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Rotate selected gcode by 180deg"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["rotate_270"],
            text=_("CCW"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("ROTATE CCW", True),
            background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)
        tkExtra.Balloon.set(b, _("Rotate selected gcode counter-clock-wise (90deg)"))
        self.addWidget(b)

        col, row = 1, 0

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["flip_horizontal"],
            text=_("Horizontal"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("MIRROR horizontal", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Mirror horizontally X=-X selected gcode"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["flip_vertical"],
            text=_("Vertical"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("MIRROR vertical", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Mirror vertically Y=-Y selected gcode"))

        self.addWidget(b)

#        submenu.add_command(label=_("Rotate command"), underline=0,
#                    command=lambda s=self:s.insertCommand("ROTATE ang x0 y0", False))


class RouteGroup(CNCRibbon.ButtonGroup):
    """Route Group"""
    def __init__(self, master, app):

        CNCRibbon.ButtonGroup.__init__(self, master, N_("Route"), app)

        self.grid3rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["conventional"],
            text=_("Conventional"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("DIRECTION CONVENTIONAL", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Change cut direction to conventional for selected gcode blocks"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["climb"],
            text=_("Climb"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("DIRECTION CLIMB", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Change cut direction to climb for selected gcode blocks"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["reverse"],
            text=_("Reverse"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("REVERSE", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Reverse cut direction for selected gcode blocks"))

        self.addWidget(b)

        col, row = 1, 0

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["rotate_90"],
            text=_("Cut CW"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("DIRECTION CW", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Change cut direction to CW for selected gcode blocks"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["rotate_270"],
            text=_("Cut CCW"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=lambda s=app: s.insertCommand("DIRECTION CCW", True),
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Change cut direction to CCW for selected gcode blocks"))

        self.addWidget(b)


class InfoGroup(CNCRibbon.ButtonGroup):
    """Info Group"""
    def __init__(self, master, app):

        CNCRibbon.ButtonGroup.__init__(self, master, N_("Info"), app)

        self.grid2rows()

        col, row = 0, 0

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["stats"],
            text=_("Statistics"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.APP.showStats,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(b, _("Show statistics for enabled gcode"))

        self.addWidget(b)

        row += 1

        b = Ribbon.LabelButton(
            self.frame,
            image=Utils.icons["info"],
            text=_("Info"),
            compound=Tk.LEFT,
            anchor=Tk.W,
            command=OCV.APP.showInfo,
            background=OCV.BACKGROUND)

        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(
            b,
            _("Show cutting information on selected blocks [Ctrl-n]"))

        self.addWidget(b)


class EditorFrame(CNCRibbon.PageFrame):
    """Main Frame of Editor"""
    def __init__(self, master, app):
        CNCRibbon.PageFrame.__init__(self, master, "Editor", app)
        self.editor = CNCList.CNCListbox(
            self,
            app,
            selectmode=Tk.EXTENDED,
            exportselection=0,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.editor.pack(side=Tk.LEFT, expand=Tk.TRUE, fill=Tk.BOTH)

        self.addWidget(self.editor)

        sb = Tk.Scrollbar(self, orient=Tk.VERTICAL, command=self.editor.yview)

        sb.pack(side=Tk.RIGHT, fill=Tk.Y)

        self.editor.config(yscrollcommand=sb.set)


class EditorPage(CNCRibbon.Page):
    """Editor Page"""
    __doc__ = _("GCode editor")
    _name_ = N_("Editor")
    _icon_ = "edit"

    def register(self):
        """Add a widget in the widgets list to enable disable during the run"""
        self._register(
            (ClipboardGroup, SelectGroup, EditGroup, MoveGroup,
             OrderGroup, TransformGroup, RouteGroup, InfoGroup),
            (EditorFrame,))
