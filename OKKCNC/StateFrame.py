"""ControlPage.py


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
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import OCV
import CNCRibbon
import tkExtra

OVERRIDES = ["Feed", "Rapid", "Spindle"]


class StateFrame(CNCRibbon.PageExLabelFrame):
    """StateFrame"""
    def __init__(self, master, app):
        CNCRibbon.PageExLabelFrame.__init__(
            self, master, "State", _("State"), app)

        self._gUpdate = False

        # print("StateFrame self.app",self.app)

        # State
        frame = Tk.Frame(self())
        frame.pack(side=Tk.TOP, fill=Tk.X)

        col, row = 0, 0
        subframe = Tk.Frame(frame)
        subframe.grid(row=row, column=col, columnspan=5, sticky=Tk.EW)

        for p, w in enumerate(OCV.WCS):
            col += 1
            but = Tk.Radiobutton(
                subframe,
                text=w,
                foreground="DarkRed",
                font=OCV.STATE_WCS_FONT,
                padx=1, pady=1,
                variable=OCV.wcsvar,
                value=p,
                indicatoron=0,
                activebackground="LightYellow",
                command=self.wcsChange)

            but.pack(side=Tk.LEFT, fill=Tk.X, expand=Tk.YES)

            tkExtra.Balloon.set(but, _("Switch to workspace {0}").format(w))

            self.addWidget(but)

        row += 1

        label_text = (_("Distance:"), _("Units:"), _("Tool:"), _("Plane:"),
                      _("Feed:"), _("Mode:"), _("TLO:"), _("G92:"))
        label_pos = ((row, 0), (row, 3), (row + 1, 0), (row + 1, 3),
                     (row + 2, 0), (row + 2, 3), (row + 3, 0), (row + 3, 3))

        for idx, val in enumerate(label_text):
            lab = Tk.Label(
                frame,
                text=label_text[idx],
                font=OCV.STATE_BUT_FONT)

            lab.grid(
                row=label_pos[idx][0],
                column=label_pos[idx][1],
                sticky=Tk.E)

        # Absolute or relative mode
        col = 1

        self.distance = tkExtra.Combobox(
            frame,
            True,
            command=self.distanceChange,
            width=5,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.distance.fill(sorted(OCV.DISTANCE_MODE.values()))
        self.distance.grid(row=row, column=col, columnspan=2, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            g17_items = OCV.DISTANCE_MODE.items()
        else:
            g17_items = OCV.DISTANCE_MODE.viewitems()

        for key, val in g17_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(
            self.distance, _("Distance Mode:\n{0}".format(bal_text)))

        self.addWidget(self.distance)

        # populate gstate dictionary
        self.gstate = {}  # $G state results widget dictionary

        for key, val in g17_items:
            self.gstate[key] = (self.distance, val)

        col += 3

        self.units = tkExtra.Combobox(
            frame,
            True,
            command=self.unitsChange,
            width=5,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.units.fill(sorted(OCV.UNITS.values()))
        self.units.grid(row=row, column=col, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            unit_items = OCV.UNITS.items()
        else:
            unit_items = OCV.UNITS.viewitems()

        for key, val in unit_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(self.units, _("Units:\n{0}".format(bal_text)))

        for key, val in unit_items:
            self.gstate[key] = (self.units, val)

        self.addWidget(self.units)

        # Tool
        row += 1
        col = 1
        self.toolEntry = tkExtra.IntegerEntry(
            frame,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            width=5)

        self.toolEntry.grid(row=row, column=col, sticky=Tk.EW)

        tkExtra.Balloon.set(self.toolEntry, _("Tool number [T#]"))
        self.addWidget(self.toolEntry)

        col += 1

        but = Tk.Button(
            frame,
            text=_("set"),
            command=self.setTool,
            padx=1, pady=1)

        but.grid(row=row, column=col, sticky=Tk.W)
        self.addWidget(but)

        # Plane

        col += 2

        self.plane = tkExtra.Combobox(
            frame,
            True,
            command=self.planeChange,
            width=5,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.plane.fill(sorted(OCV.PLANE.values()))
        self.plane.grid(row=row, column=col, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            plane_items = OCV.PLANE.items()
        else:
            plane_items = OCV.PLANE.viewitems()

        for key, val in plane_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(self.plane, _("Plane:\n{0}".format(bal_text)))

        self.addWidget(self.plane)

        for k, v in plane_items:
            self.gstate[k] = (self.plane, v)

        # Feed speed
        row += 1
        col = 1
        self.feed_rate = tkExtra.FloatEntry(
            frame,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            disabledforeground="Black",
            width=5)

        self.feed_rate.grid(row=row, column=col, sticky=Tk.EW)
        self.feed_rate.bind('<Return>', self.setFeedRate)
        self.feed_rate.bind('<KP_Enter>', self.setFeedRate)

        tkExtra.Balloon.set(self.feed_rate, _("Feed Rate [F#]"))
        self.addWidget(self.feed_rate)

        col += 1

        but = Tk.Button(
            frame,
            text=_("set"),
            command=self.setFeedRate,
            padx=1, pady=1)

        but.grid(row=row, column=col, columnspan=2, sticky=Tk.W)
        self.addWidget(but)

        # Feed mode
        col += 2
        self.feedMode = tkExtra.Combobox(
            frame,
            True,
            command=self.feedModeChange,
            width=5,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND)

        self.feedMode.fill(sorted(OCV.FEED_MODE.values()))
        self.feedMode.grid(row=row, column=col, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            feed_items = OCV.FEED_MODE.items()
        else:
            feed_items = OCV.FEED_MODE.viewitems()

        for key, val in feed_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(
            self.feedMode, _("Feed Mode:\n{0}".format(bal_text)))

        for key, val in feed_items:
            self.gstate[key] = (self.feedMode, val)

        self.addWidget(self.feedMode)

        # TLO
        row += 1
        col = 1

        self.tlo = tkExtra.FloatEntry(
            frame,
            background=tkExtra.GLOBAL_CONTROL_BACKGROUND,
            disabledforeground="Black",
            width=5)

        self.tlo.grid(row=row, column=col, sticky=Tk.EW)
        self.tlo.bind('<Return>', self.setTLO)
        self.tlo.bind('<KP_Enter>', self.setTLO)
        tkExtra.Balloon.set(self.tlo, _("Tool length offset [G43.1#]"))
        self.addWidget(self.tlo)

        col += 1

        but = Tk.Button(
            frame,
            text=_("set"),
            command=self.setTLO,
            padx=1, pady=1)

        but.grid(row=row, column=col, columnspan=2, sticky=Tk.W)
        self.addWidget(but)

        # g92
        col += 2

        self.g92 = Tk.Label(frame, text="")

        self.g92.grid(row=row, column=col, columnspan=3, sticky=Tk.EW)

        tkExtra.Balloon.set(self.g92, _("Set position [G92 X# Y# Z#]"))
        self.addWidget(self.g92)

        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(4, weight=1)

        # Spindle
        frame1 = Tk.Frame(self())
        frame1.pack(side=Tk.BOTTOM, fill=Tk.X)

        self.override = Tk.IntVar()
        self.override.set(100)
        self.spindle = Tk.BooleanVar()
        self.spindleSpeed = Tk.IntVar()

        col, row = 0, 0

        self.overrideCombo = tkExtra.Combobox(
            frame1,
            width=8,
            command=self.overrideComboChange)

        self.overrideCombo.fill(OVERRIDES)
        self.overrideCombo.grid(row=row, column=col, pady=0, sticky=Tk.EW)

        tkExtra.Balloon.set(self.overrideCombo, _("Select override type."))

        but = Tk.Button(
            frame1,
            text=_("Reset"),
            pady=0,
            command=self.resetOverride)

        but.grid(row=row+1, column=col, pady=0, sticky=Tk.NSEW)

        tkExtra.Balloon.set(but, _("Reset override to 100%"))

        col += 1

        self.overrideScale = Tk.Scale(
            frame1,
            command=self.overrideChange,
            variable=self.override,
            showvalue=True,
            orient=Tk.HORIZONTAL,
            from_=25,
            to_=200,
            resolution=1)

        self.overrideScale.bind("<Double-1>", self.resetOverride)
        self.overrideScale.bind("<Button-3>", self.resetOverride)

        self.overrideScale.grid(
            row=row, column=col, rowspan=2, columnspan=4, sticky=Tk.EW)
        tkExtra.Balloon.set(
            self.overrideScale,
            _("Set Feed/Rapid/Spindle Override. Right or Double click to reset."))

        self.overrideCombo.set(OVERRIDES[0])

        row += 2
        col = 0

        but = Tk.Checkbutton(
            frame1,
            text=_("Spindle"),
            image=OCV.icons["spinningtop"],
            command=self.spindleControl,
            compound=Tk.LEFT,
            indicatoron=0,
            variable=self.spindle,
            padx=1,
            pady=0)

        tkExtra.Balloon.set(but, _("Start/Stop spindle (M3/M5)"))

        but.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(but)

        col += 1
        but = Tk.Scale(
            frame1,
            variable=self.spindleSpeed,
            command=self.spindleControl,
            showvalue=True,
            orient=Tk.HORIZONTAL,
            from_=OCV.config.get("CNC", "spindlemin"),
            to_=OCV.config.get("CNC", "spindlemax"))

        tkExtra.Balloon.set(but, _("Set spindle RPM"))
        but.grid(row=row, column=col, sticky=Tk.EW, columnspan=3)
        self.addWidget(but)

        frame1.grid_columnconfigure(1, weight=1)

        # Coolant control
        self.coolant = Tk.BooleanVar()
        self.mist = Tk.BooleanVar()
        self.flood = Tk.BooleanVar()

        row += 1
        col = 0
        Tk.Label(
            frame1,
            text=_("Coolant:")).grid(row=row, column=col, sticky=Tk.E)

        col += 1

        coolantDisable = Tk.Checkbutton(
            frame1,
            text=_("OFF"),
            command=self.coolantOff,
            indicatoron=0,
            variable=self.coolant,
            padx=1,
            pady=0)

        tkExtra.Balloon.set(coolantDisable, _("Stop cooling (M9)"))
        coolantDisable.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(coolantDisable)

        col += 1

        floodEnable = Tk.Checkbutton(
            frame1,
            text=_("Flood"),
            command=self.coolantFlood,
            indicatoron=0,
            variable=self.flood,
            padx=1,
            pady=0)

        tkExtra.Balloon.set(floodEnable, _("Start flood (M8)"))
        floodEnable.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(floodEnable)

        col += 1

        mistEnable = Tk.Checkbutton(
            frame1,
            text=_("Mist"),
            command=self.coolantMist,
            indicatoron=0,
            variable=self.mist,
            padx=1,
            pady=0)

        tkExtra.Balloon.set(mistEnable, _("Start mist (M7)"))
        mistEnable.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(mistEnable)

        frame1.grid_columnconfigure(1, weight=1)

        # DEBUG
        # print(self.gstate)

    def overrideChange(self, event=None):
        n_val = self.overrideCombo.get()
        c_val = self.override.get()
        OCV.CD["_Ov" + n_val] = c_val
        OCV.CD["_OvChanged"] = True

    def resetOverride(self, event=None):
        self.override.set(100)
        self.overrideChange()

    def overrideComboChange(self):
        n_val = self.overrideCombo.get()
        if n_val == "Rapid":
            self.overrideScale.config(to_=100, resolution=25)
        else:
            self.overrideScale.config(to_=200, resolution=1)
        self.override.set(OCV.CD["_Ov" + n_val])

    def _gChange(self, value, dictionary):
        for key, val in dictionary.items():
            if val == value:
                self.sendGCode(key)
                return

    def distanceChange(self):
        if self._gUpdate:
            return

        self._gChange(self.distance.get(), OCV.DISTANCE_MODE)

    def unitsChange(self):
        if self._gUpdate:
            return

        self._gChange(self.units.get(), OCV.UNITS)

    def feedModeChange(self):
        if self._gUpdate:
            return

        self._gChange(self.feedMode.get(), OCV.FEED_MODE)

    def planeChange(self):
        if self._gUpdate:
            return

        self._gChange(self.plane.get(), OCV.PLANE)

    def setFeedRate(self, event=None):
        if self._gUpdate:
            return

        try:
            feed = float(self.feed_rate.get())
            self.sendGCode("F{0:.{1}f}".format(feed, OCV.digits))
            self.event_generate("<<CanvasFocus>>")
        except ValueError:
            pass

    def setTLO(self, event=None):
        # if self._probeUpdate: return

        try:
            tlo = float(self.tlo.get())
            self.sendGCode("G43.1 Z{0:.{1}f}".format(tlo, OCV.digits))
            OCV.MCTRL.viewParameters()
            self.event_generate("<<CanvasFocus>>")
        except ValueError:
            pass

    def setTool(self, event=None):
        pass

    def spindleControl(self, event=None):
        if self._gUpdate:
            return

        # Avoid sending commands before unlocking
        if OCV.c_state in (OCV.STATE_CONN, OCV.STATE_NOT_CONN):
            return

        if self.spindle.get():
            self.sendGCode("M3 S{0:d}".format(self.spindleSpeed.get()))
        else:
            self.sendGCode("M5")

    def coolantMist(self, event=None):
        if self._gUpdate:
            return

        # Avoid sending commands before unlocking
        if OCV.c_state in (OCV.STATE_CONN, OCV.STATE_NOT_CONN):
            self.mist.set(Tk.FALSE)
            return

        self.coolant.set(Tk.FALSE)
        self.mist.set(Tk.TRUE)
        self.sendGCode("M7")

    def coolantFlood(self, event=None):
        if self._gUpdate:
            return

        # Avoid sending commands before unlocking
        if OCV.c_state in (OCV.STATE_CONN, OCV.STATE_NOT_CONN):
            self.flood.set(Tk.FALSE)
            return

        self.coolant.set(Tk.FALSE)
        self.flood.set(Tk.TRUE)
        self.sendGCode("M8")

    def coolantOff(self, event=None):
        if self._gUpdate:
            return

        # Avoid sending commands before unlocking
        if OCV.c_state in (OCV.STATE_CONN, OCV.STATE_NOT_CONN):
            self.coolant.set(Tk.FALSE)
            return

        self.flood.set(Tk.FALSE)
        self.mist.set(Tk.FALSE)
        self.coolant.set(Tk.TRUE)
        self.sendGCode("M9")

    def updateG(self):
        self._gUpdate = True

        try:
            focus = self.focus_get()
        except:
            focus = None

        try:
            OCV.wcsvar.set(OCV.WCS.index(OCV.CD["WCS"]))
            self.feed_rate.set(str(OCV.CD["feed"]))
            self.feedMode.set(OCV.FEED_MODE[OCV.CD["feedmode"]])
            self.spindle.set(OCV.CD["spindle"] == "M3")
            self.spindleSpeed.set(int(OCV.CD["rpm"]))
            self.toolEntry.set(OCV.CD["tool"])
            self.units.set(OCV.UNITS[OCV.CD["units"]])
            self.distance.set(OCV.DISTANCE_MODE[OCV.CD["distance"]])
            self.plane.set(OCV.PLANE[OCV.CD["plane"]])
            self.tlo.set(str(OCV.CD["TLO"]))
            self.g92.config(text=str(OCV.CD["G92"]))
        except KeyError:
            pass

        self._gUpdate = False

    def updateFeed(self):
        if self.feed_rate.cget("state") == Tk.DISABLED:
            self.feed_rate.config(state=Tk.NORMAL)
            self.feed_rate.delete(0, Tk.END)
            self.feed_rate.insert(0, OCV.CD["curfeed"])
            self.feed_rate.config(state=Tk.DISABLED)

    def wcsChange(self):
        self.sendGCode(OCV.WCS[OCV.wcsvar.get()])
        OCV.MCTRL.viewState()
