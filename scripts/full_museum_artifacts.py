"""Additional representative exhibits for the full museum, in metres.
No new scan mesh is claimed. Photo reliefs and unknown dimensions are labelled.
"""
import bpy,math,random
import numpy as np
from pathlib import Path
from mathutils import Vector
from artifact_geometry import Builder,mat,aged,image_material,interpolate
from full_museum_spaces import cylinder,beam,text,picture
ROOT=Path(__file__).resolve().parents[1]

def photo(name,file,metal=0,rough=.6):return image_material(name,'full04/'+file,metal,rough,4096)

def surface(b,name,outline,file,image_size,height,depth,color,detail=0):
    """Closed photograph-projected relief; back/depth are explicitly approximate."""
    im=bpy.data.images.load(str(ROOT/'research/full04'/file),check_existing=True)
    iw,ih=im.size;pixels=np.empty(iw*ih*4,np.float32);im.pixels.foreach_get(pixels);pixels=pixels.reshape(ih,iw,4)
    pts=np.array(outline,float);xmin,ymin=pts.min(0);xmax,ymax=pts.max(0);scale=height/(ymax-ymin);cx=(xmin+xmax)/2
    rows=180;cols=128;v=[];uvs=[]
    for side in [-1,1]:
        for j in range(rows+1):
            py=ymax-(ymax-ymin)*(j+.001)/(rows+.002)
            crosses=[]
            for a,c in zip(pts,np.roll(pts,-1,axis=0)):
                if (a[1]<=py<c[1]) or(c[1]<=py<a[1]):crosses.append(a[0]+(py-a[1])*(c[0]-a[0])/(c[1]-a[1]))
            left,right=(min(crosses),max(crosses)) if crosses else (cx-.1,cx+.1)
            for k in range(cols+1):
                px=left+(right-left)*k/cols;u=px/image_size[0];vv=1-py/image_size[1]
                lum=float(pixels[min(ih-1,max(0,int(vv*ih))),min(iw-1,max(0,int(u*iw))),:3].mean())
                bulge=math.sin(math.pi*k/cols)*math.sin(math.pi*j/rows)
                y=side*depth*(.15+.35*bulge)
                if side<0:y-=detail*(lum-.2)*bulge
                v.append(((px-cx)*scale,y,(ymax-py)*scale));uvs.append((u,vv))
    n=(rows+1)*(cols+1);fs=[];indices=[]
    for j in range(rows):
        for k in range(cols):
            a=j*(cols+1)+k;fs.append((a,a+1,a+cols+2,a+cols+1));indices.append(1)
            fs.append((a+n,a+n+cols+1,a+n+cols+2,a+n+1));indices.append(0)
    edges=list(range(cols+1))+[j*(cols+1)+cols for j in range(1,rows+1)]+list(range(rows*(cols+1)+cols-1,rows*(cols+1)-1,-1))+[j*(cols+1) for j in range(rows-1,0,-1)]
    for a,c in zip(edges,edges[1:]+edges[:1]):fs.append((a,a+n,c+n,c));indices.append(0)
    m=aged(name+'侧背近似',color,0,.55);o=b.mesh(name,v,fs,m);o.data.materials.append(photo(name+'实拍正面',file,0,.65))
    uv=o.data.uv_layers.active
    for p,mi in zip(o.data.polygons,indices):
        p.material_index=mi
        for li in p.loop_indices:uv.data[li].uv=uvs[o.data.loops[li].vertex_index]
    o['accuracy']='closed photo-projected relief; silhouette observed, depth and back approximated; not a recovered scan'
    return o

def gold_ingot(b):
    outline=[(340,126),(409,134),(475,163),(528,204),(559,242),(564,259),(514,294),(480,342),(462,390),(461,442),(478,492),(516,528),(561,550),(569,572),(535,610),(480,651),(416,677),(350,689),(278,683),(216,652),(168,615),(143,579),(144,557),(192,524),(223,486),(246,433),(243,382),(222,336),(191,299),(147,267),(143,248),(173,216),(215,181),(278,144)]
    o=surface(b,'梁庄王金锭_束腰锭形_正面照片',outline,'liang-gold-ingot.jpeg',(640,770),.14,.015,'#b98d35',.001)
    # Photo contains genuine inscription. No text is invented or separately carved.
    o['scale_accuracy']='14 cm display height is approximate; published mass 1937g is not a dimension'

