# -*- coding: ascii -*-
# $Id: CNC.py,v 1.8 2014/10/15 15:03:49 bnv Exp $
#
# Author: carlo.dormeletti@gmail.com
# Date: 26 Oct 2019

from __future__ import absolute_import
from __future__ import print_function

import os
import re
import math
import types

import OCV
import undo
import Unicode

# from dxf import DXF
from bstl import Binary_STL_Writer
from bpath import eq, Path, Segment
from bmath import *
from copy import deepcopy
# from svgcode import SVGcode
from time import strftime, localtime

IDPAT = re.compile(r".*\bid:\s*(.*?)\)")
PARENPAT = re.compile(r"(\(.*?\))")
SEMIPAT = re.compile(r"(;.*)")
OPPAT = re.compile(r"(.*)\[(.*)\]")
CMDPAT = re.compile(r"([A-Za-z]+)")
BLOCKPAT = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
AUXPAT = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")

STOP = 0
SKIP = 1
ASK = 2
MSG = 3
WAIT = 4
UPDATE = 5

XY = 0
XZ = 1
YZ = 2

CW = 2
CCW = 3

# Modal Mode from $G and variable set
MODAL_MODES = {
    "G0": "motion",
    "G1": "motion",
    "G2": "motion",
    "G3": "motion",
    "G38.2": "motion",
    "G38.3": "motion",
    "G38.4": "motion",
    "G38.5": "motion",
    "G80": "motion",

    "G54": "WCS",
    "G55": "WCS",
    "G56": "WCS",
    "G57": "WCS",
    "G58": "WCS",
    "G59": "WCS",

    "G17": "plane",
    "G18": "plane",
    "G19": "plane",

    "G90": "distance",
    "G91": "distance",

    "G91.1": "arc",

    "G93": "feedmode",
    "G94": "feedmode",
    "G95": "feedmode",

    "G20": "units",
    "G21": "units",

    "G40": "cutter",

    "G43.1": "tlo",
    "G49": "tlo",

    "M0": "program",
    "M1": "program",
    "M2": "program",
    "M30": "program",

    "M3": "spindle",
    "M4": "spindle",
    "M5": "spindle",

    "M7": "coolant",
    "M8": "coolant",
    "M9": "coolant",
}

ERROR_HANDLING = {}
TOLERANCE = 1e-7
MAXINT = 1000000000    # python3 doesn't have maxint


def getValue(name, new, old, default=0.0):
    """Return a value combined from two dictionaries new/old"""

    try:
        return new[name]
    except Exception:
        try:
            return old[name]
        except Exception:
            return default


class Probe(object):
    """Probing class and linear interpolation"""
    def __init__(self):
        self.init()

    def init(self):
        self.filename = ""
        self.xmin = 0.0
        self.ymin = 0.0
        self.zmin = -10.0

        self.xmax = 10.0
        self.ymax = 10.0
        self.zmax = 3.0

        self._xstep = 1.0
        self._ystep = 1.0

        self.xn = 5
        self.yn = 5

        self.points = []  # probe points
        self.matrix = []  # 2D matrix with Z coordinates
        self.zeroed = False  # if probe was zeroed at any location
        self.start = False  # start collecting probes
        self.saved = False

    def clear(self):
        del self.points[:]
        del self.matrix[:]
        self.zeroed = False
        self.start = False
        self.saved = False

    def isEmpty(self):
        return len(self.matrix) == 0

    def makeMatrix(self):
        del self.matrix[:]
        for j in range(self.yn):
            self.matrix.append([0.0]*(self.xn))

    def load(self, filename=None):
        """Load autolevel information from file"""

        if filename is not None:
            self.filename = filename
        self.clear()
        self.saved = True

        def read(f):
            while True:
                line = f.readline()
                if len(line) == 0:
                    raise

                line = line.strip()

                if line:
                    return map(float, line.split())

        f = open(self.filename, "r")
        self.xmin, self.xmax, self.xn = read(f)
        self.ymin, self.ymax, self.yn = read(f)
        self.zmin, self.zmax, feed = read(f)
        OCV.CD["prbfeed"] = feed

        self.xn = max(2, int(self.xn))
        self.yn = max(2, int(self.yn))

        self.makeMatrix()
        self.xstep()
        self.ystep()

        self.start = True
        try:
            for j in range(self.yn):
                for i in range(self.xn):
                    self.add(*read(f))
        except Exception:
            raise
            # print "Error reading probe file",self.filename
        f.close()

    def save(self, filename=None):
        """Save level information to file"""

        if filename is None:
            filename = self.filename

        fn, ext = os.path.splitext(filename)
        ext = ext.lower()

        f = open(filename, "w")
        if ext != '.xyz':
            self.filename = filename
            f.write(
                "{0:0.f} {1:0.f} {2:d}".format(
                    self.xmin,
                    self.xmax,
                    self.xn)
                )

            f.write(
                "{0:0.f} {1:0.f} {2:d}".format(
                    self.ymin,
                    self.ymax,
                    self.yn)
                )

            f.write(
                "{0:0.f} {1:0.f} {2:0.f}".format(
                    self.zmin,
                    self.zmax,
                    OCV.CD["prbfeed"])
                )

            f.write("\n\n")

        for j in range(self.yn):
            y = self.ymin + self._ystep*j

            for i in range(self.xn):
                x = self.xmin + self._xstep*i

                f.write(
                    "{0:0.f} {1:0.f} {2:0.f}".format(
                        x, y, self.matrix[j][i])
                    )

            f.write("\n")

        f.close()

        self.saved = True

    def saveAsSTL(self, filename=None):
        """Save level information as STL file"""

        if filename is not None:
            self.filename = filename

        with open(self.filename, 'wb') as fp:
            writer = Binary_STL_Writer(fp)

            for j in range(self.yn - 1):
                y1 = self.ymin + self._ystep*j
                y2 = self.ymin + self._ystep*(j+1)
                for i in range(self.xn - 1):
                    x1 = self.xmin + self._xstep*i
                    x2 = self.xmin + self._xstep*(i+1)
                    v1 = [x1, y1, self.matrix[j][i]]
                    v2 = [x2, y1, self.matrix[j][i+1]]
                    v3 = [x2, y2, self.matrix[j+1][i+1]]
                    v4 = [x1, y2, self.matrix[j+1][i]]
                    writer.add_face([v1, v2, v3, v4])
            writer.close()

    def xstep(self):
        """Return X step"""
        self._xstep = (self.xmax-self.xmin)/float(self.xn-1)
        return self._xstep

    def ystep(self):
        """Return Y step"""
        self._ystep = (self.ymax-self.ymin)/float(self.yn-1)
        return self._ystep

    def scanMargins(self):
        """Return the code needed to scan margins for autoleveling"""
        lines = []

        lines.append("G0 {0:0.f} {1:0.f} {2:0.f}".format(self.xmin, self.ymin))
        lines.append("G0 {0:0.f} {1:0.f} {2:0.f}".format(self.xmin, self.ymax))
        lines.append("G0 {0:0.f} {1:0.f} {2:0.f}".format(self.xmax, self.ymax))
        lines.append("G0 {0:0.f} {1:0.f} {2:0.f}".format(self.xmax, self.ymin))
        lines.append("G0 {0:0.f} {1:0.f} {2:0.f}".format(self.xmin, self.ymin))

        return lines

    def scan(self):
        """Return the code needed to scan for autoleveling"""
        self.clear()
        self.start = True
        self.makeMatrix()
        x = self.xmin
        xstep = self._xstep
        lines = [
            "G0 Z{0:0.f}".format(OCV.CD["safe"]),
            "G0 X{0:0.f} Y{1:0.f}".format(self.xmin, self.ymin)
            ]

        for j in range(self.yn):
            y = self.ymin + self._ystep*j
            for i in range(self.xn):
                lines.append("G0 Z{0:0.f}".format(self.zmax))
                lines.append("G0 X{0:0.f} Y{1:0.f}".format(x, y))
                lines.append("%wait")  # added for smoothie

                lines.append(
                    "{0}Z{1:0.f} F{2:0.f}".format(
                        OCV.CD["prbcmd"],
                        self.zmin,
                        OCV.CD["prbfeed"])
                    )

                lines.append("%wait")  # added for smoothie
                x += xstep
            x -= xstep
            xstep = -xstep
        lines.append("G0 Z{0:0.f}".format(self.zmax))
        lines.append("G0 X{0:0.f} Y{1:0.f}".format(self.xmin, self.ymin))
        return lines

    def add(self, x, y, z):
        """Add a probed point to the list and the 3D matrix"""
        if not self.start:
            return

        i = round((x-self.xmin) / self._xstep)

        if i < 0.0 or i > self.xn:
            return

        j = round((y-self.ymin) / self._ystep)

        if j < 0.0 or j > self.yn:
            return

        rem = abs(x - (i*self._xstep + self.xmin))

        if rem > self._xstep/10.0:
            return

        rem = abs(y - (j*self._ystep + self.ymin))

        if rem > self._ystep/10.0:
            return

        try:
            self.matrix[int(j)][int(i)] = z
            self.points.append([x, y, z])
        except IndexError:
            pass

        if len(self.points) >= self.xn*self.yn:
            self.start = False

    def setZero(self, x, y):
        """Make z-level relative to the location of (x,y,0)"""
        del self.points[:]

        if self.isEmpty():
            self.zeroed = False
            return

        zero = self.interpolate(x, y)
        self.xstep()
        self.ystep()

        for j, row in enumerate(self.matrix):
            y = self.ymin + self._ystep*j

            for i in range(len(row)):
                x = self.xmin + self._xstep*i
                row[i] -= zero
                self.points.append([x, y, row[i]])

        self.zeroed = True

    def interpolate(self, x, y):
        ix = (x-self.xmin) / self._xstep
        jy = (y-self.ymin) / self._ystep
        i = int(math.floor(ix))
        j = int(math.floor(jy))

        if i < 0:
            i = 0
        elif i >= self.xn-1:
            i = self.xn-2

        if j < 0:
            j = 0
        elif j >= self.yn-1:
            j = self.yn-2

        a = ix - i
        b = jy - j
        a1 = 1.0 - a
        b1 = 1.0 - b

        return a1 * b1 * self.matrix[j][i] \
               + a1 * b  * self.matrix[j+1][i] \
               + a * b1 * self.matrix[j][i+1] \
               + a * b  * self.matrix[j+1][i+1]

    def splitLine(self, x1, y1, z1, x2, y2, z2):
        """
        Split line into multiple segments correcting for Z if needed
        return only end points
        """
        dx = x2-x1
        dy = y2-y1
        dz = z2-z1

        if abs(dx) < 1e-10:
            dx = 0.0

        if abs(dy) < 1e-10:
            dy = 0.0

        if abs(dz) < 1e-10:
            dz = 0.0

        if dx == 0.0 and dy == 0.0:
            return [(x2, y2, z2+self.interpolate(x2, y2))]

        # Length along projection on X-Y plane
        rxy = math.sqrt(dx*dx + dy*dy)
        dx /= rxy  # direction cosines along XY plane
        dy /= rxy
        dz /= rxy  # add correction for the slope in Z, versus the travel in XY

        i = int(math.floor((x1-self.xmin) / self._xstep))
        j = int(math.floor((y1-self.ymin) / self._ystep))

        if dx > 1e-10:
            # distance to next cell
            tx = (float(i+1)*self._xstep + self.xmin - x1) / dx
            tdx = self._xstep / dx
        elif dx < -1e-10:
            # distance to next cell
            tx = (float(i)*self._xstep + self.xmin - x1) / dx
            tdx = -self._xstep / dx
        else:
            tx = 1e10
            tdx = 0.0

        if dy > 1e-10:
            # distance to next cell
            ty = (float(j+1)*self._ystep + self.ymin - y1) / dy
            tdy = self._ystep / dy
        elif dy < -1e-10:
            # distance to next cell
            ty = (float(j)*self._ystep + self.ymin - y1) / dy
            tdy = -self._ystep / dy
        else:
            ty = 1e10
            tdy = 0.0

        segments = []
        rxy *= 0.999999999  # just reduce a bit to avoid precision errors
        while tx < rxy or ty < rxy:
            if tx == ty:
                t = tx
                tx += tdx
                ty += tdy
            elif tx < ty:
                t = tx
                tx += tdx
            else:
                t = ty
                ty += tdy
            x = x1 + t*dx
            y = y1 + t*dy
            z = z1 + t*dz
            segments.append((x, y, z+self.interpolate(x, y)))

        segments.append((x2, y2, z2+self.interpolate(x2, y2)))
        return segments


