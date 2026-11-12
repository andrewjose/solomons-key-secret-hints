import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from emu import *
def boot(path, level=None):
    e=Emu(path); e.run(120); e.tap(NES_INPUT_START); e.run(200)
    e.tap(NES_INPUT_START); e.run(300); return e
def dumpmap(e):
    m=e.ram(0x300,0x100)
    for r in range(16):
        print(f"{r:X}:", ' '.join(f"{b:02X}" for b in m[r*16:r*16+16]))
def grid(e):
    m=e.ram(0x314,12*16)
    for y in range(12):
        print(f"y{y:2d}:", ' '.join(f"{b:02X}" for b in m[y*16:y*16+16]))
