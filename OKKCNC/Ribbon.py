# -*- coding: ascii -*-
"""Ribbon.py


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
import Utils
import tkExtra

# Ribbon show state
RIBBON_HIDDEN = 0  # Hidden
RIBBON_SHOWN = 1   # Displayed
RIBBON_TEMP = -1   # Show temporarily


class LabelGroup(Tk.Frame):
    """Frame Group with a button at bottom"""
    def __init__(self, master, name, command=None, **kw):
        Tk.Frame.__init__(self, master, **kw)
        self.name = name
        self.config(
            background=OCV.BACKGROUND,
            borderwidth=0,
            highlightthickness=0,
            pady=0)

        # right frame as a separator
        sep = Tk.Frame(
            self,
            borderwidth=2,
            relief=Tk.GROOVE,
            background=OCV.BACKGROUND_DISABLE)

        sep.pack(side=Tk.RIGHT, fill=Tk.Y, padx=0, pady=0)

        # frame to insert the buttons
        self.frame = Tk.Frame(
            self,
            background=OCV.BACKGROUND,
            padx=0,
            pady=0)

        self.frame.pack(side=Tk.TOP, expand=Tk.TRUE,
                        fill=Tk.BOTH, padx=0, pady=0)

        if command:
            self.label = LabelButton(
                self,
                self,
                "<<{0}>>".format(name),
                text=name)

            self.label.config(
                command=command,
                image=OCV.icons["triangle_down"],
                foreground=OCV.FOREGROUND_GROUP,
                background=OCV.BACKGROUND_GROUP,
                highlightthickness=0,
                borderwidth=0,
                pady=0,
                compound=Tk.RIGHT)
        else:
            self.label = Tk.Label(
                self,
                text=_(name),
                font=OCV.RIBBON_FONT,
                foreground=OCV.FOREGROUND_GROUP,
                background=OCV.BACKGROUND_GROUP,
                padx=2,
                pady=0)    # Button takes 1px for border width

        self.label.pack(side=Tk.BOTTOM, fill=Tk.X, pady=0)

    def grid2rows(self):
        """grid2rows"""
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

    def grid3rows(self):
        """grid3rows"""
        self.grid2rows()
        self.frame.grid_rowconfigure(2, weight=1)


class _KeyboardFocus(object):
    """_KeyboardFocus class"""

    def _bind(self):
        self.bind("<Return>", self._invoke)
        self.bind("<FocusIn>", self._focusIn)
        self.bind("<FocusOut>", self._focusOut)

    def _focusIn(self, event):
        self.__backgroundColor = self.cget("background")
        self.config(background=OCV.ACTIVE_COLOR)

    def _focusOut(self, event):
        self.config(background=self.__backgroundColor)

    def _invoke(self, event):
        self.invoke()


class LabelButton(Tk.Button, _KeyboardFocus):
    """Button with Label that generates a Virtual Event or calls a command"""
    def __init__(self, master, recipient=None, event=None, **kw):
        Tk.Button.__init__(self, master, **kw)
        self.config(
            relief=Tk.FLAT,
            activebackground=OCV.ACTIVE_COLOR,
            font=OCV.RIBBON_FONT,
            borderwidth=1,
            highlightthickness=0,
            padx=2,
            pady=0)
        _KeyboardFocus._bind(self)

        if recipient is not None:
            self.config(command=self.sendEvent)
            self._recipient = recipient
            self._event = event
        else:
            self._recipient = None
            self._event = None

    def sendEvent(self):
        self._recipient.event_generate(self._event)


class LabelCheckbutton(Tk.Checkbutton, _KeyboardFocus):
    def __init__(self, master, **kw):
        Tk.Checkbutton.__init__(self, master, **kw)
        self.config(
            selectcolor=OCV.LABEL_SELECT_COLOR,
            activebackground=OCV.ACTIVE_COLOR,
            background=OCV.BACKGROUND,
            indicatoron=0,
            relief=Tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            font=OCV.RIBBON_FONT
        )

        _KeyboardFocus._bind(self)


class LabelRadiobutton(Tk.Radiobutton, _KeyboardFocus):
    def __init__(self, master, **kw):
        Tk.Radiobutton.__init__(self, master, **kw)
        self.config(
            selectcolor=OCV.LABEL_SELECT_COLOR,
            activebackground=OCV.ACTIVE_COLOR,
            background=OCV.BACKGROUND,
            indicatoron=0,
            borderwidth=0,
            highlightthickness=0,
            pady=0,
            font=OCV.RIBBON_FONT
        )

        _KeyboardFocus._bind(self)


class LabelCombobox(tkExtra.Combobox, _KeyboardFocus):
    def __init__(self, master, **kw):
        tkExtra.Combobox.__init__(self, master, **kw)

        self.config(background=OCV.BACKGROUND, font=OCV.RIBBON_FONT)

        Tk.Frame.config(self, background=OCV.BACKGROUND, padx=0, pady=0)

        _KeyboardFocus._bind(self)

    def _focusOut(self, event):
        self.config(background=OCV.BACKGROUND)

        Tk.Frame.config(self, background=OCV.BACKGROUND)


class MenuButton(Tk.Button, _KeyboardFocus):
    """Button with Label that popup a menu"""
    def __init__(self, master, menulist, **kw):
        Tk.Button.__init__(self, master, **kw)
        self.config(
            relief=Tk.FLAT,
            activebackground=OCV.ACTIVE_COLOR,
            font=OCV.RIBBON_FONT,
            borderwidth=0,
            highlightthickness=0,
            padx=2,
            pady=0,
            command=self.showMenu)

        _KeyboardFocus._bind(self)
        self.bind("<Return>", self.showMenu)

        if menulist is not None:
            self._menu = MenuButton.createMenuFromList(self, menulist)
        else:
            self._menu = None

    def showMenu(self, event=None):
        if self._menu is not None:
            self._showMenu(self._menu)
        else:
            self._showMenu(self.createMenu())

    def _showMenu(self, menu):
        if menu is not None:
            menu.tk_popup(
                self.winfo_rootx(),
                self.winfo_rooty() + self.winfo_height())

    def createMenu(self):
        return None

    @staticmethod
    def createMenuFromList(master, menulist):
        mainmenu = menu = Tk.Menu(
            master,
            tearoff=0,
            activebackground=OCV.ACTIVE_COLOR)

        for item in menulist:
            if item is None:
                menu.add_separator()
            elif isinstance(item, str):
                menu = Tk.Menu(mainmenu)
                mainmenu.add_cascade(label=item, menu=menu)
            else:
                name, icon, cmd = item

                if icon is None:
                    icon = "empty"

                menu.add_command(
                    label=name,
                    image=OCV.icons[icon],
                    compound=Tk.LEFT,
                    command=cmd)

        return menu


class MenuGroup(LabelGroup):
    """A label group with a drop down menu"""
    def __init__(self, master, name, menulist=None, **kw):
        LabelGroup.__init__(self, master, name, command=self._showMenu, **kw)
        self._menulist = menulist

    def createMenu(self):
        if self._menulist is not None:
            return MenuButton.createMenuFromList(self, self._menulist)
        else:
            return None

    def _showMenu(self):
        menu = self.createMenu()
        if menu is not None:
            menu.tk_popup(
                self.winfo_rootx(),
                self.winfo_rooty() + self.winfo_height())


class TabButton(Tk.Radiobutton):
    """Page Tab buttons"""
    def __init__(self, master, **kw):
        Tk.Radiobutton.__init__(self, master, **kw)
        self.config(
            selectcolor=OCV.BACKGROUND,
            activebackground=OCV.ACTIVE_COLOR,
            indicatoron=0,
            relief=Tk.FLAT,
            font=OCV.RIBBON_TABFONT,
            borderwidth=0,
            highlightthickness=0,
            padx=5,
            pady=0,
            background=OCV.BACKGROUND_DISABLE
        )

        self.bind("<FocusIn>", self._focusIn)
        self.bind("<FocusOut>", self._focusOut)

    def bindClicks(self, tabframe):
        """Bind events on TabFrame"""
        self.bind("<Double-1>", tabframe.double)
        self.bind("<Button-1>", tabframe.dragStart)
        self.bind("<B1-Motion>", tabframe.drag)
        self.bind("<ButtonRelease-1>", tabframe.dragStop)
        self.bind("<Control-ButtonRelease-1>", tabframe.pinActive)

        self.bind("<Left>", tabframe._tabLeft)
        self.bind("<Right>", tabframe._tabRight)
        self.bind("<Down>", tabframe._tabDown)

    def _focusIn(self, evenl=None):
        self.config(selectcolor=OCV.ACTIVE_COLOR)

    def _focusOut(self, evenl=None):
        self.config(selectcolor=OCV.BACKGROUND)


class Page(object):  # <--- should be possible to be a toplevel as well
    """Page"""
    _motionClasses = (
        LabelButton,
        LabelRadiobutton,
        LabelCheckbutton,
        LabelCombobox,
        MenuButton)

    _name_ = None

    _icon_ = None

    _doc_ = "Tooltip"

    def __init__(self, master, **kw):
        self.master = master
        self.name = self._name_
        self._icon = OCV.icons[self._icon_]
        self._tab = None  # Tab button
        self.ribbons = []
        self.frames = []
        self.init()
        self.create()

    def init(self):
        """Override initialization"""
        pass

    def create(self):
        """The tab page can change master if undocked"""
        self.createPage()

    def createPage(self):
        self.page = Tk.Frame(self.master._pageFrame)
        return self.page

    def activate(self):
        """Called when a page is activated"""
        pass

    def refresh(self):
        pass

    def canUndo(self):
        return True

    def canRedo(self):
        return True

    def resetUndo(self):
        pass

    def undo(self, event=None):
        pass

    def redo(self, event=None):
        pass

    def refreshUndoButton(self):
        """Check if frame provides undo/redo"""
        if self.master is None:
            return

        if self.page is None:
            return

        if self.canUndo():
            state = Tk.NORMAL
        else:
            state = Tk.DISABLED

        self.master.tool["undo"].config(state=state)
        self.master.tool["undolist"].config(state=state)

        if self.canRedo():
            state = Tk.NORMAL
        else:
            state = Tk.DISABLED

        self.master.tool["redo"].config(state=state)

    def keyboardFocus(self):
        self._tab.focus_set()

    @staticmethod
    def __compareDown(x, y, xw, yw):
        """Return the closest widget in Up direction"""
        return yw > y+1

    @staticmethod
    def __compareUp(x, y, xw, yw):
        """Return the closest widget in Down direction"""
        return yw < y-1

    @staticmethod
    def __compareRight(x, y, xw, yw):
        """Return the closest widget in Right direction"""
        return xw > x+1

    @staticmethod
    def __compareLeft(x, y, xw, yw):
        """Return the closest widget in Left direction"""
        return xw < x-1

    @staticmethod
    def __closest(widget, compare, x, y):
        closest = None
        dc2 = 10000000

        if widget is None:
            return closest, dc2

        for child in widget.winfo_children():

            for class_ in Page._motionClasses:

                if isinstance(child, class_):

                    if child["state"] == Tk.DISABLED:
                        continue

                    xw = child.winfo_rootx()
                    yw = child.winfo_rooty()

                    if compare(x, y, xw, yw):
                        d2 = (xw-x)**2 + (yw-y)**2
                        if d2 < dc2:
                            closest = child
                            dc2 = d2
                    break
            else:
                c, d2 = Page.__closest(child, compare, x, y)
                if d2 < dc2:
                    closest = c
                    dc2 = d2
        return closest, dc2

    def _ribbonUp(self, event=None):
        """Select/Focus the closest Up element"""
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty()
        closest, d2 = Page.__closest(self.ribbon, Page.__compareUp, x, y)
        if closest is not None:
            closest.focus_set()

    def _ribbonDown(self, event=None):
        """Select/Focus the closest Down element"""
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty()
        closest, d2 = Page.__closest(self.ribbon, Page.__compareDown, x, y)
        if closest is not None:
            closest.focus_set()

    def _ribbonLeft(self, event=None):
        """Select/Focus the closest Left element"""
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty()
        closest, d2 = Page.__closest(self.ribbon, Page.__compareLeft, x, y)
        if closest is not None:
            closest.focus_set()

    def _ribbonRight(self, event=None):
        """Select/Focus the closest Righth element"""
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty()
        closest, d2 = Page.__closest(self.ribbon, Page.__compareRight, x, y)
        if closest is not None:
            closest.focus_set()


class TabRibbonFrame(Tk.Frame):
    """TabRibbonFrame"""
    def __init__(self, master, **kw):
        Tk.Frame.__init__(self, master, kw)
        self.config(background=OCV.BACKGROUND_DISABLE)

        self.oldActive = None
        self.activePage = Tk.StringVar(self)
        self.tool = {}
        self.pages = {}

        # === Top frame with buttons ===
        frame = Tk.Frame(self, background=OCV.BACKGROUND_DISABLE)
        frame.pack(side=Tk.TOP, fill=Tk.X)

        # --- Basic buttons ---
        but = LabelButton(
            frame,
            self,
            "<<New>>",
            image=OCV.icons["new"],
            background=OCV.BACKGROUND_DISABLE)

        tkExtra.Balloon.set(but, _("New file"))

        but.pack(side=Tk.LEFT)

        but = LabelButton(
            frame,
            self,
            "<<Open>>",
            image=OCV.icons["load"],
            background=OCV.BACKGROUND_DISABLE)

        tkExtra.Balloon.set(but, _("Open file [Ctrl-O]"))

        but.pack(side=Tk.LEFT)

        but = LabelButton(
            frame,
            self,
            "<<Save>>",
            image=OCV.icons["save"],
            background=OCV.BACKGROUND_DISABLE)

        tkExtra.Balloon.set(but, _("Save all [Ctrl-S]"))

        but.pack(side=Tk.LEFT)

        but = LabelButton(
            frame,
            self, "<<Undo>>",
            image=OCV.icons["undo"],
            background=OCV.BACKGROUND_DISABLE)

        tkExtra.Balloon.set(but, _("Undo [Ctrl-Z]"))

        but.pack(side=Tk.LEFT)

        self.tool["undo"] = but

        but = LabelButton(
            frame,
            image=OCV.icons["triangle_down"],
            command=self.undolist,
            background=OCV.BACKGROUND_DISABLE)

        but.pack(side=Tk.LEFT)

        self.tool["undolist"] = but

        but = LabelButton(
            frame,
            self,
            "<<Redo>>",
            image=OCV.icons["redo"],
            background=OCV.BACKGROUND_DISABLE)

        tkExtra.Balloon.set(but, _("Redo [Ctrl-Y]"))

        but.pack(side=Tk.LEFT)

        self.tool["redo"] = but

        lab = Tk.Label(
            frame,
            image=OCV.icons["sep"],
            background=OCV.BACKGROUND_DISABLE)

        lab.pack(side=Tk.LEFT, padx=3)

        but = LabelButton(
            frame,
            self,
            "<<Help>>",
            image=OCV.icons["info"],
            background=OCV.BACKGROUND_DISABLE)

        tkExtra.Balloon.set(but, _("Help [F1]"))

        but.pack(side=Tk.RIGHT, padx=2)

        lab = Tk.Label(
            frame,
            image=OCV.icons["sep"],
            background=OCV.BACKGROUND_DISABLE)

        lab.pack(side=Tk.RIGHT, padx=3)

        # --- TabBar ---
        self._tabFrame = Tk.Frame(frame, background=OCV.BACKGROUND_DISABLE)
        self._tabFrame.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=Tk.YES)

        # ==== Ribbon Frame ====
        self._ribbonFrame = Tk.Frame(
            self,
            background=OCV.BACKGROUND,
            pady=0,
            relief=Tk.RAISED)

        self._ribbonFrame.pack(fill=Tk.BOTH, expand=Tk.YES, padx=0, pady=0)

        self.setPageFrame(None)

    def setPageFrame(self, frame):
        self._pageFrame = frame

    def undolist(self, event=None):
        self.event_generate("<<UndoList>>")

    def getActivePage(self):
        return self.pages[self.activePage.get()]

    def addPage(self, page, side=Tk.LEFT):
        """Add page to the tabs"""
        self.pages[page.name] = page
        page._tab = TabButton(
            self._tabFrame,
            image=page._icon,
            text=_(page.name),
            compound=Tk.LEFT,
            value=page.name,
            variable=self.activePage,
            command=self.changePage)

        tkExtra.Balloon.set(page._tab, page.__doc__)

        page._tab.pack(side=side, fill=Tk.Y, padx=5)

    def _forgetPage(self):
        """Unpack the old page"""
        if self.oldActive:
            for frame, args in self.oldActive.ribbons:
                frame.pack_forget()

            for frame, args in self.oldActive.frames:
                frame.pack_forget()

            self.oldActive = None

    def changePage(self, page=None):
        """Change ribbon and page"""
#       import traceback
#       traceback.print_stack()

        if page is not None:
            if not isinstance(page, Page):
                try:
                    page = self.pages[page]
                except KeyError:
                    return
            self.activePage.set(page.name)
        else:
            try:
                page = self.pages[self.activePage.get()]
            except KeyError:
                return

        if page is self.oldActive:
            return

        self._forgetPage()

        for frame, args in page.ribbons:
            frame.pack(in_=self._ribbonFrame, **args)

        for frame, args in page.frames:
            frame.pack(in_=self._pageFrame, **args)

        self.oldActive = page
        page.activate()
        self.event_generate("<<ChangePage>>", data=page.name)