class Orient:
    """
    contains a list of machine points vs position in the gcode
    calculates the transformation matrix (rotation + translation) needed
    to adjust the gcode to match the workpiece on the machine
    """

    def __init__(self):
        """
        list of points pairs (xm, ym, x, y)
        xm,ym = machine x,y mpos
        x, y  = desired or gcode location
        """
        self.markers = []
        self.paths = []
        self.errors = []
        self.filename = ""
        self.clear()

    def clear(self, item=None):
        if item is None:
            self.clearPaths()
            del self.markers[:]
        else:
            del self.paths[item]
            del self.markers[item]

        self.phi = 0.0
        self.xo = 0.0
        self.yo = 0.0
        self.valid = False
        self.saved = False

    def clearPaths(self):
        del self.paths[:]

    def add(self, xm, ym, x, y):
        self.markers.append((xm, ym, x, y))
        self.valid = False
        self.saved = False

    def addPath(self, path):
        self.paths.append(path)

    def __getitem__(self, i):
        return self.markers[i]

    def __len__(self):
        return len(self.markers)

    # -----------------------------------------------------------------------
    # For the next module
    # Transformation equation is the following

    # Xm = R * X + T

    # Xm = [xm ym]^t
    # X  = [x y]^t

    #       / cosf  -sinf \   / c  -s \
    #   R = |             | = |       |
    #       \ sinf   cosf /   \ s   c /

    # Assuming that the machine is squared. We could even solve it for
    # a skewed machine, but then the arcs have to be converted to
    # ellipses...

    # T = [xo yo]^t

    # The overdetermined system (equations) to solve are the following
    #      c*x + s*(-y) + xo      = xm
    #      s*x + c*y    + yo      = ym
    #  <=> c*y + s*y         + yo = ym

    # We are solving for the unknowns c,s,xo,yo

    #       /  x1  -y1  1 0 \ / c  \    / xm1 \
    #       |  y1   x1  0 1 | | s  |    | ym1 |
    #       |  x2  -y2  1 0 | | xo |    | xm2 |
    #       |  y2   x2  0 1 | \ yo /  = | ym2 |
    #          ...                   ..
    #       |  xn  -yn  1 0 |           | xmn |
    #       \  yn   xn  0 1 /           \ ymn /
    #
    #               A            X    =    B
    #
    # Constraints:
    # 1. orthogonal system   c^2 + s^2 = 1
    # 2. no aspect ratio

    def solve(self):
        """
        Return the rotation angle phi in radians and the offset (xo,yo)
        or none on failure
        """

        self.valid = False
        if len(self.markers) < 2:
            raise Exception("Too few markers")

        A = []
        B = []

        for xm, ym, x, y in self.markers:
            A.append([x, -y, 1.0, 0.0])
            B.append([xm])

            A.append([y, x, 0.0, 1.0])
            B.append([ym])

        # The solution of the overdetermined system A X = B
        try:
            c, s, self.xo, self.yo = solveOverDetermined(Matrix(A), Matrix(B))
        except Exception:
            raise Exception("Unable to solve system")

        # print "c,s,xo,yo=",c,s,xo,yo

        # Normalize the coefficients
        r = sqrt(c*c + s*s)  # length should be 1.0
        if abs(r-1.0) > 0.1:
            raise Exception("Resulting system is too skew")

        # print "r=",r
        # xo /= r
        # yo /= r
        self.phi = atan2(s, c)

        if abs(self.phi) < TOLERANCE:
            self.phi = 0.0  # rotation

        self.valid = True

        return self.phi, self.xo, self.yo

    def error(self):
        """@return minimum, average and maximum error"""
        # Type errors
        minerr = 1e9
        maxerr = 0.0
        sumerr = 0.0

        c = cos(self.phi)
        s = sin(self.phi)

        del self.errors[:]

        for i, (xm, ym, x, y) in enumerate(self.markers):
            dx = c*x - s*y + self.xo - xm
            dy = s*x + c*y + self.yo - ym
            err = sqrt(dx**2 + dy**2)
            self.errors.append(err)

            minerr = min(minerr, err)
            maxerr = max(maxerr, err)
            sumerr += err

        return minerr, sumerr/float(len(self.markers)), maxerr

    def gcode2machine(self, x, y):
        """Convert gcode to machine coordinates"""
        c = cos(self.phi)
        s = sin(self.phi)
        return c*x - s*y + self.xo, s*x + c*y + self.yo

    def machine2gcode(self, x, y):
        """Convert machine to gcode coordinates"""
        c = cos(self.phi)
        s = sin(self.phi)
        x -= self.xo
        y -= self.yo
        return     c*x + s*y, -s*x + c*y

    def load(self, filename=None):
        """Load orient information from file"""
        if filename is not None:
            self.filename = filename
        self.clear()
        self.saved = True

        f = open(self.filename, "r")
        for line in f:
            self.add(*map(float, line.split()))
        f.close()

    def save(self, filename=None):
        """Save orient information to file"""
        if filename is not None:
            self.filename = filename
        f = open(self.filename, "w")
        for xm, ym, x, y in self.markers:
            f.write("{0:0.f} {1:0.f} {2:0.f} {3:0.f} ".format(xm, ym, x, y))
        f.close()
        self.saved = True


