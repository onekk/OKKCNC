import re

#echo.py
mx=0
my=0
mz=0
fs0=0
fs1=0
wx=0
wy=0
wz=0

gpos = [mx,my,mz,fs0,fs1,wx,wy,wz]


def g_parser(block):
    self.codes = re.findall(r'([a-zA-Z])([0-9\.+-]+)', block)

    # Find any unmatched text by removing all the word matches.
    remainder = re.sub(r'([a-zA-Z])([0-9\.+-]+)', '', block)
    if len(remainder) > 0:
        self.extra = remainder
    
    print self.codes    

def outpos():
    pos = "<Idle|MPos: {0:.3f},{1:.3f},{2:.3f}|FS:{3},{4}|WCO:{5:.3f},{6:.3f},{7:.3f}>".format(*self.gpos)
    print pos

while True:
    s = raw_input()
    block = s.strip()
    out = ""
    if '$' in block:
        print "GRBL v1.1f"
    if '?' in block:
        outpos()

    if 'G1' in block:
        g_parser(s)
        outpos()
        print 'ok'
        
    outpos()
