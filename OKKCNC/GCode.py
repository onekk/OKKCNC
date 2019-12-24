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
import Block
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
        self.header = ""
        self.footer = ""
        self.undoredo = undo.UndoRedo()
        self.probe = Probe.Probe()
        self.orient = Orient()
        self.vars = {}  # local variables
        self.init()

    def init(self):
        self.filename = ""
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
        return self._modified

    def resetModified(self):
        self._modified = False

    def __getitem__(self, item):
        return OCV.blocks[item]

    def __setitem__(self, item, value):
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
        while (prcs is True):
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
        # for now only 'CamBam-OKK' is implemented, using the 'custom'
        # grbl.cbpp file as postprocessor in CamBam
        # others could be implemented if relevant information are supplied
        if OCV.g_code_pp in ("CamBam-OKK",):
                self.pre_process_gcode()
        else:
            # Plain Gcode file and not detected "generators" are processed
            # using the add_line method, in this case the g_code_pp value is
            # the default 'Generic' set in OCV file
            for line in OCV.gcodelines:
                self.add_line(line)

        Heuristic.trim_blocks()

        if OCV.DEBUG_PAR is True:
            OCV.printout_header("{0}", "END SCAN")

        if OCV.g_code_pp in ("CamBam-OKK",) and adv_heur is True:
            # after the loading analyze the code
            # g_parse = Heuristic.CodeAnalizer()
            # g_parse.detect_profiles()

            # g_parse.parse_blocks()
            OCV.printout_header("{0}", "PARSING FINISHED")

            # Heuristic.adjust_mops()

    def pre_process_gcode(self):
        """scan gcode lines and inject some metadata in the blocks
        ideally this will create at least 3 blocks:
            - "Header" block
            - Command block
            - "End Job" block with the end Gcode commands detected using
                some heuristic, usually a G0 Z_max followed by:
                    M5 (Spindle Stop) or M9 (Coolant Stop)
                    M2 or M30 (Program End)
        more blocks are created detecting the custom '(MOP Start:' supplied
        by CamBam postprocessor modified by onekk.
        See in Documentation for more infos.
        """
        # DEBUG_INFO
        # INT_DEBUG = OCV.DEBUG_PAR
        INT_DEBUG = True
        OCV.infos = []

        process = True
        l_idx = -1

        while (process is True):
            if l_idx < (len(OCV.gcodelines) - 1):
                l_idx += 1
            else:
                # continue here is to force the loop to terminate here
                # if not present the last lline is scanned again
                process = False
                continue

            line = OCV.gcodelines[l_idx]

            if INT_DEBUG is True:
                print("{0} Line > {1}".format(l_idx, line))

            if len(OCV.gcodelines) > 2 and l_idx > 0:
                line_prev = OCV.gcodelines[l_idx - 1]

            if l_idx == (len(OCV.gcodelines) - 1):
                print("last line fo gcode")
                line_next = None
            else:
                line_next = OCV.gcodelines[l_idx + 1]
                next_cmds = Heuristic.parse_line(line_next)

            if line.startswith("(-)"):
                continue
            if not OCV.blocks:
                OCV.blocks.append(Block.Block("Header"))

            # catch the MOP Start comment and create a new Block, if not
            # created by a MOP End istance

            if line[:10] == "(MOP Start":
                a_block_l = len(OCV.blocks[-1])
                print("MS check {0}".format(a_block_l))

                OCV.infos.append("MOP Start")

                if a_block_l < 2:
                    OCV.blocks[-1].append(line)
                else:
                    self.new_block(line, 0, INT_DEBUG)
                    self.finalize_move(INT_DEBUG)

                OCV.first_move_detect = False

                continue

            if line[:8] == "(MOP End":
                print("ES check")
                # if there is a MOP end
                move_p = [self.cnc.x, self.cnc.y, self.cnc.z]
                b_end = OCV.b_mdata_ep.format(OCV.gcodeCC(*move_p))
                OCV.blocks[-1].append(b_end)
                self.new_block(line, 1, INT_DEBUG)
                self.finalize_move(INT_DEBUG)
                continue

            cmds = Heuristic.parse_line(line)

            if cmds is None:
                # the line contains comments or no valid commands
                OCV.blocks[-1].append(line)
                continue

            self.cnc.motionStart(cmds)
            move = cmds[0]
            move_c = [self.cnc.x, self.cnc.y, self.cnc.z]
            move_cdz = self.cnc.dz

            # analyze "cut" moves
            if move in ("G1", "G2", "G3"):
                if cmds[1][:1] == "F":
                    if move_cdz < 0 and OCV.first_move_detect is False:

                        OCV.infos.append(
                            "FMD-F - SM {0} {0} DZ{1} X{2} Y{3} Z{4}".format(
                                    move, move_cdz, *move_c))
                        # insert at the top of the block the coordinates value
                        b_head = OCV.b_mdata_sp.format(OCV.gcodeCC(*move_c))
                        OCV.blocks[-1].insert(0, b_head)
                        OCV.first_move_detect = True
                    elif move_cdz < 0 and OCV.first_move_detect is True:
                        OCV.infos.append(
                            "FMD-T - {0} {0} DZ{1} X{2} Y{3} Z{4}".format(
                                    move, move_cdz, *move_c))

            OCV.min_z = min(OCV.min_z, self.cnc.z)
            OCV.max_z = max(OCV.max_z, self.cnc.z)

            # NOTE: self.cnc.gcode is not always holding the content of
            # current move commands CNC.motionStart method don't modify
            # self.cnc.gcode for the following commands
            # 4, 10, 53, 17 ,18 , 19, 20, 21, 80, 90, 91, 93, 94, 95, 98, 99
            # so other checks are needed to detectd the "cause" of this z_move
            if self.cnc.gcode == 0 and self.cnc.dz > 0.0:
                # rapid Z move up detected
                # if the commands are in set commands, probably this is the
                # z_safe move at the beginning of file, no new block is needed
                if move in OCV.set_cmds or\
                        (move == "G0" and move_c == [0, 0, 0]) or\
                        (move[:1] in ("T", "M", "S")):
                    OCV.blocks[-1].append(line)
                # To avoid false checking against == for float values
                # a small value is added and is checked for "greater than"
                elif (self.cnc.zval + 0.00001) > OCV.max_z:
                    self.evaluate_z_move(line, line_next, line_prev,
                                         next_cmds, move_c)

                # if z_val is lower than z_max this could be a tab or a z_pass
                elif self.cnc.zval < OCV.max_z:
                    OCV.blocks[-1].append(OCV.b_mdata_zp.format(*move_c))
                    OCV.blocks[-1].append(line)
                else:
                    # printout the infos for an un processed Z_up move
                    OCV.infos.append(
                        "ZD - move {0} DZ{1} X{2} Y{3} Z{4}".format(
                                move, move_cdz, *move_c))

            else:
                OCV.blocks[-1].append(line)

            self.finalize_move(INT_DEBUG)

    def evaluate_z_move(self, line, line_next, line_prev, next_cmds, move_c):
        """evaluate Z move up to determine what action is needed"""
        b_end = OCV.b_mdata_ep.format(OCV.gcodeCC(*move_c))
        # analyze if this is the end block
        if line_next is not None and next_cmds is not None:
            if next_cmds[0] in OCV.end_cmds:
                if len(OCV.blocks[-1]) < 1:
                    # print("ZUP BL = ", len(OCV.blocks[-1]))
                    # catch if a new block is occurred and is empty
                    OCV.blocks[-1].append(line)
                    OCV.blocks[-1]._name = "End Job"
                else:
                    OCV.blocks[-1].append(b_end)
                    OCV.blocks.append(Block.Block("End Job"))
                    OCV.blocks[-1].append(line)
            else:
                print("ZD - next cmds", next_cmds)
                # Here some more Heuristic
                pass
        else:
            if line_prev[:8] == "(MOP End":
                b_start = OCV.b_mdata_sp.format(
                    OCV.gcodeCC(*move_c))
                OCV.blocks[-1].append(b_start)
                OCV.blocks[-1].append(line)
            else:
                print("BEA not catched")

    def finalize_move(self, DEBUG):

        self.cnc.motionEnd()

        if DEBUG is True:
            if OCV.infos != []:
                OCV.printout_infos(OCV.infos)
                OCV.infos = []

    def new_block(self, line, b_pos, DEBUG):
        """Add a new block to the block list
        b_pos = 0 >> line placed in new block
        b_pos = 1 >> line placed in old block
        """
        # print("new block")

        if b_pos == 1:
            OCV.blocks[-1].append(line)
            OCV.blocks.append(Block.Block())
            return

        # line is moved to next block
        OCV.blocks.append(Block.Block())
        OCV.blocks[-1].append(line)

    def add_line(self, line):
        """plain addLine method from bCNC
        used by setLinesUndo method and if no postprocessor is detected in
        GCode file
        """
        if line.startswith("(-)"):
            return

        if line.startswith("(Block-name:"):
            self._blocksExist = True
            pat = OCV.BLOCKPAT.match(line)
            if pat:
                value = pat.group(2).strip()
                if not OCV.blocks or len(OCV.blocks[-1]):
                    OCV.blocks.append(Block(value))
                else:
                    OCV.blocks[-1]._name = value
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
        except Exception:
            return False

        self._lastModified = os.stat(self.filename).st_mtime

        self.cnc.initPath()
        self.cnc.resetAllMargins()
        self._blocksExist = False

        for line in f_handle:
            # Add line to the gcodelines used for display and heuristic
            OCV.gcodelines.append(line[:-1].replace("\x0d", ""))

        f_handle.close()

        self.parse_gcode(filename, True)

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

        block = Block.Block(name)
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
            block = Block.Block("new")
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
                block = Block.Block(path.name)
            else:
                block = Block.Block(path[0].name)

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
                        OCV.fmt("X", x, 7),
                        OCV.fmt("Y", y, 7)) + cm)
                else:
                    block.append("G1 {0} {1} {2}".format(
                        OCV.fmt("X", x, 7),
                        OCV.fmt("Y", y, 7),
                        OCV.fmt("Z", z, 7)) + cm)

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
                        OCV.fmt("X", x, 7),
                        OCV.fmt("Y", y, 7),
                        OCV.fmt("I", ij[0], 7),
                        OCV.fmt("J", ij[1], 7)) + cm)
                else:
                    block.append("G{0:d} {1} {2} {3} {4} {5}".format(
                        segment.type,
                        OCV.fmt("X", x, 7),
                        OCV.fmt("Y", y, 7),
                        OCV.fmt("I", ij[0], 7),
                        OCV.fmt("J", ij[1], 7),
                        OCV.fmt("Z", z, 7)) + cm)

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

        return self.addBlockUndo(pos, Block.Block(OCV.blocks[bid]))

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
        block = Block.Block()
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
        undoinfo = (self.setBlockNameUndo, bid, OCV.blocks[bid]._name)
        OCV.blocks[bid]._name = name
        return undoinfo

    def addBlockOperationUndo(self, bid, operation, remove=None):
        """Add an operation code in the name as [drill, cut, in/out...]"""
        undoinfo = (self.setBlockNameUndo, bid, OCV.blocks[bid]._name)
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
                                OCV.fmt('X', x/self.cnc.unit),
                                OCV.fmt('Y', y/self.cnc.unit),
                                OCV.fmt('Z', z/self.cnc.unit),
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

    def reverse(self, items):
        """Reverse direction of cut"""
        undoinfo = []
        remove = ["cut", "climb", "conventional", "cw", "ccw", "reverse"]
        for bid in items:
            operation = "reverse"

            if OCV.blocks[bid].name() in ("Header", "Footer"):
                continue

            newpath = Path(OCV.blocks[bid].name())

            """
            Not sure if this is good idea...
            Might get confusing if something goes wrong,
            but seems to work fine
            """
            if OCV.blocks[bid].operationTest('conventional'):
                operation += ",climb"

            if OCV.blocks[bid].operationTest('climb'):
                operation += ",conventional"

            if OCV.blocks[bid].operationTest('cw'):
                operation += ",ccw"

            if OCV.blocks[bid].operationTest('ccw'):
                operation += ",cw"

            for path in self.toPath(bid):
                path.invert()
                newpath.extend(path)

            if newpath:
                block = self.fromPath(newpath)
                undoinfo.append(self.addBlockOperationUndo(
                    bid, operation, remove))
                undoinfo.append(self.setBlockLinesUndo(bid, block))

        self.addUndo(undoinfo)

    # CHECK IF NEEDED
    def cutDirection(self, items, direction=-1):
        """
            Change cut direction
             1 > CW
            -1 > CCW
             2 > Conventional =
                 CW for inside profiles and pockets,
                 CCW for outside profiles
             -2 > Climb =
                 CCW for inside profiles and pockets,
                 CW for outside profiles
        """

        undoinfo = []
        msg = None

        remove = ["cut", "reverse", "climb", "conventional", "cw", "ccw"]

        for bid in items:
            if OCV.blocks[bid].name() in ("Header", "Footer"):
                continue

            opdir = direction
            operation = ""

            # Decide conventional/climb/error:
            side = OCV.blocks[bid].operationSide()

            if abs(direction) > 1 and side == 0:
                msg = "Conventional/Climb feature only works for paths"
                msg += " with 'in/out/pocket' tags!\n"
                msg += "Some of the selected paths were not tagged (or"
                msg += " are both in+out). You can still use CW/CCW for them."
                continue

            if direction == 2:
                operation = "conventional,"
                if side == -1:
                    opdir = 1  # inside CW

                if side == 1:
                    opdir = -1  # outside CCW
            elif direction == -2:
                operation = "climb,"

                if side == -1:
                    opdir = -1  # inside CCW

                if side == 1:
                    opdir = 1  # outside CW

            # Decide CW/CCW tag
            if opdir == 1:
                operation += "cw"
            elif opdir == -1:
                operation += "ccw"

            # Process paths
            for path in self.toPath(bid):
                if not path.directionSet(opdir):
                    msg = "Error determining direction of path!"
                if path:
                    block = self.fromPath(path)

                    undoinfo.append(self.addBlockOperationUndo(
                        bid, operation, remove))

                    undoinfo.append(self.setBlockLinesUndo(bid, block))
        self.addUndo(undoinfo)

        return msg

    '''
    # CHECK IF NEEDED
    def island(self, items, island=None):
        """Toggle or set island tag on block"""

        undoinfo = []
        remove = ["island"]
        for bid in items:
            isl = island

            if OCV.blocks[bid].name() in ("Header", "Footer"): continue

            if isl is None: isl = not OCV.blocks[bid].operationTest('island')
            if isl:
                tag = 'island'
                OCV.blocks[bid].color = '#ff0000'
            else:
                tag = ''
                OCV.blocks[bid].color = None

            undoinfo.append(self.addBlockOperationUndo(bid, tag, remove))
            # undoinfo.append(self.setBlockLinesUndo(bid, block))

        self.addUndo(undoinfo)
    '''

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
                        if c in "XYZIJKR":
                            # Coordinates
                            newcmd.append(OCV.fmt(c, new[c]/self.cnc.unit))
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
                                    OCV.fmt(c, new[c]/self.cnc.unit))
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

            if self.cnc.plane in (OCV.XY, OCV.XZ):
                new['I'] = c*i - s*j

            if self.cnc.plane in (OCV.XY, OCV.YZ):
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
        """Use probe information to modify the g-code to autolevel"""
        # lines = [self.cnc.startup]
        paths = []

        def add(line, path):
            if line is not None:
                if isinstance(line, str) or isinstance(line, unicode):
                    queue.put(line + "\n")
                else:
                    queue.put(line)

            paths.append(path)

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
                elif isinstance(cmds, str) or isinstance(cmds, unicode):
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
                                self.cnc.feed / self.cnc.unit))

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
                                    OCV.fmt('X', x/self.cnc.unit),
                                    OCV.fmt('Y', y/self.cnc.unit),
                                    OCV.fmt('Z', z/self.cnc.unit),
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

                        if opt == OCV.SKIP:
                            cmd = None

                    if cmd is not None:
                        newcmd.append(cmd)

                add("".join(newcmd), (i, j))

        return paths
