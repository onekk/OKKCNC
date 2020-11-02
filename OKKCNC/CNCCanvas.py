# -*- coding: ascii -*-
"""CNCCanvas.py


Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import sys
import math
import time
import bmath
try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
from CNC import CNC
import Commands as cmd
import IniFile
import Utils
import Camera
import tkExtra

# Probe mapping we need PIL and numpy
try:
    from PIL import Image, ImageTk
    import numpy
    # Resampling image based on PIL library and converting to RGB.
    # options possible: NEAREST, BILINEAR, BICUBIC, ANTIALIAS
    RESAMPLE = Image.NEAREST    # resize type
    # RESAMPLE = Image.BILINEAR    # resize type
except:
    HAS_NUMPY = None
    RESAMPLE = None

ANTIALIAS_CHEAP = False

VIEW_XY = 0
VIEW_XZ = 1
VIEW_YZ = 2
VIEW_ISO1 = 3
VIEW_ISO2 = 4
VIEW_ISO3 = 5
VIEWS = ["X-Y", "X-Z", "Y-Z", "ISO1", "ISO2", "ISO3"]

INSERT_WIDTH2 = 3
GANTRY_R = 4
GANTRY_X = GANTRY_R*2  # 10
GANTRY_Y = GANTRY_R  # 5
GANTRY_H = GANTRY_R*5  # 20

SELECTION_TAGS = ("sel", "sel2", "sel3", "sel4")

ACTION_SELECT = 0
ACTION_SELECT_SINGLE = 1
ACTION_SELECT_AREA = 2
ACTION_SELECT_DOUBLE = 3

ACTION_PAN = 10
ACTION_ORIGIN = 11

ACTION_MOVE = 20
ACTION_ROTATE = 21
ACTION_GANTRY = 22
ACTION_WPOS = 23

ACTION_RULER = 30
ACTION_ADDORIENT = 31

SHIFT_MASK = 1
CONTROL_MASK = 4
ALT_MASK = 8
CONTROLSHIFT_MASK = SHIFT_MASK | CONTROL_MASK
CLOSE_DISTANCE = 5
MAXDIST = 10000
ZOOM = 1.25

S60 = math.sin(math.radians(60))
C60 = math.cos(math.radians(60))

DEF_CURSOR = ""

MOUSE_CURSOR = {
    ACTION_SELECT: DEF_CURSOR,
    ACTION_SELECT_AREA: "right_ptr",

    ACTION_PAN: "fleur",
    ACTION_ORIGIN: "cross",
    # ACTION_ORBIT: "exchange",
    # ACTION_ZOOM_IN: "sizing",
    # ACTION_ZOOM_OUT: "sizing",
    # ACTION_ZOOM_ON: "sizing",

    # ACTION_VIEW_CENTER: "cross",
    # ACTION_VIEW_MOVE: "fleur",
    # ACTION_VIEW_ROTATE: "exchange",

    ACTION_MOVE: "hand1",
    ACTION_ROTATE: "exchange",
    # ACTION_GANTRY: "target", # no  proper cursor
    ACTION_GANTRY: "crosshair",
    ACTION_WPOS: "diamond_cross",

    ACTION_RULER: "tcross",
    ACTION_ADDORIENT: "tcross",

    # ACTION_EDIT: "pencil",
}


def mouseCursor(action):
    """Return MOUSE_CURSOR"""
    return MOUSE_CURSOR.get(action, DEF_CURSOR)


class AlarmException(Exception):
    """Raise an alarm exception"""
    pass


class CNCCanvas(Tk.Canvas, object):
    """Drawing canvas"""

    def __init__(self, master, app, *kw, **kwargs):
        Tk.Canvas.__init__(self, master, *kw, **kwargs)
        OCV.TK_CANVAS = self

        # Global variables
        self.view = 0
        self.cnc = OCV.TK_APP.cnc
        self.gcode = OCV.TK_APP.gcode
        self.actionVar = Tk.IntVar()

        # Canvas binding
        self.bind('<Configure>', self.configureEvent)
        self.bind('<Motion>', self.motion)

        self.bind('<Button-1>', self.click)
        self.bind('<B1-Motion>', self.buttonMotion)
        self.bind('<ButtonRelease-1>', self.release)
        self.bind('<Double-1>', self.double)

        self.bind('<B2-Motion>', self.pan)
        self.bind('<ButtonRelease-2>', self.panRelease)
        self.bind("<Button-4>", self.mouseZoomIn)
        self.bind("<Button-5>", self.mouseZoomOut)
        self.bind("<MouseWheel>", self.wheel)

        self.bind('<Shift-Button-4>', self.panLeft)
        self.bind('<Shift-Button-5>', self.panRight)
        self.bind('<Control-Button-4>', self.panUp)
        self.bind('<Control-Button-5>', self.panDown)

        self.bind('<Control-Key-Left>', self.panLeft)
        self.bind('<Control-Key-Right>', self.panRight)
        self.bind('<Control-Key-Up>', self.panUp)
        self.bind('<Control-Key-Down>', self.panDown)

        self.bind('<Escape>', self.actionCancel)
        # self.bind('<Key-a>', lambda e,s=self : s.event_generate("<<SelectAll>>"))
        # self.bind('<Key-A>', lambda e,s=self : s.event_generate("<<SelectNone>>"))
        # self.bind('<Key-e>', lambda e,s=self : s.event_generate("<<Expand>>"))
        # self.bind('<Key-f>', self.fit2Screen)
        # self.bind('<Key-g>', self.setActionGantry)
        # self.bind('<Key-l>', lambda e,s=self : s.event_generate("<<EnableToggle>>"))
        # self.bind('<Key-m>', self.setActionMove)
        # self.bind('<Key-n>', lambda e,s=self : s.event_generate("<<ShowInfo>>"))
        # self.bind('<Key-o>', self.setActionOrigin)
        # self.bind('<Key-r>', self.setActionRuler)
        # self.bind('<Key-s>', self.setActionSelect)
        # self.bind('<Key-x>', self.setActionPan)
        self.bind('<Key>', self.handleKey)

        self.bind('<Control-Key-S>', self.cameraSave)
        self.bind('<Control-Key-t>', self._test)

        self.bind('<Control-Key-equal>', self.menuZoomIn)
        self.bind('<Control-Key-minus>', self.menuZoomOut)

        # self.bind('<Control-Key-x>', self.cut)
        # self.bind('<Control-Key-c>', self.copy)
        # self.bind('<Control-Key-v>', self.paste)

        # self.bind('<Key-space>', self.commandFocus)
        # self.bind('<Control-Key-space>', self.commandFocus)
        # self.bind('<Control-Key-a>', self.selectAll)

        self.x0 = 0.0
        self.y0 = 0.0
        self.zoom = 1.0
        self.__tzoom = 1.0  # delayed zoom (temporary)
        self._items = {}

        self._x = self._y = 0
        self._xp = self._yp = 0
        self.action = ACTION_SELECT
        self._mouseAction = None
        self._inDraw = False  # semaphore for parsing
        self._gantry1 = None
        self._gantry2 = None
        self._memA = None
        self._memB = None

        self._select = None
        self._margin = None
        self._amargin = None
        self._workarea = None
        self._vector = None
        self._lastActive = None
        self._lastGantry = None

        self._probeImage = None
        self._probeTkImage = None
        self._probe = None

        self.camera = Camera.Camera("aligncam")
        self.cameraAnchor = Tk.CENTER  # Camera anchor location "" for gantry
        self.cameraRotation = 0.0  # camera Z angle
        self.cameraXCenter = 0.0  # camera X center offset
        self.cameraYCenter = 0.0  # camera Y center offset
        self.cameraScale = 10.0  # camera pixels/unit
        self.cameraEdge = False  # edge detection
        self.cameraR = 1.5875  # circle radius in units (mm/inched)
        self.cameraDx = 0  # camera shift vs gantry
        self.cameraDy = 0
        # if None it will not make any Z movement for the camera
        self.cameraZ = None
        self.cameraSwitch = False  # Look at spindle(False) or camera(True)
        self._cameraAfter = None  # Camera anchor location "" for gantry
        self._cameraMaxWidth = 640  # on zoom over this size crop the image
        self._cameraMaxHeight = 480
        self._cameraImage = None
        self._cameraHori = None  # cross hair items
        self._cameraVert = None
        self._cameraCircle = None
        self._cameraCircle2 = None

        self.draw_axes = True  # Drawing flags
        self.draw_grid = True
        self.draw_margin = True
        self.draw_probe = True
        self.draw_workarea = True
        self.draw_paths = True
        self.draw_rapid = True  # draw rapid motions
        self._wx = self._wy = self._wz = 0.0  # work position
        self._dx = self._dy = self._dz = 0.0  # work-machine position

        self._vx0 = self._vy0 = self._vz0 = 0  # vector move coordinates
        self._vx1 = self._vy1 = self._vz1 = 0  # vector move coordinates

        self._orientSelected = None
        self.tooltips = []

        # self.config(xscrollincrement=1, yscrollincrement=1)
        self.reset()
        self.initPosition()

    def antialias_args(self, args, winc=0.5, cw=2):
        """Calculate arguments for antialiasing"""

        nargs = {}

        # set defaults
        nargs['width'] = 1
        nargs['fill'] = "#000"

        # get original args
        for arg in args:
            nargs[arg] = args[arg]
        if nargs['width'] == 0:
            nargs['width'] = 1

        # calculate width
        nargs['width'] += winc

        # calculate color
        cbg = self.winfo_rgb(self.cget("bg"))
        cfg = list(self.winfo_rgb(nargs['fill']))
        # print cbg, cfg
        cfg[0] = (cfg[0] + cbg[0]*cw)/(cw+1)
        cfg[1] = (cfg[1] + cbg[1]*cw)/(cw+1)
        cfg[2] = (cfg[2] + cbg[2]*cw)/(cw+1)
        nargs['fill'] = '#{0:02x}{1:02x}{2:02x}'.format(
            int(cfg[0]/256),
            int(cfg[1]/256),
            int(cfg[2]/256))

        return nargs

    # Override alias method if antialiasing enabled:
    if ANTIALIAS_CHEAP:
        def create_line(self, *args, **kwargs):
            nkwargs = self.antialias_args(kwargs)
            super(CNCCanvas, self).create_line(*args, **nkwargs)
            return super(CNCCanvas, self).create_line(*args, **kwargs)

    def reset(self):
        self.zoom = 1.0

    def status(self, msg):
        """Set status message"""
        self.event_generate("<<Status>>", data=msg)

    def setMouseStatus(self, event):
        data = "{0:.4f} {1:.4f} {2:.4f}".format(
            *self.canvas2xyz(self.canvasx(event.x), self.canvasy(event.y)))

        self.event_generate("<<Coords>>", data=data)

    def _updateScrollBars(self):
        """Update scroll region for new size"""
        bb = self.bbox('all')
        if bb is None:
            return
        x1, y1, x2, y2 = bb
        dx = x2-x1
        dy = y2-y1
        # make it 3 times bigger in each dimension
        # so when we zoom in/out we don't touch the borders
        self.configure(scrollregion=(x1-dx, y1-dy, x2+dx, y2+dy))

    def handleKey(self, event):
        # ctrl = event.state & CONTROL_MASK
        if event.char == "a":
            self.event_generate("<<SelectAll>>")
        elif event.char == "A":
            self.event_generate("<<SelectNone>>")
        elif event.char == "e":
            self.event_generate("<<Expand>>")
        elif event.char == "f":
            self.fit2Screen()
        elif event.char == "g":
            self.setActionGantry()
        elif event.char == "l":
            self.event_generate("<<EnableToggle>>")
        elif event.char == "m":
            self.setActionMove()
        elif event.char == "n":
            self.event_generate("<<ShowInfo>>")
        elif event.char == "o":
            self.setActionOrigin()
        elif event.char == "r":
            self.setActionRuler()
        elif event.char == "s":
            self.setActionSelect()
        elif event.char == "x":
            self.setActionPan()
        elif event.char == "z":
            self.menuZoomIn()
        elif event.char == "Z":
            self.menuZoomOut()

    def setAction(self, action):
        self.action = action
        self.actionVar.set(action)
        self._mouseAction = None
        self.config(cursor=mouseCursor(self.action), background="White")

    def actionCancel(self, event=None):
        if self.action != ACTION_SELECT or \
               (self._mouseAction != ACTION_SELECT and
                self._mouseAction is not None):
            self.setAction(ACTION_SELECT)
            return "break"
        # self.draw()

    def setActionSelect(self, event=None):
        self.setAction(ACTION_SELECT)
        self.status(_("Select objects with mouse"))

    def setActionPan(self, event=None):
        self.setAction(ACTION_PAN)
        self.status(_("Pan viewport"))

    def setActionOrigin(self, event=None):
        self.setAction(ACTION_ORIGIN)
        self.status(_("Click to set the origin (zero)"))

    def setActionMove(self, event=None):
        self.setAction(ACTION_MOVE)
        self.status(_("Move graphically objects"))

    def setActionGantry(self, event=None):
        self.setAction(ACTION_GANTRY)
        self.config(background="seashell")
        self.status(_("Move CNC gantry to mouse location"))

    def setActionWPOS(self, event=None):
        self.setAction(ACTION_WPOS)
        self.config(background="ivory")
        self.status(_("Set mouse location as current machine position (X/Y only)"))

    def setActionRuler(self, event=None):
        self.setAction(ACTION_RULER)
        self.status(_("Drag a ruler to measure distances"))

    def setActionAddMarker(self, event=None):
        self.setAction(ACTION_ADDORIENT)
        self.status(_("Add an orientation marker"))

    def canvas2Machine(self, cx, cy):
        """Convert canvas cx,cy coordinates to machine space"""
        u = cx / self.zoom
        v = cy / self.zoom

        if self.view == VIEW_XY:
            return u, -v, None

        elif self.view == VIEW_XZ:
            return u, None, -v

        elif self.view == VIEW_YZ:
            return None, u, -v

        elif self.view == VIEW_ISO1:
            return 0.5*(u/S60+v/C60), 0.5*(u/S60-v/C60), None

        elif self.view == VIEW_ISO2:
            return 0.5*(u/S60-v/C60), -0.5*(u/S60+v/C60), None

        elif self.view == VIEW_ISO3:
            return -0.5*(u/S60+v/C60), -0.5*(u/S60-v/C60), None

    def image2Machine(self, x, y):
        """Image (pixel) coordinates to machine"""
        return self.canvas2Machine(self.canvasx(x), self.canvasy(y))

    def actionGantry(self, x, y):
        """Move gantry to mouse location"""
        u, v, w = self.image2Machine(x, y)
        OCV.TK_MCTRL.goto(u, v, w)
        self.setAction(ACTION_SELECT)

    def actionWPOS(self, x, y):
        """Set the work coordinates to mouse location"""
        u, v, w = self.image2Machine(x, y)
        # print("X: {0} Y: {1} U: {2} V: {3} W: {4}".format(x, y, u, v, w))
        OCV.TK_MCTRL.wcs_set(u, v, w)
        self.setAction(ACTION_SELECT)

    def actionAddOrient(self, x, y):
        """Add an orientation marker at mouse location"""
        cx, cy = self.snapPoint(self.canvasx(x), self.canvasy(y))
        u, v, w = self.canvas2Machine(cx, cy)

        if u is None or v is None:
            self.status(_("ERROR: Cannot set X-Y marker  with the current view"))
            return

        self._orientSelected = len(self.gcode.orient)
        self.gcode.orient.add(OCV.CD["wx"], OCV.CD["wy"], u, v)
        self.event_generate("<<OrientSelect>>", data=self._orientSelected)
        # self.drawOrient()
        self.setAction(ACTION_SELECT)

    def click(self, event):
        """Find item selected"""
        self.focus_set()
        self._x = self._xp = event.x
        self._y = self._yp = event.y

        if event.state & CONTROLSHIFT_MASK == CONTROLSHIFT_MASK:
            self.actionGantry(event.x, event.y)
            return

        elif self.action == ACTION_SELECT:

            # if event.state & CONTROLSHIFT_MASK == CONTROLSHIFT_MASK:
            #     self._mouseAction = ACTION_SELECT
            #     else:
            self._mouseAction = ACTION_SELECT_SINGLE

        elif self.action in (ACTION_MOVE, ACTION_RULER):
            i = self.canvasx(event.x)
            j = self.canvasy(event.y)
            if self.action == ACTION_RULER and self._vector is not None:
                # Check if we hit the existing ruler
                coords = self.coords(self._vector)
                if (abs(coords[0]-i) <= CLOSE_DISTANCE and
                        abs(coords[1]-j <= CLOSE_DISTANCE)):
                    # swap coordinates
                    coords[0], coords[2] = coords[2], coords[0]
                    coords[1], coords[3] = coords[3], coords[1]
                    self.coords(self._vector, *coords)
                    self._vx0, self._vy0, self._vz0 = self.canvas2xyz(
                        coords[0], coords[1])
                    self._mouseAction = self.action
                    return
                elif (abs(coords[2]-i) <= CLOSE_DISTANCE and
                      abs(coords[3]-j <= CLOSE_DISTANCE)):
                    self._mouseAction = self.action
                    return

            if self._vector:
                self.delete(self._vector)

            if self.action == ACTION_MOVE:
                # Check if we clicked on a selected item
                try:
                    for item in self.find_overlapping(
                            i-CLOSE_DISTANCE, j-CLOSE_DISTANCE,
                            i+CLOSE_DISTANCE, j+CLOSE_DISTANCE):

                        tags = self.gettags(item)

                        if "sel" in tags or "sel2" in tags or \
                           "sel3" in tags or "sel4" in tags:

                            break
                    else:
                        self._mouseAction = ACTION_SELECT_SINGLE
                        return

                    fill = OCV.COLOR_MOVE
                    arrow = Tk.LAST

                except:
                    self._mouseAction = ACTION_SELECT_SINGLE
                    return
            else:
                fill = OCV.COLOR_RULER
                arrow = Tk.BOTH
            self._vector = self.create_line(
                (i, j, i, j), fill=fill, arrow=arrow)
            self._vx0, self._vy0, self._vz0 = self.canvas2xyz(i, j)
            self._mouseAction = self.action

        # Move gantry to position
        elif self.action == ACTION_GANTRY:
            self.actionGantry(event.x, event.y)

        # Move gantry to position
        elif self.action == ACTION_WPOS:
            self.actionWPOS(event.x, event.y)

        # Add orientation marker
        elif self.action == ACTION_ADDORIENT:
            self.actionAddOrient(event.x, event.y)

        # Set coordinate origin
        elif self.action == ACTION_ORIGIN:
            i = self.canvasx(event.x)
            j = self.canvasy(event.y)
            x, y, z = self.canvas2xyz(i, j)
            OCV.TK_APP.insertCommand(
                _("origin {0:f} {1:f} {2:f}").format(x, y, z),
                True)

            self.setActionSelect()

        elif self.action == ACTION_PAN:
            self.pan(event)

    def buttonMotion(self, event):
        """Canvas motion button 1"""
        if self._mouseAction == ACTION_SELECT_AREA:
            self.coords(
                self._select,
                self.canvasx(self._x),
                self.canvasy(self._y),
                self.canvasx(event.x),
                self.canvasy(event.y))

        elif self._mouseAction in (ACTION_SELECT_SINGLE, ACTION_SELECT_DOUBLE):
            if abs(event.x-self._x) > 4 or abs(event.y-self._y) > 4:
                self._mouseAction = ACTION_SELECT_AREA
                self._select = self.create_rectangle(
                    self.canvasx(self._x),
                    self.canvasy(self._y),
                    self.canvasx(event.x),
                    self.canvasy(event.y),
                    outline=OCV.COLOR_SELECT_BOX)

        elif self._mouseAction in (ACTION_MOVE, ACTION_RULER):
            coords = self.coords(self._vector)
            i = self.canvasx(event.x)
            j = self.canvasy(event.y)
            coords[-2] = i
            coords[-1] = j
            self.coords(self._vector, *coords)
            if self._mouseAction == ACTION_MOVE:
                self.move("sel", event.x-self._xp, event.y-self._yp)
                self.move("sel2", event.x-self._xp, event.y-self._yp)
                self.move("sel3", event.x-self._xp, event.y-self._yp)
                self.move("sel4", event.x-self._xp, event.y-self._yp)
                self._xp = event.x
                self._yp = event.y

            self._vx1, self._vy1, self._vz1 = self.canvas2xyz(i, j)

            dx = self._vx1-self._vx0
            dy = self._vy1-self._vy0
            dz = self._vz1-self._vz0

            self.status(
                _("dx={0:f}  dy={1:f}  dz={2:f}  length={3:f}  angle={4:f}").format(
                    dx,
                    dy,
                    dz,
                    math.sqrt(dx**2+dy**2+dz**2),
                    math.degrees(math.atan2(dy, dx))
                    ))

        elif self._mouseAction == ACTION_PAN:
            self.pan(event)

        self.setMouseStatus(event)

    def release(self, event):
        """Canvas release button1. Select area"""
        if self._mouseAction in (
                ACTION_SELECT_SINGLE,
                ACTION_SELECT_DOUBLE,
                ACTION_SELECT_AREA):

            if self._mouseAction == ACTION_SELECT_AREA:
                # if event.state & SHIFT_MASK == 0:
                if self._x < event.x:  # From left->right enclosed
                    closest = self.find_enclosed(
                        self.canvasx(self._x),
                        self.canvasy(self._y),
                        self.canvasx(event.x),
                        self.canvasy(event.y))
                else:  # From right->left overlapping
                    closest = self.find_overlapping(
                        self.canvasx(self._x),
                        self.canvasy(self._y),
                        self.canvasx(event.x),
                        self.canvasy(event.y))

                self.delete(self._select)
                self._select = None
                items = []

                for i in closest:
                    try:
                        items.append(self._items[i])
                    except:
                        pass

            elif self._mouseAction in (
                    ACTION_SELECT_SINGLE, ACTION_SELECT_DOUBLE):
                closest = self.find_closest(
                    self.canvasx(event.x),
                    self.canvasy(event.y),
                    CLOSE_DISTANCE)

                items = []

                for i in closest:
                    try:
                        items.append(self._items[i])
                        # i = None
                    except KeyError:
                        tags = self.gettags(i)
                        if "Orient" in tags:
                            self.selectMarker(i)
                            return
                        # i = self.find_below(i)
                        pass

            if not items:
                return

            OCV.TK_APP.select(
                items,
                self._mouseAction == ACTION_SELECT_DOUBLE,
                event.state & CONTROL_MASK == 0)

            self._mouseAction = None

        elif self._mouseAction == ACTION_MOVE:
            i = self.canvasx(event.x)
            j = self.canvasy(event.y)
            self._vx1, self._vy1, self._vz1 = self.canvas2xyz(i, j)
            dx = self._vx1-self._vx0
            dy = self._vy1-self._vy0
            dz = self._vz1-self._vz0
            self.status(_("Move by {0:f}, {1:f}, {2:f}").format(dx, dy, dz))

            OCV.TK_APP.insertCommand(
                ("move {0:f} {1:f} {2:f}").format(dx, dy, dz), True)

        elif self._mouseAction == ACTION_PAN:
            self.panRelease(event)

    def double(self, event):
        self._mouseAction = ACTION_SELECT_DOUBLE

    def motion(self, event):
        self.setMouseStatus(event)

    def _test(self, event):
        """Testing routine"""
        i = self.canvasx(event.x)
        j = self.canvasy(event.y)
        x, y, z = self.canvas2xyz(i, j)

#        blocks =  OCV:APP.editor.getSelectedBlocks()
#
#        from bmath import Vector
#        P = Vector(x,y)
#        for bid in blocks:
#            for path in self.gcode.toPath(bid):
#                print path
#                print path.isInside(P)

    def snapPoint(self, cx, cy):
        """Snap to the closest point if any"""
        xs, ys = None, None

        if OCV.inch:
            dmin = (self.zoom/25.4)**2  # 1mm maximum distance ...
        else:
            dmin = (self.zoom)**2

        dmin = (CLOSE_DISTANCE*self.zoom)**2

        # ... and if we are closer than 5pixels
        for item in self.find_closest(cx, cy, CLOSE_DISTANCE):
            try:
                bid, lid = self._items[item]
            except KeyError:
                continue

            # Very cheap and inaccurate approach :)
            coords = self.coords(item)
            x = coords[0]    # first
            y = coords[1]    # point
            d = (cx-x)**2 + (cy-y)**2
            if d < dmin:
                dmin = d
                xs, ys = x, y

            x = coords[-2]    # last
            y = coords[-1]    # point
            d = (cx-x)**2 + (cy-y)**2
            if d < dmin:
                dmin = d
                xs, ys = x, y

            # I need to check the real code and if
            # an arc check also the center?

        if xs is not None:
            return xs, ys
        else:
            return cx, cy

    def getMargins(self):
        """Get margins of selected items"""
        bbox = self.bbox("sel")
        if not bbox:
            return None
        x1, y1, x2, y2 = bbox
        dx = (x2-x1-1)/self.zoom
        dy = (y2-y1-1)/self.zoom
        return dx, dy

    def xview(self, *args):
        ret = Tk.Canvas.xview(self, *args)
        if args:
            self.cameraPosition()
        return ret

    def yview(self, *args):
        ret = Tk.Canvas.yview(self, *args)
        if args:
            self.cameraPosition()
        return ret

    def configureEvent(self, event):
        self.cameraPosition()
        self.RefreshItems()

    def pan(self, event):
        if self._mouseAction == ACTION_PAN:
            self.scan_dragto(event.x, event.y, gain=1)
            self.cameraPosition()
            self.RefreshItems()

        else:
            self.config(cursor=mouseCursor(ACTION_PAN))
            self.scan_mark(event.x, event.y)
            self._mouseAction = ACTION_PAN

    def panRelease(self, event):
        self._mouseAction = None
        self.config(cursor=mouseCursor(self.action))

    def panLeft(self, event=None):
        self.xview(Tk.SCROLL, -1, Tk.UNITS)

    def panRight(self, event=None):
        self.xview(Tk.SCROLL, 1, Tk.UNITS)

    def panUp(self, event=None):
        self.yview(Tk.SCROLL, -1, Tk.UNITS)

    def panDown(self, event=None):
        self.yview(Tk.SCROLL, 1, Tk.UNITS)

    def zoomCanvas(self, x, y, zoom):
        """Delay zooming to cascade multiple zoom actions"""
        self._tx = x
        self._ty = y
        self.__tzoom *= zoom
        self.after_idle(self._zoomCanvas)

    def _zoomCanvas(self, event=None):
        """Zoom on screen position x,y"""

        x = self._tx
        y = self._ty
        zoom = self.__tzoom

        if OCV.DEBUG_GRAPH is True:
            print("--- _zoomCanvas ---")
            print("ACTUAL_ZOOM", self.zoom)

        self.__tzoom = 1.0

        c_zoom = self.zoom

        c_zoom *= zoom

        # limits the zoom factor as problems could arise if zoom is:
        # too high 300000 is giving error
        # too low led to division by zero or NaN
        if c_zoom > 30000:
            c_zoom = 30000
        elif c_zoom < 0.1:
            c_zoom = 0.1

        self.zoom = Utils.q_round(c_zoom, 4, 0.005)

        x0 = self.canvasx(0)
        y0 = self.canvasy(0)

        for i in self.find_all():
            self.scale(i, 0, 0, zoom, zoom)

        # Update last insert
        if self._lastGantry:
            self._drawGantry(*self.plotCoords([self._lastGantry])[0])
        else:
            self._drawGantry(0, 0)

        self._updateScrollBars()

        x0 -= self.canvasx(0)
        y0 -= self.canvasy(0)

        # Perform pin zoom
        dx = self.canvasx(x) * (1.0 - zoom)
        dy = self.canvasy(y) * (1.0 - zoom)

        if OCV.DEBUG_GRAPH is True:
            print("FACTOR ", zoom)
            print("x0 y0 ", x0, y0)
            print("dx, dy ", dx, dy)
            print("NEW ZOOM {0:f} ".format(self.zoom))

        # Drag to new location to center viewport
        self.scan_mark(0, 0)
        self.scan_dragto(int(round(dx-x0)), int(round(dy-y0)), 1)

        # Resize probe image if any
        if self._probe:
            self._projectProbeImage()
            self.itemconfig(self._probe, image=self._probeTkImage)

        self.cameraUpdate()
        self.RefreshItems()

    def selBbox(self):
        """Return selected objects bounding box"""
        x1 = None
        for tag in ("sel", "sel2", "sel3", "sel4"):
            bb = self.bbox(tag)

            if bb is None:
                continue
            elif x1 is None:
                x1, y1, x2, y2 = bb
                print("TAG {0}, bb{1}".format(tag, bb))
            else:
                x1 = min(x1, bb[0])
                y1 = min(y1, bb[1])
                x2 = max(x2, bb[2])
                y2 = max(y2, bb[3])

        if x1 is None:
            return self.bbox('all')

        return x1, y1, x2, y2

    def fit2Screen(self, event=None):
        """Zoom to Fit to Screen"""

        bb = self.selBbox()

        if bb is None:
            return

        x1, y1, x2, y2 = bb

        # add a factor to improve readability
        bbox_width = int((x2-x1) * 1.015)
        bbox_height = int((y2-y1) * 1.015)

        try:
            zx = float(self.winfo_width() / bbox_width)
        except:
            return

        try:
            zy = float(self.winfo_height() / bbox_height)
        except:
            return

        if zx > 0.98:
            c_zoom = min(zx, zy)
        else:
            c_zoom = max(zx, zy)

        if c_zoom > 0.1:
            self.__tzoom = Utils.q_round(c_zoom, 4, 0.005)
        else:
            self.__tzoom = 0.5

        if OCV.DEBUG_GRAPH is True:
            print("--- fit2Screen ---")
            print("OLD ZOOM ", self.zoom)
            print("BB", bb)
            print("canvas ", self.winfo_width(), self.winfo_height())
            print("BBCALC ", bbox_width, bbox_height)
            print("ZX, ZY ", zx, zy)
            print("C_ZOOM {0:f} - __TZOOM {1:f} ".format(c_zoom, self.__tzoom))

        self._tx = self._ty = 0
        self._zoomCanvas()

        # Find position of new selection
        x1, y1, x2, y2 = self.selBbox()
        xm = (x1+x2)//2
        ym = (y1+y2)//2
        sx1, sy1, sx2, sy2 = map(float, self.cget("scrollregion").split())

        midx = float((xm-sx1) / (sx2-sx1))
        midy = float((ym-sy1) / (sy2-sy1))

        print("xm {0} ym{1} sx1{2} sy1{3} sx2{4} sy2{5}".format(
            xm, ym, sx1, sy1, sx2, sy2))

        a, b = self.xview()
        d = (b-a)/2.0
        print(a, b, d)

        self.xview_moveto(midx - d)

        a, b = self.yview()
        d = (b-a)/2.0
        self.yview_moveto(midy-d)

        self.cameraPosition()
        self.RefreshItems()

    def RefreshItems(self):
        cmd.RefreshMemories()

    def menuZoomIn(self, event=None):
        x = int(self.cget("width"))//2
        y = int(self.cget("height"))//2
        self.zoomCanvas(x, y, 2.0)

    def menuZoomOut(self, event=None):
        x = int(self.cget("width"))//2
        y = int(self.cget("height"))//2
        self.zoomCanvas(x, y, 0.5)

    def mouseZoomIn(self, event):
        self.zoomCanvas(event.x, event.y, ZOOM)

    def mouseZoomOut(self, event):
        self.zoomCanvas(event.x, event.y, 1.0/ZOOM)

    def wheel(self, event):
        self.zoomCanvas(event.x, event.y, pow(ZOOM, (event.delta//120)))

    def activeMarker(self, item):
        """Change the insert marker location"""
        if item is None:
            return
        b, i = item
        if i is None:
            return
        block = self.gcode[b]
        item = block.path(i)

        if item is not None and item != self._lastActive:
            if self._lastActive is not None:
                self.itemconfig(self._lastActive, arrow=Tk.NONE)
            self._lastActive = item
            self.itemconfig(self._lastActive, arrow=Tk.LAST)

    def gantry(self, wx, wy, wz, mx, my, mz):
        """Display gantry"""
        self._lastGantry = (wx, wy, wz)
        self._drawGantry(*self.plotCoords([(wx, wy, wz)])[0])
        if self._cameraImage and self.cameraAnchor is Tk.NONE:
            self.cameraPosition()

        dx = wx-mx
        dy = wy-my
        dz = wz-mz
        if abs(dx-self._dx) > 0.0001 or \
           abs(dy-self._dy) > 0.0001 or \
           abs(dz-self._dz) > 0.0001:
            self._dx = dx
            self._dy = dy
            self._dz = dz

            if not self.draw_workarea:
                return
            xmin = self._dx-OCV.travel_x
            ymin = self._dy-OCV.travel_y
            zmin = self._dz-OCV.travel_z
            xmax = self._dx
            ymax = self._dy
            zmax = self._dz

            xyz = [(xmin, ymin, 0.),
                   (xmax, ymin, 0.),
                   (xmax, ymax, 0.),
                   (xmin, ymax, 0.),
                   (xmin, ymin, 0.)]

            coords = []
            for x, y in self.plotCoords(xyz):
                coords.append(x)
                coords.append(y)
            self.coords(self._workarea, *coords)

    def clearSelection(self):
        """Clear highlight of selection"""
        if self._lastActive is not None:
            self.itemconfig(self._lastActive, arrow=Tk.NONE)
            self._lastActive = None

        for i in self.find_withtag("sel"):
            bid, lid = self._items[i]
            if bid:
                try:
                    block = self.gcode[bid]
                    if block.color:
                        fill = block.color
                    else:
                        fill = OCV.COLOR_ENABLE
                except IndexError:
                    fill = OCV.COLOR_ENABLE
            else:
                    fill = OCV.COLOR_ENABLE
            self.itemconfig(i, width=1, fill=fill)

        self.itemconfig("sel2", width=1, fill=OCV.COLOR_DISABLE)
        self.itemconfig("sel3", width=1, fill=OCV.COLOR_TAB)
        self.itemconfig("sel4", width=1, fill=OCV.COLOR_DISABLE)

        for i in SELECTION_TAGS:
            self.dtag(i)

        self.delete("info")

    def select(self, items):
        """Highlight selected items"""
        for b, i in items:
            block = self.gcode[b]
            if i is None:
                sel = block.enable and "sel" or "sel2"
                for path in block._path:
                    if path is not None:
                        self.addtag_withtag(sel, path)
                sel = block.enable and "sel3" or "sel4"

            elif isinstance(i, int):
                path = block.path(i)
                if path:
                    sel = block.enable and "sel" or "sel2"
                    self.addtag_withtag(sel, path)

        self.itemconfig("sel", width=2, fill=OCV.COLOR_SELECT)
        self.itemconfig("sel2", width=2, fill=OCV.COLOR_SELECT2)
        self.itemconfig("sel3", width=2, fill=OCV.COLOR_TAB)
        self.itemconfig("sel4", width=2, fill=OCV.COLOR_TABS)

        for i in SELECTION_TAGS:
            self.tag_raise(i)

        self.drawMargin()

    def selectMarker(self, item):
        """Select orientation marker"""
        # find marker
        for i, paths in enumerate(self.gcode.orient.paths):
            if item in paths:
                self._orientSelected = i
                for j in paths:
                    self.itemconfig(j, width=2)
                self.event_generate("<<OrientSelect>>", data=i)
                return
        self._orientSelected = None

    def orientChange(self, marker):
        """Highlight marker that was selected"""
        self.itemconfig("Orient", width=1)
        if marker >= 0:
            self._orientSelected = marker
            try:
                for i in self.gcode.orient.paths[self._orientSelected]:
                    self.itemconfig(i, width=2)
            except IndexError:
                self.drawOrient()
        else:
            self._orientSelected = None

    def showInfo(self, blocks):
        """Display graphical information on selected blocks"""
        self.delete("info")    # clear any previous information

        for bid in blocks:
            block = OCV.blocks[bid]
            xyz = [(block.xmin, block.ymin, 0.),
                   (block.xmax, block.ymin, 0.),
                   (block.xmax, block.ymax, 0.),
                   (block.xmin, block.ymax, 0.),
                   (block.xmin, block.ymin, 0.)]

            self.create_line(
                self.plotCoords(xyz),
                fill=OCV.COLOR_INFO,
                tag="info")
            xc = (block.xmin + block.xmax)/2.0
            yc = (block.ymin + block.ymax)/2.0
            r = min(block.xmax-xc, block.ymax-yc)

            closed, direction = self.gcode.info(bid)

            print("ShowInfo >> ", closed, direction)

            if closed == 0:  # open path
                if direction == 1:
                    sf = math.pi/4.0
                    ef = 2.0*math.pi - sf
                else:
                    ef = math.pi/4.0
                    sf = 2.0*math.pi - ef
            elif closed == 1:
                if direction == 1:
                    sf = 0.
                    ef = 2.0*math.pi
                else:
                    ef = 0.
                    sf = 2.0*math.pi

            elif closed is None:
                continue

            n = 64
            df = (ef-sf)/float(n)
            xyz = []
            f = sf
            for i in range(n+1):
                # towards up
                xyz.append((xc+r*math.sin(f), yc+r*math.cos(f), 0.))
                f += df

            self.create_line(
                self.plotCoords(xyz),
                fill=OCV.COLOR_INFO,
                width=5,
                arrow=Tk.LAST,
                arrowshape=(32, 40, 12),
                tag="info")

    def cameraOn(self, event=None):
        if not self.camera.start():
            return
        self.cameraRefresh()

    def cameraOff(self, event=None):
        self.delete(self._cameraImage)
        self.delete(self._cameraHori)
        self.delete(self._cameraVert)
        self.delete(self._cameraCircle)
        self.delete(self._cameraCircle2)

        self._cameraImage = None
        if self._cameraAfter:
            self.after_cancel(self._cameraAfter)
            self._cameraAfter = None
        self.camera.stop()

    def cameraUpdate(self):
        if not self.camera.isOn():
            return
        if self._cameraAfter:
            self.after_cancel(self._cameraAfter)
            self._cameraAfter = None
        self.cameraRefresh()
        self.cameraPosition()

    def cameraRefresh(self):
        if not self.camera.read():
            self.cameraOff()
            return
        self.camera.rotation = self.cameraRotation
        self.camera.xcenter = self.cameraXCenter
        self.camera.ycenter = self.cameraYCenter
        if self.cameraEdge:
            self.camera.canny(50, 200)
        if self.cameraAnchor is Tk.NONE or self.zoom/self.cameraScale > 1.0:
            self.camera.resize(
                self.zoom/self.cameraScale,
                self._cameraMaxWidth,
                self._cameraMaxHeight)

        if self._cameraImage is None:
            self._cameraImage = self.create_image((0, 0), tag="CameraImage")
            self.lower(self._cameraImage)
            # create cross hair at dummy location we will correct latter
            self._cameraHori = self.create_line(
                0, 0, 1, 0,
                fill=OCV.COLOR_CAMERA,
                tag="CrossHair")

            self._cameraVert = self.create_line(
                0, 0, 0, 1,
                fill=OCV.COLOR_CAMERA,
                tag="CrossHair")

            self._cameraCircle = self.create_oval(
                0, 0, 1, 1,
                outline=OCV.COLOR_CAMERA,
                tag="CrossHair")

            self._cameraCircle2 = self.create_oval(
                0, 0, 1, 1,
                outline=OCV.COLOR_CAMERA,
                dash=(3, 3),
                tag="CrossHair")

            self.cameraPosition()
        try:
            self.itemconfig(self._cameraImage, image=self.camera.toTk())
        except:
            pass
        self._cameraAfter = self.after(100, self.cameraRefresh)

    def cameraFreeze(self, freeze):
        if self.camera.isOn():
            self.camera.freeze(freeze)

    def cameraSave(self, event=None):
        try:
            self._count += 1
        except:
            self._count = 1
        self.camera.save("camera{0:02d}.png".format(self._count))


    def cameraPosition(self):
        """Reposition camera and crosshair"""
        if self._cameraImage is None: return
        w = self.winfo_width()
        h = self.winfo_height()
        hc, wc = self.camera.image.shape[:2]
        wc //= 2
        hc //= 2
        x = w//2  # everything on center
        y = h//2
        if self.cameraAnchor is Tk.NONE:
            if self._lastGantry is not None:
                x, y = self.plotCoords([self._lastGantry])[0]
            else:
                x = y = 0
            if not self.cameraSwitch:
                x += self.cameraDx * self.zoom
                y -= self.cameraDy * self.zoom
            r = self.cameraR  * self.zoom
        else:
            if self.cameraAnchor != Tk.CENTER:
                if Tk.N in self.cameraAnchor:
                    y = hc
                elif Tk.S in self.cameraAnchor:
                    y = h-hc
                if Tk.W in self.cameraAnchor:
                    x = wc
                elif Tk.E in self.cameraAnchor:
                    x = w-wc
            x = self.canvasx(x)
            y = self.canvasy(y)
            if self.zoom/self.cameraScale > 1.0:
                r = self.cameraR * self.zoom
            else:
                r = self.cameraR * self.cameraScale

        self.coords(self._cameraImage, x, y)
        self.coords(self._cameraHori, x-wc, y, x+wc, y)
        self.coords(self._cameraVert, x, y-hc, x, y+hc)
        self.coords(self._cameraCircle, x-r, y-r, x+r, y+r)
        self.coords(self._cameraCircle2, x-r*2, y-r*2, x+r*2, y+r*2)


    def cameraMakeTemplate(self, r):
        """Crop center of camera and search it in subsequent movements"""

        if self._cameraImage is None: return
        self._template = self.camera.getCenterTemplate(r)


    def cameraMatchTemplate(self):
        return self.camera.matchTemplate(self._template)


    def draw(self, view=None): #, lines):
        """Parse and draw the file from the editor to g-code commands"""

        if self._inDraw:
            return

        self._inDraw = True

        self.__tzoom = 1.0
        xyz = self.canvas2xyz(
            self.canvasx(self.winfo_width()/2),
            self.canvasy(self.winfo_height()/2))

        if view is not None: self.view = view

        self._last = (0., 0., 0.)
        self.initPosition()

        self.drawPaths()
        self.drawGrid()
        self.drawMargin()
        self.drawWorkarea()
        self.drawProbe()
        self.drawOrient()
        self.drawAxes()
        #self.tag_lower(self._workarea)
        if self._gantry1: self.tag_raise(self._gantry1)
        if self._gantry2: self.tag_raise(self._gantry2)
        self._updateScrollBars()

        ij = self.plotCoords([xyz])[0]
        dx = int(round(self.canvasx(self.winfo_width()/2)  - ij[0]))
        dy = int(round(self.canvasy(self.winfo_height()/2) - ij[1]))
        self.scan_mark(0, 0)
        self.scan_dragto(int(round(dx)), int(round(dy)), 1)

        self._inDraw = False


    def initPosition(self):
        """Initialize gantry position"""

        self.configure(background=OCV.COLOR_CANVAS)
        self.delete(Tk.ALL)
        self._cameraImage = None
        gr = max(3, int(OCV.CD["diameter"]/2.0*self.zoom))
        mr = max(3, int(3/2.0 * self.zoom))

        if self.view == VIEW_XY:
            self._gantry1 = self.create_oval(
                (-gr, -gr), (gr, gr),
                width=2,
                outline=OCV.COLOR_GANTRY)

            self._gantry2 = None

        else:
            gx = gr
            gy = gr//2
            gh = 3*gr
            if self.view in (VIEW_XZ, VIEW_YZ):
                self._gantry1 = None
                self._gantry2 = self.create_line(
                    (-gx, -gh, 0, 0, gx, -gh, -gx, -gh),
                    width=2,
                    fill=OCV.COLOR_GANTRY)
            else:
                self._gantry1 = self.create_oval(
                    (-gx, -gh-gy, gx, -gh+gy),
                    width=2,
                    outline=OCV.COLOR_GANTRY)

                self._gantry2 = self.create_line(
                    (-gx, -gh, 0, 0, gx, -gh),
                    width=2,
                    fill=OCV.COLOR_GANTRY)

        self._lastInsert = None
        self._lastActive = None
        self._select = None
        self._vector = None
        self._items.clear()
        self.cnc.initPath()
        self.cnc.resetAllMargins()
        self.RefreshItems()


    def memDraw(self, mem_num):
        """
            Position mem on Canvas
        """

        mem_name = "mem_{0}".format(mem_num)
        mem_cross_h = mem_name + "Cross_H"
        mem_cross_v = mem_name + "Cross_V"
        mem_cross_c = mem_name + "Cross_C"
        mem_text = mem_name +"Text"
        mem_tt = mem_name +"Tt"

        self.delete(mem_cross_h)
        self.delete(mem_cross_v)
        self.delete(mem_cross_c)
        self.delete(mem_text)
        self.delete(mem_tt)

        # create cross hair at dummy location we will correct latter
        c_dim = max(6, int(6 * self.zoom))
        r_dim = c_dim // 3
        wc = c_dim // 2
        hc = c_dim // 2

        objA = self.create_line(0, 0, c_dim, 0, fill=OCV.COLOR_MEM,
                                tag=mem_cross_h)
        objB = self.create_line(0, 0, 0, c_dim, fill=OCV.COLOR_MEM,
                                tag=mem_cross_v)
        objC = self.create_oval(0, 0, r_dim, r_dim, outline=OCV.COLOR_MEM,
                                tag=mem_cross_c)
        if mem_num == 0:
            mem_id = "mem_A"
        elif mem_num == 1:
            mem_id = "mem_B"
        else:
            mem_id = mem_name

        md = OCV.WK_mems[mem_name]
        m_text = "Memory {0}\n\nName: {1}\n\nX: {2:.04f}  \nY: {3:.04f} \nZ: {4:.04f}"
        ttext = m_text.format(mem_id, md[4], md[0], md[1], md[2])

        text = mem_id
        objD = self.create_text(
            0, 0,
            text=text,
            anchor=Tk.N,
            justify=Tk.LEFT,
            fill=OCV.COLOR_MEM, tag=mem_text)

        CanvasTooltip(self, objD, text=ttext, tag=mem_tt)

        # Position created objects
        # for mem 0 and mem 1 coordinates are in working coord
        # for other memories coorddinates are in machine coord
        # need a function to translate machine to canvas

        if mem_num in (0, 1):
            pc_x = md[0]
            pc_y = md[1]
            pc_z = md[2]
        else:
            # Translate machine coordinate in w coordinates, using
            # GRBL position messages to cope with different values
            # mpos are the same, are fixed by endstops
            # wpos may vary
            # but GRBL is reporting constantly both values
            # so there is no need to mantain a table in OKKCNC

            d_x = (OCV.CD["wx"] - OCV.CD["mx"])
            d_y = (OCV.CD["wy"] - OCV.CD["my"])
            d_z = (OCV.CD["wz"] - OCV.CD["mz"])
            pc_x = md[0] + d_x
            pc_y = md[1] + d_y
            pc_z = md[2] + d_z

            if OCV.DEBUG is True:
                print(" WPOS: X{0} Y{1} Z{2}\n Delta: X{3} Y{4} Z{5}\n MPOS: X{6} Y{7} Z{8}".format(
                    pc_x, pc_y, pc_z,
                    d_x, d_y, d_z,
                    *md))

        x, y = self.plotCoords([(pc_x, pc_y, pc_z)])[0]

        self.coords(objA, x-wc, y, x+wc, y)
        self.coords(objB, x, y-hc, x, y+hc)
        self.coords(objC, x-r_dim, y-r_dim, x+r_dim, y+r_dim)
        i_bbox = self.bbox(objD)
        i_off = (i_bbox[3] - i_bbox[1]) // 4
        #print ("bbox of memA = ",offy)
        self.coords(objD, x, (y + wc + i_off))


    def memDelete(self, mem_num):
        """
            Delete mem on Canvas
        """

        mem_name = "mem_{0}".format(mem_num)
        mem_cross_h = mem_name + "Cross_H"
        mem_cross_v = mem_name + "Cross_V"
        mem_cross_c = mem_name + "Cross_C"
        mem_text = mem_name +"Text"
        mem_tt = mem_name +"Tt"

        self.delete(mem_cross_h)
        self.delete(mem_cross_v)
        self.delete(mem_cross_c)
        self.delete(mem_text)
        self.delete(mem_tt)

    # Draw gantry location

    def _drawGantry(self, x, y):
        gr = max(3, int(OCV.CD["diameter"]/2.0*self.zoom))

        if self._gantry2 is None:
            self.coords(self._gantry1, (x-gr, y-gr, x+gr, y+gr))
        else:
            gx = gr
            gy = gr//2
            gh = 3*gr
            if self._gantry1 is None:
                self.coords(
                    self._gantry2,
                    (x-gx, y-gh, x, y, x+gx, y-gh, x-gx, y-gh))
            else:
                self.coords(
                    self._gantry1,
                    (x-gx, y-gh-gy, x+gx, y-gh+gy))

                self.coords(
                    self._gantry2,
                    (x-gx, y-gh, x, y, x+gx, y-gh))


    def drawAxes(self):
        """
            Draw system axes
        """

        self.delete("Axes")
        if not self.draw_axes: return

        dx = OCV.CD["axmax"] - OCV.CD["axmin"]
        dy = OCV.CD["aymax"] - OCV.CD["aymin"]
        d = min(dx, dy)
        try:
            s = math.pow(10.0, int(math.log10(d)))
        except:
            if OCV.inch:
                s = 10.0
            else:
                s = 100.0
        xyz = [(0., 0., 0.), (s, 0., 0.)]
        self.create_line(
            self.plotCoords(xyz),
            tag="Axes",
            fill="Red",
            dash=(3, 1),
            arrow=Tk.LAST)

        xyz = [(0., 0., 0.), (0., s, 0.)]
        self.create_line(
            self.plotCoords(xyz),
            tag="Axes",
            fill="Green",
            dash=(3, 1),
            arrow=Tk.LAST)

        xyz = [(0., 0., 0.), (0., 0., s)]
        self.create_line(
            self.plotCoords(xyz),
            tag="Axes",
            fill="Blue",
            dash=(3, 1),
            arrow=Tk.LAST)


    def drawMargin(self):
        """
            Draw margins of selected blocks
        """

        if self._margin:
            self.delete(self._margin)

        if self._amargin:
            self.delete(self._amargin)

        self._margin = self._amargin = None

        if not self.draw_margin:
            return

        if CNC.isMarginValid():
            xyz = [(OCV.CD["xmin"], OCV.CD["ymin"], 0.),
                   (OCV.CD["xmax"], OCV.CD["ymin"], 0.),
                   (OCV.CD["xmax"], OCV.CD["ymax"], 0.),
                   (OCV.CD["xmin"], OCV.CD["ymax"], 0.),
                   (OCV.CD["xmin"], OCV.CD["ymin"], 0.)]

            self._margin = self.create_line(
                self.plotCoords(xyz),
                fill=OCV.COLOR_MARGIN)

            self.tag_lower(self._margin)

        if not CNC.isAllMarginValid():
            return

        xyz = [(OCV.CD["axmin"], OCV.CD["aymin"], 0.),
               (OCV.CD["axmax"], OCV.CD["aymin"], 0.),
               (OCV.CD["axmax"], OCV.CD["aymax"], 0.),
               (OCV.CD["axmin"], OCV.CD["aymax"], 0.),
               (OCV.CD["axmin"], OCV.CD["aymin"], 0.)]

        self._amargin = self.create_line(
            self.plotCoords(xyz),
            dash=(3, 2),
            fill=OCV.COLOR_MARGIN)

        self.tag_lower(self._amargin)


    def _rectCoords(self, rect, xmin, ymin, xmax, ymax, z=0.0):
        """
            Change rectangle coordinates
        """

        self.coords(rect, Tk._flatten(self.plotCoords(
            [(xmin, ymin, z),
             (xmax, ymin, z),
             (xmax, ymax, z),
             (xmin, ymax, z),
             (xmin, ymin, z)]
            )))


    def _drawPath(self, path, z=0.0, **kwargs):
        """
            Draw a 3D path
        """

        xyz = []
        for segment in path:
            xyz.append((segment.A[0], segment.A[1], z))
            xyz.append((segment.B[0], segment.B[1], z))

        rect = self.create_line(
            self.plotCoords(xyz),
            **kwargs),

        return rect


    def _drawRect(self, xmin, ymin, xmax, ymax, z=0.0, **kwargs):
        """
            Draw a 3D rectangle
        """

        xyz = [(xmin, ymin, z),
               (xmax, ymin, z),
               (xmax, ymax, z),
               (xmin, ymax, z),
               (xmin, ymin, z)]

        rect = self.create_line(
            self.plotCoords(xyz),
            **kwargs),

        return rect


    def drawWorkarea(self):
        """
            Draw a workspace rectangle
        """

        if self._workarea:
            self.delete(self._workarea)

        if not self.draw_workarea:
            return

        xmin = self._dx-OCV.travel_x
        ymin = self._dy-OCV.travel_y
        zmin = self._dz-OCV.travel_z
        xmax = self._dx
        ymax = self._dy
        zmax = self._dz

        self._workarea = self._drawRect(
            xmin, ymin, xmax, ymax,
            0.,
            fill=OCV.COLOR_WORK,
            dash=(3, 2))

        self.tag_lower(self._workarea)


    def drawGrid(self):
        """
            Draw coordinates grid
        """

        self.delete("Grid")
        if not self.draw_grid: return
        if self.view in (VIEW_XY, VIEW_ISO1, VIEW_ISO2, VIEW_ISO3):
            xmin = (OCV.CD["axmin"]//10) * 10
            xmax = (OCV.CD["axmax"]//10+1) * 10
            ymin = (OCV.CD["aymin"]//10) * 10
            ymax = (OCV.CD["aymax"]//10+1) * 10

            for i in range(int(OCV.CD["aymin"]//10), int(OCV.CD["aymax"]//10)+2):
                y = i*10.0
                xyz = [(xmin, y, 0), (xmax, y, 0)]

                item = self.create_line(
                    self.plotCoords(xyz),
                    tag="Grid",
                    fill=OCV.COLOR_GRID,
                    dash=(1, 3))

                self.tag_lower(item)

            for i in range(int(OCV.CD["axmin"]//10), int(OCV.CD["axmax"]//10)+2):
                x = i*10.0
                xyz = [(x, ymin, 0), (x, ymax, 0)]

                item = self.create_line(
                    self.plotCoords(xyz),
                    fill=OCV.COLOR_GRID,
                    tag="Grid",
                    dash=(1, 3))

                self.tag_lower(item)


    def drawOrient(self, event=None):
        """
            Display orientation markers
        """

        self.delete("Orient")
        #if not self.draw_probe: return
        if self.view in (VIEW_XZ, VIEW_YZ):
            return

        # Draw orient markers
        if OCV.inch:
            w = 0.1
        else:
            w = 2.5

        self.gcode.orient.clearPaths()

        for i, (xm, ym, x, y) in enumerate(self.gcode.orient.markers):
            paths = []

            # Machine position (cross)
            item = self.create_line(
                self.plotCoords([(xm-w, ym, 0.), (xm+w, ym, 0.)]),
                tag="Orient",
                fill="Green")

            self.tag_lower(item)

            paths.append(item)

            item = self.create_line(
                self.plotCoords([(xm, ym-w, 0.), (xm, ym+w, 0.)]),
                tag="Orient",
                fill="Green")

            self.tag_lower(item)
            paths.append(item)

            # GCode position (cross)
            item = self.create_line(
                self.plotCoords([(x-w, y, 0.), (x+w, y, 0.)]),
                tag="Orient",
                fill="Red")

            self.tag_lower(item)
            paths.append(item)

            item = self.create_line(
                self.plotCoords([(x, y-w, 0.), (x, y+w, 0.)]),
                tag="Orient",
                fill="Red")

            self.tag_lower(item)
            paths.append(item)

            # Draw error if any
            try:
                err = self.gcode.orient.errors[i]

                item = self.create_oval(
                    self.plotCoords(
                        [(xm-err, ym-err, 0.), (xm+err, ym+err, 0.)]),
                    tag="Orient",
                    outline="Red")

                self.tag_lower(item)
                paths.append(item)

                err = self.gcode.orient.errors[i]

                item = self.create_oval(
                    self.plotCoords(
                        [(x-err, y-err, 0.), (x+err, y+err, 0.)]),
                    tag="Orient",
                    outline="Red")
                self.tag_lower(item)

                paths.append(item)

            except IndexError:
                pass

            # Connecting line
            item = self.create_line(
                self.plotCoords([(xm, ym, 0.), (x, y, 0.)]),
                tag="Orient",
                fill="Blue",
                dash=(1, 1))

            self.tag_lower(item)

            paths.append(item)

            self.gcode.orient.addPath(paths)

        if self._orientSelected is not None:
            try:
                for item in self.gcode.orient.paths[self._orientSelected]:
                    self.itemconfig(item, width=2)
            except (IndexError, Tk.TclError):
                pass


    def drawProbe(self):
        """
            Display probe
        """

        self.delete("Probe")
        if self._probe:
            self.delete(self._probe)
            self._probe = None

        if not self.draw_probe:
            return

        if self.view in (VIEW_XZ, VIEW_YZ):
            return

        # Draw probe grid
        probe = self.gcode.probe

        for x in bmath.frange(probe.xmin, probe.xmax+0.00001, probe.xstep()):
            xyz = [(x, probe.ymin, 0.), (x, probe.ymax, 0.)]

            item = self.create_line(
                self.plotCoords(xyz),
                tag="Probe",
                fill='Yellow')

            self.tag_lower(item)

        for y in bmath.frange(probe.ymin, probe.ymax+0.00001, probe.ystep()):
            xyz = [(probe.xmin, y, 0.), (probe.xmax, y, 0.)]

            item = self.create_line(
                self.plotCoords(xyz),
                tag="Probe",
                fill='Yellow')

            self.tag_lower(item)

        # Draw probe points
        for i, uv in enumerate(self.plotCoords(probe.points)):
            item = self.create_text(
                uv,
                text="{0:.{1}f}".format(probe.points[i][2], OCV.digits),
                tag="Probe",
                justify=Tk.CENTER,
                fill=OCV.COLOR_PROBE_TEXT)

            self.tag_lower(item)

        # Draw image map if numpy exists
        if (HAS_NUMPY is not None and
                probe.matrix and
                self.view in (VIEW_XY, VIEW_ISO1, VIEW_ISO2, VIEW_ISO3)):

            array = numpy.array(list(reversed(probe.matrix)), numpy.float32)

            lw = array.min()
            hg = array.max()
            mx = max(abs(hg), abs(lw))
            #print "matrix=",probe.matrix
            #print "size=",array.size
            #print "array=",array
            #print "Limits:", lw, hg, mx
            # scale should be:
            #  -mx   .. 0 .. mx
            #  -127     0    127
            # -127 = light-blue
            #    0 = white
            #  127 = light-red
            dc = mx/127.        # step in colors

            if abs(dc) < 1e-8:
                return

            palette = []
            for x in bmath.frange(lw, hg+1e-10, (hg-lw)/255.):
                i = int(math.floor(x / dc))
                j = i + i>>1    # 1.5*i
                if i < 0:
                    palette.append(0xff+j)
                    palette.append(0xff+j)
                    palette.append(0xff)
                elif i > 0:
                    palette.append(0xff)
                    palette.append(0xff-j)
                    palette.append(0xff-j)
                else:
                    palette.append(0xff)
                    palette.append(0xff)
                    palette.append(0xff)
                #print ">>", x,i,palette[-3], palette[-2], palette[-1]
            #print "palette size=",len(palette)/3
            array = numpy.floor((array-lw)/(hg-lw)*255)
            self._probeImage = Image.fromarray(array.astype(numpy.int16)).convert('L')
            self._probeImage.putpalette(palette)

            # Add transparency for a possible composite operation latter on ISO*
            self._probeImage = self._probeImage.convert("RGBA")

            x, y = self._projectProbeImage()

            self._probe = self.create_image(x, y, image=self._probeTkImage, anchor='sw')
            self.tag_lower(self._probe)


    def _projectProbeImage(self):
        """
            Create the tkimage for the current projection
        """

        probe = self.gcode.probe
        size = (int((probe.xmax-probe.xmin + probe._xstep)*self.zoom),
                int((probe.ymax-probe.ymin + probe._ystep)*self.zoom))
        marginx = int(probe._xstep/2. * self.zoom)
        marginy = int(probe._ystep/2. * self.zoom)
        crop = (marginx, marginy, size[0]-marginx, size[1]-marginy)

        image = self._probeImage.resize((size), resample=RESAMPLE).crop(crop)

        if self.view in (VIEW_ISO1, VIEW_ISO2, VIEW_ISO3):
            w, h = image.size
            size2 = (int(S60*(w+h)),
                     int(C60*(w+h)))

            if self.view == VIEW_ISO1:
                transform = (0.5/S60, 0.5/C60, -h/2,
                             -0.5/S60, 0.5/C60, h/2)

                xy = self.plotCoords(
                    [(probe.xmin, probe.ymin, 0.),
                     (probe.xmax, probe.ymin, 0.)])
                x = xy[0][0]
                y = xy[1][1]

            elif self.view == VIEW_ISO2:
                transform = (0.5/S60, -0.5/C60, w/2,
                             0.5/S60, 0.5/C60, -w/2)

                xy = self.plotCoords(
                    [(probe.xmin, probe.ymax, 0.),
                     (probe.xmin, probe.ymin, 0.)])

                x = xy[0][0]
                y = xy[1][1]
            else:
                transform = (-0.5/S60, -0.5/C60, w+h/2,
                             0.5/S60, -0.5/C60, h/2)

                xy = self.plotCoords(
                    [(probe.xmax, probe.ymax, 0.),
                     (probe.xmin, probe.ymax, 0.)])

                x = xy[0][0]
                y = xy[1][1]

            affine = image.transform(
                size2,
                Image.AFFINE,
                transform,
                resample=RESAMPLE)
            # Super impose a white image
            white = Image.new('RGBA', affine.size, (255,)*4)
            # compose the two images affine and white with mask the affine
            image = Image.composite(affine, white, affine)
            del white

        else:
            x, y = self.plotCoords([(probe.xmin, probe.ymin, 0.)])[0]

        self._probeTkImage = ImageTk.PhotoImage(image)

        return x, y


    def drawPaths(self):
        """
            Draw the paths for the whole gcode file
        """

        if not self.draw_paths:
            for block in OCV.blocks:
                block.resetPath()
            return

        try:
            n = 1
            startTime = before = time.time()
            self.cnc.resetAllMargins()
            drawG = self.draw_rapid or self.draw_paths or self.draw_margin
            bid = OCV.TK_APP.editor.getSelectedBlocks()

            for i, block in enumerate(OCV.blocks):

                if i in bid:
                    selected = True
                else:
                    selected = False

                start = True    # start location found
                block.resetPath()

                # Draw block
                for j, line in enumerate(block):
                    n -= 1
                    if n == 0:
                        if time.time() - startTime > OCV.DRAW_TIME:
                            raise AlarmException()
                        # Force a periodic update since this loop can take time
                        if time.time() - before > 1.0:
                            self.update()
                            before = time.time()
                        n = 1000
                    try:
                        cmd = self.gcode.evaluate(CNC.compileLine(line))

                        if isinstance(cmd, tuple):
                            cmd = None
                        else:
                            cmd = CNC.breakLine(cmd)

                    except AlarmException:
                        raise
                    except:
                        sys.stderr.write(_(">>> ERROR: {0}\n").format(
                            str(sys.exc_info()[1])))

                        sys.stderr.write(_("     line: {0}\n").format(line))
                        cmd = None

                    if cmd is None or not drawG:
                        block.addPath(None)
                    else:
                        path = self.drawPath(block, cmd)
                        self._items[path] = i, j
                        block.addPath(path)
                        if start and self.cnc.gcode in (1, 2, 3):
                            # Mark as start the first non-rapid motion
                            block.startPath(self.cnc.x, self.cnc.y, self.cnc.z)
                            start = False
                block.endPath(self.cnc.x, self.cnc.y, self.cnc.z)

        except AlarmException:
            self.status("Rendering takes TOO Long. Interrupted...")


    def drawPath(self, block, cmds):
        """Create path for one g command
        """

        self.cnc.motionStart(cmds)
        xyz = self.cnc.motionPath()
        self.cnc.motionEnd()
        if xyz:
            self.cnc.pathLength(block, xyz)
            if self.cnc.gcode in (1, 2, 3):
                block.pathMargins(xyz)
                self.cnc.pathMargins(block)
            if block.enable:
                if self.cnc.gcode == 0 and self.draw_rapid:
                    xyz[0] = self._last
                self._last = xyz[-1]
            else:
                if self.cnc.gcode == 0:
                    return None
            coords = self.plotCoords(xyz)
            if coords:
                if block.enable:
                    if block.color:
                        fill = block.color
                    else:
                        fill = OCV.COLOR_ENABLE
                else:
                    fill = OCV.COLOR_DISABLE

                if self.cnc.gcode == 0:

                    if self.draw_rapid:

                        return self.create_line(
                            coords,
                            fill=fill,
                            width=0,
                            dash=(4, 3))

                elif self.draw_paths:

                    return self.create_line(
                        coords,
                        fill=fill,
                        width=0,
                        cap="projecting")

        return None

    def plotCoords(self, xyz):
        """
            Return plotting coordinates for a 3d xyz path

            NOTE: Use the Tkinter._flatten() to pass to self.coords() function
        """

        coords = None

        if self.view == VIEW_XY:
            coords = [(p[0]*self.zoom, -p[1]*self.zoom) for p in xyz]

        elif self.view == VIEW_XZ:
            coords = [(p[0]*self.zoom, -p[2]*self.zoom) for p in xyz]

        elif self.view == VIEW_YZ:
            coords = [(p[1]*self.zoom, -p[2]*self.zoom) for p in xyz]

        elif self.view == VIEW_ISO1:
            coords = [((p[0]*S60 + p[1]*S60)*self.zoom,
                       (+p[0]*C60 - p[1]*C60 - p[2])*self.zoom) for p in xyz]

        elif self.view == VIEW_ISO2:
            coords = [((p[0]*S60 - p[1]*S60)*self.zoom,
                       (-p[0]*C60 - p[1]*C60 - p[2])*self.zoom) for p in xyz]

        elif self.view == VIEW_ISO3:
            coords = [((-p[0]*S60 - p[1]*S60)*self.zoom,
                       (-p[0]*C60 + p[1]*C60 - p[2])*self.zoom) for p in xyz]

        # Check limits
        for i, (x, y) in enumerate(coords):

            if abs(x) > MAXDIST or abs(y) > MAXDIST:

                if x < -MAXDIST:
                    x = -MAXDIST

                elif x > MAXDIST:
                    x = MAXDIST

                if y < -MAXDIST:
                    y = -MAXDIST

                elif y > MAXDIST:
                    y = MAXDIST

                coords[i] = (x, y)

        return coords

    def canvas2xyz(self, i, j):
        """
            Canvas to real coordinates
        """

        #coords = None
        if self.view == VIEW_XY:
            x = i / self.zoom
            y = -j / self.zoom
            z = 0

        elif self.view == VIEW_XZ:
            x = i / self.zoom
            y = 0
            z = -j / self.zoom

        elif self.view == VIEW_YZ:
            x = 0
            y = i / self.zoom
            z = -j / self.zoom

        elif self.view == VIEW_ISO1:
            x = (i/S60 + j/C60) / self.zoom / 2
            y = (i/S60 - j/C60) / self.zoom / 2
            z = 0

        elif self.view == VIEW_ISO2:
            x = (i/S60 - j/C60) / self.zoom / 2
            y = -(i/S60 + j/C60) / self.zoom / 2
            z = 0

        elif self.view == VIEW_ISO3:
            x = -(i/S60 + j/C60) / self.zoom / 2
            y = -(i/S60 - j/C60) / self.zoom / 2
            z = 0

        return x, y, z


class CanvasFrame(Tk.Frame):
    """Canvas Frame with toolbar"""

    def __init__(self, master, app, *kw, **kwargs):
        Tk.Frame.__init__(self, master, *kw, **kwargs)

        self.draw_axes = Tk.BooleanVar()
        self.draw_grid = Tk.BooleanVar()
        self.draw_margin = Tk.BooleanVar()
        self.draw_probe = Tk.BooleanVar()
        self.draw_paths = Tk.BooleanVar()
        self.draw_rapid = Tk.BooleanVar()
        self.draw_workarea = Tk.BooleanVar()
        self.draw_camera = Tk.BooleanVar()
        self.view = Tk.StringVar()

        self.loadConfig()

        self.view.trace('w', self.viewChange)

        self.canvas = CNCCanvas(self, app, takefocus=True, background="White")

        print("self.canvas.winfo_id(): {0}".format(self.canvas.winfo_id())) #OpenGL context

        self.canvas.grid(row=1, column=0, sticky=Tk.NSEW)

        sby = Tk.Scrollbar(self, orient=Tk.VERTICAL, command=self.canvas.yview)
        sby.grid(row=1, column=1, sticky=Tk.NS)

        self.canvas.config(yscrollcommand=sby.set)

        sbx = Tk.Scrollbar(self, orient=Tk.HORIZONTAL, command=self.canvas.xview)
        sbx.grid(row=2, column=0, sticky=Tk.EW)
        self.canvas.config(xscrollcommand=sbx.set)


        toolbar = Tk.Frame(self, relief=Tk.RAISED)
        toolbar.grid(row=0, column=0, columnspan=2, sticky=Tk.EW)

        self.createCanvasToolbar(toolbar)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)


    def createCanvasToolbar(self, toolbar):
        """
                Canvas toolbar
        """

        obj = Tk.OptionMenu(toolbar, self.view, *VIEWS)
        obj.config(padx=0, pady=1)
        obj.unbind("F10")
        obj.pack(side=Tk.LEFT)

        tkExtra.Balloon.set(obj, _("Change viewing angle"))

        but = Tk.Button(
            toolbar,
            image=OCV.icons["zoom_in"],
            command=self.canvas.menuZoomIn)

        tkExtra.Balloon.set(but, _("Zoom In [Ctrl-=]"))

        but.pack(side=Tk.LEFT)

        but = Tk.Button(
            toolbar,
            image=OCV.icons["zoom_out"],
            command=self.canvas.menuZoomOut)

        tkExtra.Balloon.set(but, _("Zoom Out [Ctrl--]"))

        but.pack(side=Tk.LEFT)

        but = Tk.Button(
            toolbar,
            image=OCV.icons["zoom_on"],
            command=self.canvas.fit2Screen)

        tkExtra.Balloon.set(but, _("Fit to screen [F]"))

        but.pack(side=Tk.LEFT)

        lab = Tk.Label(
            toolbar,
            text=_("Tool:"),
            image=OCV.icons["sep"],
            compound=Tk.LEFT)

        lab.pack(side=Tk.LEFT, padx=2)
        # -----
        # Tools
        # -----
        but = Tk.Radiobutton(
            toolbar,
            image=OCV.icons["select"],
            indicatoron=0,
            variable=self.canvas.actionVar,
            value=ACTION_SELECT,
            command=self.canvas.setActionSelect)

        tkExtra.Balloon.set(but, _("Select tool [S]"))

        self.addWidget(but)

        but.pack(side=Tk.LEFT)

        but = Tk.Radiobutton(
            toolbar,
            image=OCV.icons["pan"],
            indicatoron=0,
            variable=self.canvas.actionVar,
            value=ACTION_PAN,
            command=self.canvas.setActionPan)

        tkExtra.Balloon.set(but, _("Pan viewport [X]"))

        but.pack(side=Tk.LEFT)

        but = Tk.Radiobutton(
            toolbar,
            image=OCV.icons["ruler"],
            indicatoron=0,
            variable=self.canvas.actionVar,
            value=ACTION_RULER,
            command=self.canvas.setActionRuler)

        tkExtra.Balloon.set(but, _("Ruler [R]"))

        but.pack(side=Tk.LEFT)

        # -----------
        # Draw flags
        # -----------
        lab = Tk.Label(
            toolbar,
            text=_("Draw:"),
            image=OCV.icons["sep"],
            compound=Tk.LEFT)

        lab.pack(side=Tk.LEFT, padx=2)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["axes"],
            indicatoron=0,
            variable=self.draw_axes,
            command=self.drawAxes)

        tkExtra.Balloon.set(but, _("Toggle display of axes"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["grid"],
            indicatoron=0,
            variable=self.draw_grid,
            command=self.drawGrid)

        tkExtra.Balloon.set(but, _("Toggle display of grid lines"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["margins"],
            indicatoron=0,
            variable=self.draw_margin,
            command=self.drawMargin)

        tkExtra.Balloon.set(but, _("Toggle display of margins"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            text="P",
            image=OCV.icons["measure"],
            indicatoron=0,
            variable=self.draw_probe,
            command=self.drawProbe)

        tkExtra.Balloon.set(but, _("Toggle display of probe"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["endmill"],
            indicatoron=0,
            variable=self.draw_paths,
            command=self.toggleDrawFlag)

        tkExtra.Balloon.set(but, _("Toggle display of paths (G1,G2,G3)"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["rapid"],
            indicatoron=0,
            variable=self.draw_rapid,
            command=self.toggleDrawFlag)

        tkExtra.Balloon.set(but, _("Toggle display of rapid motion (G0)"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["workspace"],
            indicatoron=0,
            variable=self.draw_workarea,
            command=self.drawWorkarea)

        tkExtra.Balloon.set(but, _("Toggle display of workarea"))

        but.pack(side=Tk.LEFT)

        but = Tk.Checkbutton(
            toolbar,
            image=OCV.icons["camera"],
            indicatoron=0,
            variable=self.draw_camera,
            command=self.drawCamera)

        tkExtra.Balloon.set(but, _("Toggle display of camera"))

        but.pack(side=Tk.LEFT)

        if Camera.cv is None: but.config(state=Tk.DISABLED)

        but = Tk.Button(
            toolbar,
            image=OCV.icons["refresh"],
            command=self.viewChange)

        tkExtra.Balloon.set(but, _("Redraw display [Ctrl-R]"))

        but.pack(side=Tk.LEFT)

        # -----------
        self.drawTime = tkExtra.Combobox(
            toolbar,
            width=3,
            background="White",
            command=self.drawTimeChange)

        tkExtra.Balloon.set(self.drawTime, _("Draw timeout in seconds"))

        self.drawTime.fill(["inf", "1", "2", "3", "5", "10", "20", "30", "60", "120"])

        self.drawTime.set(OCV.DRAW_TIME)

        self.drawTime.pack(side=Tk.RIGHT)

        lab = Tk.Label(toolbar, text=_("Timeout:"))

        lab.pack(side=Tk.RIGHT)

    def addWidget(self, widget):
        OCV.iface_widgets.append(widget)

    def loadConfig(self):

        self.draw_axes.set(bool(int(IniFile.get_bool("Canvas", "axes", True))))
        self.draw_grid.set(bool(int(IniFile.get_bool("Canvas", "grid", True))))
        self.draw_margin.set(
            bool(int(IniFile.get_bool("Canvas", "margin", True))))
        # self.draw_probe.set(bool(int(
        #       IniFile.get_bool("Canvas", "probe",   False))))
        self.draw_paths.set(
            bool(int(IniFile.get_bool("Canvas", "paths", True))))
        self.draw_rapid.set(
            bool(int(IniFile.get_bool("Canvas", "rapid", True))))
        self.draw_workarea.set(
            bool(int(IniFile.get_bool("Canvas", "workarea", True))))
        # self.draw_camera.set(bool(int(
        #        IniFile.get_bool("Canvas", "camera",  False))))

        self.view.set(IniFile.get_str("Canvas", "view", VIEWS[0]))

        OCV.DRAW_TIME = IniFile.get_int("Canvas", "drawtime", OCV.DRAW_TIME)

    def saveConfig(self):
        IniFile.set_value("Canvas", "drawtime", OCV.DRAW_TIME)
        IniFile.set_value("Canvas", "view", self.view.get())
        IniFile.set_value("Canvas", "axes", self.draw_axes.get())
        IniFile.set_value("Canvas", "grid", self.draw_grid.get())
        IniFile.set_value("Canvas", "margin", self.draw_margin.get())
        IniFile.set_value("Canvas", "probe", self.draw_probe.get())
        IniFile.set_value("Canvas", "paths", self.draw_paths.get())
        IniFile.set_value("Canvas", "rapid", self.draw_rapid.get())
        IniFile.set_value("Canvas", "workarea", self.draw_workarea.get())
        #IniFile.set_value("Canvas", "camera",  self.draw_camera.get())


    def redraw(self, event=None):
        self.canvas.reset()
        self.event_generate("<<ViewChange>>")


    def viewChange(self, a=None, b=None, c=None):
        self.event_generate("<<ViewChange>>")


    def viewXY(self, event=None):
        self.view.set(VIEWS[VIEW_XY])


    def viewXZ(self, event=None):
        self.view.set(VIEWS[VIEW_XZ])


    def viewYZ(self, event=None):
        self.view.set(VIEWS[VIEW_YZ])


    def viewISO1(self, event=None):
        self.view.set(VIEWS[VIEW_ISO1])


    def viewISO2(self, event=None):
        self.view.set(VIEWS[VIEW_ISO2])


    def viewISO3(self, event=None):
        self.view.set(VIEWS[VIEW_ISO3])


    def toggleDrawFlag(self):
        self.canvas.draw_axes = self.draw_axes.get()
        self.canvas.draw_grid = self.draw_grid.get()
        self.canvas.draw_margin = self.draw_margin.get()
        self.canvas.draw_probe = self.draw_probe.get()
        self.canvas.draw_paths = self.draw_paths.get()
        self.canvas.draw_rapid = self.draw_rapid.get()
        self.canvas.draw_workarea = self.draw_workarea.get()
        self.event_generate("<<ViewChange>>")


    def drawAxes(self, value=None):
        if value is not None: self.draw_axes.set(value)
        self.canvas.draw_axes = self.draw_axes.get()
        self.canvas.drawAxes()


    def drawGrid(self, value=None):
        if value is not None: self.draw_grid.set(value)
        self.canvas.draw_grid = self.draw_grid.get()
        self.canvas.drawGrid()


    def drawMargin(self, value=None):
        if value is not None: self.draw_margin.set(value)
        self.canvas.draw_margin = self.draw_margin.get()
        self.canvas.drawMargin()


    def drawProbe(self, value=None):
        if value is not None: self.draw_probe.set(value)
        self.canvas.draw_probe = self.draw_probe.get()
        self.canvas.drawProbe()


    def drawWorkarea(self, value=None):
        if value is not None: self.draw_workarea.set(value)
        self.canvas.draw_workarea = self.draw_workarea.get()
        self.canvas.drawWorkarea()


    def drawCamera(self, value=None):
        if value is not None: self.draw_camera.set(value)
        if self.draw_camera.get():
            self.canvas.cameraOn()
        else:
            self.canvas.cameraOff()


    def drawTimeChange(self):
        try:
            OCV.DRAW_TIME = int(self.drawTime.get())
        except ValueError:
            OCV.DRAW_TIME = 5*60
        self.viewChange()


class CanvasTooltip:
    """
    It creates a tooltip for a given canvas tag or id as the mouse is
    above it.

    This class has been derived from the original Tooltip class I updated
    and posted back to StackOverflow at the following link:

    https://stackoverflow.com/questions/3221956/
           what-is-the-simplest-way-to-make-tooltips-in-tkinter/
           41079350#41079350

    Alberto Vassena on 2016.12.10.

    usage:

    tooltips[]

    tooltip = CanvasTooltip(self, id_, text=text)

    self.tooltips.append(tooltip)

    """

    def __init__(self, canvas, tag_or_id,
                 bg='#FFFFEA',
                 pad=(5, 3, 5, 3),
                 text='canvas info',
                 waittime=400,
                 wraplength=250,
                 tag=None):
        self.waittime = waittime  # in miliseconds, originally 500
        self.wraplength = wraplength  # in pixels, originally 180
        self.canvas = canvas
        self.text = text
        self.canvas.tag_bind(tag_or_id, "<Enter>", self.onEnter)
        self.canvas.tag_bind(tag_or_id, "<Leave>", self.onLeave)
        self.canvas.tag_bind(tag_or_id, "<ButtonPress>", self.onLeave)
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None
        self.tag = tag

    def onEnter(self, event=None):
        self.schedule()

    def onLeave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.canvas.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.canvas.after_cancel(id_)

    def show(self, event=None):
        def tip_pos_calculator(canvas, label,
                               tip_delta=(10, 5), pad=(5, 3, 5, 3)):

            c = canvas

            s_width, s_height = c.winfo_screenwidth(), c.winfo_screenheight()

            width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                             pad[1] + label.winfo_reqheight() + pad[3])

            mouse_x, mouse_y = c.winfo_pointerxy()

            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0

            offscreen = (x_delta, y_delta) != (0, 0)

            if offscreen:

                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width

                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height

            offscreen_again = y1 < 0  # out on the top

            if offscreen_again:
                # No further checks will be done.

                # TIP:
                # A further mod might automagically augment the
                # wraplength when the tooltip is too high to be
                # kept inside the screen.
                y1 = 0

            return x1, y1

        bg = self.bg
        pad = self.pad
        canvas = self.canvas

        # creates a toplevel window
        self.tw = Tk.Toplevel(canvas.master)

        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)

        win = Tk.Frame(
            self.tw,
            background=bg,
            borderwidth=0)

        label = Tk.Label(
            win,
            text=self.text,
            justify=Tk.LEFT,
            background=bg,
            relief=Tk.SOLID,
            borderwidth=0,
            wraplength=self.wraplength)

        label.grid(
            padx=(pad[0], pad[2]),
            pady=(pad[1], pad[3]),
            sticky=Tk.NSEW)

        win.grid()

        x, y = tip_pos_calculator(canvas, label)

        self.tw.wm_geometry("+{0:d}+{1:d}".format(x, y))

    def hide(self):
        if self.tw:
            self.tw.destroy()
        self.tw = None
