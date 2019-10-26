OKKCNC
====

GRBL CNC command sender, autoleveler, g-code editor, digitizer, CAM
and swiss army knife for all your CNC needs.

An advanced fully featured g-code sender for GRBL, forked from bCNC ver 0.9.14.

The main reason to fork, is the intention to make it resembling professional CNC controller, and adding the
ability to operate the CNC like a "manual machining tool"

The main goals are:

- Add some memA memB buttons to make possible to memorize some "asolute positions", and operate on them
 using "functions" line "LINE" from posA to posB "SQUARE" like a "square pocket"

- add a Z override to make possible to correct the Z position by some amount, useful when pocketing os profiling
  using materials like plywood that are not perfectly stable in time, so a nominal 5mm plywood is 4.9 or 5.1 
  making diffcult to cut or ruining too much the sacrifical bed. 


OKKCNC is a cross platform program (Windows, Linux, Mac) written in python.

The sender is robust and fast able to work nicely with old or slow hardware like [Raspberry Pi]

Note that on Windows XP you have to use `pyserial==3.0.1` or older as newer version do not work on XP.

# Installation (manual)
You will need the following packages to run OKKCNC
- tkinter the graphical toolkit for python
  Depending your python/OS it can either be already installed,
  or under the names tkinter, python-tkinter, python-tk
- pyserial or under the name python-serial, python-pyserial
- numpy
- Optionally:
- python-imaging-tk: the PIL libraries for autolevel height map
- python-opencv: for webcam streaming on web pendant
- scipy: for 100 times faster 3D mesh slicing

Expand the directory or download it from github
and run the bCNC command

# IMPORTANT! Motion controller (GRBL) settings
- GRBL should be configured to use **MPos** rather than **Wpos**. This means that `$10=` should be set to odd number. As of GRBL 1.1 we reccomend setting `$10=3`. If you have troubles communicating with your machine, you can try to set failsafe value `$10=1`.
- CADs, OKKCNC and GRBL all work in milimeters by default. Make sure that `$13=0` is set in GRBL, if you experience strange behavior. (unless you've configured your CAD and OKKCNC to use inches)
- Before filing bug please make sure you use latest stable official release of GRBL. Older and unofficial releases might work, but we frequently see cases where they don't. So please upgrade firmware in your Arduinos to reasonably recent version if you can.
- Also read about all possible GRBL settings and make sure your setup is correct: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration

# Configuration
You can modify most of the parameters from the "Tools -> Machine"
page. Only the changes/differences from the default configuration
file will be saved in your home directory ${HOME}/.OKKCNC  or ~/.OKKCNC

The default configuration is stored on OKKCNC.ini in the
installation directory.

*PLEASE DO NOT CHANGE THIS FILE, IT'S GOING TO BE OVERWRITTEN ON EACH UPGRADE OF BCNC*

* THESE FEATURES ARE COPIED FROM BCNC, thing may change in the progress of porting *

# Features:
- simple and intuitive interface for small screens
- import/export **g-code**, **dxf** and **svg** files
- 3D mesh slicing **stl** and **ply** files
- fast g-code sender (works nicely on RPi and old hardware)
- workspace configuration (G54..G59 commands)
- user configurable buttons
- g-code **function evaluation** with run time expansion
- feed override during the running for fine tuning
- Easy probing:
  - simple probing
  - center finder with a probing ring
  - **auto leveling**, Z-probing and auto leveling by altering the g-code during
    sending (or permanently autoleveling the g-code file).
  - height color map display
  - create g-code by jogging and recording points (can even use camera for this)
  - **manual tool change** expansion and automatic tool length probing
  - **canned cycles** expansion
- Various Tools:
  - user configurable database of materials, endmills, stock
  - properties database of materials, stock, end mills etc..
  - basic **CAM** features (profiling, pocketing, drilling, flat/helical/ramp cutting, thread milling, cutout tabs, drag knife)
  - User g-code plugins:
    - bowl generator
    - finger joint box generator
    - simple spur gear generator
    - spirograph generator
    - surface flatten
    - play melody from MIDI file using stepper motor frequency
    - ...
- G-Code editor and display
    - graphical display of the g-code, and workspace
    - graphically moving and editing g-code
    - reordering code and **rapid motion optimization**
    - moving, rotating, mirroring the g-code
- Web pendant to be used via smart phones

# Debugging
You can log serial communication by changing the port to something like:

    spy:///dev/ttyUSB0?file=serial_log.txt&raw
    spy://COM1?file=serial_log.txt&raw

If a file isn't specified, the log is written to stderr.
The 'raw' option outputs the data directly, instead of creating a hex dump.
Further documentation is available at: https://pyserial.readthedocs.io/en/latest/url_handlers.html#spy

# Disclaimer
  The software is made available "AS IS". It seems quite stable, but it is in
  an early stage of development.  Hence there should be plenty of bugs not yet
  spotted. Please use/try it with care, I don't want to be liable if it causes
  any damage :)