class CNC:
    """Command operations on a CNC"""

    def __init__(self):
        self.initPath()
        self.resetAllMargins()

    @staticmethod
    def updateG():
        """Update G variables from "G" string"""
        for g in OCV.CD["G"]:
            if g[0] == "F":
                OCV.CD["feed"] = float(g[1:])
            elif g[0] == "S":
                OCV.CD["rpm"] = float(g[1:])
            elif g[0] == "T":
                OCV.CD["tool"] = int(g[1:])
            else:
                var = MODAL_MODES.get(g)
                if var is not None:
                    OCV.CD[var] = g

    def __getitem__(self, name):
        return OCV.CD[name]

    def __setitem__(self, name, value):
        OCV.CD[name] = value

    @staticmethod
    def loadConfig(config):
        section = "CNC"
        try:
            OCV.inch = bool(int(config.get(section, "units")))
        except Exception:
            pass

        try:
            OCV.lasercutter = bool(int(config.get(section, "lasercutter")))
        except Exception:
            pass

        try:
            OCV.laseradaptive = bool(int(config.get(section, "laseradaptive")))
        except Exception:
            pass

        try:
            OCV.doublesizeicon = bool(int(config.get(section, "doublesizeicon")))
        except Exception:
            pass

        try:
            OCV.acceleration_x = float(config.get(section, "acceleration_x"))
        except Exception:
            pass

        try:
            OCV.acceleration_y = float(config.get(section, "acceleration_y"))
        except Exception:
            pass

        try:
            OCV.acceleration_z = float(config.get(section, "acceleration_z"))
        except Exception:
            pass

        try:
            OCV.feedmax_x = float(config.get(section, "feedmax_x"))
        except Exception:
            pass

        try:
            OCV.feedmax_y = float(config.get(section, "feedmax_y"))
        except Exception:
            pass

        try:
            OCV.feedmax_z = float(config.get(section, "feedmax_z"))
        except Exception:
            pass

        try:
            OCV.travel_x = float(config.get(section, "travel_x"))
        except Exception:
            pass

        try:
            OCV.travel_y = float(config.get(section, "travel_y"))
        except Exception:
            pass

        try:
            OCV.travel_z = float(config.get(section, "travel_z"))
        except Exception:
            pass

        try:
            OCV.accuracy = float(config.get(section, "accuracy"))
        except Exception:
            pass

        try:
            OCV.digits = int(config.get(section, "round"))
        except Exception:
            pass

        try:
            OCV.drozeropad = int(config.get(section, "drozeropad"))
        except Exception:
            pass

        try:
            OCV.startup = config.get(section, "startup")
        except Exception:
            pass

        try:
            OCV.header = config.get(section, "header")
        except Exception:
            pass

        try:
            OCV.footer = config.get(section, "footer")
        except Exception:
            pass

        if OCV.inch:
            OCV.acceleration_x /= 25.4
            OCV.acceleration_y /= 25.4
            OCV.acceleration_z /= 25.4
            OCV.feedmax_x /= 25.4
            OCV.feedmax_y /= 25.4
            OCV.feedmax_z /= 25.4
            OCV.travel_x /= 25.4
            OCV.travel_y /= 25.4
            OCV.travel_z /= 25.4

        section = "Error"
        if OCV.drillPolicy == 1:
            ERROR_HANDLING["G98"] = 1
            ERROR_HANDLING["G99"] = 1

        for cmd, value in config.items(section):
            try:
                ERROR_HANDLING[cmd.upper()] = int(value)
            except Exception:
                pass

    @staticmethod
    def saveConfig(config):
        pass

    def initPath(self, x=None, y=None, z=None):
        if x is None:
            self.x = self.xval = OCV.CD['wx'] or 0
        else:
            self.x = self.xval = x

        if y is None:
            self.y = self.yval = OCV.CD['wy'] or 0
        else:
            self.y = self.yval = y

        if z is None:
            self.z = self.zval = OCV.CD['wz'] or 0
        else:
            self.z = self.zval = z

        self.ival = self.jval = self.kval = 0.0
        self.uval = self.vval = self.wval = 0.0
        self.dx = self.dy = self.dz = 0.0
        self.di = self.dj = self.dk = 0.0
        self.rval = 0.0
        self.pval = 0.0
        self.qval = 0.0
        self.unit = 1.0
        self.mval = 0
        self.lval = 1
        self.tool = 0
        self._lastTool = None

        self.absolute = True  # G90/G91     absolute/relative motion
        self.arcabsolute = False  # G90.1/G91.1 absolute/relative arc
        self.retractz = True  # G98/G99     retract to Z or R
        self.gcode = None
        self.plane = XY
        self.feed = 0  # Actual gcode feed rate (not to confuse with cutfeed
        self.totalLength = 0.0
        self.totalTime = 0.0

    def resetEnableMargins(self):
        # Selected blocks margin
        OCV.CD["xmin"] = OCV.CD["ymin"] = OCV.CD["zmin"] = 1000000.0
        OCV.CD["xmax"] = OCV.CD["ymax"] = OCV.CD["zmax"] = -1000000.0

    def resetAllMargins(self):
        self.resetEnableMargins()
        # All blocks margin
        OCV.CD["axmin"] = OCV.CD["aymin"] = OCV.CD["azmin"] = 1000000.0
        OCV.CD["axmax"] = OCV.CD["aymax"] = OCV.CD["azmax"] = -1000000.0

    @staticmethod
    def isMarginValid():
        return OCV.CD["xmin"] <= OCV.CD["xmax"] and \
            OCV.CD["ymin"] <= OCV.CD["ymax"] and \
            OCV.CD["zmin"] <= OCV.CD["zmax"]

    @staticmethod
    def isAllMarginValid():
        return OCV.CD["axmin"] <= OCV.CD["axmax"] and \
            OCV.CD["aymin"] <= OCV.CD["aymax"] and \
            OCV.CD["azmin"] <= OCV.CD["azmax"]

    @staticmethod
    def fmt(c, val, d=None):
        """Number formating"""
        if d is None:
            digits = OCV.digits
        # Don't know why, but in some cases floats are not truncated
        # by format string unless rounded
        # I guess it's vital idea to round them rather than truncate anyway!
        r_val = round(val, digits)
        # return ("{0}{2:0.{1}f}".format(c,d,v)).rstrip("0").rstrip(".")
        return "{0}{2:0.{1}f}".format(c, digits, r_val)

    @staticmethod
    def gcode(g, pairs):
        s = "G{0}".format(g)
        for c, v in pairs:
            s += " {0}{1:0.{2}f}".format(c, round(v, OCV.digits), OCV.digits)
        return s

    @staticmethod
    def _gcode(g, **args):
        s = "G{0}".format(g)
        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)
        return s

    @staticmethod
    def _goto(g, x=None, y=None, z=None, **args):
        s = "G{0}".format(g)
        if x is not None:
            s += ' ' + CNC.fmt('X', x)

        if y is not None:
            s += ' ' + CNC.fmt('Y', y)

        if z is not None:
            s += ' ' + CNC.fmt('Z', z)

        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)
        return s

    @staticmethod
    def grapid(x=None, y=None, z=None, **args):
        return CNC._goto(0, x, y, z, **args)

    @staticmethod
    def gline(x=None, y=None, z=None, **args):
        return CNC._goto(1, x, y, z, **args)

    @staticmethod
    def glinev(g, v, feed=None):
        pairs = zip("XYZ", v)
        if feed is not None:
            pairs.append(("F", feed))
        return CNC.gcode(g, pairs)

    @staticmethod
    def garcv(g, v, ijk):
        return CNC.gcode(g, zip("XYZ", v) + zip("IJ", ijk[:2]))

    @staticmethod
    def garc(g, x=None, y=None, z=None, i=None, j=None, k=None, **args):
        s = "G{0}".format(g)
        if x is not None:
            s += ' ' + CNC.fmt('X', x)

        if y is not None:
            s += ' ' + CNC.fmt('Y', y)

        if z is not None:
            s += ' ' + CNC.fmt('Z', z)

        if i is not None:
            s += ' ' + CNC.fmt('I', i)

        if j is not None:
            s += ' ' + CNC.fmt('J', j)

        if k is not None:
            s += ' ' + CNC.fmt('K', k)

        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)

        return s

    @staticmethod
    def zenter(z, d=None):
        """Enter to material or start the laser"""
        if OCV.lasercutter:
            if OCV.laseradaptive:
                return "M4"
            else:
                return "M3"
        else:
            return "G1 {0} {1}".format(
                CNC.fmt("Z", z, d),
                CNC.fmt("F", OCV.CD["cutfeedz"]))

    @staticmethod
    def zexit(z, d=None):
        if OCV.lasercutter:
            return "M5"
        else:
            return "G0 {0}".format(CNC.fmt("Z", z, d))

    @staticmethod
    def zsafe():
        """
        gcode to go to z-safe
        Exit from material or stop the laser
        """
        return CNC.zexit(OCV.CD["safe"])

    @staticmethod
    def parseLine(line):
        """@return
            lines breaking a line containing list of commands,
            None if empty or comment
        """
        # skip empty lines
        if len(line) == 0 or line[0] in ("%", "(", "#", ";"):
            return None

        # remove comments
        line = PARENPAT.sub("", line)
        line = SEMIPAT.sub("", line)

        # process command
        # strip all spaces
        line = line.replace(" ", "")

        # Insert space before each command
        line = CMDPAT.sub(r" \1", line).lstrip()
        return line.split()

    @staticmethod
    def compileLine(line, space=False):
        """
         @return line,comment
        line s breaking a line containing list of commands,
        None,"" if empty or comment
        else compiled expressions,""
        """
        line = line.strip()

        if not line:
            return None

        if line[0] == "$":
            return line

        # to accept #nnn variables as _nnn internally
        line = line.replace('#', '_')
        OCV.comment = ""

        # execute literally the line after the first character
        if line[0] == '%':
            # special command
            pat = AUXPAT.match(line.strip())

            if pat:
                cmd = pat.group(1)
                args = pat.group(2)
            else:
                cmd = None
                args = None

            if cmd == "%wait":
                return (WAIT,)
            elif cmd == "%msg":

                if not args:
                    args = None

                return (MSG, args)
            elif cmd == "%update":
                return (UPDATE, args)
            elif line.startswith("%if running") and not OCV.CD["running"]:
                # ignore if running lines when not running
                return None
            else:
                try:
                    return compile(line[1:], "", "exec")
                except Exception:
                    # FIXME show the error!!!!
                    return None

        # most probably an assignment like  #nnn = expr
        if line[0] == '_':
            try:
                return compile(line, "", "exec")
            except Exception:
                # FIXME show the error!!!!
                return None

        # commented line
        if line[0] == ';':
            OCV.comment = line[1:].strip()
            return None

        out = []  # output list of commands
        braket = 0  # bracket count []
        paren = 0  # parenthesis count ()
        expr = ""  # expression string
        cmd = ""  # cmd string
        inComment = False  # inside inComment
        for i, ch in enumerate(line):
            if ch == '(':
                # comment start?
                paren += 1
                inComment = (braket == 0)

                if not inComment:
                    expr += ch

            elif ch == ')':
                # comment end?
                paren -= 1
                if not inComment:
                    expr += ch

                if paren == 0 and inComment:
                    inComment = False
            elif ch == '[':
                # expression start?
                if not inComment:

                    if OCV.stdexpr:
                        ch = '('

                    braket += 1

                    if braket == 1:
                        if cmd:
                            out.append(cmd)
                            cmd = ""
                    else:
                        expr += ch
                else:
                    OCV.comment += ch

            elif ch == ']':
                # expression end?
                if not inComment:

                    if OCV.stdexpr:
                        ch = ')'
                    braket -= 1

                    if braket == 0:
                        try:
                            out.append(compile(expr, "", "eval"))
                        except Exception:
                            # FIXME show the error!!!!
                            pass
                        # out.append("<<"+expr+">>")
                        expr = ""
                    else:
                        expr += ch

                else:
                    OCV.comment += ch

            elif ch == '=':
                # check for assignments (FIXME very bad)
                if not out and braket == 0 and paren == 0:
                    for i in " ()-+*/^$":
                        if i in cmd:
                            cmd += ch
                            break
                    else:
                        try:
                            return compile(line, "", "exec")
                        except Exception:
                            # FIXME show the error!!!!
                            return None
            elif ch == ';':
                # Skip everything after the semicolon on normal lines
                if not inComment and paren == 0 and braket == 0:
                    OCV.comment += line[i+1:]
                    break
                else:
                    expr += ch

            elif braket > 0:
                expr += ch

            elif not inComment:
                if ch == ' ':
                    if space:
                        cmd += ch
                else:
                    cmd += ch

            elif inComment:
                OCV.comment += ch

        if cmd:
            out.append(cmd)

        # return output commands
        if len(out) == 0:
            return None
        if len(out) > 1:
            return out
        return out[0]

    @staticmethod
    def breakLine(line):
        """Break line into commands"""
        if line is None:
            return None
        # Insert space before each command
        line = CMDPAT.sub(r" \1", line).lstrip()
        return line.split()

    def motionStart(self, cmds):
        """Create path for one g command"""
        # print "\n<<<",cmds
        self.mval = 0  # reset m command
        for cmd in cmds:
            c = cmd[0].upper()
            try:
                value = float(cmd[1:])
            except Exception:
                value = 0

            if c == "X":
                self.xval = value*self.unit
                if not self.absolute:
                    self.xval += self.x
                self.dx = self.xval - self.x

            elif c == "Y":
                self.yval = value*self.unit
                if not self.absolute:
                    self.yval += self.y
                self.dy = self.yval - self.y

            elif c == "Z":
                self.zval = value*self.unit
                if not self.absolute:
                    self.zval += self.z
                self.dz = self.zval - self.z

            elif c == "A":
                self.aval = value*self.unit

            elif c == "F":
                self.feed = value*self.unit

            elif c == "G":
                gcode = int(value)
                decimal = int(round((value - gcode)*10))

                # Execute immediately
                if gcode in (4, 10, 53):
                    pass  # do nothing but don't record to motion
                elif gcode == 17:
                    self.plane = XY

                elif gcode == 18:
                    self.plane = XZ

                elif gcode == 19:
                    self.plane = YZ

                elif gcode == 20:  # Switch to inches
                    if OCV.inch:
                        self.unit = 1.0
                    else:
                        self.unit = 25.4

                elif gcode == 21:  # Switch to mm
                    if OCV.inch:
                        self.unit = 1.0/25.4
                    else:
                        self.unit = 1.0

                elif gcode == 80:
                    # turn off canned cycles
                    self.gcode = None
                    self.dz = 0
                    self.zval = self.z

                elif gcode == 90:
                    if decimal == 0:
                        self.absolute = True
                    elif decimal == 1:
                        self.arcabsolute = True

                elif gcode == 91:
                    if decimal == 0:
                        self.absolute = False
                    elif decimal == 1:
                        self.arcabsolute = False

                elif gcode in (93, 94, 95):
                    OCV.CD["feedmode"] = gcode

                elif gcode == 98:
                    self.retractz = True

                elif gcode == 99:
                    self.retractz = False

                else:
                    self.gcode = gcode

            elif c == "I":
                self.ival = value*self.unit
                if self.arcabsolute:
                    self.ival -= self.x

            elif c == "J":
                self.jval = value*self.unit
                if self.arcabsolute:
                    self.jval -= self.y

            elif c == "K":
                self.kval = value*self.unit
                if self.arcabsolute:
                    self.kval -= self.z

            elif c == "L":
                self.lval = int(value)

            elif c == "M":
                self.mval = int(value)

            elif c == "N":
                pass

            elif c == "P":
                self.pval = value

            elif c == "Q":
                self.qval = value*self.unit

            elif c == "R":
                self.rval = value*self.unit

            elif c == "T":
                self.tool = int(value)

            elif c == "U":
                self.uval = value*self.unit

            elif c == "V":
                self.vval = value*self.unit

            elif c == "W":
                self.wval = value*self.unit

    def motionCenter(self):
        """Return center x,y,z,r for arc motions 2,3 and set self.rval"""

        if self.rval > 0.0:
            if self.plane == XY:
                x = self.x
                y = self.y
                xv = self.xval
                yv = self.yval
            elif self.plane == XZ:
                x = self.x
                y = self.z
                xv = self.xval
                yv = self.zval
            else:
                x = self.y
                y = self.z
                xv = self.yval
                yv = self.zval

            ABx = xv-x
            ABy = yv-y
            Cx = 0.5*(x+xv)
            Cy = 0.5*(y+yv)
            AB = math.sqrt(ABx**2 + ABy**2)

            try:
                OC = math.sqrt(self.rval**2 - AB**2/4.0)
            except Exception:
                OC = 0.0

            if self.gcode == 2:
                OC = -OC  # CW

            if AB != 0.0:
                return Cx-OC*ABy/AB, Cy + OC*ABx/AB
            else:
                # Error!!!
                return x, y
        else:
            # Center
            xc = self.x + self.ival
            yc = self.y + self.jval
            zc = self.z + self.kval
            self.rval = math.sqrt(self.ival**2 + self.jval**2 + self.kval**2)

            if self.plane == XY:
                return xc, yc
            elif self.plane == XZ:
                return xc, zc
            else:
                return yc, zc

        # Error checking
        """
        err = abs(self.rval - math.sqrt((self.xval-xc)**2 + (self.yval-yc)**2 + (self.zval-zc)**2))
        if err/self.rval>0.001:
            print "Error invalid arc", self.xval, self.yval, self.zval, err
        return xc,yc,zc
        """

    def motionPath(self):
        """Create path for one g command"""
        xyz = []

        # Execute g-code
        if self.gcode in (0, 1):  # fast move or line
            if self.xval-self.x != 0.0 or \
               self.yval-self.y != 0.0 or \
               self.zval-self.z != 0.0:
                xyz.append((self.x, self.y, self.z))
                xyz.append((self.xval, self.yval, self.zval))

        elif self.gcode in (2, 3):    # CW=2,CCW=3 circle
            xyz.append((self.x, self.y, self.z))
            uc, vc = self.motionCenter()

            gcode = self.gcode
            if self.plane == XY:
                u0 = self.x
                v0 = self.y
                w0 = self.z
                u1 = self.xval
                v1 = self.yval
                w1 = self.zval
            elif self.plane == XZ:
                u0 = self.x
                v0 = self.z
                w0 = self.y
                u1 = self.xval
                v1 = self.zval
                w1 = self.yval
                gcode = 5-gcode    # flip 2-3 when XZ plane is used
            else:
                u0 = self.y
                v0 = self.z
                w0 = self.x
                u1 = self.yval
                v1 = self.zval
                w1 = self.xval
            phi0 = math.atan2(v0-vc, u0-uc)
            phi1 = math.atan2(v1-vc, u1-uc)
            try:
                sagitta = 1.0-OCV.accuracy/self.rval
            except ZeroDivisionError:
                sagitta = 0.0
            if sagitta > 0.0:
                df = 2.0*math.acos(sagitta)
                df = min(df, math.pi/4.0)
            else:
                df = math.pi/4.0

            if gcode == 2:
                if phi1 >= phi0-1e-10:
                    phi1 -= 2.0 * math.pi
                ws = (w1-w0)/(phi1-phi0)
                phi = phi0 - df

                while phi > phi1:
                    u = uc + self.rval*math.cos(phi)
                    v = vc + self.rval*math.sin(phi)
                    w = w0 + (phi-phi0)*ws
                    phi -= df
                    if self.plane == XY:
                        xyz.append((u, v, w))
                    elif self.plane == XZ:
                        xyz.append((u, w, v))
                    else:
                        xyz.append((w, u, v))
            else:
                if phi1 <= phi0+1e-10:
                    phi1 += 2.0 * math.pi

                ws = (w1-w0)/(phi1-phi0)
                phi = phi0 + df

                while phi < phi1:
                    u = uc + self.rval*math.cos(phi)
                    v = vc + self.rval*math.sin(phi)
                    w = w0 + (phi-phi0)*ws
                    phi += df

                    if self.plane == XY:
                        xyz.append((u, v, w))
                    elif self.plane == XZ:
                        xyz.append((u, w, v))
                    else:
                        xyz.append((w, u, v))

            xyz.append((self.xval, self.yval, self.zval))

        elif self.gcode == 4:  # Dwell
            self.totalTime = self.pval

        elif self.gcode in (81, 82, 83, 85, 86, 89):  # Canned cycles
            """
            print "x=",self.x
            print "y=",self.y
            print "z=",self.z
            print "dx=",self.dx
            print "dy=",self.dy
            print "dz=",self.dz
            print "abs=",self.absolute,"retract=",self.retractz
            """

            # FIXME Assuming only on plane XY
            if self.absolute:
                # FIXME is it correct?
                self.lval = 1

                if self.retractz:
                    clearz = max(self.rval, self.z)
                else:
                    clearz = self.rval
                drill = self.zval
            else:
                clearz = self.z + self.rval
                drill = clearz + self.dz
            """
            print "clearz=",clearz
            print "drill=",drill
            """
            x, y, z = self.x, self.y, self.z
            xyz.append((x, y, z))

            if z != clearz:
                z = clearz
                xyz.append((x, y, z))

            for l in range(self.lval):
                # Rapid move parallel to XY
                x += self.dx
                y += self.dy
                xyz.append((x, y, z))

                # Rapid move parallel to clearz
                if self.z > clearz:
                    xyz.append((x, y, clearz))

                # Drill to z
                xyz.append((x, y, drill))

                # Move to original position
                z = clearz
                xyz.append((x, y, z))    # ???

