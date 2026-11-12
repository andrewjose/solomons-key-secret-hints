import sys
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); out=bytearray(b'PATCH'); i=0
while i<len(b):
    if a[i]!=b[i]:
        j=i
        while j<len(b) and a[j]!=b[j] and j-i<0xFFFF: j+=1
        out+=i.to_bytes(3,'big')+(j-i).to_bytes(2,'big')+b[i:j]; i=j
    else: i+=1
out+=b'EOF'; open(sys.argv[3],'wb').write(out); print(len(out))
