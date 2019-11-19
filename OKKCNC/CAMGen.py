#!/usr/bin/env python2
# -*- coding: ascii -*-
"""
Created on Fri Nov  8 16:03:58 2019

@author: carlo
"""


from __future__ import absolute_import
from __future__ import print_function

__author__  = "Carlo Dormeletti (onekk)"
__email__   = "carlo.dormeletti@gmail.com"


try:
   import tkMessageBox
except:
    import tkinter.messagebox as tkMessageBox

import OCV
#import CNC
from CNC import Block, CNC


def RectPath(x,y,w,h):
        xR = []
        yR = []
        xR.append(x)
        yR.append(y)
        xR.append(x + w)
        yR.append(y)
        xR.append(x + w)
        yR.append(y + h)
        xR.append(x)
        yR.append(y + h)
        xR.append(x)
        yR.append(y)
        return (xR,yR)


def line(self, app, endDepth, mem_0, mem_1):

    XStart = min(OCV.WK_mems[mem_0][0],OCV.WK_mems[mem_1][0])
    YStart = min(OCV.WK_mems[mem_0][1],OCV.WK_mems[mem_1][1])

    XEnd = max(OCV.WK_mems[mem_0][0],OCV.WK_mems[mem_1][0])
    YEnd = max(OCV.WK_mems[mem_0][1],OCV.WK_mems[mem_1][1])

    startDepth = OCV.WK_mems[mem_1][2]

    toolDiam = OCV.CD['diameter']
    #toolRadius = toolDiam / 2.
    StepOverInUnitMax = toolDiam * OCV.CD['stepover'] / 100.0

    ZStepOver = OCV.CD['stepz']
    if ZStepOver==0 : ZStepOver=0.001  #avoid infinite while loop

    msg = "Line Cut Operation: \n"
    msg+= "Start: \n\n{0}\n\n".format(OCV.showC(XStart, YStart, startDepth))
    msg+= "End: \n\n{0}\n\n".format(OCV.showC(XEnd, YEnd, endDepth))
    msg+= "Tooldiam: {0:.{1}f} \n\n".format(toolDiam, OCV.digits)
    msg+= "StepDown: {0:.{1}f} \n\n".format(ZStepOver, OCV.digits)
    msg+= "StepOver: {0:.{1}f} \n\n".format(StepOverInUnitMax, OCV.digits)


    retval = tkMessageBox.askokcancel("Line Cut",msg)

    print("RetVal",retval)

    if retval is False:
        return

    # Reset the Gcode in the Editor
    # Loading an empty file


    # Set the Initialization file
    blocks = []
    block =  Block("Init")
    # Get the current WCS as the mem are related to it
    block.append(OCV.CD['WCS'])
    blocks.append(block)

    block = Block("Line")
    block.append("(Line Cut)")
    block.append("(From: {0})".format(OCV.gcodeCC(XStart, YStart, startDepth)))
    block.append("(To: {0})".format(OCV.gcodeCC(XEnd, YEnd, endDepth)))
    block.append("(StepDown: {0:.{1}f} )".format(ZStepOver, OCV.digits))
    block.append("(StepOver: {0:.{1}f} )".format(StepOverInUnitMax, OCV.digits))
    block.append("(Tool diameter = {0:.{1}f})".format(toolDiam,  OCV.digits))

    #Safe move to first point
    block.append(CNC.zsafe())
    block.append(CNC.grapid(XStart,YStart))

    # Init Depth corrected by ZStepOver
    # for the correctness of the loop
    # the first instruction of the while loop is -= ZStepOver
    # the check is done at the final depth

    currDepth = startDepth + ZStepOver

    #Create GCode from points
    while True:
        currDepth -= ZStepOver
        if currDepth < endDepth : currDepth = endDepth
        block.append(CNC.zenter(currDepth))
        block.append(CNC.gcode(1, [("F",OCV.CD["cutfeed"])]))

        block.append(CNC.gline(XEnd,YEnd))

        #Move to start in a safe way
        block.append(CNC.zsafe())
        block.append(CNC.grapid(XStart,YStart))

        #Check exit condition
        if currDepth <= endDepth : break

    # return to a safe Z
    block.append(CNC.zsafe())
    blocks.append(block)

    if blocks is not None:
        active = app.activeBlock()
        if active==0: active=1
        app.gcode.insBlocks(active, blocks, "Line Cut")
        app.refresh()
        app.setStatus(_("Line Cut: Generated line cut code"))


