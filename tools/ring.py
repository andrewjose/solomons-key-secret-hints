import sys
RING=["........",
      "........",
      "........",
      "....###.",
      "...#...#",
      "...#...#",
      "...#...#",
      "....###."]
def get(chr_,bank,t):
    o=bank*0x2000+0x1000+t*16; d=chr_[o:o+16]
    return [[((d[r]>>(7-c))&1)|(((d[r+8]>>(7-c))&1)<<1) for c in range(8)] for r in range(8)]
def put(chr_,bank,t,px):
    o=bank*0x2000+0x1000+t*16
    for r in range(8):
        lo=hi=0
        for c in range(8):
            lo|=(px[r][c]&1)<<(7-c); hi|=(px[r][c]>>1)<<(7-c)
        chr_[o+r]=lo; chr_[o+8+r]=hi
def ringify(px,color):
    return [[color if RING[r][c]=='#' else px[r][c] for c in range(8)] for r in range(8)]
def apply(rom,bg_color,blk_color,bg_tile=0x98,blk_tile=0x25):
    chr_=bytearray(rom[16+0x8000:])
    for bank in range(3):
        put(chr_,bank,bg_tile,ringify(get(chr_,bank,0x2c),bg_color))
        put(chr_,bank,blk_tile,ringify(get(chr_,bank,0x90),blk_color))
    rom[16+0x8000:]=chr_
