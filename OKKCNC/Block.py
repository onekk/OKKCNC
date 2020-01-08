#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Block.py

    splitted from CNC.py

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

import re
import Unicode

import OCV


class Block(list):
    """
    Block of g-code commands. A gcode file is represented as a list of blocks
     - Commands are grouped as (non motion commands Mxxx)
     - Basic shape from the first rapid move command to the last rapid z raise
       above the working surface
    -
     Inherits from list and contains:
        - a list list of gcode lines - (imported shape)
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
        self.sx = self.sy = self.sz = 0  # start  coordinates

        self.ex = self.ey = self.ez = 0  # ending coordinates
        self.resetPath()

    def copy(self, src):
        """Copy a Block"""
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
        """return Block Name or None"""
        return self._name is None and "block" or self._name

    def nameNop(self):
        """@return name without the operation"""
        name = self.name()
        pat = OCV.OPPAT.match(name)
        if pat is None:
            return name
        else:
            return pat.group(1).strip()

    def operationTest(self, op, name=None):
        """Tests if block contains operation type"""
        if name is None:
            name = self.name()

        pat = OCV.OPPAT.match(name)
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

        pat = OCV.OPPAT.match(name)
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
        pat = OCV.OPPAT.match(name)
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
        """Compose the block header
        do not confuse with 'header block'
        """
        header = ''
        header += "(Block-name:  {0})\n".format(self.name())
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
        """Return a dump object for json"""
        return self.name(), self.enable, self.expand, self.color, self

    @staticmethod
    def load(obj):
        """Create a block from a dump object from json"""
        name, enable, expand, color, code = obj
        block = Block(name)
        block.enable = enable
        block.expand = expand
        block.color = color
        block.extend(code)
        return block

    def append(self, line):
        if line.startswith("(Block-"):
            pat = OCV.BLOCKPAT.match(line)
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
            pat = OCV.IDPAT.match(line)

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