def pocket(self, app, endDepth, mem_0, mem_1):

    XStart = min(OCV.WK_mems[mem_0][0],OCV.WK_mems[mem_1][0])
    YStart = min(OCV.WK_mems[mem_0][1],OCV.WK_mems[mem_1][1])

    XEnd = max(OCV.WK_mems[mem_0][0],OCV.WK_mems[mem_1][0])
    YEnd = max(OCV.WK_mems[mem_0][1],OCV.WK_mems[mem_1][1])

    startDepth = OCV.WK_mems[mem_1][2]

    toolDiam = OCV.CD['diameter']
    toolRadius = toolDiam / 2.

    StepOverInUnitMax = toolDiam * OCV.CD['stepover'] / 100.0

    ZStepOver = OCV.CD['stepz']

    if ZStepOver==0 : ZStepOver=0.001  #avoid infinite while loop

    msg = "Pocket Cut Operation: \n"
    msg+= "Start: \n\n{0}\n\n".format(OCV.showC(XStart, YStart, startDepth))
    msg+= "End: \n\n{0}\n\n".format(OCV.showC(XEnd, YEnd, endDepth))
    msg+= "Tooldiam: {0:.{1}f} \n\n".format(toolDiam, OCV.digits)
    msg+= "StepDown: {0:.{1}f} \n\n".format(ZStepOver, OCV.digits)
    msg+= "StepOver: {0:.{1}f} \n\n".format(StepOverInUnitMax, OCV.digits)

    retval = tkMessageBox.askokcancel("Pocket Cut",msg)

    if retval is False:
        return

    # Set the Initialization file
    blocks = []
    block =  Block("Init")
    # Get the current WCS as the mem are related to it
    block.append(OCV.CD['WCS'])
    blocks.append(block)

    block = Block("Pocket")
    block.append("(Pocket)")
    block.append("(Start: {0})".format(OCV.gcodeCC(XStart, YStart, startDepth)))
    block.append("(End: {0})".format(OCV.gcodeCC(XEnd, YEnd, endDepth)))
    block.append("(StepDown: {0:.{1}f} )".format(ZStepOver, OCV.digits))
    block.append("(StepOver: {0:.{1}f} )".format(StepOverInUnitMax, OCV.digits))
    block.append("(Tool diameter = {0:.{1}f})".format(toolDiam,  OCV.digits))

    #Move safe to first point
    block.append(CNC.zsafe())
    block.append(CNC.grapid(XStart,YStart))

    #Init Depth

    f_width = XEnd - XStart
    f_heigth = YEnd - YStart

    CutDirection = "Conventional"

    #Offset for Border Cut

    BorderXStart = XStart + toolRadius
    BorderYStart = YStart + toolRadius

    #BorderXEnd = XStart + f_width - toolRadius
    #BorderYEnd = YStart + f_heigth - toolRadius

    PocketXStart = BorderXStart
    PocketYStart = BorderYStart

    #Calc space to work with/without border cut
    WToWork = f_width - toolDiam
    HToWork = f_heigth - toolDiam

    if(WToWork < toolRadius or HToWork < toolRadius):
        msg = "(Pocket aborted: Pocket area is too small for this End Mill.)"
        retval = tkMessageBox.askokcancel("Pocket Cut",msg)
        return

    #Prepare points for pocketing
    xP=[]
    yP=[]

    #Calc number of pass
    VerticalCount = (int)(HToWork / ZStepOver)
    HorrizontalCount = (int)(WToWork / ZStepOver)
    #Make them odd
    if VerticalCount%2 == 0 : VerticalCount += 1
    if HorrizontalCount%2 == 0 : HorrizontalCount += 1

    #Calc step minor of Max step
    StepOverInUnitH = HToWork / (VerticalCount)
    StepOverInUnitW = WToWork / (HorrizontalCount)

    #Start from border to center
    xS = PocketXStart
    yS = PocketYStart
    wS = WToWork
    hS = HToWork
    xC = 0
    yC = 0

    while (xC<=HorrizontalCount/2 and yC<=VerticalCount/2):
            #Pocket offset points
            xO,yO = RectPath(xS, yS, wS, hS)
            if CutDirection == "Conventional":
                    xO = xO[::-1]
                    yO = yO[::-1]

            xP = xP + xO
            yP = yP + yO
            xS+=StepOverInUnitH
            yS+=StepOverInUnitW
            hS-=2.0*StepOverInUnitH
            wS-=2.0*StepOverInUnitW
            xC += 1
            yC += 1

            #Reverse point to start from inside (less stres on the tool)
            xP = xP[::-1]
            yP = yP[::-1]

    #Move safe to first point
    block.append(CNC.zsafe())
    block.append(CNC.grapid(xP[0], yP[0]))

    # Init Depth corrected by ZStepOver
    # for the correctness of the loop
    # the first instruction of the while loop is -= ZStepOver
    # the check is done at the final depth
    currDepth = startDepth + ZStepOver

    #Create GCode from points
    while True:
            currDepth -= ZStepOver
            if currDepth < endDepth : currDepth = endDepth

            block.append(CNC.zenter(currDepth))
            block.append(CNC.gcode(1, [("F",OCV.CD["cutfeed"])]))

            #Pocketing
            for x,y in zip(xP,yP):
                    block.append(CNC.gline(x, y))

            #Move to the begin in a safe way
            block.append(CNC.zsafe())
            block.append(CNC.grapid(xP[0], yP[0]))

            #Verify exit condition
            if currDepth <= endDepth : break

    # end of the loop
    # return to z_safe
    block.append(CNC.zsafe())
    blocks.append(block)


    if blocks is not None:
        active = app.activeBlock()

        if active==0: active=1
        app.gcode.insBlocks(active, blocks, "Line Cut")
        app.refresh()
        app.setStatus(_("Line Cut: Generated line cut code"))

