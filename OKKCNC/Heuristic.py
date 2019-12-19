# -*- coding: ascii -*-
"""Heuristic.py
Created on Dec 2019

This module contains the Heuristic approach to determine some value analyzing
the Gcode, it is used to detect the "pass" Z height permitting "last pass"
detection to implement the Z height override to cut some material that could
have slight differences in Stock height, usually the wood and plywood

It works, analyzing and modyfing in place the Blocks of gcode created in the
Gcode file loading phase.

@author: carlo.dormeletti@gmail.com
"""

from __future__ import absolute_import
from __future__ import print_function

import OCV
import Block
# from CNC import CNC


def parseLine(line, comments=False):
    """@return
        lines breaking a line containing list of commands,
        None if empty or comment
    """
    # skip empty lines
    if len(line) == 0 or line[0] in ("%", "#", ";"):
        return None

    if line[0] == "(":
        if comments is True:
            pass
        else:
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


class CodeAnalizer(object):
    """Analyze for Z raise and XY pos of  actual and peceding blocks
    to detect the consecutive paths,
    If preceding path end and actual path start have the same XY position
    they belongs to the same shape the z raises could be the tabs,
    if they are not at the maximum Z
    This euristics works, at least for "profiles"

    Some assumptions are made:
        First move serve to place the gantry at the path starts, and generally
            is done at Z max-height, maybe if there are some auto z adjust,
            or tool lenght probe some code has to be added to cope with this
            case

        Subsequent moves aren't higher than this first move Z, generally is
            true as the endmill is lowered at Z safe_height at the beginning
            of the work

        Moves that aren't at Z safe_height are generally tabs or pecks_heights
            maybe defining some Z values for the race cases would be a good
            approach

        Actually it seems that pockets are not correctly detected, some more
        deep analisys is needed
        """

    def __init__(self):
        self.z_min = 1000
        self.z_max = 1000
        # assuming that the code is parsed at least one time to set all the
        # relevant variables
        # A proper check has to be added if this Heuristic has to be used
        # without a first gcode scan
        if OCV.inch:
            self.unit = 1.0/25.4
        else:
            self.unit = 1.0

    def detect_profiles(self):
        """analyze start and ending points to 'detect' the shapes at least
        profile """
        idx = 0
        # process control while flow if set to True will end the loop
        process = True
        match = False
        # print("Z_analisys started")
        # Not using a for loop due to OCV.Blocks in-place modifications
        while (process is True):
            start = OCV.POSPAT.findall(OCV.blocks[idx][0])
            # the block is detected as the first Z up so generally is safe
            # to skip first block as generally has no start and no end data
            if idx > 0 and len(start) != 0:
                end = OCV.POSPAT.findall(OCV.blocks[idx-1][-1])

                if len(end) != 0:
                    if start[0][1] == end[0][1] and start[1][1] == end[1][1]:
                        match = True
                        self.joinblocks(idx)

            if match is False:
                if idx < (len(OCV.blocks) - 1):
                    idx += 1
                else:
                    process = False
            else:
                idx -= 1
                match = False

        else:
            OCV.APP.event_generate("<<Modified>>")

    def joinblocks(self, index):
        """perfrom a join of the two block, the actual and the preceding
        rearranging metadata"""
        # delete last line with end position
        del OCV.blocks[index-1][-1]
        for line in OCV.blocks[index]:
            if line.startswith(OCV.b_mdata_sp[:8]):
                # match block start point no write
                pass
            else:
                # no match of start, end or pass z_height
                OCV.blocks[index-1].append(line)

        del OCV.blocks[index]

    def parse_blocks(self):
        """perform a block analisys and track all the detection"""
        al_cnt = 0
        first_z = 10000.0  # dummy height in hobby machine may be enough
        process = True
        b_idx = 0
        block_moved = False
        # we are not using loops as the Block count could be modified
        while (process is True):
            print("Scanning Block {0}".format(b_idx))
            l_cnt = 0
            process2 = True
            while (process2 is True):
                block = OCV.blocks[b_idx]
                # avoid the recheck of the first (moved) line of new block
                # as it genrated a loop that end in a AttributeError for
                # OCV.blocks
                if block_moved is True:
                    print("advance index")
                    l_cnt += 1
                    block_moved = False

                line = block[l_cnt]
                msg = []
                print(l_cnt, line)
                cmds = parseLine(line)

                # print(cmds)
                if cmds is not None and first_z > 9999 \
                        and cmds[0] == "G0" and cmds[1][:1] == "Z":
                    first_z = self.extract_value(cmds)[2]
                    msg.append("--- first z_detected {0}".format(first_z))

                if cmds is not None and first_z < 9999 \
                        and cmds[0] == "G0" and cmds[1][:1] == "Z":
                    other_z = self.extract_value(cmds)[2]
                    if other_z == first_z:
                        msg.append(
                            "--- z_safe {0} detected ?".format(other_z))
                    else:
                        msg.append(
                            "--- GO single z_move {0}".format(other_z))

                if cmds is None:
                    if line[:8] == "(B_MD SP":
                        msg.append("--- Block metadata START")
                    elif line[:8] == "(B_MD EP":
                        msg.append("--- Block metadata END")
                    elif line[:10] == "(MOP Start":
                        # msg.append("--- MOP START detected")
                        self.move_lines_next_block(b_idx, l_cnt)
                        block_moved = True
                        OCV.APP.event_generate("<<Modified>>")
                        process2 = False
                    elif line[:8] == "(MOP End":
                        msg.append("--- MOP END detected")
                    else:
                        msg.append("--- comment detected?")

                print(al_cnt, l_cnt, line)
                if msg is not []:
                    print("\n".join(msg))

                if l_cnt < (len(block) - 1):
                    l_cnt += 1
                    al_cnt += 1
                else:
                    process2 = False

            # Check all blocks are scanned
            if b_idx < (len(OCV.blocks) - 1):
                b_idx += 1
            else:
                process = False

        # rearrange blocks
        OCV.APP.event_generate("<<Modified>>")

    def move_lines_next_block(self, b_idx, l_cnt):
        boundary = l_cnt
        # print(boundary, OCV.blocks[b_idx][boundary])
        block = Block.Block()
        block.extend(OCV.blocks[b_idx][boundary:])
        block.append("(end prior block)")
        OCV.blocks.insert((b_idx + 1), block)

        cur_block = Block.Block()
        cur_block.extend(OCV.blocks[b_idx][:boundary])
        OCV.blocks[b_idx] = cur_block

        # debugging infos
        # print("block actual", OCV.blocks[b_idx])
        # print("block next", OCV.blocks[b_idx + 1])

    def extract_value(self, cmds):
        """extract X Y Z value from G0 and G1 commands"""
        for cmd in cmds:
            # print(cmd)
            c = cmd[0].upper()
            try:
                value = float(cmd[1:])
            except ValueError:
                value = float('-inf')
            x_val = y_val = z_val = float('-inf')
            if c == "X":
                x_val = value*self.unit
            elif c == "Y":
                y_val = value*self.unit
            elif c == "Z":
                z_val = value*self.unit

        return (x_val, y_val, z_val)
