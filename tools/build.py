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
 LDA $07E0
 BEQ done
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
KON=HOOK+len(code)
kcode,kl=assemble(KON,'''
konami:
 JSR $837D
 LDA $07E3
 CMP #$03
 BNE kout
 LDA $82
 TAY
 EOR $07E2
 AND $82
 STY $07E2
 BEQ kout
 LDX $07E1
 CMP kseq,X
 BEQ kadv
 CMP #$08
 BNE kzero
 CPX #$02
 BEQ kset
 LDX #$01
 BNE kset
kzero:
 LDX #$00
 BEQ kset
kadv:
 INX
 CPX #$0A
 BNE kset
 LDA #$01
 STA $07E0
 LDY #$18
 JSR $8E8D
 LDX #$00
kset:
 STX $07E1
kout:
 RTS
bankhook:
 STX $07E3
 LDA #$80
 STA $7D
 RTS
kseq:
 .byte 08,08,04,04,02,01,02,01,40,80
'''.splitlines())
code=code+kcode
assert all(b in (0,0xff) for b in rom[f(HOOK):f(HOOK)+len(code)])
# controller read in NMI -> konami detector
assert rom[f(0x80D2):f(0x80D2)+3]==bytes([0x20,0x7D,0x83])
rom[f(0x80D2)+1:f(0x80D2)+3]=bytes([kl['konami']&0xff,kl['konami']>>8])
# NMI CHR bank switch: 'LDA #$80 / STA $7D' -> JSR bankhook / NOP
assert rom[f(0x8051):f(0x8051)+4]==bytes([0xA9,0x80,0x85,0x7D])
rom[f(0x8051):f(0x8051)+4]=bytes([0x20,kl['bankhook']&0xff,kl['bankhook']>>8,0xEA])
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
