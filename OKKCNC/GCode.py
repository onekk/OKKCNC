#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""GCode.py

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
import re
import types

from time import strftime, localtime

import OCV
from Block import Block
import Heuristic
import Probe
import bmath
import undo

from CNC import CNC, Orient, get_dict_value
from bpath import Path, Segment  # eq,


class GCode(object):
    """Gcode file"""
    LOOP_MERGE = False

    def __init__(self):
        self.cnc = CNC()
        self.undoredo = undo.UndoRedo()
        self.probe = Probe.Probe()
        self.orient = Orient()
        self.vars = {}  # local variables
        self.init()

    def init(self):
        """Reusable part of GCode initialisation"""
        self.filename = ""
        self.header = ""
        self.footer = ""

        OCV.blocks = []  # list of blocks
        # dummy values for min_z and max_z to correctly test when setted
        OCV.max_z = -9999
        OCV.min_z = 10000
        # TODO: maybe this could be used to name the blocks ?
        OCV.gcp_mop_name = ""
        #
        OCV.gcodelines = ["(-)",]  # Add a starting 0 pos to better align index
        self.vars.clear()
        self.undoredo.reset()
        # FIXME check if this is needed
        # self.probe.init()

        self._lastModified = 0
        self._modified = False

    def calculateEnableMargins(self):
        """Recalculate enabled path margins"""
        self.cnc.resetEnableMargins()
        for block in OCV.blocks:
            if block.enable:
                OCV.CD["xmin"] = min(OCV.CD["xmin"], block.xmin)
                OCV.CD["ymin"] = min(OCV.CD["ymin"], block.ymin)
                OCV.CD["zmin"] = min(OCV.CD["zmin"], block.zmin)
                OCV.CD["xmax"] = max(OCV.CD["xmax"], block.xmax)
                OCV.CD["ymax"] = max(OCV.CD["ymax"], block.ymax)
                OCV.CD["zmax"] = max(OCV.CD["zmax"], block.zmax)

    def isModified(self):
        """return internal _modifiedvalue"""
        return self._modified

    def resetModified(self):
        """reset internal _modified"""
        self._modified = False

    def __getitem__(self, item):
        """get block item"""
        return OCV.blocks[item]

    def __setitem__(self, item, value):
        """set block item"""
        OCV.blocks[item] = value

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

    def parse_gcode(self, filename, adv_heur=False):
        """scan lines from gcodelines and parse them to create
        a proper OCV.blocks structure
        """

        if OCV.DEBUG_PAR is True:
            OCV.printout_header("Scanning {0}", filename)

        # preprocess file to find a Post processor marker
        prcs = True
        l_idx = 1
        l_bound = min(10, len(OCV.gcodelines))
        while prcs is True:
            line = OCV.gcodelines[l_idx]

            if line.startswith("( ver: okk-"):
                OCV.g_code_pp = "CamBam-OKK"
            else:
                pass

            if l_idx < (l_bound - 1):
                l_idx += 1
            else:
                prcs = False

        # act depending on prostprocessor marker
        # for now only 'CamBam-OKK' is implemented, using 'custom' grbl.cbpp
        # file as postprocessor in CamBam
        # others could be implemented if relevant information are supplied
        if OCV.g_code_pp in ("CamBam-OKK",):
            self.pre_process_gcode()
        else:
            # Plain Gcode file or not implemented "generators" are processed
            # using "add_line" method, in this case the g_code_pp value is
            # left 'Generic' as set in OCV file
            for line in OCV.gcodelines:
                self.add_line(line)

        Heuristic.trim_blocks()

        if OCV.DEBUG_PAR is True:
            OCV.printout_header("{0}", "END SCAN")

    def debug_info(self, line, move, move_s, move_f, delta_z):

        print(line)

        if (move_s[0], move_s[1]) != (move_f[0], move_f[1]):
            print("Motion {} Move start = {} \nMove end = {}".format(
                    move, move_s, move_f))
            print("Delta Z = ", delta_z)
        else:
            if delta_z > 0:
                print("Z_UP Move from {} to {} at X{} Y{}".format(
                        move_s[2], move_f[2], move_s[0], move_s[1]))
                print("Delta Z = {}".format(delta_z))
            elif delta_z < 0:
                print("Z_DOWN Move from {} to {} at X{} Y{}".format(
                        move_s[2], move_f[2], move_s[0], move_s[1]))
                print("Delta Z = {}".format(delta_z))
            else:
                print("Stationary Move at Point {}".format(move_s))

        print(OCV.str_sep)

    def pre_process_gcode(self):
        """scan gcode lines and inject some metadata, it create only one Block.
        The main scope is to populate OCV.blocks_ev list used in later
        elaboration done by Heuristic.process_blocks().
        See the Documentation in Heuristic.process_blocks() for more info.
        """
        # DEBUG_INFO activation only for this method
        INT_DEBUG = False
        OCV.infos = []

        process = True
        l_idx = -1
        OCV.blocks_ev = ["",]

        while process is True:
            if l_idx < (len(OCV.gcodelines) - 1):
                l_idx += 1
            else:
                # continue here is to force the loop to terminate here
                # if not present last line is scanned again
                process = False
                continue

            line = OCV.gcodelines[l_idx]

            if INT_DEBUG is True:
                print("{0} Line > {1}".format(l_idx, line))

                if l_idx == (len(OCV.gcodelines) - 1):
                    print("last line fo gcode")

            # discard the dummy first item
            if line.startswith("(-)"):
                continue

            if not OCV.blocks:
                OCV.blocks.append(Block("Header"))

            # events are processes later

            if line[:10] == "(MOP Start":
                OCV.blocks_ev.append(
                    ("MS", l_idx, line,
                     ((self.cnc.x, self.cnc.y, self.cnc.z),
                      self.cnc.zval,
                      (self.cnc.dx, self.cnc.dy, self.cnc.dz))))
                OCV.blocks[-1].append(line)
                continue

            if line[:8] == "(MOP End":
                # if there is a MOP end
                OCV.blocks_ev.append(
                    ("ME", l_idx, line,
                     ((self.cnc.x, self.cnc.y, self.cnc.z),
                      self.cnc.zval,
                      (self.cnc.dx, self.cnc.dy, self.cnc.dz))))
                OCV.blocks[-1].append(line)
                continue

            cmds = Heuristic.parse_line(line)
            # Debug infos do not delete
            # print(cmds)

            if cmds is None:
                # the line contains comments or no valid commands
                OCV.blocks[-1].append(line)
                continue

            # self.cnc.motionStart(cmds), analyze the move and populate the
            # positions, but the action is ended by sel.cnc.motionEnd(cmds)
            # in some condition the self.cnc.x(yz) variables hold a different
            # value at the start and at the end of operation, theese values
            # are both significative for the event, so this block of code
            # take care to "generate" the start value and the end value for
            # each line

            self.cnc.motionStart(cmds)
            move = cmds[0]
            move_s = (self.cnc.x, self.cnc.y, self.cnc.z)
            move_s_dz = self.cnc.dz

            self.cnc.motionEnd()
            move_f = (self.cnc.x, self.cnc.y, self.cnc.z)

            # at this point we have all the motion infos neede to generate
            # properly an event

            delta_z = move_f[2] - move_s[2]
            move_c = ((move_s[0], move_s[1], move_s[2]), delta_z,
                      (move_f[0], move_f[1], move_f[2]))

            OCV.min_z = min(OCV.min_z, move_f[2])
            OCV.max_z = max(OCV.max_z, move_f[2])

            # debug info useful only for development
            self.debug_info(line, move, move_s, move_f, delta_z)

            # analyze moves
            if move in ("G1", "G2", "G3"):
                # 'cut move' with feedrate
                if cmds[1][0] == "F":
                    if cmds[2][0] == "Z":
                        ev_label = "GMZ"
                    else:
                        ev_label = "GMXY"
                    OCV.blocks_ev.append(
                            (ev_label, l_idx, line, move_c, cmds))
                    OCV.blocks[-1].append(line)
                    continue
                else:
                    # 'cut move' with no feedrate, generally a plain move no
                    # event to process
                    OCV.blocks[-1].append(line)
            elif move == "G0":
                # original code using self.cnc.gcode == 0
                # will also detect come G0 move that don't contains Z value
                # leading to some 'false' positive
                if cmds[1][0] == "Z" and move_s_dz > 0.0:
                    # rapid Z move up detected
                    OCV.blocks_ev.append(("ZU", l_idx, line, move_c))
                    OCV.blocks[-1].append(line)
                    continue
                elif cmds[1][0] == "Z" and move_s_dz < 0:
                    # rapid Z move down detected
                    OCV.blocks_ev.append(("ZD", l_idx, line, move_c))
                    OCV.blocks[-1].append(line)
                elif cmds[1][0] == "Z" and move_s_dz == 0:
                    # Z neutral move this catch G0 Z(same level of prior move)
                    # that sometimes could appear in code
                    OCV.blocks_ev.append(("ZN", l_idx, line, move_c))
                    OCV.blocks[-1].append(line)
                else:
                    # a normal G0 move is detected
                    # this could catch "G0 Zxx" moves
                    OCV.blocks_ev.append(("G0", l_idx, line, move_c, cmds))
                    OCV.blocks[-1].append(line)
                    continue
            elif move in OCV.end_cmds:
                # catch the end commands
                OCV.blocks_ev.append((move, l_idx, line, move_c))
                OCV.blocks[-1].append(line)
            else:
                # other 'moves' T, M () not catched as end_cmds and S
                OCV.blocks[-1].append(line)

        # one line to pass the work to Heuristic module single that take care
        # of susbsequent work on parsing and block splitting
        Heuristic.process_blocks()

    def add_line(self, line):
        """plain addLine method from bCNC
        used by setLinesUndo method and if no postprocessor is detected in
        GCode file
        """
        if line.startswith("(-)"):
            return

        if line.startswith("(Block-name:"):
            self._blocksExist = True
            pat = OCV.RE_BLOCK.match(line)
            if pat:
                value = pat.group(2).strip()
                if not OCV.blocks or len(OCV.blocks[-1]):
                    OCV.blocks.append(Block(value))
                else:
                    OCV.blocks[-1].b_name = value
                return

        if not OCV.blocks:
            OCV.blocks.append(Block("Header"))

        cmds = Heuristic.parse_line(line)
        if cmds is None:
            OCV.blocks[-1].append(line)
            return

        self.cnc.motionStart(cmds)

        # rapid move up = end of block
        if self._blocksExist:
            OCV.blocks[-1].append(line)
        elif self.cnc.gcode == 0 and self.cnc.dz > 0.0:
            OCV.blocks[-1].append(line)
            OCV.blocks.append(Block())
        elif self.cnc.gcode == 0 and len(OCV.blocks) == 1:
            OCV.blocks.append(Block())
            OCV.blocks[-1].append(line)
        else:
            OCV.blocks[-1].append(line)

        self.cnc.motionEnd()

    def load(self, filename=None):
        """Load a file into editor"""
        if filename is None:
            filename = self.filename

        self.init()
        self.filename = filename

        try:
            f_handle = open(self.filename, "r")
        except Exception as e:
            return False

        self._lastModified = os.stat(self.filename).st_mtime

        self.cnc.initPath()
        self.cnc.resetAllMargins()
        self._blocksExist = False

        for line in f_handle:
            # Add line to the gcodelines used for display and heuristic
            OCV.gcodelines.append(line[:-1].replace("\x0d", ""))

        f_handle.close()

        self.parse_gcode(filename, False)

        return True

    def save(self, filename=None):
        """Save to a file"""
        if filename is not None:
            self.filename = filename

        try:
            f = open(self.filename, "w")
        except Exception:
            return False

        for block in OCV.blocks:
            block.write(f)
        f.close()
        self._lastModified = os.stat(self.filename).st_mtime
        self._modified = False
        return True

    def saveNGC(self, filename, comments=False):
        """Save in NGC format
        Cleaned from Block OKKCNC metadata with or without comments
        """
        f_handle = open(filename, 'w')
        for block in OCV.blocks:
            # print(block.enable)
            if block.enable:
                for line in block:
                    if comments is False:
                        cmds = Heuristic.parse_line(line)
                        # print(cmds)
                        if cmds is None:
                            continue

                    f_handle.write("{0}\n".format(line))

        f_handle.close()
        return True

    def saveOKK(self, filename):
        """Save in OKK format
        with OKKCNC metadata and comments
        """
        okkf = open(filename, 'w')
        for block in OCV.blocks:
            block.write(okkf)
        okkf.close()
        return True

    def addBlockFromString(self, name, text):

        if not text:
            return

        block = Block(name)
        block.extend(text.splitlines())
        OCV.blocks.append(block)

    def headerFooter(self):
        """Check if Block is empty:
             If empty insert a header and a footer
            """
        if not OCV.blocks:
            currDate = strftime("%Y-%m-%d - %H:%M:%S", localtime())
            curr_header = "(Created By {0} version {1}) \n".format(
                OCV.PRG_NAME, OCV.PRG_VER)
            curr_header += "(Date: {0})\n".format(currDate)
            curr_header += self.header

            self.addBlockFromString("Header", curr_header)
            self.addBlockFromString("Footer", self.footer)
            return True
        return False

    def toPath(self, bid):
        """convert a block to path"""
        block = OCV.blocks[bid]
        paths = []
        path = Path(block.name())
        self.initPath(bid)
        start = bmath.Vector(self.cnc.x, self.cnc.y)

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

            cmds = Heuristic.parse_line(line)

            if cmds is None:
                continue

            self.cnc.motionStart(cmds)
            end = bmath.Vector(self.cnc.xval, self.cnc.yval)
            if self.cnc.gcode == 0:  # rapid move (new block)
                if path:
                    paths.append(path)
                    path = Path(block.name())
            elif self.cnc.gcode == 1:  # line
                if self.cnc.dx != 0.0 or self.cnc.dy != 0.0:
                    path.append(Segment(1, start, end))
            elif self.cnc.gcode in (2, 3):  # arc
                xc, yc = self.cnc.motionCenter()
                center = bmath.Vector(xc, yc)
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

    def syncFileTime(self):
        """sync file timestamp"""
        try:
            self._lastModified = os.stat(self.filename).st_mtime
        except Exception:
            return False

    def checkFile(self):
        """Check if a new version exists"""
        try:
            return os.stat(self.filename).st_mtime > self._lastModified
        except Exception:
            return False

    def undo(self):
        """Undo operation"""
        # print ">u>",self.undoredo.undoText()
        self.undoredo.undo()

    def redo(self):
        """Redo operation"""
        # print ">r>",self.undoredo.redoText()
        self.undoredo.redo()

    def addUndo(self, undoinfo, msg=None):

        if not undoinfo:
            return

        self.undoredo.add(undoinfo, msg)
        self._modified = True

    def canUndo(self):
        return self.undoredo.canUndo()

    def canRedo(self):
        return self.undoredo.canRedo()

    def setLinesUndo(self, lines):
        """Change all lines in editor"""
        undoinfo = (self.setLinesUndo, list(self.lines()))
        # Delete all blocks and create new ones
        del OCV.blocks[:]
        self.cnc.initPath()
        self._blocksExist = False

        for line in lines:
            self.add_line(line)

        Heuristic.trim_blocks()
        return undoinfo

    def setAllBlocksUndo(self, blocks=[]):
        undoinfo = [self.setAllBlocksUndo, OCV.blocks]
        OCV.blocks = blocks
        return undoinfo

    def setLineUndo(self, bid, lid, line):
        """Change a single line in a block"""
        undoinfo = (self.setLineUndo, bid, lid, OCV.blocks[bid][lid])
        OCV.blocks[bid][lid] = line
        return undoinfo

    def insLineUndo(self, bid, lid, line):
        """Insert a new line into block"""
        undoinfo = (self.delLineUndo, bid, lid)
        block = OCV.blocks[bid]

        if lid >= len(block):
            block.append(line)
        else:
            block.insert(lid, line)

        return undoinfo

    def cloneLineUndo(self, bid, lid):
        """Clone line inside a block"""
        return self.insLineUndo(bid, lid, OCV.blocks[bid][lid])

    def delLineUndo(self, bid, lid):
        """Delete line from block"""
        block = OCV.blocks[bid]
        undoinfo = (self.insLineUndo, bid, lid, block[lid])
        del block[lid]
        return undoinfo

    def addBlockUndo(self, bid, block):
        """Add a block"""

        if bid is None:
            bid = len(OCV.blocks)

        if bid >= len(OCV.blocks):
            undoinfo = (self.delBlockUndo, len(OCV.blocks))
            OCV.blocks.append(block)
        else:
            undoinfo = (self.delBlockUndo, bid)
            OCV.blocks.insert(bid, block)
        return undoinfo

    def cloneBlockUndo(self, bid, pos=None):
        """Clone a block"""
        if pos is None:
            pos = bid

        return self.addBlockUndo(pos, Block(OCV.blocks[bid]))

    def delBlockUndo(self, bid):
        """Delete a whole block"""
        block = OCV.blocks.pop(bid)
        undoinfo = (self.addBlockUndo, bid, block)
        return undoinfo

    def insBlocksUndo(self, bid, blocks):
        """Insert a list of other blocks from another gcode file probably"""
        if bid is None or bid >= len(OCV.blocks):
            bid = len(OCV.blocks)
        undoinfo = ("Insert blocks", self.delBlocksUndo, bid, bid+len(blocks))
        OCV.blocks[bid:bid] = blocks
        return undoinfo

    def delBlocksUndo(self, from_, to_):
        """Delete a range of blocks"""
        blocks = OCV.blocks[from_:to_]
        undoinfo = ("Delete blocks", self.insBlocksUndo, from_, blocks)
        del OCV.blocks[from_:to_]
        return undoinfo

    def insBlocks(self, bid, blocks, msg=""):
        """Insert blocks and push the undo info"""
        if self.headerFooter():    # just in case
            bid = 1
        self.addUndo(self.insBlocksUndo(bid, blocks), msg)

    def setBlockExpandUndo(self, bid, expand):
        """Set block expand"""
        undoinfo = (self.setBlockExpandUndo, bid, OCV.blocks[bid].expand)
        OCV.blocks[bid].expand = expand
        return undoinfo

    def setBlockEnableUndo(self, bid, enable):
        """Set block state"""
        undoinfo = (self.setBlockEnableUndo, bid, OCV.blocks[bid].enable)
        OCV.blocks[bid].enable = enable
        return undoinfo

    def setBlockColorUndo(self, bid, color):
        """Set block color"""
        undoinfo = (self.setBlockColorUndo, bid, OCV.blocks[bid].color)
        OCV.blocks[bid].color = color
        return undoinfo

    def swapBlockUndo(self, a, b):
        """Swap two blocks"""
        undoinfo = (self.swapBlockUndo, a, b)
        tmp = OCV.blocks[a]
        OCV.blocks[a] = OCV.blocks[b]
        OCV.blocks[b] = tmp
        return undoinfo

    def moveBlockUndo(self, src, dst):
        """Move block from location src to location dst"""
        if src == dst:
            return None

        undoinfo = (self.moveBlockUndo, dst, src)

        if dst > src:
            OCV.blocks.insert(dst-1, OCV.blocks.pop(src))
        else:
            OCV.blocks.insert(dst, OCV.blocks.pop(src))

        return undoinfo

    def invertBlocksUndo(self, blocks):
        """Invert selected blocks"""
        undoinfo = []
        first = 0
        last = len(blocks) - 1
        while first < last:
            undoinfo.append(self.swapBlockUndo(blocks[first], blocks[last]))
            first += 1
            last = 1
        return undoinfo

    def orderUpBlockUndo(self, bid):
        """Move block upwards"""
        if bid == 0:
            return None
        undoinfo = (self.orderDownBlockUndo, bid - 1)
        # swap with the block above
        before = OCV.blocks[bid-1]
        OCV.blocks[bid-1] = OCV.blocks[bid]
        OCV.blocks[bid] = before
        return undoinfo

    def orderDownBlockUndo(self, bid):
        """Move block downwards"""
        if bid >= len(OCV.blocks) - 1:
            return None
        undoinfo = (self.orderUpBlockUndo, bid+1)
        # swap with the block below
        after = self[bid+1]
        self[bid+1] = self[bid]
        self[bid] = after
        return undoinfo

    def insBlockLinesUndo(self, bid, lines):
        """Insert block lines"""
        undoinfo = (self.delBlockLinesUndo, bid)
        block = Block()
        for line in lines:
            block.append(line)
        OCV.blocks.insert(bid, block)
        return undoinfo

    def delBlockLinesUndo(self, bid):
        """Delete a whole block lines"""
        lines = [x for x in OCV.blocks[bid]]
        undoinfo = (self.insBlockLinesUndo, bid, lines)
        del OCV.blocks[bid]
        return undoinfo

    def setBlockNameUndo(self, bid, name):
        """Set Block name"""
        undoinfo = (self.setBlockNameUndo, bid, OCV.blocks[bid].b_name)
        OCV.blocks[bid].b_name = name
        return undoinfo

    def addBlockOperationUndo(self, bid, operation, remove=None):
        """Add an operation code in the name as [drill, cut, in/out...]"""
        undoinfo = (self.setBlockNameUndo, bid, OCV.blocks[bid].b_name)
        OCV.blocks[bid].addOperation(operation, remove)
        return undoinfo

    def setBlockLinesUndo(self, bid, lines):
        """Replace the lines of a block"""
        block = OCV.blocks[bid]
        undoinfo = (self.setBlockLinesUndo, bid, block[:])
        del block[:]
        block.extend(lines)
        return undoinfo

    def orderUpLineUndo(self, bid, lid):
        """Move line upwards"""
        if lid == 0:
            return None

        block = OCV.blocks[bid]
        undoinfo = (self.orderDownLineUndo, bid, lid-1)
        block.insert(lid-1, block.pop(lid))
        return undoinfo

    def orderDownLineUndo(self, bid, lid):
        """Move line downwards"""
        block = OCV.blocks[bid]

        if lid >= len(block) - 1:
            return None

        undoinfo = (self.orderUpLineUndo, bid, lid+1)
        block.insert(lid+1, block.pop(lid))
        return undoinfo

    def autolevelBlock(self, block):
        """Expand block with autolevel information"""
        new = []
        autolevel = not self.probe.isEmpty()
        for line in block:
            # newcmd = [] # seems to be not used
            cmds = CNC.compileLine(line)
            if cmds is None:
                new.append(line)
                continue
            elif isinstance(cmds, str):
                cmds = CNC.breakLine(cmds)
            else:
                new.append(line)
                continue

            self.cnc.motionStart(cmds)

            if autolevel and self.cnc.gcode in (0, 1, 2, 3) and\
                  self.cnc.mval == 0:

                xyz = self.cnc.motionPath()

                if not xyz:
                    # while auto-levelling, do not ignore non-movement
                    # commands, just append the line as-is
                    new.append(line)
                else:
                    extra = ""
                    for c in cmds:
                        if c[0].upper() not in (
                            'G', 'X', 'Y', 'Z',
                            'I', 'J', 'K', 'R'):

                            extra += c

                    x1, y1, z1 = xyz[0]

                    if self.cnc.gcode == 0:
                        g = 0
                    else:
                        g = 1

                    for x2, y2, z2 in xyz[1:]:
                        for x, y, z in self.probe.splitLine(
                                x1, y1, z1, x2, y2, z2):

                            new.append("G{0:d} {1} {2} {3} {4}".format(
                                g,
                                OCV.fmt('X', x/OCV.unit),
                                OCV.fmt('Y', y/OCV.unit),
                                OCV.fmt('Z', z/OCV.unit),
                                extra))

                            extra = ""
                        x1, y1, z1 = x2, y2, z2
                self.cnc.motionEnd()
            else:
                self.cnc.motionEnd()
                new.append(line)
        return new

    def autolevel(self, items):
        """Execute autolevel on selected blocks"""
        undoinfo = []
        operation = "autolevel"
        for bid in items:
            block = OCV.blocks[bid]

            if block.name() in ("Header", "Footer"):
                continue

            if not block.enable:
                continue

            lines = self.autolevelBlock(block)
            undoinfo.append(self.addBlockOperationUndo(bid, operation))
            undoinfo.append(self.setBlockLinesUndo(bid, lines))

        if undoinfo:
            self.addUndo(undoinfo)

    def __repr__(self):
        """Return string representation of whole file"""
        return "\n".join(list(self.lines()))

    def iterate(self, items):
        """Iterate over the items"""
        for bid, lid in items:
            if lid is None:
                block = OCV.blocks[bid]
                for i in range(len(block)):
                    yield bid, i
            else:
                yield bid, lid

    def lines(self):
        """Iterate over all lines"""
        for block in OCV.blocks:
            for line in block:
                yield line

    def initPath(self, bid=0):
        """initialize cnc path based on block bid"""
        if bid == 0:
            self.cnc.initPath()
        else:
            # Use the ending point of the previous block
            # since the starting (sxyz is after the rapid motion)
            block = OCV.blocks[bid-1]
            self.cnc.initPath(block.ex, block.ey, block.ez)

    def orderUp(self, items):
        """Move blocks/lines up"""
        sel = []  # new selection
        undoinfo = []
        for bid, lid in items:
            if isinstance(lid, int):
                undoinfo.append(self.orderUpLineUndo(bid, lid))
                sel.append((bid, lid - 1))
            elif lid is None:
                undoinfo.append(self.orderUpBlockUndo(bid))
                if bid == 0:
                    return items
                else:
                    sel.append((bid - 1, None))
        self.addUndo(undoinfo, "Move Up")
        return sel

    def orderDown(self, items):
        """Move blocks/lines down"""
        sel = []    # new selection
        undoinfo = []
        for bid, lid in reversed(items):
            if isinstance(lid, int):
                undoinfo.append(self.orderDownLineUndo(bid, lid))
                sel.append((bid, lid + 1))
            elif lid is None:
                undoinfo.append(self.orderDownBlockUndo(bid))
                if bid >= len(OCV.blocks) - 1:
                    return items
                else:
                    sel.append((bid + 1, None))
        self.addUndo(undoinfo, "Move Down")
        sel.reverse()
        return sel

    def close(self, items):
        """Close paths by joining end with start with a line segment"""
        undoinfo = []
        for bid in items:
            block = OCV.blocks[bid]

            if block.name() in ("Header", "Footer"):
                continue

            undoinfo.append(self.insLineUndo(
                bid, OCV.MAXINT,
                self.cnc.gline(block.sx, block.sy)))
        self.addUndo(undoinfo)

    def info(self, bid):
        """Return information for a block
           return XXX
        """
        # block = OCV.blocks[bid] # seems to be unused
        paths = self.toPath(bid)

        if not paths:
            return None, 1

        if len(paths) > 1:
            closed = paths[0].isClosed()
            return int(closed), paths[0]._direction(closed)
            # No treatment for closed not 0 or 1 or None
            # len(paths) could return 2 or plus
            # return len(paths), paths[0]._direction(closed)
        else:
            closed = paths[0].isClosed()
            return int(closed), paths[0]._direction(closed)

    def modify(self, items, func, tabFunc, *args):
        """Modify the lines according to the supplied function and arguments"""
        undoinfo = []
        old = {}  # Motion commands: Last value
        new = {}  # Motion commands: New value
        relative = False

        for bid, lid in self.iterate(items):
            block = OCV.blocks[bid]

            if isinstance(lid, int):
                cmds = Heuristic.parse_line(block[lid])

                if cmds is None:
                    continue

                self.cnc.motionStart(cmds)

                # Collect all values
                new.clear()
                for cmd in cmds:

                    if cmd.upper() == 'G91':
                        relative = True
                    if cmd.upper() == 'G90':
                        relative = False

                    c = cmd[0].upper()
                    # record only coordinates commands
                    if c not in "XYZIJKR":
                        continue

                    try:
                        new[c] = old[c] = float(cmd[1:])*OCV.unit
                    except Exception:
                        new[c] = old[c] = 0.0

                # Modify values with func
                if func(new, old, relative, *args):
                    # Reconstruct new line
                    newcmd = []
                    present = ""
                    for cmd in cmds:
                        c = cmd[0].upper()
                        if c in "XYZIJKR":
                            # Coordinates
                            newcmd.append(OCV.fmt(c, new[c]/OCV.unit))
                        elif c == "G" and int(cmd[1:]) in (0, 1, 2, 3):
                            # Motion
                            newcmd.append("G{0}".format(self.cnc.gcode))
                        else:
                            # the rest leave unchanged
                            newcmd.append(cmd)
                        present += c
                    # Append motion commands if not exist and changed
                    check = "XYZ"

                    if 'I' in new or 'J' in new or 'K' in new:
                        check += "IJK"

                    for c in check:
                        try:
                            if c not in present and new.get(c) != old.get(c):
                                newcmd.append(
                                    OCV.fmt(c, new[c]/OCV.unit))
                        except Exception:
                            pass

                    undoinfo.append(
                        self.setLineUndo(bid, lid, " ".join(newcmd)))

                self.cnc.motionEnd()
                # reset arc offsets

                for i in "IJK":
                    if i in old:
                        old[i] = 0.0

        # FIXME I should add it later, check all functions using it
        self.addUndo(undoinfo)

    def moveFunc(self, new, old, relative, dx, dy, dz):
        """Move position by dx,dy,dz"""
        if relative:
            return False

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

    def orderLines(self, items, direction):
        """Order Lines"""
        if direction == "UP":
            self.orderUp(items)
        elif direction == "DOWN":
            self.orderDown(items)
        else:
            pass

    def moveLines(self, items, dx, dy, dz=0.0):
        """Move position by dx,dy,dz"""
        return self.modify(items, self.moveFunc, None, dx, dy, dz)

    def rotateFunc(self, new, old, relative, c, s, x0, y0):
        """Rotate position by
           c(osine), s(ine) of an angle around center (x0,y0)
        """

        if 'X' not in new and 'Y' not in new:
            return False

        x = get_dict_value('X', new, old)

        y = get_dict_value('Y', new, old)

        new['X'] = c*(x-x0) - s*(y-y0) + x0

        new['Y'] = s*(x-x0) + c*(y-y0) + y0

        if 'I' in new or 'J' in new:
            i = get_dict_value('I', new, old)
            j = get_dict_value('J', new, old)

            if self.cnc.plane in (OCV.CNC_XY, OCV.CNC_XZ):
                new['I'] = c*i - s*j

            if self.cnc.plane in (OCV.CNC_XY, OCV.CNC_YZ):
                new['J'] = s*i + c*j

        return True

    def transformFunc(self, new, old, relative, c, s, xo, yo):
        """Transform (rototranslate) position with the following function:
           xn = c*x - s*y + xo
           yn = s*x + c*y + yo
           it is like the rotate but the rotation center is not defined
           """

        if 'X' not in new and 'Y' not in new:
            return False

        x = get_dict_value('X', new, old)
        y = get_dict_value('Y', new, old)
        new['X'] = c*x - s*y + xo
        new['Y'] = s*x + c*y + yo

        if 'I' in new or 'J' in new:
            i = get_dict_value('I', new, old)
            j = get_dict_value('J', new, old)
            new['I'] = c*i - s*j
            new['J'] = s*i + c*j
        return True

    def rotateLines(self, items, ang, x0=0.0, y0=0.0):
        """Rotate items around optional center (on XY plane)
           ang in degrees (counter-clockwise)
           """

        a = math.radians(ang)
        c = math.cos(a)
        s = math.sin(a)

        if ang in (0.0, 90.0, 180.0, 270.0, -90.0, -180.0, -270.0):
            # round numbers to avoid nasty extra digits
            c = round(c)
            s = round(s)
        return self.modify(items, self.rotateFunc, None, c, s, x0, y0)

    def orientLines(self, items):
        """Use the orientation information to orient selected code"""

        if not self.orient.valid:
            return "ERROR: Orientation information is not valid"

        c = math.cos(self.orient.phi)
        s = math.sin(self.orient.phi)

        return self.modify(
            items,
            self.transformFunc,
            None,
            c, s,
            self.orient.xo, self.orient.yo)

    def mirrorHFunc(self, new, old, relative, *kw):
        """Mirror Horizontal"""
        changed = False
        for axis in 'XI':
            if axis in new:
                new[axis] = -new[axis]
                changed = True
        if self.cnc.gcode in (2, 3):    # Change  2<->3
            self.cnc.gcode = 5 - self.cnc.gcode
            changed = True
        return changed

    def mirrorVFunc(self, new, old, relative, *kw):
        """Mirror Vertical"""
        changed = False
        for axis in 'YJ':
            if axis in new:
                new[axis] = -new[axis]
                changed = True
        if self.cnc.gcode in (2, 3):    # Change  2<->3
            self.cnc.gcode = 5 - self.cnc.gcode
            changed = True
        return changed

    def mirrorHLines(self, items):
        """Mirror horizontally"""
        return self.modify(items, self.mirrorHFunc, None)

    def mirrorVLines(self, items):
        """"Mirror vertically"""
        return self.modify(items, self.mirrorVFunc, None)

    def roundFunc(self, new, old, relative):
        """Round all digits with accuracy"""
        for name, value in new.items():
            new[name] = round(value, OCV.digits)
        return bool(new)

    def roundLines(self, items, acc=None):
        """Round line by the amount of digits"""
        if acc is not None:
            OCV.digits = acc

        return self.modify(items, self.roundFunc, None)

    def removeNlines(self, items):
        """Remove the line number for lines"""
        pass

    def optimize(self, items):
        """Re-arrange using genetic algorithms a set of blocks to minimize
           rapid movements.
        """
        n = len(items)

        matrix = []
        for i in range(n):
            matrix.append([0.0] * n)

        # Find distances between blocks (end to start)
        for i in range(n):
            block = OCV.blocks[items[i]]
            x1 = block.ex
            y1 = block.ey
            for j in range(n):
                if i == j:
                    continue
                block = OCV.blocks[items[j]]
                x2 = block.sx
                y2 = block.sy
                dx = x1-x2
                dy = y1-y2
                # Compensate for machines,
                # which have different speed of X and Y:
                dx /= OCV.feedmax_x
                dy /= OCV.feedmax_y
                matrix[i][j] = math.sqrt(dx*dx + dy*dy)
