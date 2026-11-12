import sys,os,tempfile; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
TMP=tempfile.gettempdir()
from boot import *
SRC=sys.argv[1] if len(sys.argv)>1 and sys.argv[1].endswith(".nes") else "Solomon's Key (USA).nes"; rom=bytearray(open(SRC,'rb').read())
def nt_of(e):
    s=bytes(e.n.save()); i=s.find(bytes([0x1c,0x0c,0x18,0x1b,0x0e])); return s[i-68:i-68+1024]
def boot_level(L, src=None):
    r=bytearray(src if src else rom); r[0x10+0x1135]=L
    p=os.path.join(TMP,f'lv{L}.nes'); open(p,'wb').write(r); return boot(p)
if __name__=='__main__':
    used=set()
    for L in range(53):
        e=boot_level(L); nt=nt_of(e); used|=set(nt[:960]); e.shot(os.path.join(TMP,f'lv{L}.png'))
    print(sorted(hex(x) for x in set(range(256))-used))
