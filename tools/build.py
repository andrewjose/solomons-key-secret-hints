import sys
from py65.devices.mpu6502 import MPU
from py65.assembler import Assembler
SRC=sys.argv[2] if len(sys.argv)>2 else "Solomon's Key (USA).nes"
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
 BCC mark
 AND #$3F
 CMP #$10
 BEQ chkbj
mark:
 LDA #${MARK:02X}
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
 BEQ mark
nxt:
 CMP #$27
 BNE done
 CPX #$56
 BEQ mark
done:
 RTS
""".splitlines())
assert all(b in (0,0xff) for b in rom[f(HOOK):f(HOOK)+len(code)])
rom[f(HOOK):f(HOOK)+len(code)]=code
# redirect bulk drawer JSR $9E21 at $96A6
assert rom[f(0x96A6):f(0x96A6)+3]==bytes([0x20,0x21,0x9E])
rom[f(0x96A6)+1:f(0x96A6)+3]=bytes([HOOK&0xff,HOOK>>8])
out=sys.argv[1] if len(sys.argv)>1 else '/home/claude/work/sk_hints.nes'
open(out,'wb').write(rom); print(code.hex(' '), labels)
