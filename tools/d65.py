import sys
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
rom=open("/home/claude/rom/Solomon's Key (USA).nes",'rb').read()
prg=rom[16:16+0x8000]
m=MPU()
for i,b in enumerate(prg): m.memory[0x8000+i]=b
d=Disassembler(m)
def dis(start,n=40):
    a=start
    for _ in range(n):
        l,t=d.instruction_at(a)
        print(f"{a:04X}  {' '.join('%02X'%m.memory[a+k] for k in range(l)):9s} {t}")
        a+=l
if __name__=='__main__':
    dis(int(sys.argv[1],16), int(sys.argv[2]) if len(sys.argv)>2 else 40)