#        for a in xyz: print a

        return xyz

    def motionEnd(self):
        """move to end position"""
        """
        print "x=",self.x
        print "y=",self.y
        print "z=",self.z
        print "dx=",self.dx
        print "dy=",self.dy
        print "dz=",self.dz
        print "abs=",self.absolute,"retract=",self.retractz
        """

        if self.gcode in (0, 1, 2, 3):
            self.x = self.xval
            self.y = self.yval
            self.z = self.zval
            self.dx = 0
            self.dy = 0
            self.dz = 0

            if self.gcode >= 2:  # reset at the end
                self.rval = self.ival = self.jval = self.kval = 0.0

        elif self.gcode in (28, 30, 92):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0
            self.dx = 0
            self.dy = 0
            self.dz = 0

        # FIXME L is not taken into account for repetitions!!!
        elif self.gcode in (81, 82, 83):
            # FIXME Assuming only on plane XY
            if self.absolute:
                self.lval = 1
                if self.retractz:
                    retract = max(self.rval, self.z)
                else:
                    retract = self.rval
                drill = self.zval
            else:
                retract = self.z + self.rval
                drill = retract + self.dz

            self.x += self.dx*self.lval
            self.y += self.dy*self.lval
            self.z = retract

            self.xval = self.x
            self.yval = self.y
            self.dx = 0
            self.dy = 0
            self.dz = drill - retract

    def pathLength(self, block, xyz):
        """Calculate Path Length"""
        # FIXME: Doesn't work correctly for G83 (peck drilling)
        # For XY plan
        p = xyz[0]
        length = 0.0
        for i in xyz:
            length += math.sqrt(
                (i[0]-p[0])**2 + (i[1]-p[1])**2 + (i[2]-p[2])**2)
            p = i

        if self.gcode == 0:
            # FIXME calculate the correct time with the feed direction
            # and acceleration
            block.time += length / OCV.feedmax_x
            self.totalTime += length / OCV.feedmax_x
            block.rapid += length
        else:
            try:
                if OCV.CD["feedmode"] == 94:
                    # Normal mode
                    t = length / self.feed
                elif OCV.CD["feedmode"] == 93:
                    # Inverse mode
                    t = length * self.feed

                block.time += t
                self.totalTime += t
            except Exception:
                pass

            block.length += length

        self.totalLength += length

    def pathMargins(self, block):
        if block.enable:
            OCV.CD["xmin"] = min(OCV.CD["xmin"], block.xmin)
            OCV.CD["ymin"] = min(OCV.CD["ymin"], block.ymin)
            OCV.CD["zmin"] = min(OCV.CD["zmin"], block.zmin)
            OCV.CD["xmax"] = max(OCV.CD["xmax"], block.xmax)
            OCV.CD["ymax"] = max(OCV.CD["ymax"], block.ymax)
            OCV.CD["zmax"] = max(OCV.CD["zmax"], block.zmax)

        OCV.CD["axmin"] = min(OCV.CD["axmin"], block.xmin)
        OCV.CD["aymin"] = min(OCV.CD["aymin"], block.ymin)
        OCV.CD["azmin"] = min(OCV.CD["azmin"], block.zmin)
        OCV.CD["axmax"] = max(OCV.CD["axmax"], block.xmax)
        OCV.CD["aymax"] = max(OCV.CD["aymax"], block.ymax)
        OCV.CD["azmax"] = max(OCV.CD["azmax"], block.zmax)

    @staticmethod
    def compile(program):
        """
        Instead of the current code, override with the custom user lines
        # @param program a list of lines to execute
        # @return the new list of lines
        """

        lines = []

        for j, line in enumerate(program):
            newcmd = []
            cmds = CNC.compileLine(line)

            if cmds is None:
                continue

            if isinstance(cmds, str):
                cmds = CNC.breakLine(cmds)
            else:
                # either CodeType or tuple, list[] append at it as is
                lines.append(cmds)
                continue

            for cmd in cmds:
                c = cmd[0]
                try:
                    value = float(cmd[1:])
                except Exception:
                    value = 0.0

                if c.upper() in ("F", "X", "Y", "Z", "I", "J", "K", "R", "P"):
                    cmd = CNC.fmt(c, value)
                else:
                    opt = ERROR_HANDLING.get(cmd.upper(), 0)

                    if opt == SKIP:
                        cmd = None

                if cmd is not None:
                    newcmd.append(cmd)
            lines.append("".join(newcmd))
        return lines

    def toolChange(self, tool=None):
        """code to change manually tool"""
        if tool is not None:
            # Force a change
            self.tool = tool
            self._lastTool = None

        # check if it is the same tool
        if self.tool is None or self.tool == self._lastTool:
            return []

        # create the necessary code
        lines = []
        # FIXME:
        # move to ./controllers/_GenericController.py
        lines.append("$G")  # remember state and populate variables,

        lines.append("M5")  # stop spindle
        lines.append("%wait")
        lines.append("%_x,_y,_z = wx,wy,wz")    # remember position
        lines.append("G53 G0 z[toolchangez]")
        lines.append("G53 G0 x[toolchangex] y[toolchangey]")
        lines.append("%wait")

        if OCV.comment:
            lines.append(
                "%%msg Tool change T{0:2d} (1)".format(
                    self.tool,
                    OCV.comment)
                )
        else:
            lines.append(
                "%%msg Tool change T{1:2d}".format(self.tool))

        lines.append("M0")  # feed hold

        if OCV.toolPolicy < 4:
            lines.append("G53 G0 x[toolprobex] y[toolprobey]")
            lines.append("G53 G0 z[toolprobez]")

            # fixed WCS
            if OCV.CD["fastprbfeed"]:
                prb_reverse = {"2": "4", "3": "5", "4": "2", "5": "3"}
                OCV.CD["prbcmdreverse"] = (
                    OCV.CD["prbcmd"][:-1] +
                    prb_reverse[OCV.CD["prbcmd"][-1]])

                currentFeedrate = OCV.CD["fastprbfeed"]

                while currentFeedrate > OCV.CD["prbfeed"]:
                    lines.append("%wait")
                    lines.append(
                        "G91 [prbcmd] {0} z[toolprobez-mz-tooldistance]".format(
                            CNC.fmt('f', currentFeedrate)))
                    lines.append("%wait")
                    lines.append("[prbcmdreverse] {0} z[toolprobez-mz]".format(
                        CNC.fmt('f', currentFeedrate)))
                    currentFeedrate /= 10
            lines.append("%wait")
            lines.append(
                "G91 [prbcmd] F[prbfeed] Z[toolprobez-mz-tooldistance]")

            if OCV.toolPolicy == 2:
                # Adjust the current WCS to fit to the tool
                # FIXME could be done dynamically in the code
                p = OCV.WCS.index(OCV.CD["WCS"])+1
                lines.append("G10L20P{0:d} Z[toolheight]".format(p))
                lines.append("%wait")

            elif OCV.toolPolicy == 3:
                # Modify the tool length, update the TLO
                lines.append("G4 P1")    # wait a sec to get the probe info
                lines.append("%wait")
                lines.append("%global TLO; TLO=prbz-toolmz")
                lines.append("G43.1 Z[TLO]")
                lines.append("%update TLO")

            lines.append("G53 G0 z[toolchangez]")
            lines.append("G53 G0 x[toolchangex] y[toolchangey]")

        if OCV.toolWaitAfterProbe:
            lines.append("%wait")
            lines.append("%msg Restart spindle")
            lines.append("M0")    # feed hold

        # restore state
        lines.append("G90")  # restore mode
        lines.append("G0 x[_x] y[_y]")     # x,y position
        lines.append("G0 z[_z]")           # z position
        lines.append("F[feed] [spindle]")  # feed and spindle
        lines.append("G4 P5")              # wait 5s for spindle to speed up

        # remember present tool
        self._lastTool = self.tool
        return lines

    # --------------------------------------------------------------
    # example:
    # code to expand G83 code - peck drilling cycle
    # format:    (G98 / G99 opt.) G83 X~ Y~ Z~ A~ R~ L~ Q~
    # example:    N150 G98 G83 Z-1.202 R18. Q10. F50.
    #            ...
    #            G80
    # Notes: G98, G99, Z, R, Q, F are unordered parameters
    # --------------------------------------------------------------
    def macroGroupG8X(self):
        """code to expand G80-G89 macro code - canned cycles"""
        lines = []

        """
        print "x=",self.x
        print "y=",self.y
        print "z=",self.z
        print "dx=",self.dx
        print "dy=",self.dy
        print "dz=",self.dz
        print "abs=",self.absolute,"retract=",self.retractz
        """
        # FIXME Assuming only on plane XY
        if self.absolute:
            # FIXME is it correct?
            self.lval = 1

            if self.retractz:
                clearz = max(self.rval, self.z)
            else:
                clearz = self.rval

            drill = self.zval
            retract = self.rval
        else:
            clearz = self.z + self.rval
            retract = clearz
            drill = clearz + self.dz
        """
        print "clearz=",clearz
        print "drill=",drill
        """

        if self.gcode == 83:    # peck drilling
            peck = self.qval
        else:
            peck = 100000.0    # a large value

        x, y, z = self.x, self.y, self.z
        if z < clearz:
            z = clearz
            lines.append(CNC.grapid(z=z/self.unit))

        for l in range(self.lval):
            # Rapid move parallel to XY
            x += self.dx
            y += self.dy
            lines.append(CNC.grapid(x/self.unit, y/self.unit))

            # Rapid move parallel to retract
            zstep = max(drill, retract - peck)
            while z > drill:
                if z != retract:
                    z = retract
                    lines.append(CNC.grapid(z=z/self.unit))

                z = max(drill, zstep)
                zstep -= peck

                # Drill to z
                lines.append(CNC.gline(z=z/self.unit, f=self.feed/self.unit))

            # 82=dwell, 86=boring-stop, 89=boring-dwell
            if self.gcode in (82, 86, 89):
                lines.append(CNC._gcode(4, p=self.pval))

                if self.gcode == 86:
                    lines.append("M5")    # stop spindle???

            # Move to original position
            if self.gcode in (85, 89):     # boring cycle
                z = retract
                lines.append(CNC.gline(z=z/self.unit, f=self.feed/self.unit))

            z = clearz
            lines.append(CNC.grapid(z=z/self.unit))

            if self.gcode == 86:
                lines.append("M3")    # restart spindle???
        """
        print "-"*50
        for a in lines: print a
        print "-"*50
        """
        return lines


class Block(list):
    """
    Block of g-code commands. A gcode file is represented as a list of blocks
     - Commands are grouped as (non motion commands Mxxx)
     - Basic shape from the first rapid move command to the last rapid z raise
       above the working surface
    -
     Inherits from list and contains:
        - a list list of gcode lines
        - (imported shape)
    """

    def __init__(self, name=None):
        # Copy constructor
        if isinstance(name, Block):
            self.copy(name)
            return
        self._name = name
        self.enable = True      # Enabled/Visible in drawing
        self.expand = False     # Expand in editor
        self.color = None       # Custom color for path
        self._path = []         # canvas drawing paths
        # (entry point first non rapid motion)
        self.sx = self.sy = self.sz = 0    # start  coordinates

        self.ex = self.ey = self.ez = 0    # ending coordinates
        self.resetPath()

    def copy(self, src):
        self._name = src._name
        self.enable = src.enable
        self.expand = src.expand
        self.color = src.color
        self[:] = src[:]
        self._path = []
        self.sx = src.sx
        self.sy = src.sy
        self.sz = src.sz
        self.ex = src.ex
        self.ey = src.ey
        self.ez = src.ez

    def name(self):
        return self._name is None and "block" or self._name

    def nameNop(self):
        """@return name without the operation"""
        name = self.name()
        pat = OPPAT.match(name)
        if pat is None:
            return name
        else:
            return pat.group(1).strip()

    def operationTest(self, op, name=None):
        """Tests if block contains operation type"""
        if name is None:
            name = self.name()

        pat = OPPAT.match(name)
        if pat is not None:
            ops = pat.group(2)
            ops = re.split('\W+', ops)

            if op in ops:
                return True
        return False

    def operationGet(self, op, name=None):
        """Get block operation value"""
        if name is None:
            name = self.name()

        pat = OPPAT.match(name)
        if pat is not None:
            ops = pat.group(2)
            ops = re.split(',', ops)
            for opp in ops:
                t = re.split(':', opp)

                if t[0] == op:
                    return t[1]
        return None

    def operationSide(self, name=None):
        """
        Tests if block contains operation on
        inside of the part (-1), outside (1), or can't decide (0)
        """
        # if self.operationTest('pocket', name): return -1

        if self.operationTest('in', name) and not self.operationTest('out', name):
            return -1

        if self.operationTest('out', name) and not self.operationTest('in', name):
            return 1

        return 0

    @staticmethod
    def operationName(name, operation, remove=None):
        """@return the new name with an operation (static)"""
        pat = OPPAT.match(name)
        if pat is None:
            return "{0} [{1}]".format(name, operation)
        else:
            name = pat.group(1).strip()
            ops = pat.group(2).split(',')
            if ":" in operation:
                oid, opt = operation.split(":")
            else:
                oid = operation
                opt = None

            found = False
            for i, o in enumerate(ops):
                if ":" in o:
                    o, c = o.split(":")
                    try:
                        c = int(c)
                    except Exception:
                        c = 1
                else:
                    c = 1

                if remove and o in remove:
                    ops[i] = ""

                if not found and o == oid:
                    if opt is not None or c is None:
                        ops[i] = operation
                    else:
                        ops[i] = "{0}:{1}".format(oid, c+1)
                    found = True

            # remove all empty
            ops = filter(lambda x: x != "", ops)

            if not found:
                ops.append(operation)

            return "{0} [{1}]".format(name, ','.join(ops))

    def addOperation(self, operation, remove=None):
        """Add a new operation to the block's name"""
        self._name = Block.operationName(self.name(), operation, remove)

    def header(self):
        e = self.expand and Unicode.BLACK_DOWN_POINTING_TRIANGLE \
            or Unicode.BLACK_RIGHT_POINTING_TRIANGLE

        v = self.enable and Unicode.BALLOT_BOX_WITH_X \
            or Unicode.BALLOT_BOX

        try:
            # return "%s %s %s - [%d]"%(e, v, self.name(), len(self))
            return u"{0} {1} {2} - [{3}]".format(
                e, v, self.name(), len(self))
        except UnicodeDecodeError:
            return u"{0} {1} {2} - [{3}]".format(
                e, v, self.name().decode("ascii", "replace"), len(self))
        except UnicodeEncodeError:
            print(e, v, self.name(), len(self))

    def write_header(self):
        header = ''
        header += "(Block-name: {0})\n".format(self.name())
        header += "(Block-expand: {0:d})\n".format(int(self.expand))
        header += "(Block-enable: {0:d})\n".format(int(self.enable))
        if self.color:
            header += "(Block-color: {0})\n".format(self.color)
        return header

    def write(self, f):
        f.write(self.write_header())
        for line in self:

            if self.enable:
                f.write("{0}\n".format(line))
            else:
                f.write("(Block-X: {0})\n".format(
                    line.replace('(', '[').replace(')', ']')))

    def dump(self):
        """Return a dump object for pickler"""
        return self.name(), self.enable, self.expand, self.color, self

    @staticmethod
    def load(obj):
        """Create a block from a dump object from unpickler"""
        name, enable, expand, color, code = obj
        block = Block(name)
        block.enable = enable
        block.expand = expand
        block.color = color
        block.extend(code)
        return block

    def append(self, line):
        if line.startswith("(Block-"):
            pat = BLOCKPAT.match(line)
            if pat:
                name, value = pat.groups()
                value = value.strip()

                if name == "name":
                    self._name = value
                    return
                elif name == "expand":
                    self.expand = bool(int(value))
                    return
                elif name == "enable":
                    self.enable = bool(int(value))
                    return
                elif name == "tab":
                    # Handled elsewhere
                    return
                elif name == "color":
                    self.color = value
                    return
                elif name == "X":  # uncomment
                    list.append(
                        self,
                        value.replace('[', '(').replace(']', ')'))
                    return

        if self._name is None and ("id:" in line) and ("End" not in line):
            pat = IDPAT.match(line)

            if pat:
                self._name = pat.group(1)

        list.append(self, line)

    def resetPath(self):
        del self._path[:]
        self.xmin = self.ymin = self.zmin = 1000000.0
        self.xmax = self.ymax = self.zmax = -1000000.0
        self.length = 0.0    # cut length
        self.rapid = 0.0     # rapid length
        self.time = 0.0

    def hasPath(self):
        return bool(self._path)

    def addPath(self, p):
        self._path.append(p)

    def path(self, item):
        try:
            return self._path[item]
        except Exception:
            return None

    def startPath(self, x, y, z):
        self.sx = x
        self.sy = y
        self.sz = z

    def endPath(self, x, y, z):
        self.ex = x
        self.ey = y
        self.ez = z

    def pathMargins(self, xyz):
        self.xmin = min(self.xmin, min([i[0] for i in xyz]))
        self.ymin = min(self.ymin, min([i[1] for i in xyz]))
        self.zmin = min(self.zmin, min([i[2] for i in xyz]))
        self.xmax = max(self.xmax, max([i[0] for i in xyz]))
        self.ymax = max(self.ymax, max([i[1] for i in xyz]))
        self.zmax = max(self.zmax, max([i[2] for i in xyz]))