#         from pprint import pprint
#         pprint(matrix)

        best = [0]
        unvisited = range(1, n)
        while unvisited:
            last = best[-1]
            row = matrix[last]
            # from all the unvisited places search the closest one
            mindist = 1e30

            for i, u in enumerate(unvisited):
                d = row[u]

                if d < mindist:
                    mindist = d
                    si = i

            best.append(unvisited.pop(si))
        # print "best=",best

        undoinfo = []
        for i in range(len(best)):
            b = best[i]

            if i == b:
                continue

            ptr = best.index(i)
            # swap i,b in items
            undoinfo.append(self.swapBlockUndo(items[i], items[b]))
            # swap i,ptr in best
            best[i], best[ptr] = best[ptr], best[i]
        self.addUndo(undoinfo, "Optimize")

    def comp_level(self, queue, stopFunc=None):
        """Use probe information (if exist) to modify the g-code to autolevel"""
      
        paths = []
        # empty the gctos value
        OCV.gctos = []

        def add(line, path):
            if line is not None:
                if isinstance(line, str):
                    queue.put(line + "\n")
                    OCV.gctos.append(line)
                else:
                    queue.put(line)
                    OCV.gctos.append(line)

            paths.append(path)
        
        # check the existence of an autolevel file        
        autolevel = not self.probe.isEmpty()

        self.initPath()

        for line in CNC.compile_pgm(OCV.startup.splitlines()):
            add(line, None)

        every = 1
        for i, block in enumerate(OCV.blocks):

            if not block.enable:
                continue

            for j, line in enumerate(block):
                every -= 1
                if every <= 0:
                    if stopFunc is not None and stopFunc():
                        return None
                    every = 50

                newcmd = []
                cmds = CNC.compileLine(line)
                if cmds is None:
                    continue
                elif isinstance(cmds, str):
                    cmds = CNC.breakLine(cmds)
                else:
                    # either CodeType or tuple, list[] append at it as is
                    if isinstance(cmds, types.CodeType) or\
                          isinstance(cmds, int):
                        add(cmds, None)
                    else:
                        add(cmds, (i, j))
                    continue

                skip = False
                expand = None
                self.cnc.motionStart(cmds)

                # FIXME append feed on cut commands.
                # It will be obsolete in grbl v1.0
                if OCV.appendFeed and self.cnc.gcode in (1, 2, 3):
                    # Check is not existing in cmds
                    for c in cmds:
                        if c[0] in ('f', 'F'):
                            break
                    else:
                        cmds.append(
                            OCV.fmt(
                                'F',
                                self.cnc.feed / OCV.unit))

                if autolevel and self.cnc.gcode in (0, 1, 2, 3) and \
                      self.cnc.mval == 0:
                    xyz = self.cnc.motionPath()

                    if not xyz:
                        # while auto-levelling, do not ignore non-movement
                        # commands, just append the line as-is
                        add(line, None)
                    else:
                        extra = ""
                        for c in cmds:
                            if c[0].upper() not in (
                                    'G', 'X', 'Y', 'Z', 'I', 'J', 'K', 'R'):
                                extra += c
                        x1, y1, z1 = xyz[0]
                        if self.cnc.gcode == 0:
                            g = 0
                        else:
                            g = 1
                        for x2, y2, z2 in xyz[1:]:
                            for x, y, z in self.probe.splitLine(
                                    x1, y1, z1, x2, y2, z2):
                                add("G{0:d} {1} {2} {3} {4}".format(
                                    g,
                                    OCV.fmt('X', x/OCV.unit),
                                    OCV.fmt('Y', y/OCV.unit),
                                    OCV.fmt('Z', z/OCV.unit),
                                    extra),
                                    (i, j))

                                extra = ""

                            x1, y1, z1 = x2, y2, z2
                    self.cnc.motionEnd()
                    continue
                else:
                    # FIXME expansion policy here variable needed
                    # Canned cycles
                    if OCV.drillPolicy == 1 and \
                       self.cnc.gcode in (81, 82, 83, 85, 86, 89):
                        expand = self.cnc.macroGroupG8X()
                    # Tool change
                    elif self.cnc.mval == 6:
                        if OCV.toolPolicy == 0:
                            # send to grbl
                            pass
                        elif OCV.toolPolicy == 1:
                            # skip whole line
                            skip = True
                        elif OCV.toolPolicy >= 2:
                            expand = CNC.compile_pgm(self.cnc.toolChange())
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

                    if c.upper() in (
                            "F", "X", "Y", "Z",
                            "I", "J", "K", "R", "P"):

                        cmd = OCV.fmt(c, value)
                    else:
                        opt = OCV.ERROR_HANDLING.get(cmd.upper(), 0)

                        if opt == OCV.GSTATE_SKIP:
                            cmd = None

                    if cmd is not None:
                        newcmd.append(cmd)

                add("".join(newcmd), (i, j))

        return paths
