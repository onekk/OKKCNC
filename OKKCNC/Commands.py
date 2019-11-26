#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:59:17 2019

@author: carlo
"""

import OCV

#----------------------------------------------------------------------
def setX0():
    OCV.application.mcontrol._wcsSet("0", None, None)

#----------------------------------------------------------------------
def setY0():
    OCV.application.mcontrol._wcsSet(None, "0", None)

#----------------------------------------------------------------------
def setZ0():
    OCV.application.mcontrol._wcsSet(None, None, "0")

#----------------------------------------------------------------------
def setXY0():
    OCV.application.mcontrol._wcsSet("0", "0", None)

#----------------------------------------------------------------------
def setXYZ0():
    OCV.application.mcontrol._wcsSet("0", "0", "0")