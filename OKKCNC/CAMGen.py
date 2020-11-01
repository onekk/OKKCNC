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
import numpy as np

# TODO uniform the metadata in CAMGen with those used by heuristic
# eliminate all gcodeCC formatting and substitute them with '(B_MD ...'

#--- Calculation methods

def a2P(a, b):
    """calculate the angle between two vectors
        angle is returned in degrees
    """
    deltaY = b[1] - a[1]
    deltaX = b[0] - a[0]
    angle = np.arctan2(deltaX, deltaY) * 180/np.pi * -1
    return angle

def dest_pt(sp, angle, length):
    """Calculate the end point given starting point, angle and length"""
    px = sp[0] + np.cos(np.deg2rad(angle)) * length;
    py = sp[1] + np.sin(np.deg2rad(angle)) * length;
    return (px, py)

#--- Codegen methods

def mop(self, app, mem_0, mem_1, mop_type):
    """create GCode for a pocket
    Values are stored in OCV.mop_vars as a dictionary"""

    end_depth = OCV.mop_vars["tdp"]
    x_start = min(OCV.WK_mems[mem_0][0], OCV.WK_mems[mem_1][0])
    y_start = min(OCV.WK_mems[mem_0][1], OCV.WK_mems[mem_1][1])

    x_end = max(OCV.WK_mems[mem_0][0], OCV.WK_mems[mem_1][0])
    y_end = max(OCV.WK_mems[mem_0][1], OCV.WK_mems[mem_1][1])

    z_start = OCV.WK_mems[mem_1][2]

    tool_dia = OCV.mop_vars["tdia"]
    tool_rad = tool_dia / 2.

    xy_stepover = OCV.mop_vars["mso"]

    z_stepover = OCV.mop_vars["msd"]

    # avoid infinite while loop
    if z_stepover == 0:
        z_stepover = 0.001

    if mop_type == "PK":
        # Pocketing
        isSpiral = OCV.mop_vars["pks"]

        isInt = OCV.mop_vars["sin"]

        if isSpiral is True:
            op_name = "Spiral Pocket"
        else:
            op_name = "Rectangular Pocket"

    elif mop_type == "LN":
        op_name = "Line"


    """
    cut_dir passed to the calculation method depends on starting point,
    If we cut from internal we minimize "full stock" cut
    in which the endmill is 'surrounded' by the material.
    For calculation these assumptions are done, maybe is wrong

    Conventionl cut is when piece is cut on left side of the cutter

    Climb cut is when piece is cut on right side
    """

    if mop_type == "PK":
        # Pocketing
        if isInt is True:
            cut_dir = 1
            reverse = True
        else:
            cut_dir = 0
            reverse = False

    msg = (
        "{} Operation: \n\n".format(op_name),
        "Start: \n\n{0}\n\n".format(OCV.showC(x_start, y_start, z_start)),
        "End: \n\n{0}\n\n".format(OCV.showC(x_end, y_end, end_depth)),
        "Tool diameter: {0:.{1}f} \n\n".format(tool_dia, OCV.digits),
        "StepDown: {0:.{1}f} \n\n".format(z_stepover, OCV.digits),
        "StepOver: {0:.{1}f} \n\n".format(xy_stepover, OCV.digits))

    retval = tkMessageBox.askokcancel(
        "MOP {} Cut".format(op_name), "".join(msg))

    if retval is False:
        return

    # Start Calculations

    start = (x_start, y_start)
    end = (x_end, y_end)

    if mop_type == "PK":
            # Pocketing
        # Assign points here
        if isSpiral is True:
            msg,x_p,y_p = spiral_pocket(start, end, tool_rad, xy_stepover, cut_dir)
        else:
            msg,x_p,y_p = spiral_pocket(start, end, tool_rad, xy_stepover, cut_dir)

        if msg != "OK":
            retval = tkMessageBox.askokcancel(op_name, msg)
            return

        if reverse is True:
            x_p.reverse()
            y_p.reverse()

    # Reset the editor and write the Gcode generated Here
    OCV.APP.clear_gcode()
    OCV.APP.clear_editor()
    OCV.APP.reset_canvas()
    blocks = []
    block = Block.Block("Init")
    # Get the current WCS as the mem are related to it
    block.append(OCV.CD['WCS'])
    blocks.append(block)

    block = Block.Block(op_name)
    block.append("({})".format(op_name))
    block.append("(Tool diameter = {0:.{1}f})".format(tool_dia, OCV.digits))
    block.append("(Start: {0})".format(OCV.gcodeCC(x_start, y_start, z_start)))
    block.append("(End: {0})".format(OCV.gcodeCC(x_end, y_end, end_depth)))
    block.append("(StepDown: {0:.{1}f} )".format(z_stepover, OCV.digits))
    block.append("(StepOver: {0:.{1}f} )".format(xy_stepover, OCV.digits))

    if mop_type == "PK":
            # Pocketing
            # Move safe to first point
        block.append(CNC.zsafe())
        block.append(CNC.grapid(x_p[0], y_p[0]))
    elif mop_type == "LN":
        # Move safe to first point
        block.append(CNC.zsafe())
        block.append(CNC.grapid(x_start, y_start))
    else:
        return

    # the check is done at the final depth
    curr_depth = z_start

    print("curr_depth, z_start", curr_depth, z_start)
    # Create GCode from points
    while True:
        curr_depth -= z_stepover

        if curr_depth < end_depth:
            curr_depth = end_depth

        block.append(CNC.zenter(curr_depth))
        block.append(CNC.gcode_string(1, [("F", OCV.CD["cutfeed"])]))

        if mop_type == "PK":
            # Pocketing
            for x_l, y_l in zip(x_p, y_p):
                block.append(CNC.gline(x_l, y_l))

            # Move to the begin in a safe way
            block.append(CNC.zsafe())
            block.append(CNC.grapid(x_p[0], y_p[0]))

        elif mop_type == "LN":
            block.append(CNC.gline(x_end, y_end))
            # Move to the begin in a safe way
            block.append(CNC.zsafe())
            block.append(CNC.grapid(x_start, y_start))

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

        OCV.APP.gcode.insBlocks(active, blocks, op_name)
        OCV.APP.refresh()
        OCV.APP.setStatus(_("{}: GCode Generated".format(op_name)))

