import sys
rom=open(sys.argv[1],'rb').read()
P=lambda o: o  # file offsets include header
ITAB=0x6A2C; BLK=0x603C
def ptr(tab,i,n=53): return rom[tab+i] | rom[tab+n+i]<<8
def cpu2file(a): return a-0x8000+0x10
levels=[]
for L in range(53):
    a=ptr(ITAB,L); o=cpu2file(a)
    hdr=rom[o:o+10]; o+=10; items=[]
    while True:
        c=rom[o]; o+=1
        if c==0 or 0xE0<=c<=0xEF: end=('end',c); break
        if 0xF0<=c<=0xFB: end=('const',c,rom[o]); o+=1; break
        if 0xC0<=c<=0xDF:
            n=c-0xBF; code=rom[o]; o+=1
            for k in range(n): items.append((code,rom[o])); o+=1
        else:
            items.append((c,rom[o])); o+=1
    levels.append((L,a,hdr,items,end))
    hid=[(f"{c:02X}",f"x{p&15},y{(p>>4)-1}") for c,p in items]
    print(L+1, f"{a:04X}", "key%02X"%hdr[4], "keypos%02X"%hdr[6], end, "hidden:",hid)
