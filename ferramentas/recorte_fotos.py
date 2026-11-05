import numpy as np, cv2
from PIL import Image
from scipy.ndimage import binary_fill_holes
HULL={4,5,7}
def below(xx,yy,pts):
    # True where point is below polyline pts (display coords *1.5)
    res=np.zeros(xx.shape,bool)
    for (x0,y0),(x1,y1) in zip(pts[:-1],pts[1:]):
        seg=(xx>=x0)&(xx<x1)
        yl=y0+(y1-y0)*(xx-x0)/(x1-x0)
        res|=seg&(yy>yl)
    return res
for i in range(1,8):
    im=Image.open(f'src{i}.jpg').convert('RGB'); A=np.asarray(im); H,W=A.shape[:2]; tot=H*W
    a=np.asarray(Image.open(f'isnet{i}.png'),np.float32)/255
    hsv=cv2.cvtColor(A,cv2.COLOR_RGB2HSV); V=hsv[...,2].astype(int); Sa=hsv[...,1].astype(int)
    col=((V<70)|((Sa>90)&(V>60))).astype(np.uint8)
    col=cv2.morphologyEx(col,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    m=((a>0.5)|(col>0)).astype(np.uint8)
    yy,xx=np.mgrid[0:H,0:W]
    if i==6:
        pts=[(700,815),(1205,1201),(1500,815)]
        m[(xx>702)&below(xx,yy,pts)]=0
    if i==1:
        pts=[(828,1292),(1400,992),(W,992)]
        m[(xx>828)&below(xx,yy,pts)]=0
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    m=binary_fill_holes(m).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    SS=4; big=np.zeros((H*SS,W*SS),np.uint8)
    for j in range(1,n):
        if st[j,cv2.CC_STAT_AREA]<0.03*tot or st[j,cv2.CC_STAT_TOP]==0: continue
        cs,_=cv2.findContours((lab==j).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        c=max(cs,key=cv2.contourArea)
        if i in HULL: c=cv2.convexHull(c)
        c=cv2.approxPolyDP(c,2.5,True)
        cv2.fillPoly(big,[(c.astype(np.float64)*SS+SS/2).astype(np.int32)],255,lineType=cv2.LINE_8)
    alpha=np.asarray(Image.fromarray(big).resize((W,H),Image.BOX),np.float32)/255
    # shrink 1px to avoid grey halo
    alpha=np.minimum(alpha, cv2.erode(alpha,np.ones((3,3),np.uint8)) * 0.5 + alpha*0.5)
    rgba=im.convert('RGBA'); rgba.putalpha(Image.fromarray((alpha*255).astype(np.uint8)))
    bb=Image.fromarray(((alpha>0.05)*255).astype(np.uint8)).getbbox(); o=rgba.crop(bb); S=int(max(o.size)*1.14)
    cv_=Image.new('RGB',(S,S),'white'); cv_.paste(o,((S-o.width)//2,(S-o.height)//2),o)
    cv_.resize((1200,1200),Image.LANCZOS).save(f"n{i}.jpg",quality=94); o.save(f"obj{i}.png")
tiles=[Image.open(f'n{i}.jpg').resize((500,500)) for i in range(1,8)]
c=Image.new('RGB',(2000,1000),'gray')
for k,t in enumerate(tiles): c.paste(t,((k%4)*500,(k//4)*500))
c.save('n_prev.jpg')
