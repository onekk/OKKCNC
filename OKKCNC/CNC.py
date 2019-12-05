# -*- coding: ascii -*-
"""CNC.py

Credits:
    this module code is based on bCNC
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

# import os
# import re
import math

import OCV
# import Probe
# import Block

# from dxf import DXF

import bmath
# from copy import deepcopy
# from svgcode import SVGcode

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


def getValue(name, new, old, default=0.0):
    """Return a value combined from two dictionaries new/old"""

    try:
        return new[name]
    except Exception:
        try:
            return old[name]
        except Exception:
            return default


class Orient(object):
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
            c, s, self.xo, self.yo = bmath.solveOverDetermined(
                bmath.Matrix(A),
                bmath.Matrix(B))
        except Exception:
            raise Exception("Unable to solve system")

        # print "c,s,xo,yo=",c,s,xo,yo

        # Normalize the coefficients
        r = math.sqrt(c*c + s*s)  # length should be 1.0
        if abs(r-1.0) > 0.1:
            raise Exception("Resulting system is too skew")

        # print "r=",r
        # xo /= r
        # yo /= r
        self.phi = math.atan2(s, c)

        if abs(self.phi) < OCV.TOLERANCE:
            self.phi = 0.0  # rotation

        self.valid = True

        return self.phi, self.xo, self.yo

    def error(self):
        """@return minimum, average and maximum error"""
        # Type errors
        minerr = 1e9
        maxerr = 0.0
        sumerr = 0.0

        c = math.cos(self.phi)
        s = math.sin(self.phi)

        del self.errors[:]

        for i, (xm, ym, x, y) in enumerate(self.markers):
            dx = c*x - s*y + self.xo - xm
            dy = s*x + c*y + self.yo - ym
            err = math.sqrt(dx**2 + dy**2)
            self.errors.append(err)

            minerr = min(minerr, err)
            maxerr = max(maxerr, err)
            sumerr += err

        return minerr, sumerr/float(len(self.markers)), maxerr

    def gcode2machine(self, x, y):
        """Convert gcode to machine coordinates"""
        c = math.cos(self.phi)
        s = math.sin(self.phi)
        return c*x - s*y + self.xo, s*x + c*y + self.yo

    def machine2gcode(self, x, y):
        """Convert machine to gcode coordinates"""
        c = math.cos(self.phi)
        s = math.sin(self.phi)
        x -= self.xo
        y -= self.yo
        return c*x + s*y, -s*x + c*y

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


class CNC(object):
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
            OCV.ERROR_HANDLING["G98"] = 1
            OCV.ERROR_HANDLING["G99"] = 1

        for cmd, value in config.items(section):
            try:
                OCV.ERROR_HANDLING[cmd.upper()] = int(value)
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
        self.plane = OCV.XY
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
    def gcode_string(g, pairs):
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
        return CNC.gcode_string(g, pairs)

    @staticmethod
    def garcv(g, v, ijk):
        return CNC.gcode_string(g, zip("XYZ", v) + zip("IJ", ijk[:2]))

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
        line = OCV.PARENPAT.sub("", line)
        line = OCV.SEMIPAT.sub("", line)

        # process command
        # strip all spaces
        line = line.replace(" ", "")

        # Insert space before each command
        line = OCV.CMDPAT.sub(r" \1", line).lstrip()
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
            pat = OCV.AUXPAT.match(line.strip())

            if pat:
                cmd = pat.group(1)
                args = pat.group(2)
            else:
                cmd = None
                args = None

            if cmd == "%wait":
                return (OCV.WAIT,)
            elif cmd == "%msg":

                if not args:
                    args = None

                return (OCV.MSG, args)
            elif cmd == "%update":
                return (OCV.UPDATE, args)
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
        line = OCV.CMDPAT.sub(r" \1", line).lstrip()
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
                    self.plane = OCV.XY

                elif gcode == 18:
                    self.plane = OCV.XZ

                elif gcode == 19:
                    self.plane = OCV.YZ

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
            if self.plane == OCV.XY:
                x = self.x
                y = self.y
                xv = self.xval
                yv = self.yval
            elif self.plane == OCV.XZ:
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

            if self.plane == OCV.XY:
                return xc, yc
            elif self.plane == OCV.XZ:
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
            if self.plane == OCV.XY:
                u0 = self.x
                v0 = self.y
                w0 = self.z
                u1 = self.xval
                v1 = self.yval
                w1 = self.zval
            elif self.plane == OCV.XZ:
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
                    if self.plane == OCV.XY:
                        xyz.append((u, v, w))
                    elif self.plane == OCV.XZ:
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

                    if self.plane == OCV.XY:
                        xyz.append((u, v, w))
                    elif self.plane == OCV.XZ:
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
            print("clearz=", clearz)
            print("drill=",drill)
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
    def compile_pgm(program):
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
                    opt = OCV.ERROR_HANDLING.get(cmd.upper(), 0)

                    if opt == OCV.SKIP:
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
                "%msg Tool change T{0:2d} {1}".format(
                    self.tool,
                    OCV.comment))
        else:
            lines.append(
                "%msg Tool change T{0:2d}".format(self.tool))

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