class GCode(object):
    """Gcode file"""
    LOOP_MERGE = False

    def __init__(self):
        self.cnc = CNC()
        self.header = ""
        self.footer = ""
        self.undoredo = undo.UndoRedo()
        self.probe = Probe()
        self.orient = Orient()
        self.vars = {}  # local variables
        self.init()

    def init(self):
        self.filename = ""
        self.blocks = []  # list of blocks
        self.gcodelines = ["",]  # Add a starting 0 pos to better align index
        self.vars.clear()
        self.undoredo.reset()
        # self.probe.init()

        self._lastModified = 0
        self._modified = False

    def calculateEnableMargins(self):
        """Recalculate enabled path margins"""
        self.cnc.resetEnableMargins()
        for block in self.blocks:
            if block.enable:
                OCV.CD["xmin"] = min(OCV.CD["xmin"], block.xmin)
                OCV.CD["ymin"] = min(OCV.CD["ymin"], block.ymin)
                OCV.CD["zmin"] = min(OCV.CD["zmin"], block.zmin)
                OCV.CD["xmax"] = max(OCV.CD["xmax"], block.xmax)
                OCV.CD["ymax"] = max(OCV.CD["ymax"], block.ymax)
                OCV.CD["zmax"] = max(OCV.CD["zmax"], block.zmax)

    def isModified(self):
        return self._modified

    def resetModified(self):
        self._modified = False

    def __getitem__(self, item):
        return self.blocks[item]

    def __setitem__(self, item, value):
        self.blocks[item] = value

    def evaluate(self, line, app=None):
        """Evaluate code expressions if any and return line"""
        if isinstance(line, int):
            return None

        elif isinstance(line, list):
            for i, expr in enumerate(line):

                if isinstance(expr, types.CodeType):
                    result = eval(expr, OCV.CD, self.vars)

                    if isinstance(result, float):
                        line[i] = str(round(result, OCV.digits))
                    else:
                        line[i] = str(result)
            return "".join(line)

        elif isinstance(line, types.CodeType):
            # import traceback
            # traceback.print_stack()
            v = self.vars
            v['os'] = os
            v['app'] = app
            return eval(line, OCV.CD, self.vars)

        else:
            return line

    def _addLine(self, line):
        """add new line to list create block if necessary"""
        if line.startswith("(Block-name:"):
            self._blocksExist = True
            pat = BLOCKPAT.match(line)
            if pat:
                value = pat.group(2).strip()
                if not self.blocks or len(self.blocks[-1]):
                    self.blocks.append(Block(value))
                else:
                    self.blocks[-1]._name = value
                return

        # FIXME: Code to import legacy tabs
        # can be probably removed in year 2020 or so:
        if line.startswith("(Block-tab:"):
            pat = BLOCKPAT.match(line)
            if pat:
                value = pat.group(2).strip()
                items = map(float, value.split())
                tablock = Block(
                    "legacy [tab,island,minz:{0:0.f}]".format(items[4]))
                tablock.color = "orange"
                tablock.extend(self.createTab(*items))
                self.insBlocks(-1, [tablock], "Legacy tab")
                print("WARNING: Converted legacy tabs loaded from file to new g-code island tabs: %s"%(tablock._name))

        if not self.blocks:
            self.blocks.append(Block("Header"))

        cmds = CNC.parseLine(line)
        # print("_addLine ", line, cmds)
        if cmds is None:
            self.blocks[-1].append(line)
            return

        self.cnc.motionStart(cmds)

        # Add line to the list for display
        self.gcodelines.append(line)
        # print("_addLine ", len(self.gcodelines), line)

        # rapid move up = end of block
        if self._blocksExist:
            self.blocks[-1].append(line)
        elif self.cnc.gcode == 0 and self.cnc.dz > 0.0:
            self.blocks[-1].append(line)
            self.blocks.append(Block())
        elif self.cnc.gcode == 0 and len(self.blocks) == 1:
            self.blocks.append(Block())
            self.blocks[-1].append(line)
        else:
            self.blocks[-1].append(line)

        self.cnc.motionEnd()

    def load(self, filename=None):
        """Load a file into editor"""
        if filename is None:
            filename = self.filename

        self.init()
        self.filename = filename

        try:
            f = open(self.filename, "r")
        except Exception:
            return False

        self._lastModified = os.stat(self.filename).st_mtime
        self.cnc.initPath()
        self.cnc.resetAllMargins()
        self._blocksExist = False
        for line in f:
            self._addLine(line[:-1].replace("\x0d", ""))
        self._trim()
        f.close()
        return True

    def save(self, filename=None):
        """Save to a file"""
        if filename is not None:
            self.filename = filename

        try:
            f = open(self.filename, "w")
        except Exception:
            return False

        for block in self.blocks:
            block.write(f)
        f.close()
        self._lastModified = os.stat(self.filename).st_mtime
        self._modified = False
        return True

    def saveTXT(self, filename):
        """
        Save in TXT format
        Enabled Blocks only
        Cleaned from OKKCNC metadata and comments
        Uppercase
        """
        txt = open(filename, 'w')
        for block in self.blocks:
            if block.enable:
                for line in block:
                    cmds = CNC.parseLine(line)

                    if cmds is None:
                        continue

                txt.write("{0}\n".format(line.upper()))
        txt.close()
        return True

    def addBlockFromString(self, name, text):

        if not text:
            return

        block = Block(name)
        block.extend(text.splitlines())
        self.blocks.append(block)

    def headerFooter(self):
        """Check if Block is empty:
             If Empty insert a header and a footer
            """
        if not self.blocks:
            currDate = strftime("%Y-%m-%d - %H:%M:%S", localtime())
            curr_header = "(Created By OKKCNC version {0}) \n".format(
                OCV._version)
            curr_header += "(Date: {0})\n".format(currDate)
            curr_header += self.header

            self.addBlockFromString("Header", curr_header)
            self.addBlockFromString("Footer", self.footer)
            return True
        return False

