import cynes, numpy as np
from PIL import Image
from cynes import *
class Emu:
    def __init__(s,path):
        s.n=NES(path)
    def run(s,frames,buttons=0):
        s.n.controller=buttons
        for _ in range(frames): fr=s.n.step()
        s.n.controller=0
        s.fr=fr; return fr
    def tap(s,b,hold=3,after=10):
        s.run(hold,b); return s.run(after)
    def shot(s,fn):
        Image.fromarray(s.fr).save(fn)
    def ram(s,a,n=1): return bytes(s.n[a+i] for i in range(n))