#--- Generation Methods

def spiral_pocket(start, end, tool_rad, step_over, cut_dir=0):
    """Calculation for a spiral pocket.

    Parameters:
    start       (x,y) start point
    end         (x,y) end point
    tool_rad    tool radius
    step_over   step over xy
    cut dir     0 = conventional 1=climb
    """
    f_width = end[0] - start[0]
    f_height = end[1] - start[1]

    if(f_width < tool_rad or f_height < tool_rad):
            msg = "Abort: Flatten area is too small for this End Mill."
            return msg,(),()

    xP = []
    yP = []

    slx = f_width
    sly = f_height
    #infos = "pint: ({0:.3f}, {1:.3f})  slx: {2:.{dgt}f} sly: {3:.{dgt}f} angle {4:.{dgt}f}"


    if cut_dir == 0:
        spx = start[0] + tool_rad
        spy = end[1] - tool_rad
        # calculate starting point
        xP.append(spx)
        yP.append(spy)

        p3 = (spx, spy)
        sly -=  tool_rad * 2
        p0 = dest_pt(p3, 270, sly)
        xP.append(p0[0])
        yP.append(p0[1])
        slx -= tool_rad * 2
        p1 = dest_pt(p0, 0, slx)
        xP.append(p1[0])
        yP.append(p1[1])
        p2 = dest_pt(p1, 90, sly)
        xP.append(p2[0])
        yP.append(p2[1])
        slx -= step_over
        p3 = dest_pt(p2, 180, slx)
        xP.append(p3[0])
        yP.append(p3[1])

        angle = 270
        loop = True

        while loop is True:
            sly -= step_over
            #print("spiral1 : ",slx, sly)
            if sly < step_over:
                break
            p0 = dest_pt(p3, angle, sly)
            xP.append(p0[0])
            yP.append(p0[1])
            angle += 90
            slx -= step_over
            #print("spiral2 : ",slx, sly)
            if slx < step_over:
                break
            p1 = dest_pt(p0, angle, slx)
            xP.append(p1[0])
            yP.append(p1[1])
            angle +=90
            sly -= step_over
            #print("spiral3 : ",slx, sly)
            if sly < step_over:
                break
            p2 = dest_pt(p1, angle, sly)
            xP.append(p2[0])
            yP.append(p2[1])
            angle +=90
            slx -= step_over
            #print("spiral4 : ",slx, sly)
            if slx < step_over:
                break
            p3 = dest_pt(p2, angle, slx)
            xP.append(p3[0])
            yP.append(p3[1])
            angle = 270

    else:
        spx = start[0] + tool_rad
        spy = end[1] - tool_rad
        # calculate starting point
        xP.append(spx)
        yP.append(spy)
        p3 = (spx, spy)
        p0 = dest_pt(p3, 0, slx)
        xP.append(p0[0])
        yP.append(p0[1])
        p1 = dest_pt(p0, 90, sly)
        xP.append(p1[0])
        yP.append(p1[1])
        p2 = dest_pt(p1, 180, slx)
        xP.append(p2[0])
        yP.append(p2[1])
        sly -= step_over
        p3 = dest_pt(p2, 270, sly)
        xP.append(p3[0])
        yP.append(p3[1])

        angle = 0
        loop = True

        while loop is True:
            slx -= step_over
            #print("spiral1 : ",slx, sly)
            if slx < step_over:
                break
            p0 = dest_pt(p3, angle, slx)
            xP.append(p0[0])
            yP.append(p0[1])
            angle += 90
            sly -= step_over
            #print("spiral2 : ",slx, sly)
            if sly < step_over:
                break
            p1 = dest_pt(p0, angle, sly)
            xP.append(p1[0])
            yP.append(p1[1])
            angle +=90
            slx -= step_over
            #print("spiral3 : ",slx, sly)
            if slx < step_over:
                break
            p2 = dest_pt(p1, angle, slx)
            xP.append(p2[0])
            yP.append(p2[1])
            angle +=90
            sly -= step_over
            #print("spiral4 : ",slx, sly)
            if sly < step_over:
                break
            p3 = dest_pt(p2, angle, sly)
            xP.append(p3[0])
            yP.append(p3[1])
            angle = 0

    # End calculation

    return "OK", xP, yP

