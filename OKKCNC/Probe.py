#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Probe.py

    splitted from CNC.py

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import os
import math
import OCV
from bstl import Binary_STL_Writer


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
                    raise ValueError("Line is empty")

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

        lines.append("G0 {0:0.f} {1:0.f}".format(self.xmin, self.ymin))
        lines.append("G0 {0:0.f} {1:0.f}".format(self.xmin, self.ymax))
        lines.append("G0 {0:0.f} {1:0.f}".format(self.xmax, self.ymax))
        lines.append("G0 {0:0.f} {1:0.f}".format(self.xmax, self.ymin))
        lines.append("G0 {0:0.f} {1:0.f}".format(self.xmin, self.ymin))

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
