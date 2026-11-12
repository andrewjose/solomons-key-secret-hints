import sys; sys.path.insert(0,'/home/claude/work')
from survey import boot_level
from PIL import Image
src=open(sys.argv[1],'rb').read(); Ls=[int(x) for x in sys.argv[3].split(',')]
c=Image.new('RGB',(256*min(4,len(Ls)),240*((len(Ls)+3)//4)))
for k,L in enumerate(Ls):
    e=boot_level(L,src); c.paste(Image.fromarray(e.fr),((k%4)*256,(k//4)*240))
c=c.resize((c.width*2,c.height*2),Image.NEAREST); c.save(sys.argv[2])
