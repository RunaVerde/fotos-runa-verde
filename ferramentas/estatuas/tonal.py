"""Fotos com fundo branco + tonalidade igual em todas (histograma de luminância casado com a foto de referência, sem dominante de cor)."""
from PIL import Image
import numpy as np, sys
D='/home/claude/odin/'
ordem=[2,6,1,4,5,7,3]   # capa: frente 3/4 (2), frente (6), frente baixa (1), frente clara (4), lado (5), outro lado (7), costas (3)
REF=2
def lum(a): return 0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
ref=np.array(Image.open(D+f'pr/pr{REF}.png').convert('RGBA')).astype(np.float32)
rm=ref[...,3]>200; rl=np.sort(lum(ref)[rm])
for k,i in enumerate(ordem,1):
    im=Image.open(D+f'pr/pr{i}.png').convert('RGBA'); a=np.array(im).astype(np.float32)
    m=a[...,3]>200; L=lum(a)
    # casamento de histograma (quantis)
    src=np.sort(L[m]); q=np.interp(L, src, np.linspace(0,1,len(src)))
    L2=np.interp(q, np.linspace(0,1,len(rl)), rl)
    # tom neutro com leve frio igual em todas (preto grafite)
    L2=255*(np.clip(L2,0,255)/255)**0.72*1.08
    rgb=np.stack([L2*0.97, L2*0.99, L2*1.03],-1)
    out=np.concatenate([np.clip(rgb,0,255), a[...,3:4]],-1).astype(np.uint8)
    o=Image.fromarray(out,'RGBA'); al=np.array(o)[...,3]; ys,xs=np.where(al>10)
    o=o.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)); o.save(D+f'obj{k}.png')
    S=1200; mg=int(S*0.14); sc=min((S-2*mg)/o.width,(S-2*mg)/o.height)
    o2=o.resize((int(o.width*sc),int(o.height*sc)),Image.LANCZOS)
    c=Image.new('RGB',(S,S),'white'); c.paste(o2,((S-o2.width)//2,(S-o2.height)//2),o2); c.save(D+f'final/busto-odin-{k}.jpg',quality=92)
ims=[Image.open(D+f'final/busto-odin-{k}.jpg').resize((400,400)) for k in range(1,8)]
s=Image.new('RGB',(1600,800),'gray')
for k,im in enumerate(ims): s.paste(im,((k%4)*400,(k//4)*400))
s.save(D+'grade.jpg',quality=85); print('ok')
