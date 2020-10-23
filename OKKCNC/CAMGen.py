# -*- coding: ascii -*-
"""CAMGen.py
Created on Nov 2019

@author: carlo.dormeletti@gmail.com
"""

from __future__ import absolute_import
from __future__ import print_function

try:
    import tkMessageBox
except:
    import tkinter.messagebox as tkMessageBox

import OCV
import Block
from CNC import CNC

# TODO uniform the metadata in CAMGen with those used by heuristic
# eliminate all gcodeCC formatting and substitute them with '(B_MD ...'

def rect_path(x_0, y_0, r_w, r_h):
    """calculate the rectangular path"""
    x_r = []
    y_r = []

    x_r.append(x_0)
    y_r.append(y_0)
    x_r.append(x_0 + r_w)
    y_r.append(y_0)
    x_r.append(x_0 + r_w)
    y_r.append(y_0 + r_h)
    x_r.append(x_0)
    y_r.append(y_0 + r_h)
    x_r.append(x_0)
    y_r.append(y_0)

    return (x_r, y_r)


def line(self, app, end_depth, mem_0, mem_1):
    """Create GCode for a Line"""
    x_start = min(OCV.WK_mems[mem_0][0], OCV.WK_mems[mem_1][0])
    y_start = min(OCV.WK_mems[mem_0][1], OCV.WK_mems[mem_1][1])

    x_end = max(OCV.WK_mems[mem_0][0], OCV.WK_mems[mem_1][0])
    y_end = max(OCV.WK_mems[mem_0][1], OCV.WK_mems[mem_1][1])

    z_start = OCV.WK_mems[mem_1][2]

    tool_dia = OCV.CD['diameter']
    # tool_rad = tool_dia / 2.
    xy_stepover = tool_dia * OCV.CD['stepover'] / 100.0

    z_stepover = OCV.CD['stepz']

    # avoid infinite while loop
    if z_stepover == 0:
        z_stepover = 0.001

    msg = (
        "Line Cut Operation: \n",
        "Start: \n\n{0}\n\n".format(OCV.showC(x_start, y_start, z_start)),
        "End: \n\n{0}\n\n".format(OCV.showC(x_end, y_end, end_depth)),
        "Tool diameter: {0:.{1}f} \n\n".format(tool_dia, OCV.digits),
        "StepDown: {0:.{1}f} \n\n".format(z_stepover, OCV.digits),
        "StepOver: {0:.{1}f} \n\n".format(xy_stepover, OCV.digits))

    retval = tkMessageBox.askokcancel("Line Cut", "".join(msg))

    if OCV.DEBUG is True:
        print("RetVal", retval)

    if retval is False:
        return

    # Reset the Gcode in the Editor
    # Loading an empty file

    # Set the Initialization file
    blocks = []
    block = Block.Block("Init")
    # Get the current WCS as the mem are related to it
    block.append(OCV.CD['WCS'])
    blocks.append(block)

    block = Block.Block("Line")
    block.append("(Line Cut)")
    block.append("(From: {0})".format(OCV.gcodeCC(x_start, y_start, z_start)))
    block.append("(To: {0})".format(OCV.gcodeCC(x_end, y_end, end_depth)))
    block.append("(StepDown: {0:.{1}f} )".format(z_stepover, OCV.digits))
    block.append("(StepOver: {0:.{1}f} )".format(xy_stepover, OCV.digits))
    block.append("(Tool diameter = {0:.{1}f})".format(tool_dia, OCV.digits))

    # Safe move to first point
    block.append(CNC.zsafe())
    block.append(CNC.grapid(x_start, y_start))

    # Init Depth corrected by z_stepover
    # for the correctness of the loop
    # the first instruction of the while loop is -= z_stepover
    # the check is done at the final depth

    curr_depth = z_start + z_stepover

    # Create GCode from points
    while True:
        curr_depth -= z_stepover

        if curr_depth < end_depth:
            curr_depth = end_depth

        block.append(CNC.zenter(curr_depth))
        block.append(CNC.gcode_string(1, [("F", OCV.CD["cutfeed"])]))

        block.append(CNC.gline(x_end, y_end))

        # Move to start in a safe way
        block.append(CNC.zsafe())
        block.append(CNC.grapid(x_start, y_start))

        # Check exit condition
        if curr_depth <= end_depth:
            break

    # return to a safe Z
    block.append(CNC.zsafe())
    blocks.append(block)

    if blocks is not None:
        active = OCV.APP.activeBlock()

        if active == 0:
            active = 1

        OCV.APP.gcode.insBlocks(active, blocks, "Line Cut")
        OCV.APP.refresh()
        OCV.APP.setStatus(_("Line Cut: Generated line cut code"))


