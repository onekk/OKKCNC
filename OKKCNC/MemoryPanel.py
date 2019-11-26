#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 10:38:02 2019

@author: carlo
"""
from __future__ import absolute_import
from __future__ import print_function

# Import Tkinter
try:
    import Tkinter as Tk
except ImportError:
    import tkinter as Tk

import OCV
import tkExtra
import Utils
import CNCRibbon


#===============================================================================
# Memory Group
#===============================================================================
class MemoryGroup(CNCRibbon.ButtonMenuGroup):

    def __init__(self, master, app):
        CNCRibbon.ButtonMenuGroup.__init__(self, master, N_("Memory"), app,
            [(_("Save Memories"), "save", lambda a=app:a.event_generate("<<SaveMems>>")),
             (_("Show this Bank"), "view", self.showBankMem),
             (_("Don't Show this Bank"), "view", self.showBankMem),
             (_("Don't Show Memories"), "view", self.resetMemView),

             ])

        col, row = 0,0
        b = Tk.Button(self.frame,
                #image=Utils.icons["start32"],
                font = OCV.FONT,
                text=_("M2A"),
                background=OCV.BACKGROUND,
                command = None
                )
        b.grid(row=row, column=col)# padx=0, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Memory to A"))
        self.addWidget(b)

        row +=1
        b = Tk.Button(self.frame,
                #image=Utils.icons["pause32"],
                font = OCV.FONT,
                text=_("M2B"),
                background=OCV.BACKGROUND,
                command = None)
        b.grid(row=row, column=col)#, padx=0, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Memory to B"))
        self.addWidget(b)

        row +=1
        b = Tk.Button(self.frame,
                #image=Utils.icons["stop32"],
                font = OCV.FONT,
                text=_("C_M"),
                command = self.clrX,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col)#, padx=0, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Cancel mem X"))
        self.addWidget(b)

        row, col = 0, 1

        b = Tk.Label(self.frame, name = "lab_bank", text = "B {0}".format(OCV.WK_bank),
                  background=OCV.BACKGROUND_LABELS)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Bank Number \n Mem {0}".format(OCV.WK_mem_num)))
        self.addWidget(b)

        row +=1

        b = Tk.Button(self.frame,
                #image=Utils.icons["pause32"],
                font = OCV.FONT,
                text=_("B +"),
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.EW)
        b.bind("<1>", lambda event, obj="B+": self.onClickBank(event, obj))
        tkExtra.Balloon.set(b, _("Upper Memory Bank"))
        self.addWidget(b)

        row +=1

        b = Tk.Button(self.frame,
                #image=Utils.icons["stop32"],
                font = OCV.FONT,
                text=_("B -"),
                compound=Tk.TOP,
                background=OCV.BACKGROUND)
        b.grid(row=row, column=col, padx=0, pady=0, sticky=Tk.EW)
        b.bind("<1>", lambda event, obj="B-": self.onClickBank(event, obj))
        tkExtra.Balloon.set(b, _("Lower Memory Bank"))
        self.addWidget(b)


        for x in range(0, OCV.WK_bank_mem, 3):
            col +=1
            rows = 0
            for xa in range(x, x+3):
                but_name = "but_m_{0}".format(str(xa))
                #print("creation", but_name)
                b = Tk.Button(self.frame,
                    #image=Utils.icons["pause32"],
                    font = OCV.FONT,
                    name = but_name,
                    text="M_{0}".format(xa + 2),
                    compound=Tk.TOP,
                    background=OCV.BACKGROUND)

                b.grid(row=rows, column=col, padx=0, pady=0, sticky=Tk.NSEW)
                b.bind("<Button-1>",
                       lambda event, obj=xa: self.onClickMem(event, obj))
                b.bind("<Button-3>",
                       lambda event, obj=xa: self.onClickMem(event, obj))
                tkExtra.Balloon.set(b, _("Set {0}"))
                self.addWidget(b)
                rows +=1

        print("MemoryGroup: Init end")
        self.selectBank(0)

    def onClickMem(self, event, obj):
        if OCV.CD["state"] == "Idle":
            #print(event.num)
            #print("Button {0} CLicked".format(obj))
            mem_clicked = (OCV.WK_bank * OCV.WK_bank_mem) + 2 + obj
            mem_key = "mem_{0}".format(mem_clicked)
            #print ("{0} clicked".format(mem_key))

            # Left Button Clicked, goto position
            if event.num == 1:
                if mem_key in OCV.WK_mems:
                    md = OCV.WK_mems[mem_key]
                    if md[3] == 1:
                        self.sendGCode("$J=G90 G53 {0}{1:f} {2}{3:f} F100000".format(
                                "X", md[0],
                                "Y", md[1]))

            # Right Button Clicked, set mem
            if event.num == 3:
                OCV.WK_mem = mem_clicked
                mem_name = Utils.InputValue(OCV.application, "ME")
                #print("MG mem_name = ", mem_name)
                if mem_name is None:
                    mem_name = mem_key

                OCV.WK_mems[mem_key] = [
                        OCV.CD["mx"],
                        OCV.CD["my"],
                        OCV.CD["mz"],
                        1,
                        mem_name]

                # refresh buttons
                # force the refres of all buttons as the creation is done
                # in batch
                self.selectBank(OCV.WK_bank)

                self.event_generate("<<SetMem>>")
        else:
            return

    def onClickBank(self, event, obj):
        #print("you clicked on", obj)
        if (obj == "B+"):
            mem_bank = OCV.WK_bank + 1
        elif (obj == "B-"):
            mem_bank = OCV.WK_bank - 1
        else:
            return

        if (mem_bank < 0):
            OCV.WK_bank = 0
            mem_bank = 0
        elif (mem_bank > 3):
            OCV.WK_bank = 3
            mem_bank = 3

        self.selectBank(mem_bank)


    def selectBank(self, mem_bank):
        # assign the proper values
        OCV.WK_bank = mem_bank
        OCV.WK_bank_start = (OCV.WK_bank * OCV.WK_bank_mem) + 2
        wd = self.frame.nametowidget("lab_bank")
        wd.config(text="B {0}".format(OCV.WK_bank))
        but_color = OCV.BACKGROUND

        for x in range(0, OCV.WK_bank_mem):
            but_name = "but_m_{0}".format(str(x))
            label = "M_{0}".format(OCV.WK_bank_start + x)
            mem_addr = "mem_{0}".format(OCV.WK_bank_start + x)
            mem_tt = "{0}\n\n name: {5}\n\nX: {1}\n\nY: {2}\n\nZ: {3}"
            wd = self.frame.nametowidget(but_name)

            if mem_addr in OCV.WK_mems:
                if OCV.WK_mems[mem_addr][3] == 1:
                    but_color = "aquamarine"
                    md = OCV.WK_mems[mem_addr]
                    #print("Select Bank ", md)
                    tkExtra.Balloon.set(wd,mem_tt.format(mem_addr, *md))
            else:
                but_color = OCV.BACKGROUND
                tkExtra.Balloon.set(wd,"Empty")

            wd.config(text=label, background=but_color)

    def clrX(self):
        mem_num = Utils.InputValue(OCV.application, "MN")

        #print("clrX >", mem_num)

        if mem_num is not None:
            mem_addr = "mem_{0}".format(mem_num)
            OCV.WK_mems[mem_addr] = [0,0,0,0,"Empty"]
            # clear the marker on canvas
            # and the canvas memnory shown list
            OCV.WK_mem = mem_num
            self.event_generate("<<ClrMem>>")
            #check if the button is shown
            b_check = self.checkBtnV(mem_num)

            #print ("clrX check > ",b_check)

            if ( b_check > 0):
                # reset the button state
                but_name = "but_m_{0}".format(mem_num - OCV.WK_bank_start)
                label = "M_{0}".format(mem_num)
                print("clrX but_name > ", but_name)
                wd = self.frame.nametowidget(but_name)
                but_color = OCV.BACKGROUND
                tkExtra.Balloon.set(wd,"Empty")
                wd.config(text=label, background=but_color)

        #print(OCV.WK_mems)

    def checkBtnV(self, mem_num):
        upp_mem = OCV.WK_bank_start + OCV.WK_bank_mem
        #print ("check Button {0} in range {1} {2}".format(
        #        mem_num, OCV.WK_bank_start, upp_mem))
        if mem_num in range(OCV.WK_bank_start, upp_mem):
            return mem_num
        else:
            return -1

    def showBankMem(self):
        #print("sBM Bank >> ", OCV.WK_bank)
        for x in range(0, OCV.WK_bank_mem):
            mem_num = OCV.WK_bank_start + x
            mem_addr = "mem_{0}".format(mem_num)

            # check the presence of the key in dictionary
            if mem_addr in OCV.WK_mems:
                # chek if the memory is valid
                md = OCV.WK_mems[mem_addr]
                #print("sBM md >> ", md)
                if  md[3] == 1:
                    OCV.WK_mem = mem_num
                    OCV.application.event_generate("<<SetMem>>")

    def resetMemView(self):
        indices = [i for i, x in enumerate(OCV.WK_active_mems) if x == 2]
        for mem in indices:
            print("resetMemView index = ", mem)
            OCV.WK_mem = mem
            OCV.application.event_generate("<<ClrMem>>")



class Config():

    @staticmethod
    def loadMemory():
        # maybe soem values in Memory
        #relative to WK_bank_max and WK_bank_num
        # init the memory vars
        OCV.WK_mem_num = ((OCV.WK_bank_max + 1) * OCV.WK_bank_mem) + 1
        OCV.WK_active_mems = []

        for i in range(0, OCV.WK_mem_num + 1):
            OCV.WK_active_mems.append(0)

        OCV.WK_bank_show = []

        for i in range(0, OCV.WK_bank_max + 1):
            OCV.WK_bank_show.append(0)

        for name, value in Utils.config.items("Memory"):
            content = value.split(",")
            #print("Key: {0}  Name: {1} Value: X{2} Y{3} Z{4}".format(name, *content ))
            OCV.WK_mems[name] = [
                float(content[1]),
                float(content[2]),
                float(content[3]),
                1,
                content[0]]
        #print("Load Memory ended")

    @staticmethod
    def saveMemory():
        for mem_name in OCV.WK_mems:
            md = OCV.WK_mems[mem_name]
            # Test the indicator and delete the memory from config if
            # indicator = 0
            if md[3] is not 0:
                mem_value = "{0}, {1:.4f}, {2:.4f}, {3:.4f}, {4:d}".format(
                    md[4], md[0], md[1], md[2], md[3])
                Utils.setStr("Memory", mem_name, mem_value)
            else:
                Utils.removeValue("Memory", mem_name)

