import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
BGC=int(os.environ.get('BGC','2')); BLKC=int(os.environ.get('BLKC','1'))
from py65.devices.mpu6502 import MPU
from py65.assembler import Assembler
SRC="/home/claude/rom/Solomon's Key (USA).nes"
rom=bytearray(open(SRC,'rb').read())
def f(a): return a-0x8000+0x10
mpu=MPU(); asm=Assembler(mpu)
def assemble(org, lines, labels_pass=None):
    # two-pass simple label resolver
    labels={}
    for p in range(2):
        pc=org; out=bytearray()
        for ln in lines:
            ln=ln.split(';')[0].strip()
            if not ln: continue
            if ln.endswith(':'): labels[ln[:-1]]=pc; continue
            if ln.startswith('.byte'):
                bs=bytes(int(x.strip().lstrip('$'),16) for x in ln[5:].split(',')); out+=bs; pc+=len(bs); continue
            for k,v in sorted(labels.items(),key=lambda kv:-len(kv[0])):
                ln=ln.replace(k,'$%04X'%v)
            if p==0 and any(c.isalpha() and c.islower() for c in ln.split(' ',1)[-1]):
                ln=ln.split(' ')[0]+' $'+('%04X'%pc) if ln.split(' ')[0] not in ('BNE','BEQ','BCC','BCS','BPL','BMI','BVC','BVS') else ln.split(' ')[0]+' $%04X'%pc
            b=asm.assemble(ln,pc)
            if b is None: raise SystemExit('asm fail: '+ln)
            out+=bytes(b); pc+=len(b)
    return bytes(out),labels
MARK=0x98
HOOK=0xB500
code,labels=assemble(HOOK,f"""
hook:
 JSR $9E21
 LDX $00
 LDA $0304,X
 CMP #$F8
 BCS chkbj
 CMP #$40
 BCC chkbj
 CMP #$80
 BCC markbg
 AND #$3F
 CMP #$10
 BEQ chkbj
 BNE mark
markbg:
 LDA #$98
 BNE store
mark:
 LDA #$25
 BNE store
markw:
 LDA #$27
store:
 STA $03E9
 RTS
chkbj:
 LDA $7C
 AND #$10
 BNE done
 LDA $0428
 CMP #$10
 BNE nxt
 CPX #$7E
 BEQ bj
nxt:
 CMP #$27
 BNE done
 CPX #$56
 BEQ bj
done:
 RTS
bj:
 LDA $0304,X
 CMP #$F8
 BCS markw
 CMP #$80
 BCS mark
 BCC markbg
""".splitlines())
assert all(b in (0,0xff) for b in rom[f(HOOK):f(HOOK)+len(code)])
rom[f(HOOK):f(HOOK)+len(code)]=code
# redirect bulk drawer JSR $9E21 at $96A6
assert rom[f(0x96A6):f(0x96A6)+3]==bytes([0x20,0x21,0x9E])
rom[f(0x96A6)+1:f(0x96A6)+3]=bytes([HOOK&0xff,HOOK>>8])
out=sys.argv[1] if len(sys.argv)>1 else '/home/claude/work/sk_hints.nes'
import ring
ring.apply(rom,BGC,BLKC)
WHC=1
for bank in range(3):
    chr_=bytearray(rom[16+0x8000:])
    ring.put(chr_,bank,0x27,ring.ringify(ring.get(chr_,bank,0x84),WHC)); rom[16+0x8000:]=chr_
open(out,'wb').write(rom); print(code.hex(' '), labels)
