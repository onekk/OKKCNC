# -*- coding: ascii -*-
"""ControlPage.py


Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import absolute_import
from __future__ import print_function

try:
    import Tkinter as Tk
    import tkMessageBox
except ImportError:
    import tkinter as Tk
    import tkinter.messagebox as tkMessageBox

import math

import OCV
import CAMGen
import CNCRibbon
import IniFile
import Interface
import StateFrame
import tkExtra
import Unicode
import Utils

_LOWSTEP = 0.0001
_HIGHSTEP = 1000.0
_HIGHZSTEP = 10.0

class ControlFrame(CNCRibbon.PageLabelFrame):
    """ControlFrame
    --
    Some possible evolution:
        a) no combobox for step, but a two button or pair to the wheel scroll
            to increase and decrease steps using the list saved in config
        b) automatically add the step = 1/2 tool width
        c) smaller interface to compensate for the enlarged statusframe
        d) more CAM buttons?
    """

    z_step_font = ('Helvetica', 7, 'bold')

    def __init__(self, master, app):
        CNCRibbon.PageLabelFrame.__init__(
            self, master, "Control", _("Control"), app)

        """
        print("ControlFrame self.app > ", self.app)
        print("OCV.APP > ", OCV.APP)
        """

        Tk.Label(self, text="", width=1).grid(row=1, column=17)

        b_width = 4
        b_height = 2

        z_step_font = Utils.get_font("z_step.font", ControlFrame.z_step_font)

        Utils.set_steps()
       

        row = 0

        self.zstep = tkExtra.Combobox(
            self, width=4, background="White", command=self.set_z_fromcb)
        self.zstep.grid(row=row, column=0, columnspan=4, sticky=Tk.EW)
        self.zstep.fill(
            map(float, OCV.config.get("Control", "zsteplist").split()))
        self.zstep.set(str(OCV.stepz))
        tkExtra.Balloon.set(self.zstep, _("Step for Z move operation"))
        self.addWidget(self.zstep)

        but = Tk.Button(
            self,
            text="{0}".format(OCV.step1),
            name="step_1",
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=4, columnspan=3, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("S1"))
        but.bind("<Button-3>", lambda event: self.edit_pre_step("S1"))
        bal_text = _("Step1 = {0}").format(OCV.step1)
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="{0}".format(OCV.step2),
            name="step_2",
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=7, columnspan=3, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("S2"))
        but.bind("<Button-3>", lambda event: self.edit_pre_step("S2"))
        bal_text = _("Step2 = {0}").format(OCV.step2)
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="{0}".format(OCV.step3),
            name="step_3",
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=10, columnspan=3, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("S3"))        
        but.bind("<Button-3>", lambda event: self.edit_pre_step("S3"))
        bal_text = _("Step3 = {0}").format(OCV.step3)
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)
 
        but = Tk.Button(
            self,
            text="{0}".format(OCV.step4),
            name="step_4",
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=13, columnspan=3, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("S4"))        
        but.bind("<Button-3>", lambda event: self.edit_pre_step("S4"))
        bal_text = _("Step4 = {0}").format(OCV.step4)
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)
        row = 1

        but = Tk.Button(
            self, text="-",
            command=self.dec_z_step,
            padx=1, pady=1)
        but.grid(row=row, column=0, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Decrease zstep"))
        self.addWidget(but)

        but = Tk.Button(
            self, text="+",
            command=self.inc_z_step,
            padx=1, pady=1)
        but.grid(row=row, column=1, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Increase zstep"))
        self.addWidget(but)


        but = Tk.Button(
            self,
            text=u"\u00F75",
            command=self.div_step,
            width=3,
            padx=1, pady=1)
        but.grid(row=row, column=4, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Divide step by 5"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=u"\u00D75",
            command=self.mul_step,
            width=3,
            padx=1, pady=1)
        but.grid(row=row, column=6,columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Multiply step by 5"))
        self.addWidget(but)

        self.step = tkExtra.Combobox(
                self, width=6, background="White", command=self.set_xy_fromcb)
        self.step.grid(row=row, column=8, columnspan=4, sticky=Tk.EW)
        self.step.fill(
            map(float, OCV.config.get("Control", "steplist").split()))
        self.step.set(OCV.stepxy)
        tkExtra.Balloon.set(self.step, _("Step for coarse move operation"))
        self.addWidget(self.step)

        but = Tk.Button(
            self,
            text="<",
            command=self.dec_xy_step,
            width=3,
            padx=1, pady=1)
        but.grid(row=row, column=12, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Decrease step"))
        self.addWidget(but)

        but = Tk.Button(
            self, text=">",
            command=self.inc_xy_step,
            width=3,
            padx=1, pady=1)
        but.grid(row=row, column=14, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Increase step"))
        self.addWidget(but)

        row = 3

        but = Tk.Button(
            self,
            text=Unicode.BLACK_UP_POINTING_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-ZUP>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")
        but.grid(row=row, column=0, columnspan=2, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move +Z"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.UPPER_LEFT_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-XDWYUP>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")

        but.grid(row=row, column=4, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move -X +Y"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.BLACK_UP_POINTING_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-YUP>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")
        but.grid(row=row, column=8, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move +Y"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.UPPER_RIGHT_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-XYUP>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")
        but.grid(row=row, column=12, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move +X +Y"))
        self.addWidget(but)

        row = 5

        but = Tk.Button(
            self,
            text="{0}".format(OCV.zstep1),
            name="zstep_1",
            font=z_step_font,
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=0, columnspan=1, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("ZS1"))
        but.bind("<Button-3>", lambda event: self.edit_pre_step("ZS1"))
        bal_text = _("Z Step1 = {0}".format(OCV.zstep1))
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="{0}".format(OCV.zstep2),
            name="zstep_2",
            font=z_step_font,
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=1, columnspan=1, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("ZS2"))
        but.bind("<Button-3>", lambda event: self.edit_pre_step("ZS2"))
        bal_text = _("Z Step2 = {0}".format(OCV.zstep2))
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.BLACK_LEFT_POINTING_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-XDW>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")
        but.grid(row=row, column=4, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move -X"))
        self.addWidget(but)

        but = Utils.UserButton(
            self,
            OCV.APP,
            0,
            text=Unicode.LARGE_CIRCLE,
            command=self.go_to_origin,
            width=b_width, height=b_height,
            activebackground="LightYellow")

        but.grid(row=row, column=8, columnspan=4, rowspan=2, sticky=Tk.EW)

        tkExtra.Balloon.set(
            but,
            _("Move to Origin.\nRight click to configure."))

        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.BLACK_RIGHT_POINTING_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-XUP>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")

        but.grid(row=row, column=12, columnspan=4, rowspan=2, sticky=Tk.EW)

        tkExtra.Balloon.set(but, _("Move +X"))

        self.addWidget(but)

        row = 6

        but = Tk.Button(
            self,
            text="{0}".format(OCV.zstep3),
            name="zstep_3",
            font=z_step_font,
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=0, columnspan=1, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("ZS3"))
        but.bind("<Button-3>", lambda event: self.edit_pre_step("ZS3"))

        bal_text = _("Z Step3 = {0}".format(OCV.zstep3))

        tkExtra.Balloon.set(but, bal_text)

        self.addWidget(but)

        but = Tk.Button(
            self,
            text="{0}".format(OCV.zstep4),
            name="zstep_4",
            font=z_step_font,
            width=2,
            padx=1, pady=1)
        but.grid(row=row, column=1, columnspan=1, sticky=Tk.EW)
        but.bind("<Button-1>", lambda event: self.apply_preset("ZS4"))
        but.bind("<Button-3>", lambda event: self.edit_pre_step("ZS4"))
        bal_text = _("Z Step4 = {0}".format(OCV.zstep4))
        tkExtra.Balloon.set(but, bal_text)
        self.addWidget(but)

        row = 7

        but = Tk.Button(
            self,
            text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-ZDW>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")
        but.grid(row=row, column=0, columnspan=2, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move -Z"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.LOWER_LEFT_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-XYDW>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")

        but.grid(row=row, column=4, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move -X -Y"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-YDW>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")

        but.grid(row=row, column=8, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move -Y"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text=Unicode.LOWER_RIGHT_TRIANGLE,
            command=lambda s=self: s.event_generate('<<JOG-XUPYDW>>'),
            width=b_width, height=b_height,
            activebackground="LightYellow")

        but.grid(row=row, column=12, columnspan=4, rowspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Move +X -Y"))
        self.addWidget(but)

        """CAM controls"""
        column = 18
        b_padx = 0
        b_pady = -1

        but = Tk.Button(
            self,
            text="RST",
            name="rst",
            command=self.reset_all,
            width=3,
            padx=b_padx, pady=b_pady,
            background="salmon",
            activebackground="LightYellow")

        but.grid(row=0, column=column, columnspan=2, rowspan=1, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Reset Gcode"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="m A",
            name="memA",
            command=self.mem_a,
            width=3,
            padx=b_padx, pady=b_pady,
            background="orchid1",
            activebackground="LightYellow")

        but.grid(row=1, column=column, columnspan=2, rowspan=1, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Mem A"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="m B",
            name="memB",
            command=self.mem_b,
            width=3,
            padx=b_padx, pady=b_pady,
            background="orchid1",
            activebackground="LightYellow")

        but.grid(row=2, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Mem B"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="LN",
            command=self.line,
            width=3,
            padx=b_padx, pady=b_pady,
            activebackground="LightYellow")

        but.grid(row=3, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Cut Line from memA to memB"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="R_PK",
            command=self.pocket,
            width=3,
            padx=b_padx, pady=b_pady,
            activebackground="LightYellow")

        but.grid(row=4, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Cut Rectangula Pocket from memA to memB"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="RmA",
            command=self.ret_a,
            width=3,
            padx=b_padx, pady=b_pady,
            activebackground="LightYellow")

        but.grid(row=5, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Return to mem A"))
        self.addWidget(but)

        but = Tk.Button(
            self,
            text="RmB",
            command=self.ret_b,
            width=3,
            padx=b_padx, pady=b_pady,
            activebackground="LightYellow")

        but.grid(row=6, column=column, columnspan=2, sticky=Tk.EW)
        tkExtra.Balloon.set(but, _("Return to mem B"))
        self.addWidget(but)

        try:
#            self.grid_anchor(CENTER)
            self.tk.call("grid", "anchor", self, Tk.CENTER)
        except Tk.TclError:
            pass

    def saveConfig(self):
        IniFile.set_value("Control", "step", OCV.stepxy)
        IniFile.set_value("Control", "zstep", OCV.stepz)
      
    def reset_all(self):
        """reset all thing related to cam operation and memory
        This means to clear the editor and reset memA and memB
        """
        self.event_generate("<<ClearEditor>>")
        wid = self.nametowidget("memA")
        tkExtra.Balloon.set(wid, "Empty")
        wid.configure(background="orchid1")

        OCV.WK_mem = 0 # memA
        self.event_generate("<<ClrMem>>")

        OCV.WK_mem = 1 # memB
        wid = self.nametowidget("memB")
        tkExtra.Balloon.set(wid, "Empty")
        wid.configure(background="orchid1")

        self.event_generate("<<ClrMem>>")

    def mem_a(self):
        """set mem_a
        mem_a == OCV.WKmems["mem_0"]
        coordinate values are kept in WCS
        """
        if OCV.c_state == "Idle":
            print("mem_A 1st")
            pos_x = OCV.CD["wx"]
            pos_y = OCV.CD["wy"]
            pos_z = OCV.CD["wz"]
            OCV.WK_mem = 0  # 1= memB

            mem_name = "memA"
            OCV.WK_mems["mem_0"] = [pos_x, pos_y, pos_z, 1, "mem A"]
            wid = self.nametowidget(mem_name)

            wdata = "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(
                mem_name, pos_x, pos_y, pos_z)

            tkExtra.Balloon.set(wid, wdata)
            wid.configure(background="aquamarine")

            self.event_generate("<<SetMem>>")
        else:
            pass

    def mem_b(self):
        """set mem_b
        mem_b == OCV.WKmems["mem_1"]
        coordinate values are kept in WCS
        """
        if OCV.c_state == "Idle":
            pos_x = OCV.CD["wx"]
            pos_y = OCV.CD["wy"]
            pos_z = OCV.CD["wz"]
            OCV.WK_mem = 1  # 1= memB

            mem_name = "memB"
            OCV.WK_mems["mem_1"] = [pos_x, pos_y, pos_z, 1, "mem B"]
            wid = self.nametowidget(mem_name)

            wdata = "{0} = \nX: {1:f} \nY: {2:f} \nZ: {3:f}".format(
                mem_name, pos_x, pos_y, pos_z)

            tkExtra.Balloon.set(wid, wdata)
            wid.configure(background="aquamarine")

            self.event_generate("<<SetMem>>")
        else:
            pass

    def ret_a(self):
        """return to pos mem_a"""
        if OCV.c_state == "Idle":
            if "mem_0" in OCV.WK_mems:
                mem_data = OCV.WK_mems["mem_0"]
                # print ("RmA {0} {1}".format(mem_data[0],mem_data[1]))
                self.sendGCode(
                    "$J=G90 {0}{1:f} {2}{3:f} F100000".format(
                        "X", mem_data[0],
                        "Y", mem_data[1]))
        else:
            pass

    def ret_b(self):
        """return to pos mem_b"""
        if OCV.c_state == "Idle":
            if "mem_1" in OCV.WK_mems:
                mem_data = OCV.WK_mems["mem_1"]
                #print ("RmB {0} {1}".format(mem_data[0],mem_data[1]))
                self.sendGCode(
                    "$J=G90 {0}{1:f} {2}{3:f} F100000".format(
                        "X", mem_data[0],
                        "Y", mem_data[1]))
        else:
            pass

    def line(self):
        """generate a line from mem_a to mem_b"""
        # avoid a dry run if both mem pos are not set
        if OCV.WK_mems["mem_0"][3] > 0 and OCV.WK_mems["mem_1"][3] > 0:

            end_depth = Utils.ask_for_value(OCV.APP, "TD")

            if end_depth is None:
                return

            CAMGen.line(self, OCV.APP, end_depth, "mem_0", "mem_1")

    def pocket(self):
        """generate a rectangular pocket from mem_a to mem_b"""
        # avoid a dry run if both mem pos are not set
        if OCV.WK_mems["mem_0"][3] > 0 and OCV.WK_mems["mem_1"][3] > 0:
            end_depth = Utils.ask_for_value(OCV.APP, "TD")

            if end_depth is None:
                return

            CAMGen.pocket(self, OCV.APP, end_depth, "mem_0", "mem_1")


    def go_to_origin(self, event=None):
        """go to X0 Y0 raising Z to safe height prior to move"""
        self.sendGCode("G90")
        self.sendGCode("G0Z{0:.{1}f}".format(OCV.CD['safe'], OCV.digits))
        self.sendGCode("G0X0Y0")
        # for safety no descend to Z0
        # self.sendGCode("G0Z0")

    
    def set_xy_fromcb(self):
        OCV.stepxy = self.step.get()
        self.event_generate(
                "<<Status>>",
                data=_("Step: {0:.{2}f}    Zstep: {1:.{2}f} ").format(
                    float(OCV.stepxy), float(OCV.stepz), OCV.digits))        

    def set_z_fromcb(self):
        OCV.stepz = self.zstep.get()
        self.event_generate(
                "<<Status>>",
                data=_("Step: {0:.{2}f}    Zstep: {1:.{2}f} ").format(
                    float(OCV.stepxy), float(OCV.stepz), OCV.digits))       


    def set_step_view(self, xy_step, z_step=None):
        """set step value shown on the interface"""
        self.step.set("{0:.{1}f}".format(float(xy_step), OCV.cb_dig))

        if self.zstep is self.step or z_step is None:
            self.event_generate(
                "<<Status>>",
                data=_("Step: {0:.{1}f}").format(float(xy_step), OCV.digits))
        else:
            self.zstep.set("{0:.{1}f}".format(float(z_step), OCV.cb_dig))
            self.event_generate(
                "<<Status>>",
                data=_("Step: {0:.{2}f}    Zstep: {1:.{2}f} ").format(
                    float(xy_step), float(z_step), OCV.digits))

    @staticmethod
    def _step_power(step):
        """increment or decrement the step using an algorithm
        the increment is small until the higher order level is reached
        i.e. is 1 from 1 to 9 at 10 the subsequent press jump to 20, 30
        and so on until 100 when the subsequent press jump to 200...
        """
        try:
            step = float(step)
            if step <= 0.0:
                step = 1.0
        except Exception:
            step = 1.0

        power = math.pow(10.0, math.floor(math.log10(step)))
        retval = round(step/power)*power

        if retval < _LOWSTEP:
            retval = _LOWSTEP + power
        elif retval > (_HIGHSTEP - power):
            retval = _HIGHSTEP - power

        return retval, power

    def inc_xy_step(self, event=None):
        """increment XY step using _step_power"""
        if event is not None and not self.acceptKey():
            return
        step, power = ControlFrame._step_power(OCV.stepxy)
        tg_step = step + power

        self.set_step_view(tg_step, None)
        OCV.stepxy = tg_step

    def inc_z_step(self, event=None):
        """increment Z step using _step_power"""
        if event is not None and not self.acceptKey():
            return

        step, power = ControlFrame._step_power(OCV.stepz)
        tgz_step = step + power

        self.set_step_view(OCV.stepxy, tgz_step)
        OCV.stepz = tgz_step
        
    def dec_xy_step(self, event=None):
        """decrement XY step using _step_power"""
        if event is not None and not self.acceptKey():
            return

        step, power = ControlFrame._step_power(OCV.stepxy)
        tg_step = step - power

        self.set_step_view(tg_step, None)
        OCV.stepxy = tg_step

    def dec_z_step(self, event=None):
        """decrement Z step using _step_power"""
        if event is not None and not self.acceptKey():
            return

        step, power = ControlFrame._step_power(OCV.stepz)

        tgz_step = step - power

        self.set_step_view(OCV.stepxy, tgz_step)
        OCV.stepz = tgz_step

    def mul_step(self, event=None):
        """multiply xy step by 5"""
        if event is not None and not self.acceptKey():
            return

        tg_step = float(OCV.stepxy) * 5.0

        if tg_step < _LOWSTEP:
            tg_step = _LOWSTEP
        elif tg_step > _HIGHSTEP:
            tg_step = _HIGHSTEP

        self.set_step_view(tg_step, None)
        OCV.stepxy = tg_step

    def div_step(self, event=None):
        """divide xy step by 5"""
        if event is not None and not self.acceptKey():
            return

        tg_step = float(OCV.stepxy) / 5.0

        if tg_step < _LOWSTEP:
            tg_step = _LOWSTEP
        elif tg_step > _HIGHSTEP:
            tg_step = _HIGHSTEP

        self.set_step_view(tg_step, None)
        OCV.stepxy = tg_step

    def apply_preset(self, caller):
        """apply preselected step"""
        #print("event {0} preset triggered".format(caller))
        if caller in ("ZS1", "ZS2", "ZS3", "ZS4"):
            if caller == "ZS1":            
                self.set_step_view(OCV.stepxy, OCV.zstep1)
            elif caller == "ZS2":            
                self.set_step_view(OCV.stepxy, OCV.zstep2)
            elif caller == "ZS3":            
                self.set_step_view(OCV.stepxy, OCV.zstep3)
            elif caller == "ZS4":            
                self.set_step_view(OCV.stepxy, OCV.zstep4)
        elif caller in ("S1", "S2", "S3", "S4"):
            if caller == "S1":            
                self.set_step_view(OCV.step1, OCV.stepz)
            elif caller == "S2":            
                self.set_step_view(OCV.step2, OCV.stepz)
            elif caller == "S3":            
                self.set_step_view(OCV.step3, OCV.stepz)
            elif caller == "S4":            
                self.set_step_view(OCV.step4, OCV.stepz)
                    

    def edit_pre_step(self, caller):
        """edit a preselected step value
        This method is valid for all the preselction buttons
        correct step is found using "caller" parameter
        """
        #print("edit_pre_step caller > ", caller)

        retval = Utils.ask_for_value(self, caller)

        if retval is None:
            return

        #print("retval > ", retval)

        if caller in ("S1", "S2", "S3", "S4"):
            if caller == "S1":
                wid = self.nametowidget("step_1")
                OCV.step1 = retval
                bal_text = "Step1 = {0}".format(OCV.step1)
                IniFile.set_value("Control", "step1", retval)
            elif caller == "S2":
                wid = self.nametowidget("step_2")
                OCV.step2 = retval
                bal_text = "Step2 = {0}".format(OCV.step2)
                IniFile.set_value("Control", "step2", retval)
            elif caller == "S3":
                wid = self.nametowidget("step_3")
                OCV.step3 = retval
                IniFile.set_value("Control", "step3", retval)
                bal_text = "Step3 = {0}".format(OCV.step3)
            elif caller == "S4":
                wid = self.nametowidget("step_4")
                OCV.step4 = retval
                IniFile.set_value("Control", "step4", retval)
                bal_text = "Step4 = {0}".format(OCV.step4)


        elif caller in ("ZS1", "ZS2", "ZS3", "ZS4"):
            if caller == "ZS1":
                wid = self.nametowidget("zstep_1")
                OCV.zstep1 = retval
                bal_text = "Zstep1 = {0}".format(OCV.zstep1)
                IniFile.set_value("Control", "zstep1", retval)
            elif caller == "ZS2":
                wid = self.nametowidget("zstep_2")
                OCV.zstep2 = retval
                bal_text = "Zstep2 = {0}".format(OCV.zstep2)
                IniFile.set_value("Control", "zstep2", retval)
            elif caller == "ZS3":
                wid = self.nametowidget("zstep_3")
                OCV.zstep3 = retval
                bal_text = "Zstep2 = {0}".format(OCV.zstep3)
                IniFile.set_value("Control", "zstep3", retval)
            elif caller == "ZS4":
                wid = self.nametowidget("zstep_4")
                OCV.zstep4 = retval
                bal_text = "Zstep4 = {0}".format(OCV.zstep4)
                IniFile.set_value("Control", "zstep4", retval)
        
        Utils.populate_cyclelist()
        
        if wid is not None:
            wid.configure(text=retval)
            tkExtra.Balloon.set(wid, bal_text)


class ControlPage(CNCRibbon.Page):
    """Control Page"""
    __doc__ = _("CNC communication and control")
    _name_ = N_("Control")
    _icon_ = "control"

    def register(self):
        """Add a widget in the widgets
        list to enable disable during the run
        """
        OCV.wcsvar = Tk.IntVar()
        OCV.wcsvar.set(0)

        self._register(
            (Interface.ConnectionGroup,
             Interface.UserGroup,
             Interface.RunGroup,
             Interface.MemoryGroup),
            (Interface.DROFrame, ControlFrame, StateFrame.StateFrame))