# CHECK if it is a remnant of SVG or DXF imports
    def getMargins(self):
        """get document margins"""
        # Get bounding box of document
        min_x, min_y, max_x, max_y = 0, 0, 0, 0
        for idx, block in enumerate(self.blocks):
            paths = self.toPath(idx)

            for path in paths:
                min_x2, min_y2, max_x2, max_y2 = path.bbox()
                min_x = min(min_x, min_x2)
                min_y = min(min_y, min_y2)
                max_x = max(max_x, max_x2)
                max_y = max(max_y, max_y2)

        return min_x, min_y, max_x, max_y

    def importEntityPoints(self, pos, entities, name, enable=True, color=None):
        """Import POINTS from entities"""
        undoinfo = []
        i = 0

        while i < len(entities):
            if entities[i].type != "POINT":
                i += 1
                continue

            block = Block("{0} [P]".format(name))
            block.enable = enable

            block.color = entities[i].color()
            if block.color is None:
                block.color = color

            x, y = entities[i].start()
            block.append("G0 {0} {1}}".format(
                self.fmt("X", x, 7),
                self.fmt("Y", y, 7)))
            block.append(CNC.zenter(self.cnc["surface"]))
            block.append(CNC.zsafe())
            undoinfo.append(self.addBlockUndo(pos, block))

            if pos is not None:
                pos += 1

            del entities[i]

        return undoinfo

    def toPath(self, bid):
        """convert a block to path"""
        block = self.blocks[bid]
        paths = []
        path = Path(block.name())
        self.initPath(bid)
        start = Vector(self.cnc.x, self.cnc.y)

        # get only first path that enters the surface
        # ignore the deeper ones
        passno = 0
        for line in block:
            # flatten helical paths
            line = re.sub(r"\s?z-?[0-9\.]+", "", line)

            # break after first depth pass
            if line == "( ---------- cut-here ---------- )":
                passno = 0
                if path:
                    paths.append(path)
                    path = Path(block.name())

            if line[:5] == "(pass":
                passno += 1

            if passno > 1:
                continue

            cmds = CNC.parseLine(line)

            if cmds is None:
                continue

            self.cnc.motionStart(cmds)
            end = Vector(self.cnc.xval, self.cnc.yval)
            if self.cnc.gcode == 0:  # rapid move (new block)
                if path:
                    paths.append(path)
                    path = Path(block.name())
            elif self.cnc.gcode == 1:  # line
                if self.cnc.dx != 0.0 or self.cnc.dy != 0.0:
                    path.append(Segment(1, start, end))
            elif self.cnc.gcode in (2, 3):  # arc
                xc, yc = self.cnc.motionCenter()
                center = Vector(xc, yc)
                path.append(Segment(self.cnc.gcode, start, end, center))
            self.cnc.motionEnd()
            start = end

        if path:
            paths.append(path)

        return paths

    def fromPath(self, path, block=None, z=None, retract=True, entry=False,
                 exit=True, zstart=None, ramp=None, comments=True,
                 exitpoint=None, truncate=None):
        """Create a block from Path
        @param z    I       ending depth
        @param zstart    I       starting depth
        """

        # Recursion for multiple paths
        if not isinstance(path, Path):
            block = Block("new")
            for p in path:
                block.extend(
                    self.fromPath(
                            p, None, z, retract, entry, exit,
                            zstart, ramp, comments, exitpoint, truncate))

                block.append("( ---------- cut-here ---------- )")
            del block[-1]  # remove trailing cut-here
            return block

        if z is None:
            z = self.cnc["surface"]

        if zstart is None:
            zstart = z

        # Calculate helix step
        zstep = abs(z-zstart)

        # Preprocess ramp
        if ramp is None:
            ramp = 0

        if ramp == 0:
            ramp = path.length()  # full helix (default)

        ramp = min(ramp, path.length())  # Never ramp longer than single pass!

        # Calculate helical feedrate
        helixfeed = self.cnc["cutfeed"]

        if zstep > 0:
            # Compensate helix feed
            # so we never plunge too fast on short/steep paths
            # FIXME: Add UI to disable this feature???
            # Not sure if that's needed.
            rampratio = zstep/min(path.length(), ramp)
            helixfeed2 = round(self.cnc["cutfeedz"] / rampratio)
            helixfeed = min(self.cnc["cutfeed"], helixfeed2)

        if block is None:
            if isinstance(path, Path):
                block = Block(path.name)
            else:
                block = Block(path[0].name)

        # Generate g-code for single path segment
        def addSegment(segment, z=None, cm=""):
            x, y = segment.B

            # Generate LINE
            if segment.type == Segment.LINE:
                x, y = segment.B
                # rounding problem from #903 was manifesting here.
                # Had to lower the decimal precision to OCV.digits
                if z is None:
                    block.append("G1 {0} {1}".format(
                        self.fmt("X", x, 7),
                        self.fmt("Y", y, 7)) + cm)
                else:
                    block.append("G1 {0} {1} {2}".format(
                        self.fmt("X", x, 7),
                        self.fmt("Y", y, 7),
                        self.fmt("Z", z, 7)) + cm)

            # Generate ARCS
            elif segment.type in (Segment.CW, Segment.CCW):
                ij = segment.C - segment.A

                if abs(ij[0]) < 1e-5:
                    ij[0] = 0.

                if abs(ij[1]) < 1e-5:
                    ij[1] = 0.

                if z is None:
                    block.append("G{0:d} {1} {2} {3} {4}".format(
                            segment.type,
                            self.fmt("X", x, 7),
                            self.fmt("Y", y, 7),
                            self.fmt("I", ij[0], 7),
                            self.fmt("J", ij[1], 7)) + cm)
                else:
                    block.append("G{0:d} {1} {2} {3} {4} {5}".format(
                            segment.type,
                            self.fmt("X", x, 7),
                            self.fmt("Y", y, 7),
                            self.fmt("I", ij[0], 7),
                            self.fmt("J", ij[1], 7),
                            self.fmt("Z", z, 7)) + cm)

        # Get island height of segment
        def getSegmentZTab(segment, altz=float("-inf")):
            if segment._inside:
                return max(segment._inside)
            else:
                return altz

        # Generate block from path
        if isinstance(path, Path):
            x, y = path[0].A

            # decide if flat or ramp/helical:
            if z == zstart:
                zh = z

            elif zstart is not None:
                zh = zstart

            # test if not starting in tab/island!
            ztab = getSegmentZTab(path[0], z)

            # Retract to zsafe
            if retract:
                block.append(
                    "G0 {0}".format(
                        self.fmt("Z", OCV.CD["safe"], 7)))

            # Rapid to beginning of the path
            block.append(
                "G0 {0} {1}".format(
                        self.fmt("X", x, 7),
                        self.fmt("Y", y, 7)))

            # Descend to pass (plunge to the beginning of path)
            if entry:
                # if entry feed to Z
                block.append(CNC.zenter(max(zh, ztab), 7))
            else:
                # without entry just rapid to Z
                block.append(
                    "G0 {0}".format(self.fmt("Z", max(zh, ztab), 7)))

            # Begin pass
            # if comments: block.append("(pass %f)"%(max(zh, ztab)))
            if comments:
                block.append("(entered)")

            # Loop over segments
            setfeed = True
            ztabprev = float("-inf")
            ramping = True

            for sid, segment in enumerate(path):
                zhprev = zh

                # Ramp down
                zh -= (segment.length()/ramp)*zstep  # ramp
                zh = max(zh, z)  # Never cut deeper than z!

                # Reset feedrate if not ramping anymore
                if zh == zhprev and ramping:
                    helixfeed = self.cnc["cutfeed"]
                    setfeed = True
                    ramping = False

                # Get tab height
                ztab = getSegmentZTab(segment)

                # Retract over tabs
                if ztab != ztabprev:
                    # has tab height changed? tab boundary crossed?
                    if (ztab == float("-inf") or ztab < ztabprev) and \
                          (zh < ztabprev or zhprev < ztabprev):
                        # Check if we need to enter the toolpath after
                        # having done clearing the tab

                        if comments:
                            block.append(
                                    "(tab down "+str(max(zhprev, ztab))+")")

                        block.append(CNC.zenter(max(zhprev, ztab), 7))
                        setfeed = True
                    elif zh < ztab or zhprev < ztab:
                        # Check if we need to go higher in order to
                        # clear the tab
                        if comments:
                            block.append("(tab up "+str(max(zh, ztab))+")")
                        block.append(CNC.zexit(max(zh, ztab), 7))
                        setfeed = True
                ztabprev = ztab

                # Cut next segment of toolpath
                # has tab height changed? tab boundary crossed?
                addSegment(segment, max(zh, ztab))

                # Set feed if needed
                if setfeed:
                    block[-1] += " {0}".format(self.fmt("f", round(helixfeed)))
                    setfeed = False

                # Truncate
                if truncate is not None:
                    truncate -= segment.length()

                    if truncate <= -1e-7:
                        break

            # Exit toolpath
            if exit:
                if comments:
                    block.append("(exiting)")

                if exitpoint is not None:
                    block.append(
                            'G1 {0} {1}'.format(
                                    self.fmt("X", exitpoint[0]),
                                    self.fmt("Y", exitpoint[1])))
                block.append(CNC.zsafe())

        return block

    def importPath(self, pos, paths, newblocks=None,
                   enable=True, multiblock=True):
        """
        Import paths as block
        return ids of blocks added in newblocks list if declared
        """

        undoinfo = []

        if isinstance(paths, Path):
            block = self.fromPath(paths)
            block.enable = enable
            block.color = paths.color
            undoinfo.append(self.addBlockUndo(pos, block))

            if newblocks is not None:
                newblocks.append(pos)
        else:
            block = None

            for path in paths:
                if block is None:
                    block = Block(path.name)
                block = self.fromPath(path, block)
                if multiblock:
                    block.enable = enable
                    undoinfo.append(self.addBlockUndo(pos, block))

                    if newblocks is not None:
                        newblocks.append(pos)

                    if pos is not None:
                        pos += 1

                    block = None
            if not multiblock:
                block.enable = enable
                undoinfo.append(self.addBlockUndo(pos, block))

                if newblocks is not None:
                    newblocks.append(pos)

        return undoinfo

    def syncFileTime(self):
        """sync file timestamp"""
        try:
            self._lastModified = os.stat(self.filename).st_mtime
        except Exception:
            return False

    #----------------------------------------------------------------------
    # Check if a new version exists
    #----------------------------------------------------------------------
    def checkFile(self):
        try:
            return os.stat(self.filename).st_mtime > self._lastModified
        except Exception:
            return False

    #----------------------------------------------------------------------
    def fmt(self, c, v, d=None): return self.cnc.fmt(c,v,d)

    #----------------------------------------------------------------------
    def _trim(self):
        if not self.blocks: return
        # Delete last block if empty
        last = self.blocks[-1]
        if len(last)==1 and len(last[0])==0: del last[0]
        if len(self.blocks[-1])==0:
            self.blocks.pop()

    #----------------------------------------------------------------------
    # Undo/Redo operations
    #----------------------------------------------------------------------
    def undo(self):
        #print ">u>",self.undoredo.undoText()
        self.undoredo.undo()

    #----------------------------------------------------------------------
    def redo(self):
        #print ">r>",self.undoredo.redoText()
        self.undoredo.redo()

    #----------------------------------------------------------------------
    def addUndo(self, undoinfo, msg=None):
        if not undoinfo: return
        self.undoredo.add(undoinfo, msg)
        self._modified = True

    #----------------------------------------------------------------------
    def canUndo(self):    return self.undoredo.canUndo()

    #----------------------------------------------------------------------
    def canRedo(self):    return self.undoredo.canRedo()

    #----------------------------------------------------------------------
    # Change all lines in editor
    #----------------------------------------------------------------------
    def setLinesUndo(self, lines):
        undoinfo = (self.setLinesUndo, list(self.lines()))
        # Delete all blocks and create new ones
        del self.blocks[:]
        self.cnc.initPath()
        self._blocksExist = False
        for line in lines: self._addLine(line)
        self._trim()
        return undoinfo

    #----------------------------------------------------------------------
    def setAllBlocksUndo(self, blocks=[]):
        undoinfo = [self.setAllBlocksUndo, self.blocks]
        self.blocks = blocks
        return undoinfo

    #----------------------------------------------------------------------
    # Change a single line in a block
    #----------------------------------------------------------------------
    def setLineUndo(self, bid, lid, line):
        undoinfo = (self.setLineUndo, bid, lid, self.blocks[bid][lid])
        self.blocks[bid][lid] = line
        return undoinfo

    #----------------------------------------------------------------------
    # Insert a new line into block
    #----------------------------------------------------------------------
    def insLineUndo(self, bid, lid, line):
        undoinfo = (self.delLineUndo, bid, lid)
        block = self.blocks[bid]
        if lid>=len(block):
            block.append(line)
        else:
            block.insert(lid, line)
        return undoinfo

    #----------------------------------------------------------------------
    # Clone line inside a block
    #----------------------------------------------------------------------
    def cloneLineUndo(self, bid, lid):
        return self.insLineUndo(bid, lid, self.blocks[bid][lid])

    #----------------------------------------------------------------------
    # Delete line from block
    #----------------------------------------------------------------------
    def delLineUndo(self, bid, lid):
        block = self.blocks[bid]
        undoinfo = (self.insLineUndo, bid, lid, block[lid])
        del block[lid]
        return undoinfo

    #----------------------------------------------------------------------
    # Add a block
    #----------------------------------------------------------------------
    def addBlockUndo(self, bid, block):
        if bid is None: bid = len(self.blocks)
        if bid>=len(self.blocks):
            undoinfo = (self.delBlockUndo, len(self.blocks))
            self.blocks.append(block)
        else:
            undoinfo = (self.delBlockUndo, bid)
            self.blocks.insert(bid, block)
        return undoinfo

    #----------------------------------------------------------------------
    # Clone a block
    #----------------------------------------------------------------------
    def cloneBlockUndo(self, bid, pos=None):
        if pos is None: pos = bid
        return self.addBlockUndo(pos, Block(self.blocks[bid]))

    #----------------------------------------------------------------------
    # Delete a whole block
    #----------------------------------------------------------------------
    def delBlockUndo(self, bid):
        lines = [x for x in self.blocks[bid]]
        block = self.blocks.pop(bid)
        undoinfo = (self.addBlockUndo, bid, block)
        return undoinfo

    #----------------------------------------------------------------------
    # Insert a list of other blocks from another gcode file probably
    #----------------------------------------------------------------------
    def insBlocksUndo(self, bid, blocks):
        if bid is None or bid >= len(self.blocks):
            bid = len(self.blocks)
        undoinfo = ("Insert blocks", self.delBlocksUndo, bid, bid+len(blocks))
        self.blocks[bid:bid] = blocks
        return undoinfo

    #----------------------------------------------------------------------
    # Delete a range of blocks
    #----------------------------------------------------------------------
    def delBlocksUndo(self, from_, to_):
        blocks = self.blocks[from_:to_]
        undoinfo = ("Delete blocks", self.insBlocksUndo, from_, blocks)
        del self.blocks[from_:to_]
        return undoinfo

    #----------------------------------------------------------------------
    # Insert blocks and push the undo info
    #----------------------------------------------------------------------
    def insBlocks(self, bid, blocks, msg=""):
        if self.headerFooter():    # just in case
            bid = 1
        self.addUndo(self.insBlocksUndo(bid, blocks), msg)

    #----------------------------------------------------------------------
    # Set block expand
    #----------------------------------------------------------------------
    def setBlockExpandUndo(self, bid, expand):
        undoinfo = (self.setBlockExpandUndo, bid, self.blocks[bid].expand)
        self.blocks[bid].expand = expand
        return undoinfo

    #----------------------------------------------------------------------
    # Set block state
    #----------------------------------------------------------------------
    def setBlockEnableUndo(self, bid, enable):
        undoinfo = (self.setBlockEnableUndo, bid, self.blocks[bid].enable)
        self.blocks[bid].enable = enable
        return undoinfo

    #----------------------------------------------------------------------
    # Set block color
    #----------------------------------------------------------------------
    def setBlockColorUndo(self, bid, color):
        undoinfo = (self.setBlockColorUndo, bid, self.blocks[bid].color)
        self.blocks[bid].color = color
        return undoinfo

    #----------------------------------------------------------------------
    # Swap two blocks
    #----------------------------------------------------------------------
    def swapBlockUndo(self, a, b):
        undoinfo = (self.swapBlockUndo, a, b)
        tmp = self.blocks[a]
        self.blocks[a] = self.blocks[b]
        self.blocks[b] = tmp
        return undoinfo

    #----------------------------------------------------------------------
    # Move block from location src to location dst
    #----------------------------------------------------------------------
    def moveBlockUndo(self, src, dst):
        if src == dst: return None
        undoinfo = (self.moveBlockUndo, dst, src)
        if dst > src:
            self.blocks.insert(dst-1, self.blocks.pop(src))
        else:
            self.blocks.insert(dst, self.blocks.pop(src))
        return undoinfo

    #----------------------------------------------------------------------
    # Invert selected blocks
    #----------------------------------------------------------------------
    def invertBlocksUndo(self, blocks):
        undoinfo = []
        first = 0
        last  = len(blocks)-1
        while first < last:
            undoinfo.append(self.swapBlockUndo(blocks[first],blocks[last]))
            first += 1
            last  -= 1
        return undoinfo

    #----------------------------------------------------------------------
    # Move block upwards
    #----------------------------------------------------------------------
    def orderUpBlockUndo(self, bid):
        if bid==0: return None
        undoinfo = (self.orderDownBlockUndo, bid-1)
        # swap with the block above
        before      = self.blocks[bid-1]
        self.blocks[bid-1] = self.blocks[bid]
        self.blocks[bid]   = before
        return undoinfo

    #----------------------------------------------------------------------
    # Move block downwards
    #----------------------------------------------------------------------
    def orderDownBlockUndo(self, bid):
        if bid>=len(self.blocks)-1: return None
        undoinfo = (self.orderUpBlockUndo, bid+1)
        # swap with the block below
        after       = self[bid+1]
        self[bid+1] = self[bid]
        self[bid]   = after
        return undoinfo

    #----------------------------------------------------------------------
    # Insert block lines
    #----------------------------------------------------------------------
    def insBlockLinesUndo(self, bid, lines):
        undoinfo = (self.delBlockLinesUndo, bid)
        block = Block()
        for line in lines:
            block.append(line)
        self.blocks.insert(bid, block)
        return undoinfo

    #----------------------------------------------------------------------
    # Delete a whole block lines
    #----------------------------------------------------------------------
    def delBlockLinesUndo(self, bid):
        lines = [x for x in self.blocks[bid]]
        undoinfo = (self.insBlockLinesUndo, bid, lines) #list(self.blocks[bid])[:])
        del self.blocks[bid]
        return undoinfo

    #----------------------------------------------------------------------
    # Set Block name
    #----------------------------------------------------------------------
    def setBlockNameUndo(self, bid, name):
        undoinfo = (self.setBlockNameUndo, bid, self.blocks[bid]._name)
        self.blocks[bid]._name = name
        return undoinfo

    #----------------------------------------------------------------------
    # Add an operation code in the name as [drill, cut, in/out...]
    #----------------------------------------------------------------------
    def addBlockOperationUndo(self, bid, operation, remove=None):
        undoinfo = (self.setBlockNameUndo, bid, self.blocks[bid]._name)
        self.blocks[bid].addOperation(operation, remove)
        return undoinfo

    #----------------------------------------------------------------------
    # Replace the lines of a block
    #----------------------------------------------------------------------
    def setBlockLinesUndo(self, bid, lines):
        block = self.blocks[bid]
        undoinfo = (self.setBlockLinesUndo, bid, block[:])
        del block[:]
        block.extend(lines)
        return undoinfo

    #----------------------------------------------------------------------
    # Move line upwards
    #----------------------------------------------------------------------
    def orderUpLineUndo(self, bid, lid):
        if lid==0: return None
        block = self.blocks[bid]
        undoinfo = (self.orderDownLineUndo, bid, lid-1)
        block.insert(lid-1, block.pop(lid))
        return undoinfo

    #----------------------------------------------------------------------
    # Move line downwards
    #----------------------------------------------------------------------
    def orderDownLineUndo(self, bid, lid):
        block = self.blocks[bid]
        if lid>=len(block)-1: return None
        undoinfo = (self.orderUpLineUndo, bid, lid+1)
        block.insert(lid+1, block.pop(lid))
        return undoinfo

    #----------------------------------------------------------------------
    # Expand block with autolevel information
    #----------------------------------------------------------------------
    def autolevelBlock(self, block):
        new = []
        autolevel = not self.probe.isEmpty()
        for line in block:
            newcmd = []
            cmds = CNC.compileLine(line)
            if cmds is None:
                new.append(line)
                continue
            elif isinstance(cmds,str):
                cmds = CNC.breakLine(cmds)
            else:
                new.append(line)
                continue

            self.cnc.motionStart(cmds)
            if autolevel and self.cnc.gcode in (0,1,2,3) and self.cnc.mval==0:
                xyz = self.cnc.motionPath()
                if not xyz:
                    # while auto-levelling, do not ignore non-movement
                    # commands, just append the line as-is
                    new.append(line)
                else:
                    extra = ""
                    for c in cmds:
                        if c[0].upper() not in ('G','X','Y','Z','I','J','K','R'):
                            extra += c
                    x1,y1,z1 = xyz[0]
                    if self.cnc.gcode == 0:
                        g = 0
                    else:
                        g = 1
                    for x2,y2,z2 in xyz[1:]:
                        for x,y,z in self.probe.splitLine(x1,y1,z1,x2,y2,z2):
                            new.append("G%d%s%s%s%s"%\
                                (g,
                                 self.fmt('X',x/self.cnc.unit),
                                 self.fmt('Y',y/self.cnc.unit),
                                 self.fmt('Z',z/self.cnc.unit),
                                 extra))
                            extra = ""
                        x1,y1,z1 = x2,y2,z2
                self.cnc.motionEnd()
            else:
                self.cnc.motionEnd()
                new.append(line)
        return new

    #----------------------------------------------------------------------
    # Execute autolevel on selected blocks
    #----------------------------------------------------------------------
    def autolevel(self, items):
        undoinfo = []
        operation = "autolevel"
        for bid in items:
            block = self.blocks[bid]
            if block.name() in ("Header", "Footer"): continue
            if not block.enable: continue
            lines = self.autolevelBlock(block)
            undoinfo.append(self.addBlockOperationUndo(bid, operation))
            undoinfo.append(self.setBlockLinesUndo(bid, lines))
        if undoinfo: self.addUndo(undoinfo)

    #----------------------------------------------------------------------
    # Merge or split blocks depending on motion
    #
    # Each block should start with a rapid move and end with a rapid move
    #----------------------------------------------------------------------
