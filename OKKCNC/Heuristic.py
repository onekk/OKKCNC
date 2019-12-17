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


class CodeAnalyzer(object):
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