def rect_pocket(start, end, tool_rad, step_over, cut_dir=0):

    f_width = end[0] - start[0]
    f_height = end[1] - start[1]

    if(f_width < tool_rad or f_height < tool_rad):
            msg = "Abort: Flatten area is too small for this End Mill."
            return msg,(),()

    xP = []
    yP = []

    slx = f_width
    sly = f_height
    #infos = "pint: ({0:.3f}, {1:.3f})  slx: {2:.{dgt}f} sly: {3:.{dgt}f} angle {4:.{dgt}f}"


    if cut_dir == 0:
        print("Conventional Cut")
        spx = start[0] + tool_rad
        spy = end[1] - tool_rad
        # calculate starting point
        xP.append(spx)
        yP.append(spy)

        p3 = (spx, spy)
        sly -=  tool_rad * 2
        p0 = dest_pt(p3, 270, sly)
        xP.append(p0[0])
        yP.append(p0[1])
        slx -= tool_rad * 2
        p1 = dest_pt(p0, 0, slx)
        xP.append(p1[0])
        yP.append(p1[1])
        p2 = dest_pt(p1, 90, sly)
        xP.append(p2[0])
        yP.append(p2[1])
        slx -= step_over
        p3 = dest_pt(p2, 180, slx)
        xP.append(p3[0])
        yP.append(p3[1])

        angle = 270
        loop = True

        while loop is True:
            sly -= step_over
            #print("spiral1 : ",slx, sly)
            if sly < step_over:
                break
            p0 = dest_pt(p3, angle, sly)
            xP.append(p0[0])
            yP.append(p0[1])
            angle += 90
            slx -= step_over
            #print("spiral2 : ",slx, sly)
            if slx < step_over:
                break
            p1 = dest_pt(p0, angle, slx)
            xP.append(p1[0])
            yP.append(p1[1])
            angle +=90
            sly -= step_over
            #print("spiral3 : ",slx, sly)
            if sly < step_over:
                break
            p2 = dest_pt(p1, angle, sly)
            xP.append(p2[0])
            yP.append(p2[1])
            angle +=90
            slx -= step_over
            #print("spiral4 : ",slx, sly)
            if slx < step_over:
                break
            p3 = dest_pt(p2, angle, slx)
            xP.append(p3[0])
            yP.append(p3[1])
            angle = 270

    else: # climb mill

        xP.append(spx)
        yP.append(spy)
        p3 = (spx, spy)
        p0 = dest_pt(p3, 0, slx)
        xP.append(p0[0])
        yP.append(p0[1])
        p1 = dest_pt(p0, 90, sly)
        xP.append(p1[0])
        yP.append(p1[1])
        p2 = dest_pt(p1, 180, slx)
        xP.append(p2[0])
        yP.append(p2[1])
        sly -= step_over
        p3 = dest_pt(p2, 270, sly)
        xP.append(p3[0])
        yP.append(p3[1])

        angle = 0
        loop = True

        while loop is True:
            slx -= step_over
            print("spiral1 : ",slx, sly)
            if slx < step_over:
                break
            p0 = dest_pt(p3, angle, slx)
            xP.append(p0[0])
            yP.append(p0[1])
            angle += 90
            sly -= step_over
            print("spiral2 : ",slx, sly)
            if sly < step_over:
                break
            p1 = dest_pt(p0, angle, sly)
            xP.append(p1[0])
            yP.append(p1[1])
            angle +=90
            slx -= step_over
            print("spiral3 : ",slx, sly)
            if slx < step_over:
                break
            p2 = dest_pt(p1, angle, slx)
            xP.append(p2[0])
            yP.append(p2[1])
            angle +=90
            sly -= step_over
            print("spiral4 : ",slx, sly)
            if sly < step_over:
                break
            p3 = dest_pt(p2, angle, sly)
            xP.append(p3[0])
            yP.append(p3[1])
            angle = 0

    # End calculation

    return "OK", xP, yP

