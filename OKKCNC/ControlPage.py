# -*- coding: ascii -*-
# $Id$
#
# Author: carlo.dormeletti@gmail.com
# Date: 26 Oct 2019

from __future__ import absolute_import
from __future__ import print_function

try:
    import Tkinter as Tk
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import math
from math import * #Math in DRO

import OCV
import CAMGen
import CNCRibbon
import Commands as cmd
import Interface
import Ribbon
import Sender
import tkExtra
import Unicode
import Utils

#from CNC import Block

OCV.FONT = ("Sans", "-10")

_LOWSTEP = 0.0001
_HIGHSTEP = 1000.0
_HIGHZSTEP = 10.0
_NOZSTEP = 'XY'

OVERRIDES = ["Feed", "Rapid", "Spindle"]



#===============================================================================
# ControlFrame
#===============================================================================
class ControlFrame(CNCRibbon.PageLabelFrame):

    z_step_font = ('Helvetica', 7, 'bold')

    def __init__(self, master, app):
        CNCRibbon.PageLabelFrame.__init__(self, master, "Control", _("Control"), app)

        """
        print("ControlFrame self.app > ", self.app)
        print("OCV.APP > ", OCV.APP)
        """

        Tk.Label(self, text="Y").grid(row=6, column=3)

        Tk.Label(self, "", width=1).grid(row=1, column=10)

        b_width = 2
        b_height = 2

        z_step_font = Utils.getFont("z_step.font", ControlFrame.z_step_font)

        Utils.SetSteps()

        row = 0

        zstep = Utils.config.get("Control", "zstep")
        self.zstep = tkExtra.Combobox(self, width=4, background="White")
        self.zstep.grid(row=row, column=0, columnspan=4, sticky=Tk.EW)
        self.zstep.set(zstep)
        self.zstep.fill(map(float, Utils.config.get("Control","zsteplist").split()))
        tkExtra.Balloon.set(self.zstep, _("Step for Z move operation"))
        self.addWidget(self.zstep)

        b = Tk.Button(
            self,
            text="{0}".format(OCV.step1),
            name="step_1",
            command=self.setStep1,
            width=2,
            padx=1, pady=1)
        b.grid(row=row, column = 4, columnspan = 2, sticky=Tk.EW)
        b.bind("<Button-3>", lambda event: self.editStep("S1"))
        bal_text = _("Step1 = {0}").format(OCV.step1)
        tkExtra.Balloon.set(b, bal_text)
        self.addWidget(b)

        b = Tk.Button(
            self,
            text="{0}".format(OCV.step2),
            name="step_2",
            command=self.setStep2,
            width=2,
            padx=1, pady=1)
        b.grid(row=row, column = 6, columnspan = 2, sticky=Tk.EW)
        b.bind("<Button-3>", lambda event: self.editStep("S2"))
        bal_text = _("Step2 = {0}").format(OCV.step2)
        tkExtra.Balloon.set(b, bal_text)
        self.addWidget(b)

        b = Tk.Button(
            self,
            text="{0}".format(OCV.step3),
            name="step_3",
            command=self.setStep3,
            width=2,
            padx=1, pady=1)
        b.grid(row=row, column=8, columnspan = 2, sticky=Tk.EW)
        b.bind("<Button-3>", lambda event: self.editStep("S3"))
        bal_text = _("Step3 = {0}").format(OCV.step3)
        tkExtra.Balloon.set(b, bal_text)
        self.addWidget(b)

        row = 1

        b = Tk.Button(
            self,
            text=u"\u00F75",
            command=self.divStep,
            width=3,
            padx=1, pady=1)
        b.grid(row=row, column=4, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Divide step by 5"))
        self.addWidget(b)

        b = Tk.Button(
            self,
            text=u"\u00D75",
            command=self.mulStep,
            width=3,
            padx=1, pady=1)
        b.grid(row=row, column=5, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Multiply step by 5"))
        self.addWidget(b)

        self.step = tkExtra.Combobox(self, width=6, background="White")
        self.step.grid(row=row, column=6, columnspan=2, sticky=Tk.EW)
        self.step.set(Utils.config.get("Control","step"))
        self.step.fill(map(float, Utils.config.get("Control","steplist").split()))
        tkExtra.Balloon.set(self.step, _("Step for coarse move operation"))
        self.addWidget(self.step)

        b = Tk.Button(self, text="<",
                    command=self.decStep,
                    width=3,
                    padx=1, pady=1)
        b.grid(row=row, column=8, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Decrease step"))
        self.addWidget(b)

        b = Tk.Button(self, text=">",
                command=self.incStep,
                width=3,
                padx=1, pady=1)
        b.grid(row=row, column=9, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Increase step"))
        self.addWidget(b)

        row = 2

        b = Tk.Button(self, text="-",
                command=self.decZStep,
                padx=1, pady=1)
        b.grid(row=row, column=0, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Decrease zstep"))
        self.addWidget(b)

        b = Tk.Button(self, text="+",
                command=self.incZStep,
                padx=1, pady=1)
        b.grid(row=row, column=1, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Increase zstep"))
        self.addWidget(b)

        b = Tk.Button(self, text="-",
                    command=self.decStepF,
                    width=3,
                    padx=1, pady=1)
        b.grid(row=row, column=8, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Decrease step fine"))
        self.addWidget(b)

        b = Tk.Button(self, text="+",
                command=self.incStepF,
                width=3,
                padx=1, pady=1)
        b.grid(row=row, column=9, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Increase step fine"))
        self.addWidget(b)

        row = 3

        Tk.Label(self, text="Z").grid(row=3, column=0, columnspan=2)
        Tk.Label(self, text="X").grid(row=3,column=6, columnspan=2)

        row = 4

        b = Tk.Button(self, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
                    command=self.moveZup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=0,columnspan=2,rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move +Z"))
        self.addWidget(b)

        b = Tk.Button(self, text=Unicode.UPPER_LEFT_TRIANGLE,
                    command=self.moveXdownYup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")

        b.grid(row=row, column=4, columnspan=2,rowspan=2,  sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move -X +Y"))
        self.addWidget(b)

        b = Tk.Button(self, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
                    command=self.moveYup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=6, columnspan=2, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move +Y"))
        self.addWidget(b)

        b = Tk.Button(self, text=Unicode.UPPER_RIGHT_TRIANGLE,
                    command=self.moveXupYup,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=8, columnspan=2, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move +X +Y"))
        self.addWidget(b)

        row = 6

        b = Tk.Button(self, text="{0}".format(OCV.zstep1),
                name="zstep_1",
                font =  z_step_font,
                command=self.setZStep1,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=0, columnspan = 1, sticky=Tk.EW)
        b.bind("<Button-3>" ,lambda event: self.editStep("ZS1"))
        bal_text = _("Z Step1 = {0}".format(OCV.zstep1))
        tkExtra.Balloon.set(b, bal_text)
        self.addWidget(b)

        b = Tk.Button(self, text="{0}".format(OCV.zstep2),
                name="zstep_2",
                font =  z_step_font,
                command=self.setZStep2,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=1, columnspan = 1, sticky=Tk.EW)
        b.bind("<Button-3>" ,lambda event: self.editStep("ZS2"))
        bal_text = _("Z Step2 = {0}".format(OCV.zstep2))
        tkExtra.Balloon.set(b, bal_text)
        self.addWidget(b)


        b = Tk.Button(self, text=Unicode.BLACK_LEFT_POINTING_TRIANGLE,
                    command=self.moveXdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=4, columnspan=2, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move -X"))
        self.addWidget(b)

        b = Utils.UserButton(
                self, OCV.APP,
                0,
                text=Unicode.LARGE_CIRCLE,
                command=self.go2origin,
                width=b_width, height=b_height,
                activebackground="LightYellow")

        b.grid(row=row, column=6, columnspan=2, rowspan=2, sticky=Tk.EW)

        tkExtra.Balloon.set(b, _("Move to Origin.\nUser configurable button.\nRight click to configure."))

        self.addWidget(b)

        b = Tk.Button(
                self,
                text=Unicode.BLACK_RIGHT_POINTING_TRIANGLE,
                command=self.moveXup,
                width=b_width, height=b_height,
                activebackground="LightYellow")

        b.grid(row=row, column=8, columnspan=2, rowspan=2, sticky=Tk.EW)

        tkExtra.Balloon.set(b, _("Move +X"))

        self.addWidget(b)


        row = 7

        b = Tk.Button(
                self,
                text="{0}".format(OCV.zstep3),
                name="zstep_3",
                font =  z_step_font,
                command=self.setZStep3,
                width=2,
                padx=1, pady=1)

        b.grid(row=row, column=0, columnspan = 1, sticky=Tk.EW)

        b.bind("<Button-3>" ,lambda event: self.editStep("ZS3"))

        bal_text = _("Z Step3 = {0}".format(OCV.zstep3))

        tkExtra.Balloon.set(b, bal_text)

        self.addWidget(b)

        b = Tk.Button(self, text="{0}".format(OCV.zstep4),
                name="zstep_4",
                font =  z_step_font,
                command=self.setZStep4,
                width=2,
                padx=1, pady=1)
        b.grid(row=row, column=1, columnspan = 1, sticky=Tk.EW)
        b.bind("<Button-3>" ,lambda event: self.editStep("ZS4"))
        bal_text = _("Z Step4 = {0}".format(OCV.zstep4))
        tkExtra.Balloon.set(b, bal_text)
        self.addWidget(b)

        row = 8

        b = Tk.Button(self, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
                    command=self.moveZdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=0, columnspan=2, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move -Z"))
        self.addWidget(b)


        b = Tk.Button(self, text=Unicode.LOWER_LEFT_TRIANGLE,
                    command=self.moveXdownYdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=4,columnspan=2,rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move -X -Y"))
        self.addWidget(b)

        b = Tk.Button(self, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
                    command=self.moveYdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=6,columnspan=2,rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move -Y"))
        self.addWidget(b)

        b = Tk.Button(self, text=Unicode.LOWER_RIGHT_TRIANGLE,
                    command=self.moveXupYdown,
                    width=b_width, height=b_height,
                    activebackground="LightYellow")
        b.grid(row=row, column=8,columnspan=2,rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Move +X -Y"))
        self.addWidget(b)

        #----------------
        #- CAM controls -
        #----------------
        column = 11
        b_padx = 0
        b_pady = -1

        b = Tk.Button(self, text="RST",
                    name = "rst",
                    command=self.resetAll,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    background = "salmon",
                    activebackground="LightYellow")
        b.grid(row=0, column=column, columnspan=2, rowspan=1, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Reset Gcode"))
        self.addWidget(b)

        b = Tk.Button(self, text="m A",
                    name = "memA",
                    command=self.memA,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    background = "orchid1",
                    activebackground="LightYellow")
        b.grid(row=1, column=column, columnspan=2, rowspan=1, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Mem A"))
        self.addWidget(b)


        b = Tk.Button(self, text="m B",
                    name = "memB",
                    command=self.memB,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    background = "orchid1",
                    activebackground="LightYellow")
        b.grid(row=2, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Mem B"))
        self.addWidget(b)

        b = Tk.Button(self, text="line",
                    command=self.line,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=3, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Cut Line from memA to memB"))
        self.addWidget(b)

        b = Tk.Button(self, text="r_pt",
                    command=self.pocket,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=4, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Cut Pocket from memA to memB"))
        self.addWidget(b)

        b = Tk.Button(self, text="RmA",
                    command=self.retA,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=5, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Return to mem A"))
        self.addWidget(b)

        b = Tk.Button(self, text="RmB",
                    command=self.retB,
                    width=3,
                    padx=b_padx, pady=b_pady,
                    activebackground="LightYellow")
        b.grid(row=6, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(b, _("Return to mem B"))
        self.addWidget(b)

        try:
#            self.grid_anchor(CENTER)
            self.tk.call("grid", "anchor", self, Tk.CENTER)
        except Tk.TclError:
            pass


    def saveConfig(self):
        Utils.setFloat("Control", "step", self.step.get())
        Utils.setFloat("Control", "zstep", self.zstep.get())

    def resetAll(self):
        self.event_generate("<<ClearEditor>>")
        wd = self.nametowidget("memA")
        tkExtra.Balloon.set(wd, "Empty")
        wd.configure(background = "orchid1")

        OCV.WK_mem = 0 # memA
        self.event_generate("<<ClrMem>>")

        OCV.WK_mem = 1 # memB
        wd = self.nametowidget("memB")
        tkExtra.Balloon.set(wd, "Empty")
        wd.configure(background = "orchid1")

        self.event_generate("<<ClrMem>>")


    def memA(self):
        if OCV.c_state == "Idle":
            print("mem_A 1st")
            px = OCV.CD["wx"]
            py = OCV.CD["wy"]
            pz = OCV.CD["wz"]
            OCV.WK_mem = 0 # 1= memB

            mem_name = "memA"
            OCV.WK_mems["mem_0"] = [px, py, pz, 1,"mem A"]
            wd = self.nametowidget(mem_name)

            wdata =  "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(mem_name, px, py, pz)

            tkExtra.Balloon.set(wd, wdata)
            wd.configure(background = "aquamarine")

            self.event_generate("<<SetMem>>")
        else:
            pass


    def memB(self):
        if OCV.c_state == "Idle":
            px = OCV.CD["wx"]
            py = OCV.CD["wy"]
            pz = OCV.CD["wz"]
            OCV.WK_mem = 1 # 1= memB

            mem_name = "memB"
            OCV.WK_mems["mem_1"] = [px, py, pz,1, "mem B"]
            wd = self.nametowidget(mem_name)

            wdata =  "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(mem_name, px, py, pz)

            tkExtra.Balloon.set(wd, wdata)
            wd.configure(background = "aquamarine")

            self.event_generate("<<SetMem>>")
        else:
            pass

    def retA(self):
        if OCV.c_state == "Idle":
            if ("mem_0" in OCV.WK_mems):
                md = OCV.WK_mems["mem_0"]
                #print ("RmA {0} {1}".format(md[0],md[1]))
                self.sendGCode("$J=G90 {0}{1:f} {2}{3:f} F100000".format(
                            "X", md[0],
                            "Y", md[1]))
        else:
            pass

    def retB(self):
        if OCV.c_state == "Idle":
            if ("mem_1" in OCV.WK_mems):
                md = OCV.WK_mems["mem_1"]
                #print ("RmB {0} {1}".format(md[0],md[1]))
                self.sendGCode("$J=G90 {0}{1:f} {2}{3:f} F100000".format(
                            "X", md[0],
                            "Y", md[1]))
        else:
            pass

    def line(self):
        # avoid a dry run if both mem pos are not set
        if (OCV.WK_mems["mem_0"][3] > 0 and OCV.WK_mems["mem_1"][3] > 0):

            endDepth = Utils.InputValue(OCV.APP, "TD")

            if endDepth is None:
                return

            CAMGen.line(self, OCV.APP, endDepth, "mem_0", "mem_1")

    def pocket(self):

        # avoid a dry run if both mem pos are not set
        if (OCV.WK_mems["mem_0"][3] > 0 and OCV.WK_mems["mem_1"][3] > 0):
            endDepth = Utils.InputValue(OCV.APP, "TD")

            if endDepth is None:
                return

            CAMGen.pocket(self, OCV.APP, endDepth, "mem_0", "mem_1")


    #----------------------------------------------------------------------
    # Jogging
    #----------------------------------------------------------------------

    def moveXup(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f}".format("X", float(self.step.get())))

    def moveXdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f}".format("X-", float(self.step.get())))

    def moveYup(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f}".format("Y",float(self.step.get())))

    def moveYdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f}".format("Y-", float(self.step.get())))

    def moveXdownYup(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X-", float(self.step.get()),
                "Y", float(self.step.get())))

    def moveXupYup(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X", float(self.step.get()),
                "Y", float(self.step.get())))

    def moveXdownYdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X-", float(self.step.get()),
                "Y-", float(self.step.get())))

    def moveXupYdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f} {2}{3:f}".format(
                "X", float(self.step.get()),
                "Y-", float(self.step.get())))

    def moveZup(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f}".format("Z", float(self.zstep.get())))

    def moveZdown(self, event=None):
        if event is not None and not self.acceptKey(): return
        OCV.mcontrol.jog("{0}{1:f}".format("Z-", float(self.zstep.get())))

    def go2origin(self, event=None):
        self.sendGCode("G90")
        self.sendGCode("G0Z{0:.{1}f}".format(OCV.CD['safe'], OCV.digits))
        self.sendGCode("G0X0Y0")
        self.sendGCode("G0Z0")


    def setStep(self, s, zs=None,fs=None):
        self.step.set("{0:.4f}".format(float(s)))

        if fs is not None:
            #FIXME the stepf is not defined, maybe a leftover.
            #self.stepf.set("{0:.4f}".format(fs))
            pass

        if self.zstep is self.step or zs is None:
            self.event_generate("<<Status>>",
                data=_("Step: {0:.4f}".format(float(s))))
        else:
            self.zstep.set("{0:.4f}".format(float(zs)))
            self.event_generate("<<Status>>",
                data=_("Step: {0:.4f}    Zstep: {1:.4f} ".format(float(s),float(zs))))

    #----------------------------------------------------------------------
    @staticmethod
    def _stepPower(step):
        try:
            step = float(step)
            if step <= 0.0: step = 1.0
        except:
            step = 1.0
        power = math.pow(10.0,math.floor(math.log10(step)))
        return round(step/power)*power, power

    #----------------------------------------------------------------------
    def incStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step+power
        zs = None
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def incStepF(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(OCV.step1)
        s = float(self.step.get()) + power
        zs = None
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def incZStep(self, event=None):
        step, power = ControlFrame._stepPower(self.zstep.get())
        s = float(self.step.get())
        zs = step+power
        if zs<_LOWSTEP: zs = _LOWSTEP
        elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
        self.setStep(s,zs)

    #----------------------------------------------------------------------
    def decStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step - power
        zs = None
        if s<=0.0: s = step-power/10.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def decStepF(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(OCV.step1)
        s = float(self.step.get()) - power
        zs = None
        if s<=0.0: s = step-power/10.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        self.setStep(s, zs)

    def decZStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.zstep.get())
        s = float(self.step.get())
        zs = step-power
        if zs<=0.0: zs = step-power/10.0
        if zs<_LOWSTEP: zs = _LOWSTEP
        elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
        self.setStep(s,zs)

    #----------------------------------------------------------------------
    def mulStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step*5.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        zs=None
        self.setStep(s, zs)

    #----------------------------------------------------------------------
    def divStep(self, event=None):
        if event is not None and not self.acceptKey(): return
        step, power = ControlFrame._stepPower(self.step.get())
        s = step/5.0
        if s<_LOWSTEP: s = _LOWSTEP
        elif s>_HIGHSTEP: s = _HIGHSTEP
        zs=None
        self.setStep(s, zs)

    def setZStep1(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep1)

    #----------------------------------------------------------------------
    def setZStep2(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep2)

    #----------------------------------------------------------------------
    def setZStep3(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep3)

   #----------------------------------------------------------------------
    def setZStep4(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(float(self.step.get()), OCV.zstep4)

    #----------------------------------------------------------------------
    def setStep1(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(OCV.step1, float(self.zstep.get()))

    #----------------------------------------------------------------------
    def setStep2(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(OCV.step2, float(self.zstep.get()))

    #----------------------------------------------------------------------
    def setStep3(self, event=None):
        if event is not None and not self.acceptKey(): return
        self.setStep(OCV.step3, float(self.zstep.get()))

    def editStep(self, caller):
        print ("caller > ", caller)
        retval = Utils.InputValue(self, caller)
        if retval == None: return

        print ("retval > ", retval)
        if caller in ("S1", "S2", "S3"):
            if caller == "S1":
                wd = self.nametowidget("step_1")
                OCV.step1 = retval
                bal_text = "Step1 = {0}".format(OCV.step1)
                Utils.setFloat("Control", "step1", retval)
            elif caller == "S2":
                wd = self.nametowidget("step_2")
                OCV.step2 = retval
                bal_text = "Step2 = {0}".format(OCV.step2)
                Utils.setFloat("Control", "step2", retval)
            elif caller == "S3":
                wd = self.nametowidget("step_3")
                OCV.step3 = retval
                Utils.setFloat("Control", "step3", retval)
                bal_text = "Step2 = {0}".format(OCV.step3)

        elif caller in ("ZS1", "ZS2", "ZS3", "ZS4"):
            if caller == "ZS1":
                wd = self.nametowidget("zstep_1")
                OCV.zstep1 = retval
                bal_text = "Zstep1 = {0}".format(OCV.zstep1)
                Utils.setFloat("Control", "zstep1", retval)
            elif caller == "ZS2":
                wd = self.nametowidget("zstep_2")
                OCV.zstep2 = retval
                bal_text = "Zstep2 = {0}".format(OCV.zstep2)
                Utils.setFloat("Control", "zstep2", retval)
            elif caller == "ZS3":
                wd = self.nametowidget("zstep_3")
                OCV.zstep3 = retval
                bal_text = "Zstep2 = {0}".format(OCV.zstep3)
                Utils.setFloat("Control", "zstep3", retval)
            elif caller == "ZS4":
                wd = self.nametowidget("zstep_4")
                OCV.zstep4 = retval
                bal_text = "Zstep4 = {0}".format(OCV.zstep4)
                Utils.setFloat("Control", "zstep4", retval)

        if wd is not None:
            wd.configure(text = retval)
            tkExtra.Balloon.set(wd, bal_text)


#===============================================================================
# StateFrame
#===============================================================================
class StateFrame(CNCRibbon.PageExLabelFrame):
    def __init__(self, master, app):
        CNCRibbon.PageExLabelFrame.__init__(self, master, "State", _("State"), app)
        self._gUpdate = False

        #print("StateFrame self.app",self.app)

        # State
        f = Tk.Frame(self())
        f.pack(side=Tk.TOP, fill=Tk.X)

        col,row = 0,0
        f2 = Tk.Frame(f)
        f2.grid(row=row, column=col, columnspan=5,sticky=Tk.EW)
        for p,w in enumerate(OCV.WCS):
            col += 1
            b = Tk.Radiobutton(f2, text=w,
                    foreground="DarkRed",
                    font = OCV.STATE_WCS_FONT,
                    padx=1, pady=1,
                    variable=OCV.wcsvar,
                    value=p,
                    indicatoron=0,
                    activebackground="LightYellow",
                    command=self.wcsChange)
            b.pack(side=Tk.LEFT, fill=Tk.X, expand=Tk.YES)
            tkExtra.Balloon.set(b, _("Switch to workspace %s")%(w))
            self.addWidget(b)


        row += 1

        label_text = (_("Distance:"), _("Units:"), _("Tool:"), _("Plane:"),
                      _("Feed:"), _("Mode:"), _("TLO:"), _("G92:"))
        label_pos  = ((row, 0), (row, 3), (row + 1, 0), (row + 1, 3),
                      (row + 2, 0), (row + 2, 3), (row + 3, 0), (row + 3, 3))

        for idx, val in enumerate(label_text):
            lab = Tk.Label(
                f,
                text=label_text[idx],
                font=OCV.STATE_BUT_FONT)
            lab.grid(row=label_pos[idx][0], column=label_pos[idx][1], sticky=Tk.E)

        # Absolute or relative mode
        col = 1
        self.distance = tkExtra.Combobox(
                f,
                True,
                command=self.distanceChange,
                width=5,
                background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.distance.fill(sorted(OCV.DISTANCE_MODE.values()))
        self.distance.grid(row=row, column=col, columnspan=2, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            g17_items = OCV.DISTANCE_MODE.items()
        else:
            g17_items = OCV.DISTANCE_MODE.viewitems()

        for key, val in g17_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(self.distance, _("Distance Mode:\n{0}".format(bal_text)))

        self.addWidget(self.distance)

        # populate gstate dictionary
        self.gstate = {}  # $G state results widget dictionary

        for key, val in g17_items:
            self.gstate[key] = (self.distance, val)

        col += 3
        self.units = tkExtra.Combobox(f, True,
                    command=self.unitsChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.units.fill(sorted(OCV.UNITS.values()))
        self.units.grid(row=row, column=col, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            unit_items = OCV.UNITS.items()
        else:
            unit_items = OCV.UNITS.viewitems()

        for key, val in unit_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(self.units, _("Units:\n{0}".format(bal_text)) )

        for key, val in unit_items:
            self.gstate[key] = (self.units, val)

        self.addWidget(self.units)

        # Tool
        row += 1
        col = 1
        self.toolEntry = tkExtra.IntegerEntry(f, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, width=5)
        self.toolEntry.grid(row=row, column=col, sticky=Tk.EW)
        tkExtra.Balloon.set(self.toolEntry, _("Tool number [T#]"))
        self.addWidget(self.toolEntry)

        col += 1
        b = Tk.Button(f, text=_("set"),
                command=self.setTool,
                padx=1, pady=1)
        b.grid(row=row, column=col, sticky=Tk.W)
        self.addWidget(b)

        # Plane
        col += 2
        self.plane = tkExtra.Combobox(f, True,
                    command=self.planeChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.plane.fill(sorted(OCV.PLANE.values()))
        self.plane.grid(row=row, column=col, sticky=Tk.EW)

        bal_text = ""

        if OCV.IS_PY3 is True:
            plane_items = OCV.PLANE.items()
        else:
            plane_items = OCV.PLANE.viewitems()


        for key, val in plane_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(self.plane, _("Plane:\n{0}".format(bal_text)) )

        self.addWidget(self.plane)

        for k,v in plane_items:
            self.gstate[k] = (self.plane, v)

        # Feed speed
        row += 1
        col = 1
        self.feedRate = tkExtra.FloatEntry(f, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, disabledforeground="Black", width=5)
        self.feedRate.grid(row=row, column=col, sticky=Tk.EW)
        self.feedRate.bind('<Return>',   self.setFeedRate)
        self.feedRate.bind('<KP_Enter>', self.setFeedRate)
        tkExtra.Balloon.set(self.feedRate, _("Feed Rate [F#]"))
        self.addWidget(self.feedRate)

        col += 1
        b = Tk.Button(f, text=_("set"),
                command=self.setFeedRate,
                padx=1, pady=1)
        b.grid(row=row, column=col, columnspan=2, sticky=Tk.W)
        self.addWidget(b)

        #Feed mode
        col += 2
        self.feedMode = tkExtra.Combobox(f, True,
                    command=self.feedModeChange,
                    width=5,
                    background=tkExtra.GLOBAL_CONTROL_BACKGROUND)
        self.feedMode.fill(sorted(OCV.FEED_MODE.values()))
        self.feedMode.grid(row=row, column=col, sticky=Tk.EW)


        bal_text = ""

        if OCV.IS_PY3 is True:
            feed_items = OCV.FEED_MODE.items()
        else:
            feed_items = OCV.FEED_MODE.viewitems()

        for key, val in feed_items:
            bal_text += "{0} > {1}\n".format(key, val)

        tkExtra.Balloon.set(self.feedMode, _("Feed Mode:\n{0}".format(bal_text)) )

        for key, val in feed_items:
            self.gstate[key] = (self.feedMode, val)

        self.addWidget(self.feedMode)

        # TLO
        row += 1
        col = 1
        self.tlo = tkExtra.FloatEntry(f, background=tkExtra.GLOBAL_CONTROL_BACKGROUND, disabledforeground="Black", width=5)
        self.tlo.grid(row=row, column=col, sticky=Tk.EW)
        self.tlo.bind('<Return>', self.setTLO)
        self.tlo.bind('<KP_Enter>', self.setTLO)
        tkExtra.Balloon.set(self.tlo, _("Tool length offset [G43.1#]"))
        self.addWidget(self.tlo)

        col += 1
        b = Tk.Button(f, text=_("set"),
                command=self.setTLO,
                padx=1, pady=1)
        b.grid(row=row, column=col, columnspan=2, sticky=Tk.W)
        self.addWidget(b)

        # g92
        col += 2
        self.g92 = Tk.Label(f, text="")
        self.g92.grid(row=row, column=col, columnspan=3, sticky=Tk.EW)
        tkExtra.Balloon.set(self.g92, _("Set position [G92 X# Y# Z#]"))
        self.addWidget(self.g92)

        f.grid_columnconfigure(1, weight=1)
        f.grid_columnconfigure(4, weight=1)

        # Spindle
        f = Tk.Frame(self())
        f.pack(side=Tk.BOTTOM, fill=Tk.X)

        self.override = Tk.IntVar()
        self.override.set(100)
        self.spindle = Tk.BooleanVar()
        self.spindleSpeed = Tk.IntVar()

        col, row=0, 0
        self.overrideCombo = tkExtra.Combobox(f, width=8, command=self.overrideComboChange)
        self.overrideCombo.fill(OVERRIDES)
        self.overrideCombo.grid(row=row, column=col, pady=0, sticky=Tk.EW)
        tkExtra.Balloon.set(self.overrideCombo, _("Select override type."))

        b = Tk.Button(f, text=_("Reset"), pady=0, command=self.resetOverride)
        b.grid(row=row+1, column=col, pady=0, sticky=Tk.NSEW)
        tkExtra.Balloon.set(b, _("Reset override to 100%"))

        col += 1
        self.overrideScale = Tk.Scale(
                f,
                command=self.overrideChange,
                variable=self.override,
                showvalue=True,
                orient=Tk.HORIZONTAL,
                from_=25,
                to_=200,
                resolution=1)
        self.overrideScale.bind("<Double-1>", self.resetOverride)
        self.overrideScale.bind("<Button-3>", self.resetOverride)
        self.overrideScale.grid(row=row, column=col, rowspan=2, columnspan=4, sticky=Tk.EW)
        tkExtra.Balloon.set(self.overrideScale, _("Set Feed/Rapid/Spindle Override. Right or Double click to reset."))

        self.overrideCombo.set(OVERRIDES[0])

        row += 2
        col = 0
        b = Tk.Checkbutton(f, text=_("Spindle"),
                image=Utils.icons["spinningtop"],
                command=self.spindleControl,
                compound=Tk.LEFT,
                indicatoron=0,
                variable=self.spindle,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(b, _("Start/Stop spindle (M3/M5)"))
        b.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(b)

        col += 1
        b = Tk.Scale(f,    variable=self.spindleSpeed,
                command=self.spindleControl,
                showvalue=True,
                orient=Tk.HORIZONTAL,
                from_=Utils.config.get("CNC","spindlemin"),
                to_=Utils.config.get("CNC","spindlemax"))
        tkExtra.Balloon.set(b, _("Set spindle RPM"))
        b.grid(row=row, column=col, sticky=Tk.EW, columnspan=3)
        self.addWidget(b)

        f.grid_columnconfigure(1, weight=1)

        # Coolant control

        self.coolant = Tk.BooleanVar()
        self.mist = Tk.BooleanVar()
        self.flood = Tk.BooleanVar()


        row += 1
        col = 0
        Tk.Label(f, text=_("Coolant:")).grid(row=row, column=col, sticky=Tk.E)
        col += 1

        coolantDisable = Tk.Checkbutton(f, text=_("OFF"),
                command=self.coolantOff,
                indicatoron=0,
                variable=self.coolant,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(coolantDisable, _("Stop cooling (M9)"))
        coolantDisable.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(coolantDisable)

        col += 1
        floodEnable = Tk.Checkbutton(f, text=_("Flood"),
                command=self.coolantFlood,
                indicatoron=0,
                variable=self.flood,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(floodEnable, _("Start flood (M8)"))
        floodEnable.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(floodEnable)

        col += 1
        mistEnable = Tk.Checkbutton(f, text=_("Mist"),
                command=self.coolantMist,
                indicatoron=0,
                variable=self.mist,
                padx=1,
                pady=0)
        tkExtra.Balloon.set(mistEnable, _("Start mist (M7)"))
        mistEnable.grid(row=row, column=col, pady=0, sticky=Tk.NSEW)
        self.addWidget(mistEnable)
        f.grid_columnconfigure(1, weight=1)

        # DEBUG
        #print(self.gstate)

    #----------------------------------------------------------------------
    def overrideChange(self, event=None):
        n = self.overrideCombo.get()
        c = self.override.get()
        OCV.CD["_Ov"+n] = c
        OCV.CD["_OvChanged"] = True

    #----------------------------------------------------------------------
    def resetOverride(self, event=None):
        self.override.set(100)
        self.overrideChange()

    #----------------------------------------------------------------------
    def overrideComboChange(self):
        n = self.overrideCombo.get()
        if n=="Rapid":
            self.overrideScale.config(to_=100, resolution=25)
        else:
            self.overrideScale.config(to_=200, resolution=1)
        self.override.set(OCV.CD["_Ov"+n])

    #----------------------------------------------------------------------
    def _gChange(self, value, dictionary):
        for k,v in dictionary.items():
            if v==value:
                self.sendGCode(k)
                return

    #----------------------------------------------------------------------
    def distanceChange(self):
        if self._gUpdate: return
        self._gChange(self.distance.get(), OCV.DISTANCE_MODE)

    #----------------------------------------------------------------------
    def unitsChange(self):
        if self._gUpdate: return
        self._gChange(self.units.get(), OCV.UNITS)

    #----------------------------------------------------------------------
    def feedModeChange(self):
        if self._gUpdate: return
        self._gChange(self.feedMode.get(), OCV.FEED_MODE)

    #----------------------------------------------------------------------
    def planeChange(self):
        if self._gUpdate: return
        self._gChange(self.plane.get(), OCV.PLANE)

    #----------------------------------------------------------------------
    def setFeedRate(self, event=None):
        if self._gUpdate: return
        try:
            feed = float(self.feedRate.get())
            self.sendGCode("F{0:.{1}f}".format(feed, OCV.digits))
            self.event_generate("<<CanvasFocus>>")
        except ValueError:
            pass

    #----------------------------------------------------------------------
    def setTLO(self, event=None):
        #if self._probeUpdate: return
        try:
            tlo = float(self.tlo.get())
            self.sendGCode("G43.1 Z{0:.{1}f}".format(tlo, OCV.digits))
            OCV.mcontrol.viewParameters()
            self.event_generate("<<CanvasFocus>>")
        except ValueError:
            pass

    #----------------------------------------------------------------------
    def setTool(self, event=None):
        pass

    #----------------------------------------------------------------------
    def spindleControl(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.c_state in (Sender.CONNECTED, Sender.NOT_CONNECTED): return
        if self.spindle.get():
            self.sendGCode("M3 S{0:d}".format(self.spindleSpeed.get()))
        else:
            self.sendGCode("M5")

    #----------------------------------------------------------------------
    def coolantMist(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.c_state in (Sender.CONNECTED, Sender.NOT_CONNECTED):
            self.mist.set(Tk.FALSE)
            return
        self.coolant.set(Tk.FALSE)
        self.mist.set(Tk.TRUE)
        self.sendGCode("M7")

    #----------------------------------------------------------------------
    def coolantFlood(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.c_state in (Sender.CONNECTED, Sender.NOT_CONNECTED):
            self.flood.set(Tk.FALSE)
            return
        self.coolant.set(Tk.FALSE)
        self.flood.set(Tk.TRUE)
        self.sendGCode("M8")

    #----------------------------------------------------------------------
    def coolantOff(self, event=None):
        if self._gUpdate: return
        # Avoid sending commands before unlocking
        if OCV.c_state in (Sender.CONNECTED, Sender.NOT_CONNECTED):
            self.coolant.set(Tk.FALSE)
            return
        self.flood.set(Tk.FALSE)
        self.mist.set(Tk.FALSE)
        self.coolant.set(Tk.TRUE)
        self.sendGCode("M9")

    #----------------------------------------------------------------------
    def updateG(self):
        self._gUpdate = True
        try:
            focus = self.focus_get()
        except:
            focus = None

        try:
            OCV.wcsvar.set(OCV.WCS.index(OCV.CD["WCS"]))
            self.feedRate.set(str(OCV.CD["feed"]))
            self.feedMode.set(OCV.FEED_MODE[OCV.CD["feedmode"]])
            self.spindle.set(OCV.CD["spindle"]=="M3")
            self.spindleSpeed.set(int(OCV.CD["rpm"]))
            self.toolEntry.set(OCV.CD["tool"])
            self.units.set(OCV.UNITS[OCV.CD["units"]])
            self.distance.set(OCV.DISTANCE_MODE[OCV.CD["distance"]])
            self.plane.set(OCV.PLANE[OCV.CD["plane"]])
            self.tlo.set(str(OCV.CD["TLO"]))
            self.g92.config(text=str(OCV.CD["G92"]))
        except KeyError:
            pass

        self._gUpdate = False

    #----------------------------------------------------------------------
    def updateFeed(self):
        if self.feedRate.cget("state") == Tk.DISABLED:
            self.feedRate.config(state=Tk.NORMAL)
            self.feedRate.delete(0, Tk.END)
            self.feedRate.insert(0, OCV.CD["curfeed"])
            self.feedRate.config(state=Tk.DISABLED)

    #----------------------------------------------------------------------
    def wcsChange(self):
        self.sendGCode(OCV.WCS[OCV.wcsvar.get()])
        OCV.mcontrol.viewState()


#===============================================================================
# Control Page
#===============================================================================
class ControlPage(CNCRibbon.Page):
    __doc__ = _("CNC communication and control")
    _name_ = N_("Control")
    _icon_ = "control"

    #----------------------------------------------------------------------
    # Add a widget in the widgets list to enable disable during the run
    #----------------------------------------------------------------------
    def register(self):
        OCV.wcsvar = Tk.IntVar()
        OCV.wcsvar.set(0)

        self._register(
            (Interface.ConnectionGroup,
             Interface.UserGroup,
             Interface.RunGroup,
             Interface.MemoryGroup),
            (Interface.DROFrame, ControlFrame, StateFrame))