def jade_figure(b):
    outline=[(245,166),(469,166),(466,215),(458,228),(457,251),(468,260),(466,322),(473,343),(470,374),(461,389),(466,412),(465,467),(250,469),(246,411),(250,390),(241,369),(245,332),(239,269),(246,251),(251,230),(242,217)]
    surface(b,'石家河玉人_实拍浅浮雕',outline,'ancient-shijiahe-jade.jpeg',(700,600),.07,.012,'#ad9961',.0018)

def carving(b):
    outline=[(795,165),(825,176),(827,219),(858,220),(879,252),(916,244),(976,247),(996,280),(1018,309),(1016,329),(1061,348),(1055,400),(1074,445),(1072,475),(1088,505),(1080,557),(1087,604),(1073,651),(1060,694),(1089,731),(1080,760),(1051,789),(1067,834),(1050,873),(1050,922),(1038,961),(1048,992),(1010,1018),(959,1031),(903,1031),(871,1052),(803,1047),(759,1062),(692,1045),(639,1049),(578,1029),(554,998),(517,977),(526,940),(516,906),(491,877),(493,847),(478,813),(489,772),(484,725),(501,682),(506,639),(511,590),(543,564),(551,506),(567,471),(561,436),(578,398),(587,358),(613,318),(641,272),(675,232),(702,234),(738,195),(779,190)]
    sculpture=surface(b,'武当朝圣图_实拍轮廓浮雕投影',outline,'craft-wudang-chaosheng.jpeg',(1583,1568),.44,.25,'#2e7977',.005)
    sculpture.location.z=.085
    jade=aged('独山玉底座近似','#4a6760',0,.42);wood=aged('雕刻木底座近似','#36251e',0,.46)
    b.ellipsoid('独山玉随形托座',(0,0,.074),(.167,.13,.035),jade,64,24)
    b.box('木底座',(0,0,.018),(.38,.29,.036),wood,.025)
    for x in [-.15,.15]:
        for y in [-.10,.10]:b.ellipsoid('木托卷足',(x,y,.023),(.037,.035,.025),wood,32,16)

def ding(b):
    bronze=aged('方鼎青绿铜锈','#657063',.20,.84);dark=aged('方鼎暗部','#354536',.3,.79)
    # Rectangular hollow vessel, slightly splayed rim, four tapering legs and paired ears.
    sections=[(.14,.105,.235),(.18,.135,.455),(.191,.146,.475)]
    vs=[]
    for w,d,z in sections:
        for x,y in [(-w,-d),(w,-d),(w,d),(-w,d)]:vs.append((x,y,z))
    for w,d,z in [(.178,.133,.475),(.167,.122,.448),(.125,.090,.256)]:
        for x,y in [(-w,-d),(w,-d),(w,d),(-w,d)]:vs.append((x,y,z))
    fs=[]
    for j in range(5):
        for k in range(4):fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
    fs+=[(0,3,2,1),(20,21,22,23)]
    body=b.mesh('铜方鼎_折壁内腔',vs,fs,bronze,False)
    body.data.materials.append(photo('方鼎实拍前腹纹饰','zeng-jian-ding-cc-by-sa.jpg',.1,.82))
    for face in body.data.polygons:
        if face.index in [0,4]:
            face.material_index=1
            for li in face.loop_indices:
                v=body.data.vertices[body.data.loops[li].vertex_index].co;t=(v.z-.235)/.24
                px=(240+(v.x/.191+1)/2*530)*(1-t)+(211+(v.x/.191+1)/2*613)*t
                py=783*(1-t)+523*t
                body.data.uv_layers.active.data[li].uv=(px/1824,1-py/1368)
    for x in [-.115,.115]:
        for y in [-.080,.080]:
            b.tube('四柱足',[(x*1.13,y*1.1,0),(x*1.06,y*1.05,.11),(x,y,.25)],[(.022,.023),(.024,.024),(.026,.026)],bronze,24)
            for z in [.17,.21]:b.tube('柱足凸弦纹',[(x+.021*math.cos(t),y+.021*math.sin(t),z) for t in np.linspace(0,math.tau,49)],.0018,dark,6)
    for x in [-.15,.15]:
        b.tube('竖向环耳',interpolate([(x,-.065,.470),(x,-.063,.540),(x,-.040,.560),(x,.035,.560),(x,.06,.540),(x,.06,.470)]),(.014,.008),bronze,14)
    for y in [.131]:
        for z in [.266,.394,.447]:b.tube('鼎腹横带',[(-.171,y,z),(.171,y,z)],.004,dark,8)
        for x in [-.13,-.044,.044,.13]:
            pts=[]
            for t in np.linspace(0,math.tau*1.4,54):
                rr=.030*(1-t/(math.tau*1.8));pts.append((x+rr*math.cos(t),y,.417+rr*.55*math.sin(t)))
            b.tube('兽面纹旋曲近似',pts,.003,bronze,8)
    for x in [-.18,.18]:
        for y in [-.13,.13]:
            b.box('鼎角扉棱',(x,y,.352),(.013,.023,.215),bronze,.003)
            for z in [.31,.405]:b.box('扉棱凸齿',(x*1.035,y,.352+(z-.352)),(.019,.04,.015),bronze,.002)
    b.objects[0]['scale_accuracy']='56 cm display height inferred from photo proportions, no verified original dimensions'