def pocket(self, app, end_depth, mem_0, mem_1):
    """create GCode for a pocket"""
    x_start = min(OCV.WK_mems[mem_0][0], OCV.WK_mems[mem_1][0])
    y_start = min(OCV.WK_mems[mem_0][1], OCV.WK_mems[mem_1][1])

    x_end = max(OCV.WK_mems[mem_0][0], OCV.WK_mems[mem_1][0])
    y_end = max(OCV.WK_mems[mem_0][1], OCV.WK_mems[mem_1][1])

    z_start = OCV.WK_mems[mem_1][2]

    tool_dia = OCV.CD['diameter']
    tool_rad = tool_dia / 2.

    xy_stepover = tool_dia * OCV.CD['stepover'] / 100.0

    z_stepover = OCV.CD['stepz']

    # avoid infinite while loop
    if z_stepover == 0:
        z_stepover = 0.001

    msg = (
        "Pocket Cut Operation: \n",
        "Start: \n\n{0}\n\n".format(OCV.showC(x_start, y_start, z_start)),
        "End: \n\n{0}\n\n".format(OCV.showC(x_end, y_end, end_depth)),
        "Tool diameter: {0:.{1}f} \n\n".format(tool_dia, OCV.digits),
        "StepDown: {0:.{1}f} \n\n".format(z_stepover, OCV.digits),
        "StepOver: {0:.{1}f} \n\n".format(xy_stepover, OCV.digits))

    retval = tkMessageBox.askokcancel("Pocket Cut", "".join(msg))

    if retval is False:
        return

    # Set the Initialization file
    blocks = []
    block = Block.Block("Init")
    # Get the current WCS as the mem are related to it
    block.append(OCV.CD['WCS'])
    blocks.append(block)

    block = Block.Block("Pocket")
    block.append("(Pocket)")
    block.append("(Start: {0})".format(OCV.gcodeCC(x_start, y_start, z_start)))
    block.append("(End: {0})".format(OCV.gcodeCC(x_end, y_end, end_depth)))
    block.append("(StepDown: {0:.{1}f} )".format(z_stepover, OCV.digits))
    block.append("(StepOver: {0:.{1}f} )".format(xy_stepover, OCV.digits))
    block.append("(Tool diameter = {0:.{1}f})".format(tool_dia, OCV.digits))

    # Move safe to first point
    block.append(CNC.zsafe())
    block.append(CNC.grapid(x_start, y_start))

    # Init Depth

    f_width = x_end - x_start
    f_heigth = y_end - y_start

    cut_dir = "Conventional"

    x_start_pocket = x_start + tool_rad
    y_start_pocket = y_start + tool_rad

    # Calc space to work with/without border cut
    travel_width = f_width - tool_dia
    travel_height = f_heigth - tool_dia

    if travel_width < tool_rad or travel_height < tool_rad:
        msg = "(Pocket aborted: Pocket area is too small for this End Mill.)"
        retval = tkMessageBox.askokcancel("Pocket Cut", msg)
        return

    # Prepare points for pocketing
    x_p = []
    y_p = []

    # Calc number of pass
    v_count = (int)(travel_height / xy_stepover)
    h_count = (int)(travel_width / xy_stepover)

    # Make them odd
    if v_count%2 == 0:
        v_count += 1

    if h_count%2 == 0:
        h_count += 1

    # Calc step minor of Max step
    h_stepover = travel_height / v_count
    w_stepover = travel_width / h_count

    # Start from border to center
    x_s = x_start_pocket
    y_s = y_start_pocket
    w_s = travel_width
    h_s = travel_height
    x_c = 0
    y_c = 0

    while x_c <= h_count/2 and y_c <= v_count/2:
        # Pocket offset points
        x_0, y_0 = rect_path(x_s, y_s, w_s, h_s)

        if cut_dir == "Conventional":
            x_0 = x_0[::-1]
            y_0 = y_0[::-1]

        x_p = x_p + x_0
        y_p = y_p + y_0
        x_s += h_stepover
        y_s += w_stepover
        h_s -= 2.0 * h_stepover
        w_s -= 2.0 * w_stepover
        x_c += 1
        y_c += 1

        # Reverse point to start from inside (less stres on the tool)
        x_p = x_p[::-1]
        y_p = y_p[::-1]

    # Move safe to first point
    block.append(CNC.zsafe())
    block.append(CNC.grapid(x_p[0], y_p[0]))

    # Init Depth corrected by z_stepover
    # for the correctness of the loop
    # the first instruction of the while loop is -= z_stepover
    # the check is done at the final depth
    curr_depth = z_start + z_stepover

    # Create GCode from points
    while True:
        curr_depth -= z_stepover

        if curr_depth < end_depth:
            curr_depth = end_depth

        block.append(CNC.zenter(curr_depth))
        block.append(CNC.gcode_string(1, [("F", OCV.CD["cutfeed"])]))

        # Pocketing
        for x_l, y_l in zip(x_p, y_p):
                block.append(CNC.gline(x_l, y_l))

        # Move to the begin in a safe way
        block.append(CNC.zsafe())
        block.append(CNC.grapid(x_p[0], y_p[0]))

        # Verify exit condition
        if curr_depth <= end_depth:
            break

    # end of the loop
    # return to z_safe
    block.append(CNC.zsafe())
    blocks.append(block)

    if blocks is not None:
        active = OCV.APP.activeBlock()

        if active == 0:
            active = 1

        OCV.APP.gcode.insBlocks(active, blocks, "Line Cut")
        OCV.APP.refresh()
        OCV.APP.setStatus(_("Line Cut: Generated line cut code"))
