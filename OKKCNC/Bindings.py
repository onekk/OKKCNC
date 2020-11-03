# -*- coding: utf-8 -*-
"""Bindings.py

OKKCNC Binding module, it brings out many bindings from the __main__
module to make it shorter and more readable

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

# Import Tkinter needed for Tk.TclError to be defined
try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
import tkExtra

class Bindings():
    def __init__(self):

        #--- Global bindings
        OCV.TK_MAIN.bind('<<Undo>>', OCV.TK_MAIN.undo)
        OCV.TK_MAIN.bind('<<Redo>>', OCV.TK_MAIN.redo)
        OCV.TK_MAIN.bind('<<Copy>>', OCV.TK_MAIN.copy)
        OCV.TK_MAIN.bind('<<Cut>>', OCV.TK_MAIN.cut)
        OCV.TK_MAIN.bind('<<Paste>>', OCV.TK_MAIN.paste)

        OCV.TK_MAIN.bind('<<Connect>>', OCV.TK_MAIN.openClose)

        OCV.TK_MAIN.bind('<<New>>', OCV.TK_MAIN.newFile)
        OCV.TK_MAIN.bind('<<Open>>', OCV.TK_MAIN.loadDialog)
        OCV.TK_MAIN.bind('<<Import>>', lambda x, s=OCV.TK_MAIN: s.importFile())
        OCV.TK_MAIN.bind('<<Save>>', OCV.TK_MAIN.saveAll)
        OCV.TK_MAIN.bind('<<SaveAs>>', OCV.TK_MAIN.saveDialog)
        OCV.TK_MAIN.bind('<<Reload>>', OCV.TK_MAIN.reload)

        OCV.TK_MAIN.bind('<<Recent0>>', OCV.TK_MAIN._loadRecent0)
        OCV.TK_MAIN.bind('<<Recent1>>', OCV.TK_MAIN._loadRecent1)
        OCV.TK_MAIN.bind('<<Recent2>>', OCV.TK_MAIN._loadRecent2)
        OCV.TK_MAIN.bind('<<Recent3>>', OCV.TK_MAIN._loadRecent3)
        OCV.TK_MAIN.bind('<<Recent4>>', OCV.TK_MAIN._loadRecent4)
        OCV.TK_MAIN.bind('<<Recent5>>', OCV.TK_MAIN._loadRecent5)
        OCV.TK_MAIN.bind('<<Recent6>>', OCV.TK_MAIN._loadRecent6)
        OCV.TK_MAIN.bind('<<Recent7>>', OCV.TK_MAIN._loadRecent7)
        OCV.TK_MAIN.bind('<<Recent8>>', OCV.TK_MAIN._loadRecent8)
        OCV.TK_MAIN.bind('<<Recent9>>', OCV.TK_MAIN._loadRecent9)
        OCV.TK_MAIN.bind('<<AlarmClear>>', OCV.TK_MAIN.alarmClear)
        OCV.TK_MAIN.bind('<<About>>', OCV.TK_MAIN.about)
        OCV.TK_MAIN.bind('<<Help>>', OCV.TK_MAIN.help)        


        OCV.TK_MAIN.bind('<FocusIn>', OCV.TK_MAIN.focus_in)
        OCV.TK_MAIN.protocol("WM_DELETE_WINDOW", OCV.TK_MAIN.quit)

        OCV.TK_MAIN.bind('<<Resume>>', lambda e, s=OCV.TK_MAIN: s.resume())
        OCV.TK_MAIN.bind('<<Run>>', lambda e, s=OCV.TK_MAIN: s.run())
        OCV.TK_MAIN.bind('<<Stop>>', OCV.TK_MAIN.stopRun)
        OCV.TK_MAIN.bind('<<Pause>>', OCV.TK_MAIN.pause)
        
        OCV.TK_MAIN.bind("<<ListboxSelect>>", OCV.TK_MAIN.selectionChange)
        OCV.TK_MAIN.bind("<<Modified>>", OCV.TK_MAIN.drawAfter)

        #--- Selection Binding

        OCV.TK_MAIN.bind('<Control-Key-a>', OCV.TK_MAIN.selectAll)
        OCV.TK_MAIN.bind('<Control-Key-A>', OCV.TK_MAIN.unselectAll)
        OCV.TK_MAIN.bind('<Escape>', OCV.TK_MAIN.unselectAll)
        OCV.TK_MAIN.bind('<Control-Key-i>', OCV.TK_MAIN.selectInvert)

        OCV.TK_MAIN.bind('<<SelectAll>>', OCV.TK_MAIN.selectAll)
        OCV.TK_MAIN.bind('<<SelectNone>>', OCV.TK_MAIN.unselectAll)
        OCV.TK_MAIN.bind('<<SelectInvert>>', OCV.TK_MAIN.selectInvert)
        OCV.TK_MAIN.bind('<<SelectLayer>>', OCV.TK_MAIN.selectLayer)
        OCV.TK_MAIN.bind('<<ShowInfo>>', OCV.TK_MAIN.showInfo)
        OCV.TK_MAIN.bind('<<ShowStats>>', OCV.TK_MAIN.showStats)


        OCV.TK_MAIN.bind("<<ERR_HELP>>", OCV.TK_MAIN.show_error_panel)
        OCV.TK_MAIN.bind("<<SET_HELP>>", OCV.TK_MAIN.show_settings_panel)

        tkExtra.bindEventData(OCV.TK_MAIN, "<<Status>>", OCV.TK_MAIN.updateStatus)
        tkExtra.bindEventData(OCV.TK_MAIN, "<<Coords>>", OCV.TK_MAIN.updateCanvasCoords)

        #--- Editor bindings
        OCV.TK_MAIN.bind("<<Add>>", OCV.TK_EDITOR.insertItem)
        OCV.TK_MAIN.bind("<<AddBlock>>", OCV.TK_EDITOR.insertBlock)
        OCV.TK_MAIN.bind("<<AddLine>>", OCV.TK_EDITOR.insertLine)
        OCV.TK_MAIN.bind("<<Clone>>", OCV.TK_EDITOR.clone)
        OCV.TK_MAIN.bind("<<ClearEditor>>", OCV.TK_MAIN.ClearEditor)
        OCV.TK_MAIN.bind("<<Delete>>", OCV.TK_EDITOR.deleteBlock)
        OCV.TK_MAIN.bind('<<Invert>>', OCV.TK_EDITOR.invertBlocks)
        OCV.TK_MAIN.bind('<<Expand>>', OCV.TK_EDITOR.toggleExpand)
        OCV.TK_MAIN.bind('<<EnableToggle>>', OCV.TK_EDITOR.toggleEnable)
        OCV.TK_MAIN.bind('<<Enable>>', OCV.TK_EDITOR.enable)
        OCV.TK_MAIN.bind('<<Disable>>', OCV.TK_EDITOR.disable)
        OCV.TK_MAIN.bind('<<ChangeColor>>', OCV.TK_EDITOR.changeColor)
        OCV.TK_MAIN.bind('<<Comment>>', OCV.TK_EDITOR.commentRow)
        OCV.TK_MAIN.bind('<<Join>>', OCV.TK_EDITOR.joinBlocks)
        OCV.TK_MAIN.bind('<<Split>>', OCV.TK_EDITOR.splitBlocks)

        OCV.TK_MAIN.bind('<Control-Key-e>', OCV.TK_EDITOR.toggleExpand)
        OCV.TK_MAIN.bind('<Control-Key-l>', OCV.TK_EDITOR.toggleEnable)

        #--- Canvas X-bindings
        OCV.TK_MAIN.bind("<<ViewChange>>", OCV.TK_MAIN.viewChange)
        OCV.TK_MAIN.bind("<<AddMarker>>", OCV.TK_CANVAS_F.canvas.setActionAddMarker)
        OCV.TK_MAIN.bind('<<MoveGantry>>', OCV.TK_CANVAS_F.canvas.setActionGantry)
        OCV.TK_MAIN.bind('<<SetWPOS>>', OCV.TK_CANVAS_F.canvas.setActionWPOS)
        OCV.TK_MAIN.bind('<<CameraOn>>', OCV.TK_CANVAS_F.canvas.cameraOn)
        OCV.TK_MAIN.bind('<<CameraOff>>', OCV.TK_CANVAS_F.canvas.cameraOff)
        OCV.TK_MAIN.bind('<<DrawProbe>>',
                  lambda e, c=OCV.TK_CANVAS_F: c.drawProbe(True))
        OCV.TK_MAIN.bind('<<DrawOrient>>', OCV.TK_CANVAS_F.canvas.drawOrient)

        OCV.TK_CANVAS_F.canvas.bind(
            "<Control-Key-Prior>", OCV.TK_EDITOR.orderUp)
        OCV.TK_CANVAS_F.canvas.bind(
            "<Control-Key-Next>", OCV.TK_EDITOR.orderDown)
        OCV.TK_CANVAS_F.canvas.bind('<Control-Key-c>', OCV.TK_MAIN.copy)
        OCV.TK_CANVAS_F.canvas.bind('<Control-Key-d>', OCV.TK_EDITOR.clone)
        OCV.TK_CANVAS_F.canvas.bind('<Control-Key-x>', OCV.TK_MAIN.cut)
        OCV.TK_CANVAS_F.canvas.bind('<Control-Key-v>', OCV.TK_MAIN.paste)
        OCV.TK_CANVAS_F.canvas.bind("<Delete>", OCV.TK_EDITOR.deleteBlock)
        OCV.TK_CANVAS_F.canvas.bind("<BackSpace>", OCV.TK_EDITOR.deleteBlock)

        try:
            OCV.TK_CANVAS_F.canvas.bind(
                "<KP_Delete>", OCV.TK_EDITOR.deleteBlock)
        except:
            pass

        #--- Misc Bindings
        OCV.TK_MAIN.bind('<<CanvasFocus>>', OCV.TK_MAIN.canvasFocus)
        OCV.TK_MAIN.bind('<<Draw>>', OCV.TK_MAIN.draw)


        OCV.TK_MAIN.bind('<Control-Key-n>', OCV.TK_MAIN.showInfo)
        OCV.TK_MAIN.bind('<<ShowInfo>>', OCV.TK_MAIN.showInfo)
        OCV.TK_MAIN.bind('<Control-Key-q>', OCV.TK_MAIN.quit)
        OCV.TK_MAIN.bind('<Control-Key-o>', OCV.TK_MAIN.loadDialog)
        OCV.TK_MAIN.bind('<Control-Key-r>', OCV.TK_MAIN.drawAfter)
        OCV.TK_MAIN.bind("<Control-Key-s>", OCV.TK_MAIN.saveAll)
        OCV.TK_MAIN.bind('<Control-Key-y>', OCV.TK_MAIN.redo)
        OCV.TK_MAIN.bind('<Control-Key-z>', OCV.TK_MAIN.undo)
        OCV.TK_MAIN.bind('<Control-Key-Z>', OCV.TK_MAIN.redo)
        OCV.TK_CANVAS_F.canvas.bind('<Key-space>', OCV.TK_MAIN.commandFocus)
        OCV.TK_MAIN.bind('<Control-Key-space>', OCV.TK_MAIN.commandFocus)
        OCV.TK_MAIN.bind('<<CommandFocus>>', OCV.TK_MAIN.commandFocus)

        #--- Tools Bindings
        OCV.TK_MAIN.bind('<<ToolAdd>>', OCV.TK_MAIN.pages["Tools"].add)
        OCV.TK_MAIN.bind('<<ToolDelete>>', OCV.TK_MAIN.pages["Tools"].delete)
        OCV.TK_MAIN.bind('<<ToolClone>>', OCV.TK_MAIN.pages["Tools"].clone)
        OCV.TK_MAIN.bind('<<ToolRename>>', OCV.TK_MAIN.pages["Tools"].rename)

        #--- Command Line Bindings
        OCV.TK_CMD_W.bind("<Return>", OCV.TK_MAIN.cmdExecute)
        OCV.TK_CMD_W.bind("<Up>", OCV.TK_MAIN.commandHistoryUp)
        OCV.TK_CMD_W.bind("<Down>", OCV.TK_MAIN.commandHistoryDown)
        OCV.TK_CMD_W.bind("<FocusIn>", OCV.TK_MAIN.commandFocusIn)
        OCV.TK_CMD_W.bind("<FocusOut>", OCV.TK_MAIN.commandFocusOut)
        OCV.TK_CMD_W.bind("<Key>", OCV.TK_MAIN.commandKey)
        OCV.TK_CMD_W.bind("<Control-Key-z>", OCV.TK_MAIN.undo)
        OCV.TK_CMD_W.bind("<Control-Key-Z>", OCV.TK_MAIN.redo)
        OCV.TK_CMD_W.bind("<Control-Key-y>", OCV.TK_MAIN.redo)
        
        #--- Machine control Bindings        
        OCV.TK_MAIN.bind('<<Home>>', OCV.TK_MAIN.ctrl_home)
        OCV.TK_MAIN.bind('<<FeedHold>>', OCV.TK_MAIN.ctrl_feedhold)
        OCV.TK_MAIN.bind('<<SoftReset>>', OCV.TK_MAIN.ctrl_softreset)
        OCV.TK_MAIN.bind('<<Unlock>>', OCV.TK_MAIN.ctrl_unlock)

        OCV.TK_MAIN.bind('<<JOG-XUP>>', OCV.TK_MAIN.jog_x_up)
        OCV.TK_MAIN.bind('<<JOG-XDW>>', OCV.TK_MAIN.jog_x_down)
        OCV.TK_MAIN.bind('<<JOG-YUP>>', OCV.TK_MAIN.jog_y_up)
        OCV.TK_MAIN.bind('<<JOG-YDW>>', OCV.TK_MAIN.jog_y_down)
        OCV.TK_MAIN.bind('<<JOG-ZUP>>', OCV.TK_MAIN.jog_z_up)
        OCV.TK_MAIN.bind('<<JOG-ZDW>>', OCV.TK_MAIN.jog_z_down)

        OCV.TK_MAIN.bind('<<JOG-XYUP>>', OCV.TK_MAIN.jog_x_up_y_up)
        OCV.TK_MAIN.bind('<<JOG-XUPYDW>>', OCV.TK_MAIN.jog_x_up_y_down)
        OCV.TK_MAIN.bind('<<JOG-XYDW>>', OCV.TK_MAIN.jog_x_down_y_down)
        OCV.TK_MAIN.bind('<<JOG-XDWYUP>>', OCV.TK_MAIN.jog_x_down_y_up)
        
                
        if OCV.TK_MAIN._swapKeyboard == 1:
            OCV.TK_MAIN.bind('<Right>', OCV.TK_MAIN.jog_y_up)
            OCV.TK_MAIN.bind('<Left>', OCV.TK_MAIN.jog_y_down)
            OCV.TK_MAIN.bind('<Up>', OCV.TK_MAIN.jog_x_down)
            OCV.TK_MAIN.bind('<Down>', OCV.TK_MAIN.jog_x_up)
        elif OCV.TK_MAIN._swapKeyboard == -1:
            OCV.TK_MAIN.bind('<Right>', OCV.TK_MAIN.jog_y_down)
            OCV.TK_MAIN.bind('<Left>', OCV.TK_MAIN.jog_y_up)
            OCV.TK_MAIN.bind('<Up>', OCV.TK_MAIN.jog_x_up)
            OCV.TK_MAIN.bind('<Down>', OCV.TK_MAIN.jog_x_down)
        else:
            OCV.TK_MAIN.bind('<Right>', OCV.TK_MAIN.jog_x_up)
            OCV.TK_MAIN.bind('<Left>', OCV.TK_MAIN.jog_x_down)
            OCV.TK_MAIN.bind('<Up>', OCV.TK_MAIN.jog_y_up)
            OCV.TK_MAIN.bind('<Down>', OCV.TK_MAIN.jog_y_down)

        OCV.TK_MAIN.bind('<Prior>', OCV.TK_MAIN.jog_z_up)
        OCV.TK_MAIN.bind('<Next>', OCV.TK_MAIN.jog_z_down)

        #--- KEYPAD Controls
        OCV.TK_MAIN.bind('<KP_Prior>', OCV.TK_MAIN.jog_z_up)
        OCV.TK_MAIN.bind('<KP_Next>', OCV.TK_MAIN.jog_z_down)

        try:
            if OCV.TK_MAIN._swapKeyboard == 1:
                OCV.TK_MAIN.bind('<KP_Right>', OCV.TK_MAIN.jog_y_up)
                OCV.TK_MAIN.bind('<KP_Left>', OCV.TK_MAIN.jog_y_down)
                OCV.TK_MAIN.bind('<KP_Up>', OCV.TK_MAIN.jog_x_down)
                OCV.TK_MAIN.bind('<KP_Down>', OCV.TK_MAIN.jog_x_up)
            elif OCV.TK_MAIN._swapKeyboard == -1:
                OCV.TK_MAIN.bind('<KP_Right>', OCV.TK_MAIN.jog_y_down)
                OCV.TK_MAIN.bind('<KP_Left>', OCV.TK_MAIN.jog_y_up)
                OCV.TK_MAIN.bind('<KP_Up>', OCV.TK_MAIN.jog_x_up)
                OCV.TK_MAIN.bind('<KP_Down>', OCV.TK_MAIN.jog_x_down)
            else:
                OCV.TK_MAIN.bind('<KP_Right>', OCV.TK_MAIN.jog_x_up)
                OCV.TK_MAIN.bind('<KP_Left>', OCV.TK_MAIN.jog_x_down)
                OCV.TK_MAIN.bind('<KP_Up>', OCV.TK_MAIN.jog_y_up)
                OCV.TK_MAIN.bind('<KP_Down>', OCV.TK_MAIN.jog_y_down)
        except Tk.TclError:
            pass

        OCV.TK_MAIN.bind('<Key-plus>', OCV.TK_MAIN.cycle_up_step_xy)
        OCV.TK_MAIN.bind('<KP_Add>', OCV.TK_MAIN.cycle_up_step_xy)

        OCV.TK_MAIN.bind('<Key-minus>', OCV.TK_MAIN.cycle_dw_step_xy)
        OCV.TK_MAIN.bind('<KP_Subtract>', OCV.TK_MAIN.cycle_dw_step_xy)

        OCV.TK_MAIN.bind('<Key-asterisk>', OCV.TK_MAIN.cycle_up_step_z)
        OCV.TK_MAIN.bind('<KP_Multiply>', OCV.TK_MAIN.cycle_up_step_z)

        OCV.TK_MAIN.bind('<Key-slash>', OCV.TK_MAIN.cycle_dw_step_z)
        OCV.TK_MAIN.bind('<KP_Divide>', OCV.TK_MAIN.cycle_dw_step_z)
        
        #--- Memory Bindings
        OCV.TK_MAIN.bind('<<SetMem>>', OCV.TK_MAIN.setMem)
        OCV.TK_MAIN.bind('<<ClrMem>>', OCV.TK_MAIN.clrMem)
        OCV.TK_MAIN.bind('<<SaveMems>>', OCV.TK_MAIN.saveMems)

        #--- CAMGen Bindings
        OCV.TK_MAIN.bind("<<MOP_OK>>", OCV.TK_MAIN.mop_ok)
        