def bronze_drum(b):
    bronze=aged('崇阳鼓灰褐青铜','#655d49',.48,.74);relief=aged('铜鼓凸纹','#817057',.42,.68)
    # Horizontal barrel. Height fixed at 75.5 cm; depth inferred from three-quarter photo.
    profile=[(0,-.24),(.181,-.24),(.191,-.21),(.219,-.12),(.23,0),(.219,.12),(.191,.21),(.181,.24),(0,.24)]
    o=b.lathe('横置铜鼓鼓身',[(r,z) for r,z in profile],bronze,144);o.rotation_euler.y=math.pi/2;o.location.z=.39
    # Square hollow base, arched lower opening and concave top crown.
    for side in [-1,1]:b.box('铜鼓方座足',(side*.095,0,.085),(.07,.18,.17),bronze,.010)
    b.box('铜鼓方座横部',(0,0,.159),(.26,.19,.085),bronze,.010)
    crown=[(-.103,.620),(-.11,.73),(-.095,.755),(-.075,.748),(-.067,.703),(-.043,.686),(.043,.686),(.067,.703),(.075,.748),(.095,.755),(.11,.73),(.103,.620)]
    b.polygon('弧凹冠',crown,.042,bronze,.005)
    # Photograph projection on observed front, with approximate cylindrical depth.
    m=photo('崇阳铜鼓馆方实拍纹饰','chongyang-drum.jpeg',.08,.83)
    bpy.context.view_layer.update()
    for obj in b.objects:
        if obj.type!='MESH':continue
        obj.data.materials.append(m);index=len(obj.data.materials)-1
        for face in obj.data.polygons:
            normal=obj.matrix_world.to_3x3()@face.normal
            if normal.y<-.15:
                face.material_index=index
                for li in face.loop_indices:
                    v=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
                    if '鼓身' in obj.name:
                        px=222+(v.x+.24)/.48*215;py=421-(v.z-.16)/.46*245
                    elif '冠' in obj.name:
                        px=309+(v.x+.11)/.22*97;py=148-(v.z-.62)/.135*82
                    else:
                        px=275+(v.x+.13)/.26*145;py=531-v.z/.20*106
                    obj.data.uv_layers.active.data[li].uv=(px/700,1-py/600)
        obj['accuracy']='photo projected visible bronze decoration; curvature and hidden faces approximate'

def medal(b):
    metal=aged('勋章氧化银灰','#595851',.67,.46)
    n=96;outline=[]
    for i in range(n):
        a=i*math.tau/n;r=.038*(1+.08*math.cos(a*16));outline.append((r*math.cos(a),.044+r*math.sin(a)))
    o=b.polygon('勋四位章多瓣边饰',outline,.004,metal,.0005)
    m=photo('勋四位章正面实拍','modern-lizuodong-medal.jpeg',.18,.44);o.data.materials.append(m)
    for p in o.data.polygons:
        if p.normal.y<-.5:p.material_index=1
    b.uv(o,lambda v:((995+v.x/.038*230)/1920,1-(630-(v.z-.044)/.038*230)/1280))
    center=b.ellipsoid('中央章面凸起',(0,-.003,.044),(.016,.003,.016),m,64,24)
    b.uv(center,lambda v:((995+v.x/.038*230)/1920,1-(630-(v.z)/.038*230)/1280))