#    def correctBlocks(self):
#        # Working in place tricky
#        bid = 0    # block index
#        while bid < len(self.blocks):
#            block = self.blocks[bid]
#            li = 0    # line index
#            prefix = True
#            suffix = False
#            lastg0 = None
#            while li < len(block):
#                line = block[li]
#                cmds = CNC.parseLine(line)
#                if cmds is None:
#                    li += 1
#                    continue
#
#                self.cnc.motionStart(cmds)
#
#                # move
#                if self.gcode in (1,2,3):
#                    if prefix is None: prefix = li-1
#
#                # rapid movement
#                elif self.gcode == 0:
#                    lastg0 = li
#                    if prefix is not None: suffix = li
#
#                    # moving up = end of block
#                    if self.cnc.dz > 0.0:
#                        if suffix:
#                            # Move all subsequent lines to a new block
#                            #self.blocks.append(Block())
#                            pass
#                self.cnc.motionEnd()

    #----------------------------------------------------------------------
    # Start a new iterator
    #----------------------------------------------------------------------
#    def __iter__(self):
#        self._iter = 0    #self._iter_start
#        self._iter_block = self.blocks[self._iter]
#        self._iter_block_i = 0
#        self._iter_end   = len(self.blocks)
#        return self
#
#    #----------------------------------------------------------------------
#    # Next iterator item
#    #----------------------------------------------------------------------
#    def next(self):
#        if self._iter >= self._iter_end: raise StopIteration()
#
#        while self._iter_block_i >= len(self._iter_block):
#            self._iter += 1
#            if self._iter >= self._iter_end: raise StopIteration()
#            self._iter_block = self.blocks[self._iter]
#            self._iter_block_i = 0
#
#        item = self._iter_block[self._iter_block_i]
#        self._iter_block_i += 1
#        return item

    #----------------------------------------------------------------------
    # Return string representation of whole file
    #----------------------------------------------------------------------
    def __repr__(self):
        return "\n".join(list(self.lines()))

    #----------------------------------------------------------------------
    # Iterate over the items
    #----------------------------------------------------------------------
    def iterate(self, items):
        for bid,lid in items:
            if lid is None:
                block = self.blocks[bid]
                for i in range(len(block)):
                    yield bid,i
            else:
                yield bid,lid

    #----------------------------------------------------------------------
    # Iterate over all lines
    #----------------------------------------------------------------------
    def lines(self):
        for block in self.blocks:
            for line in block:
                yield line

    #----------------------------------------------------------------------
    # initialize cnc path based on block bid
    #----------------------------------------------------------------------
    def initPath(self, bid=0):
        if bid == 0:
            self.cnc.initPath()
        else:
            # Use the ending point of the previous block
            # since the starting (sxyz is after the rapid motion)
            block = self.blocks[bid-1]
            self.cnc.initPath(block.ex, block.ey, block.ez)

    #----------------------------------------------------------------------
    # Move blocks/lines up
    #----------------------------------------------------------------------
    def orderUp(self, items):
        sel = []    # new selection
        undoinfo = []
        for bid,lid in items:
            if isinstance(lid,int):
                undoinfo.append(self.orderUpLineUndo(bid,lid))
                sel.append((bid, lid-1))
            elif lid is None:
                undoinfo.append(self.orderUpBlockUndo(bid))
                if bid==0:
                    return items
                else:
                    sel.append((bid-1,None))
        self.addUndo(undoinfo,"Move Up")
        return sel

    #----------------------------------------------------------------------
    # Move blocks/lines down
    #----------------------------------------------------------------------
    def orderDown(self, items):
        sel = []    # new selection
        undoinfo = []
        for bid,lid in reversed(items):
            if isinstance(lid,int):
                undoinfo.append(self.orderDownLineUndo(bid,lid))
                sel.append((bid,lid+1))
            elif lid is None:
                undoinfo.append(self.orderDownBlockUndo(bid))
                if bid>=len(self.blocks)-1:
                    return items
                else:
                    sel.append((bid+1,None))
        self.addUndo(undoinfo,"Move Down")
        sel.reverse()
        return sel

    #----------------------------------------------------------------------
    # Close paths by joining end with start with a line segment
    #----------------------------------------------------------------------
    def close(self, items):
        undoinfo = []
        for bid in items:
            block = self.blocks[bid]
            if block.name() in ("Header", "Footer"): continue
            undoinfo.append(self.insLineUndo(bid, MAXINT,
                    self.cnc.gline(block.sx, block.sy)))
        self.addUndo(undoinfo)

    #----------------------------------------------------------------------
    # Reverse direction of cut
    #----------------------------------------------------------------------
    def reverse(self, items):
        undoinfo = []
        remove = ["cut","climb","conventional","cw","ccw","reverse"]
        for bid in items:
            operation = "reverse"

            if self.blocks[bid].name() in ("Header", "Footer"): continue
            newpath = Path(self.blocks[bid].name())

            #Not sure if this is good idea...
            #Might get confusing if something goes wrong, but seems to work fine
            if self.blocks[bid].operationTest('conventional'): operation+= ",climb"
            if self.blocks[bid].operationTest('climb'): operation+= ",conventional"
            if self.blocks[bid].operationTest('cw'): operation+= ",ccw"
            if self.blocks[bid].operationTest('ccw'): operation+= ",cw"

            for path in self.toPath(bid):
                path.invert()
                newpath.extend(path)
            if newpath:
                block = self.fromPath(newpath)
                undoinfo.append(self.addBlockOperationUndo(bid, operation, remove))
                undoinfo.append(self.setBlockLinesUndo(bid, block))
        self.addUndo(undoinfo)

    #----------------------------------------------------------------------
    # Change cut direction
    # 1    CW
    # -1    CCW
    # 2    Conventional = CW for inside profiles and pockets, CCW for outside profiles
    # -2    Climb = CCW for inside profiles and pockets, CW for outside profiles
    #----------------------------------------------------------------------
    def cutDirection(self, items, direction=-1):

        undoinfo = []
        msg = None

        remove = ["cut","reverse","climb","conventional","cw","ccw"]
        for bid in items:
            if self.blocks[bid].name() in ("Header", "Footer"): continue

            opdir = direction
            operation = ""

            #Decide conventional/climb/error:
            side = self.blocks[bid].operationSide()
            if abs(direction) > 1 and side == 0:
                msg = "Conventional/Climb feature only works for paths with 'in/out/pocket' tags!\n"
                msg += "Some of the selected paths were not taged (or are both in+out). You can still use CW/CCW for them."
                continue
            if direction==2:
                operation = "conventional,"
                if side==-1: opdir=1 #inside CW
                if side==1: opdir=-1 #outside CCW
            elif direction==-2:
                operation = "climb,"
                if side==-1: opdir=-1 #inside CCW
                if side==1: opdir=1 #outside CW

            #Decide CW/CCW tag
            if opdir==1:
                operation += "cw"
            elif opdir==-1:
                operation += "ccw"

            #Process paths
            for path in self.toPath(bid):
                if not path.directionSet(opdir):
                    msg = "Error determining direction of path!"
                if path:
                    block = self.fromPath(path)
                    undoinfo.append(self.addBlockOperationUndo(bid, operation,remove))
                    undoinfo.append(self.setBlockLinesUndo(bid, block))
        self.addUndo(undoinfo)

        return msg

    #----------------------------------------------------------------------
    # Toggle or set island tag on block
    #----------------------------------------------------------------------
    def island(self, items, island=None):

        undoinfo = []
        remove = ["island"]
        for bid in items:
            isl = island

            if self.blocks[bid].name() in ("Header", "Footer"): continue

            if isl is None: isl = not self.blocks[bid].operationTest('island')
            if isl:
                tag = 'island'
                self.blocks[bid].color = '#ff0000'
            else:
                tag = ''
                self.blocks[bid].color = None

            undoinfo.append(self.addBlockOperationUndo(bid, tag,remove))
            #undoinfo.append(self.setBlockLinesUndo(bid, block))

        self.addUndo(undoinfo)

    #----------------------------------------------------------------------
    # Return information for a block
    # return XXX
    #----------------------------------------------------------------------
    def info(self, bid):
        block = self.blocks[bid]
        paths = self.toPath(bid)
        if not paths:
            return None, 1
        if len(paths)>1:
            closed = paths[0].isClosed()
            return len(paths), paths[0]._direction(closed)
        else:
            closed = paths[0].isClosed()
            return int(closed), paths[0]._direction(closed)

    #----------------------------------------------------------------------
    # Modify the lines according to the supplied function and arguments
    #----------------------------------------------------------------------
    def modify(self, items, func, tabFunc, *args):
        undoinfo = []
        old = {}    # Motion commands: Last value
        new = {}    # Motion commands: New value
        relative = False

        for bid,lid in self.iterate(items):
            block = self.blocks[bid]

            if isinstance(lid, int):
                cmds = CNC.parseLine(block[lid])
                if cmds is None: continue
                self.cnc.motionStart(cmds)

                # Collect all values
                new.clear()
                for cmd in cmds:
                    if cmd.upper() == 'G91': relative = True
                    if cmd.upper() == 'G90': relative = False
                    c = cmd[0].upper()
                    # record only coordinates commands
                    if c not in "XYZIJKR": continue
                    try:
                        new[c] = old[c] = float(cmd[1:])*self.cnc.unit
                    except Exception:
                        new[c] = old[c] = 0.0

                # Modify values with func
                if func(new, old, relative, *args):
                    # Reconstruct new line
                    newcmd = []
                    present = ""
                    for cmd in cmds:
                        c = cmd[0].upper()
                        if c in "XYZIJKR":    # Coordinates
                            newcmd.append(self.fmt(c,new[c]/self.cnc.unit))
                        elif c == "G" and int(cmd[1:]) in (0,1,2,3):    # Motion
                            newcmd.append("G%d"%(self.cnc.gcode))
                        else:    # the rest leave unchanged
                            newcmd.append(cmd)
                        present += c
                    # Append motion commands if not exist and changed
                    check = "XYZ"
                    if 'I' in new or 'J' in new or 'K' in new:
                        check += "IJK"
                    for c in check:
                        try:
                            if c not in present and new.get(c) != old.get(c):
                                newcmd.append(self.fmt(c,new[c]/self.cnc.unit))
                        except Exception:
                            pass
                    undoinfo.append(self.setLineUndo(bid,lid," ".join(newcmd)))
                self.cnc.motionEnd()
                # reset arc offsets
                for i in "IJK":
                    if i in old: old[i] = 0.0

        # FIXME I should add it later, check all functions using it
        self.addUndo(undoinfo)

    #----------------------------------------------------------------------
    # Move position by dx,dy,dz
    #----------------------------------------------------------------------
    def moveFunc(self, new, old, relative, dx, dy, dz):
        if relative: return False
        changed = False
        if 'X' in new:
            changed = True
            new['X'] += dx
        if 'Y' in new:
            changed = True
            new['Y'] += dy
        if 'Z' in new:
            changed = True
            new['Z'] += dz
        return changed

    #----------------------------------------------------------------------
    def orderLines(self, items, direction):
        if direction == "UP":
            self.orderUp(items)
        elif direction == "DOWN":
            self.orderDown(items)
        else:
            pass

    #----------------------------------------------------------------------
    # Move position by dx,dy,dz
    #----------------------------------------------------------------------
    def moveLines(self, items, dx, dy, dz=0.0):
        return self.modify(items, self.moveFunc, None, dx, dy, dz)

    #----------------------------------------------------------------------
    # Rotate position by c(osine), s(ine) of an angle around center (x0,y0)
    #----------------------------------------------------------------------
    def rotateFunc(self, new, old, relative, c, s, x0, y0):
        if 'X' not in new and 'Y' not in new: return False
        x = getValue('X',new,old)
        y = getValue('Y',new,old)
        new['X'] = c*(x-x0) - s*(y-y0) + x0
        new['Y'] = s*(x-x0) + c*(y-y0) + y0

        if 'I' in new or 'J' in new:
            i = getValue('I',new,old)
            j = getValue('J',new,old)
            if self.cnc.plane in (XY, XZ): new['I'] = c*i - s*j
            if self.cnc.plane in (XY, YZ): new['J'] = s*i + c*j
        return True

    #----------------------------------------------------------------------
    # Transform (rototranslate) position with the following function:
    #     xn = c*x - s*y + xo
    #     yn = s*x + c*y + yo
    # it is like the rotate but the rotation center is not defined
    #----------------------------------------------------------------------
    def transformFunc(self, new, old, relative, c, s, xo, yo):
        if 'X' not in new and 'Y' not in new: return False
        x = getValue('X',new,old)
        y = getValue('Y',new,old)
        new['X'] = c*x - s*y + xo
        new['Y'] = s*x + c*y + yo

        if 'I' in new or 'J' in new:
            i = getValue('I',new,old)
            j = getValue('J',new,old)
            new['I'] = c*i - s*j
            new['J'] = s*i + c*j
        return True

    #----------------------------------------------------------------------
    # Rotate items around optional center (on XY plane)
    # ang in degrees (counter-clockwise)
    #----------------------------------------------------------------------
    def rotateLines(self, items, ang, x0=0.0, y0=0.0):
        a = math.radians(ang)
        c = math.cos(a)
        s = math.sin(a)
        if ang in (0.0,90.0,180.0,270.0,-90.0,-180.0,-270.0):
            c = round(c)    # round numbers to avoid nasty extra digits
            s = round(s)
        return self.modify(items, self.rotateFunc, None, c, s, x0, y0)

    #----------------------------------------------------------------------
    # Use the orientation information to orient selected code
    #----------------------------------------------------------------------
    def orientLines(self, items):
        if not self.orient.valid: return "ERROR: Orientation information is not valid"
        c = math.cos(self.orient.phi)
        s = math.sin(self.orient.phi)
        return self.modify(items, self.transformFunc, None, c, s,
                    self.orient.xo, self.orient.yo)

    #----------------------------------------------------------------------
    # Mirror Horizontal
    #----------------------------------------------------------------------
    def mirrorHFunc(self, new, old, relative, *kw):
        changed = False
        for axis in 'XI':
            if axis in new:
                new[axis] = -new[axis]
                changed = True
        if self.cnc.gcode in (2,3):    # Change  2<->3
            self.cnc.gcode = 5-self.cnc.gcode
            changed = True
        return changed

    #----------------------------------------------------------------------
    # Mirror Vertical
    #----------------------------------------------------------------------
    def mirrorVFunc(self, new, old, relative, *kw):
        changed = False
        for axis in 'YJ':
            if axis in new:
                new[axis] = -new[axis]
                changed = True
        if self.cnc.gcode in (2,3):    # Change  2<->3
            self.cnc.gcode = 5-self.cnc.gcode
            changed = True
        return changed

    #----------------------------------------------------------------------
    # Mirror horizontally/vertically
    #----------------------------------------------------------------------
    def mirrorHLines(self, items):
        return self.modify(items, self.mirrorHFunc, None)

    #----------------------------------------------------------------------
    def mirrorVLines(self, items):
        return self.modify(items, self.mirrorVFunc, None)

    #----------------------------------------------------------------------
    # Round all digits with accuracy
    #----------------------------------------------------------------------
    def roundFunc(self, new, old, relative):
        for name,value in new.items():
            new[name] = round(value, OCV.digits)
        return bool(new)

    #----------------------------------------------------------------------
    # Round line by the amount of digits
    #----------------------------------------------------------------------
    def roundLines(self, items, acc=None):
        if acc is not None: OCV.digits = acc
        return self.modify(items, self.roundFunc, None)

    #----------------------------------------------------------------------
    # Inkscape g-code tools on slice/slice it raises the tool to the
    # safe height then plunges again.
    # Comment out all these patterns
    #
    # FIXME needs re-working...
    #----------------------------------------------------------------------
    def inkscapeLines(self):
        # Loop over all blocks
        self.initPath()
        newlines = []
        #last = None
        last = -1    # line location when it was last raised with dx=dy=0.0

        #for line in self.iterate():
        #for bid,block in enumerate(self.blocks):
        #    for li,line in enumerate(block):
        for line in self.lines():
            # step id
            # 0 - normal cutting z<0
            # 1 - z>0 raised  with dx=dy=0.0
            # 2 - z<0 plunged with dx=dy=0.0
            cmd = CNC.parseLine(line)
            if cmd is None:
                newlines.append(line)
                continue
            self.cnc.motionStart(cmd)
            xyz = self.cnc.motionPath()
            if self.cnc.dx==0.0 and self.cnc.dy==0.0:
                if self.cnc.z>0.0 and self.cnc.dz>0.0:
                    last = len(newlines)
                elif self.cnc.z<0.0 and self.cnc.dz<0.0 and last>=0:
                    for i in range(last,len(newlines)):
                        s = newlines[i]
                        if s and s[0] != '(':
                            newlines[i] = "({0})".format(s)
                    last = -1
            else:
                last = -1
            newlines.append(line)
            self.cnc.motionEnd()

        self.addUndo(self.setLinesUndo(newlines))

    #----------------------------------------------------------------------
    # Remove the line number for lines
    #----------------------------------------------------------------------
    def removeNlines(self, items):
        pass

    #----------------------------------------------------------------------
    # Re-arrange using genetic algorithms a set of blocks to minimize
    # rapid movements.
    #----------------------------------------------------------------------
    def optimize(self, items):
        n = len(items)

        matrix = []
        for i in range(n):
            matrix.append([0.0] * n)

        # Find distances between blocks (end to start)
        for i in range(n):
            block = self.blocks[items[i]]
            x1 = block.ex
            y1 = block.ey
            for j in range(n):
                if i==j: continue
                block = self.blocks[items[j]]
                x2 = block.sx
                y2 = block.sy
                dx = x1-x2
                dy = y1-y2
                #Compensate for machines, which have different speed of X and Y:
                dx/= OCV.feedmax_x
                dy/= OXV.feedmax_y
                matrix[i][j] = sqrt(dx*dx + dy*dy)
        #from pprint import pprint
        #pprint(matrix)

        best = [0]
        unvisited = range(1,n)
        while unvisited:
            last = best[-1]
            row = matrix[last]
            # from all the unvisited places search the closest one
            mindist = 1e30
            for i,u in enumerate(unvisited):
                d = row[u]
                if d < mindist:
                    mindist = d
                    si = i
            best.append(unvisited.pop(si))
        #print "best=",best

        undoinfo = []
        for i in range(len(best)):
            b = best[i]
            if i==b: continue
            ptr = best.index(i)
            # swap i,b in items
            undoinfo.append(self.swapBlockUndo(items[i], items[b]))
            # swap i,ptr in best
            best[i], best[ptr] = best[ptr], best[i]
        self.addUndo(undoinfo, "Optimize")

    #----------------------------------------------------------------------
    # Use probe information to modify the g-code to autolevel
    #----------------------------------------------------------------------
    def compile(self, queue, stopFunc=None):
        #lines  = [self.cnc.startup]
        paths   = []

        def add(line, path):
            if line is not None:
                if isinstance(line,str) or isinstance(line,unicode):
                    queue.put(line+"\n")
                else:
                    queue.put(line)
            paths.append(path)
        autolevel = not self.probe.isEmpty()
        self.initPath()
        for line in CNC.compile(OCV.startup.splitlines()):
            add(line, None)

        every = 1
        for i,block in enumerate(self.blocks):
            if not block.enable: continue
            for j,line in enumerate(block):
                every -= 1
                if every<=0:
                    if stopFunc is not None and stopFunc():
                        return None
                    every = 50

                newcmd = []
                cmds = CNC.compileLine(line)
                if cmds is None:
                    continue
                elif isinstance(cmds,str) or isinstance(cmds,unicode):
                    cmds = CNC.breakLine(cmds)
                else:
                    # either CodeType or tuple, list[] append at it as is
                    #lines.append(cmds)
                    if isinstance(cmds,types.CodeType) or isinstance(cmds,int):
                        add(cmds, None)
                    else:
                        add(cmds, (i,j))
                    continue

                skip   = False
                expand = None
                self.cnc.motionStart(cmds)

                # FIXME append feed on cut commands. It will be obsolete in grbl v1.0
                if OCV.appendFeed and self.cnc.gcode in (1,2,3):
                    # Check is not existing in cmds
                    for c in cmds:
                        if c[0] in ('f','F'):
                            break
                    else:
                        cmds.append(self.fmt('F',self.cnc.feed/self.cnc.unit))

                if autolevel and self.cnc.gcode in (0,1,2,3) and self.cnc.mval==0:
                    xyz = self.cnc.motionPath()
                    if not xyz:
                        # while auto-levelling, do not ignore non-movement
                        # commands, just append the line as-is
                        #lines.append(line)
                        #paths.append(None)
                        add(line, None)
                    else:
                        extra = ""
                        for c in cmds:
                            if c[0].upper() not in ('G','X','Y','Z','I','J','K','R'):
                                extra += c
                        x1,y1,z1 = xyz[0]
                        if self.cnc.gcode == 0:
                            g = 0
                        else:
                            g = 1
                        for x2,y2,z2 in xyz[1:]:
                            for x,y,z in self.probe.splitLine(x1,y1,z1,x2,y2,z2):
                                add("G%d%s%s%s%s"%\
                                    (g,
                                     self.fmt('X',x/self.cnc.unit),
                                     self.fmt('Y',y/self.cnc.unit),
                                     self.fmt('Z',z/self.cnc.unit),
                                     extra),
                                    (i,j))
                                extra = ""
                            x1,y1,z1 = x2,y2,z2
                    self.cnc.motionEnd()
                    continue
                else:
                    # FIXME expansion policy here variable needed
                    # Canned cycles
                    if OCV.drillPolicy==1 and \
                       self.cnc.gcode in (81,82,83,85,86,89):
                        expand = self.cnc.macroGroupG8X()
                    # Tool change
                    elif self.cnc.mval == 6:
                        if OCV.toolPolicy == 0:
                            pass    # send to grbl
                        elif OCV.toolPolicy == 1:
                            skip = True    # skip whole line
                        elif OCV.toolPolicy >= 2:
                            expand = CNC.compile(self.cnc.toolChange())
                    self.cnc.motionEnd()

                if expand is not None:
                    for line in expand:
                        add(line, None)
                    expand = None
                    continue
                elif skip:
                    skip = False
                    continue

                for cmd in cmds:
                    c = cmd[0]
                    try:
                        value = float(cmd[1:])
                    except Exception:
                        value = 0.0

                    if c.upper() in ("F","X","Y","Z","I","J","K","R","P"):
                        cmd = self.fmt(c,value)
                    else:
                        opt = ERROR_HANDLING.get(cmd.upper(),0)

                        if opt == SKIP:
                            cmd = None

                    if cmd is not None:
                        newcmd.append(cmd)

                add("".join(newcmd), (i,j))

        return paths

#if __name__=="__main__":
#    orient = Orient()
#    orient.add(  0,  0, 100, 50)
#    orient.add( 50, 10, 150, 60)
#    orient.add(100, 20, 200, 70)
#    phi,xo,yo = orient.solve()
#    print phi,degrees(phi),xo,yo
#
#    orient.clear()
#    orient.add(  0,  0, -50, 100)
#    orient.add( 50, 10, -60, 150)
#    orient.add(100, 20, -70, 200)
#    phi,xo,yo = orient.solve()
#    print phi,degrees(phi),xo,yo
#
#    import pdb; pdb.set_trace()
#    #print Block.operationName("door","in")
#    print Block.operationName("door [in:2,cut:0.1]","cut:0.5")
#    print Block.operationName("door [in:2,cut:0.1]","in")