def manuscript(b):
    paper=mat('稿本纸页黄褐','#c8b18a',0,.92);cover=mat('稿本封底','#765e43',0,.88)
    b.box('稿本纸册',(0,.006,.145),(.214,.013,.29),paper,.0012)
    b.box('稿本封底',(0,.014,.145),(.219,.002,.295),cover,.001)
    # Actual photographed leaf; no missing manuscript words are synthesized.
    m=photo('熊秉坤稿本实拍页','modern-xiongbingkun-manuscript.jpeg',0,.96)
    o=b.mesh('稿本微曲纸面',[(-.105,-.001,0),(.105,-.001,0),(.105,-.001,.29),(-.105,-.001,.29)],[(0,1,2,3)],m,False)
    b.uv(o,lambda v:((.028+(v.x+.105)/.21*.819),.024+v.z/.29*.956))
    for j in range(14):b.box('纸页叠层',(0,.007+j*.00045,.002),(.21,.00013,.001),paper,0)

def office(b):
    wood=aged('办公室深褐木材近似','#493426',0,.48);pale=aged('木窗与护墙板','#806138',0,.55)
    wall=mat('办公室灰米墙','#c5b69a',0,.89);floor=aged('办公室拼花木地板','#664330',0,.47);black=mat('家具黑褐部位','#231f19',0,.4)
    b.box('场景地台',(0,0,.065),(4.3,3.8,.13),floor,.02)
    b.box('办公室后墙',(0,1.8,1.65),(4.3,.13,3.3),wall,0)
    b.box('办公室右墙',(2.1,0,1.65),(.13,3.7,3.3),wall,0)
    b.box('窗下木护墙',(0,1.7,.6),(3,.08,1.2),pale,0)
    sky=mat('窗景近似柔和蓝绿','#718e89',0,.8)
    b.box('窗内示意背景',(-.45,1.70,2.05),(2.7,.03,1.65),sky,0)
    for x in [-1.8,-.9,0,.9]:b.box('木窗竖梃',(x,1.63,2.05),(.055,.08,1.75),pale,.008)
    for z in [1.18,1.61,2.04,2.47,2.90]:b.box('木窗横梃',(-.45,1.63,z),(2.8,.08,.045),pale,.005)
    for x in range(-20,21):
        b.box('木地板条缝',(x*.10,0,.132),(.003,3.65,.002),pale,0)
    # Desk, drawers, chair, bookshelf and tea furniture observable in the museum photograph.
    b.box('写字台桌面',(-.65,.75,.88),(1.75,.78,.075),wood,.022)
    for x in [-1.24,-.06]:
        b.box('书桌抽屉柜',(x,.79,.49),(.44,.66,.71),wood,.015)
        for z in [.29,.49,.69]:
            b.box('书桌抽屉面',(x,.435,z),(.405,.035,.17),wood,.010)
            b.box('抽屉金属拉手',(x,.403,z),(.080,.018,.011),black,.005)
    def chair(x,y,turn=0):
        start=len(b.objects)
        b.box('木椅座',(x,y,.52),(.49,.46,.055),wood,.018)
        for dx in [-.2,.2]:
            for dy in [-.18,.18]:b.box('木椅腿',(x+dx,y+dy,.28),(.038,.038,.50),wood,.004)
        for dx in [-.2,.2]:b.box('木椅靠背立柱',(x+dx,y+.18,.85),(.04,.04,.69),wood,.008)
        b.box('木椅上横档',(x,y+.18,1.16),(.47,.04,.06),wood,.010)
        for dx in [-.10,0,.10]:b.box('木椅靠背竖条',(x+dx,y+.18,.94),(.027,.025,.35),wood,.005)
    chair(-.60,-.15);chair(1.53,-.63);chair(1.53,.55)
    b.box('书架左侧',(1.02,1.27,.84),(.06,.39,1.42),wood,.012);b.box('书架右侧',(1.87,1.27,.84),(.06,.39,1.42),wood,.012)
    for z in [.16,.53,.9,1.27,1.57]:b.box('木书架层板',(1.445,1.27,z),(.9,.40,.045),wood,.008)
    rng=random.Random(44)
    for z in [.19,.56,.93,1.30]:
        x=1.08
        while x<1.78:
            w=rng.uniform(.025,.047);m=mat('书脊无拟造文字',rng.choice(['#66573f','#948365','#503c2e','#b1a488']),0,.9)
            b.box('书架陈列册',(x,1.20,z+.12),(w,.20,rng.uniform(.20,.27)),m,.002);x+=w+.015
    cylinder(b,'圆茶几',(1.42,-.03,.70),.30,.055,wood)
    for a in [0,2.1,4.2]:b.box('茶几足',(1.42+.19*math.cos(a),-.03+.19*math.sin(a),.40),(.038,.038,.55),wood,.003)
    porcelain=mat('茶具乳白釉','#d6d8c9',0,.25)
    for x in [1.28,1.57]:
        o=b.lathe('茶杯近似',[(0,0),(.045,0),(.048,.065),(.042,.068),(.036,.008),(0,.008)],porcelain,64);o.location=(x,-.03,.735)
    green=mat('台灯绿色玻璃','#1d8053',0,.25);brass=mat('台灯铜支架','#9c8349',.6,.35)
    cylinder(b,'台灯底',(-1.12,.91,.94),.09,.025,brass)
    cylinder(b,'台灯杆',(-1.12,.91,1.08),.012,.28,brass)
    b.ellipsoid('绿色台灯罩',(-1.12,.91,1.22),(.19,.075,.055),green,48,16)
    for x in [-.80,-.5]:b.box('案头纸页',(x,.76,.925),(.16,.21,.002),mat('案头素纸','#bba888',0,.96),0)
    for o in b.objects:o['accuracy']='museum office display reconstructed from photograph; furniture identity, dimensions and unobserved sides unknown'

def pottery_bell(b):
    clay=aged('陶铃橙褐陶胎','#a16f4c',0,.9)
    profile=[(.049,0),(.047,.006),(.040,.023),(.032,.043),(.029,.051),(.023,.054),(0,.054),(0,.047),(.022,.047),(.025,.045),(.033,.024),(.042,.006),(.044,0),(.049,0)]
    o=b.lathe('石家河陶铃_椭圆梯形中空器身',profile,clay,192)
    for v in o.data.vertices:v.co.y*=7/9.8
    image=photo('陶铃正面实拍刻花','tianlai-taoling-vr.png',0,.89);o.data.materials.append(image)
    for face in o.data.polygons:
        if face.index<5*192 and face.center.y<=0:
            # Assign using polygon vertices because mesh centers may need update.
            pass
    o.data.update()
    for face in o.data.polygons:
        if face.index<5*192 and face.center.y<-.005:
            face.material_index=1
            for li in face.loop_indices:
                v=o.data.vertices[o.data.loops[li].vertex_index].co
                t=v.z/.054;half=.049*(1-t)+.029*t
                front=min(1,max(0,-v.y/(half*7/9.8)));px=315+(v.x/half)*(166*(1-t)+87*t);py=(232+60*front)*(1-t)+(64-21*front)*t
                o.data.uv_layers.active.data[li].uv=(px/856,1-py/745)
    for x in [-.006,.006]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.0016,depth=.018,location=(x,0,.052))
        cutter=bpy.context.object;mod=o.modifiers.new('系铃双孔','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    o['accuracy']='official VR dimensions; photo front, approximate hidden incisions and wall thickness'

BUILDERS={'pottery-bell':pottery_bell,'ding-jian':ding,'gold-liang':gold_ingot,'drum-chongyang':bronze_drum,'jade-shijiahe':jade_figure,'carving-wudang':carving,'medal-lizuodong':medal,'manuscript-xiong':manuscript,'office-dong':office}

def build(slug,collection):
    b=Builder(collection);BUILDERS[slug](b)
    for o in b.objects:
        o['artifact_id']=slug;o['part']='06_Artifacts_04'
        if not o.get('accuracy'):o['accuracy']='photo-guided reconstruction, not scan; unobserved decoration and back approximate'
        if o.type=='MESH' and o.data.uv_layers.active:o.data.uv_layers.active.name='ArtifactUV'
    return b.objects
