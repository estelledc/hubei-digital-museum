"""Photo-guided full-museum spaces. Approximate dimensions, editable geometry.
Used by build_full_museum.py; all image-derived surfaces retain source notes.
"""
import bpy, math, random
from pathlib import Path
from mathutils import Vector
from artifact_geometry import Builder, mat, linear, aged
ROOT=Path(__file__).resolve().parents[1]
FONT=None

def text(b,body,loc,size=.25,color=None):
    global FONT
    FONT=next((f for f in bpy.data.fonts if f.filepath.endswith('STHeiti Medium.ttc')),None)
    if FONT is None:
        FONT=bpy.data.fonts.load(__import__('os').environ.get('MUSEUM_FONT', ''));FONT.pack()
    d=bpy.data.curves.new(body,'FONT');d.body=body;d.size=size;d.font=FONT;d.align_x='CENTER';d.extrude=.0001
    o=bpy.data.objects.new(body,d);b.add(o,body,color);o.location=loc;o.rotation_euler=(math.pi/2,0,0)
    o['accuracy']='digital interpretive label';return o

def beam(b,name,a,z,width,m):
    delta=Vector(z)-Vector(a);o=b.box(name,(Vector(a)+Vector(z))*.5,(width,width,delta.length),m,.01)
    o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return o

def cylinder(b,name,loc,r,depth,m,vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    o=b.add(bpy.context.object,name,m)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def luminous(name,color='#fff4dd',strength=2):
    m=mat(name,color,0,.35);p=m.node_tree.nodes['Principled BSDF'];p.inputs['Emission Color'].default_value=(*linear(color),1);p.inputs['Emission Strength'].default_value=strength;return m

def area(c,name,loc,target,power=450,size=3):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.specular_factor=0
    o=bpy.data.objects.new(name,d);c.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def spot(c,name,loc,target,power=50,angle=65):
    d=bpy.data.lights.new(name,'SPOT');d.energy=power;d.spot_size=math.radians(angle);d.spot_blend=.7;d.shadow_soft_size=.12
    o=bpy.data.objects.new(name,d);c.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def glass_material():
    m=mat('展柜低反射玻璃','#ffffff',0,.025);p=m.node_tree.nodes['Principled BSDF'];p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.46;return m

def picture(b,name,file,center,width,height,m=None):
    """An explicitly labelled reference board; never called a 3D artifact."""
    if m is None:
        m=mat(name+'_照片','#ffffff',0,.85)
        im=bpy.data.images.load(str(file),check_existing=True)
        if max(im.size)>2048:
            f=2048/max(im.size);im.scale(round(im.size[0]*f),round(im.size[1]*f))
        im.pack();n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im
        m.node_tree.links.new(n.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    x,y,z=center
    o=b.mesh(name,[(x-width/2,y,z-height/2),(x+width/2,y,z-height/2),(x+width/2,y,z+height/2),(x-width/2,y,z+height/2)],[(0,1,2,3)],m,False)
    uv=o.data.uv_layers.active
    for li,xy in zip(o.data.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=xy
    o['accuracy']='reference photograph displayed in digital gallery; not a scanned scene';return o

def case(b,name,x,y,w,d,h,base=.78,wall=False):
    dark=mat(name+'深灰柜体','#252827',.25,.42);edge=mat(name+'金属窄框','#4c4e49',.6,.32)
    lining=mat(name+'展台衬布','#c2bbaa',0,.91);glass=glass_material();lamp=luminous(name+'顶灯')
    b.box(name+'柜座',(x,y,base/2),(w,d,base),dark,.018)
    b.box(name+'衬台',(x,y,base+.022),(w-.06,d-.06,.04),lining,.012)
    for dx in [-1,1]:
        for dy in [-1,1]:b.box(name+'细立框',(x+dx*w/2,y+dy*d/2,base+h/2),(.018,.018,h),edge,0)
    for dy in [-1,1]:b.box(name+'透光面',(x,y+dy*d/2,base+h/2),(w,.006,h),glass,0)
    for dx in [-1,1]:b.box(name+'透光侧面',(x+dx*w/2,y,base+h/2),(.006,d,h),glass,0)
    b.box(name+'柜顶',(x,y,base+h+.04),(w+.04,d+.04,.08),dark,.015)
    b.box(name+'柜内灯',(x,y,base+h-.02),(w-.12,.045,.02),lamp,0)
    spot(b.c,name+'展品照明',(x,y-.1,base+h-.12),(x,y,base),32,55)
    return base+.045

def gallery_shell(b,g):
    w,d=g['size'];h=5.2
    wall=mat(g['id']+'展墙',g['wall'],0,.83);floor=aged(g['id']+'石材地坪',g['floor_color'],0,.55)
    black=mat('吊顶石墨灰','#171b1e',.1,.75);skirt=mat('踢脚灰','#494945',.1,.65)
    copper=mat('展厅文字暖白','#e8ddc1',.12,.6);light=luminous('展厅洗墙线灯','#fff3db',3)
    b.box('分区地坪',(0,0,-.15),(w,d,.3),floor,.02)
    b.box('后部展墙',(0,d/2,h/2),(w,.2,h),wall,.02)
    for side in [-1,1]:
        b.box('侧展墙',(side*w/2,0,h/2),(.2,d,h),wall,.02)
        b.box('入口侧墙',(side*(w/4+1),-d/2,h/2),(w/2-2,.2,h),wall,.02)
        b.box('金属踢脚',(side*(w/2-.13),0,.07),(.035,d,.14),skirt,0)
        b.box('洗墙灯槽',(side*(w/2-.35),0,h-.12),(.08,d-.7,.055),light,0)
    b.box('展厅吊顶',(0,0,h+.1),(w,d,.18),black,0)['roof']=True
    for x in [i*.35 for i in range(-int(w/.7)+1,int(w/.7))]:
        b.box('可见顶棚格栅',(x,0,h-.11),(.035,d,.20),black,0)['roof']=True
    for x in range(-int(w/2)+2,int(w/2),4):
        b.box('轨道灯横轨',(x,0,h-.28),(.04,d-.6,.045),black,0)
        for y in [-d*.29,0,d*.29]:
            cylinder(b,'轨道射灯',(x,y,h-.41),.075,.18,black,20)
            spot(b.c,'轨道灯',(x,y,h-.5),(x,y+.3,.4),70,80)
    for x in range(-int(w/2),int(w/2)+1,2):b.box('地坪纵缝',(x,0,.006),(.007,d,.002),skirt,0)
    for y in range(-int(d/2),int(d/2)+1,2):b.box('地坪横缝',(0,y,.006),(w,.007,.002),skirt,0)
    text(b,g['title'],(0,d/2-.15,3.8),.65,copper)
    text(b,g.get('subtitle',''),(0,d/2-.16,3.05),.21,copper)
    # Partitions and display routes are explicitly approximate, photo-guided.
    for side in [-1,1]:
        x=side*w*.36
        b.box('分段展墙',(x,d*.13,2.2),(.16,d*.43,4.4),wall,.035)
    for side in [-1,1]:
        for y in [-d*.25,d*.25]:
            b.box('休息凳',(side*(w/2-1.1),y,.38),(.65,1.9,.1),skirt,.045)
            for dy in [-.7,.7]:b.box('凳脚',(side*(w/2-1.1),y+dy,.18),(.40,.07,.36),black,.008)
    area(b.c,'柔和环境补光',(0,-d*.12,4.7),(0,d*.1,0),3000,max(w,d)*.45)
    area(b.c,'前部展陈照明',(0,-4,4.5),(0,1,1),1500,6)
    area(b.c,'后部洗墙',(0,d*.3,4.4),(0,d/2,2),1200,5)
    return copper

def enrich_public(scene):
    """Surgical refinement of public source scene, retaining previous materials."""
    c=bpy.data.collections.new('03_Public_公共空间细化_照片依据');scene.collection.children.link(c);b=Builder(c)
    white=mat('中庭暖白石材细化','#e5e4df',0,.38);metal=mat('中庭铝框','#8a9191',.65,.3)
    gray=aged('中庭白灰纹理石材','#b9b7af',0,.35);black=mat('入口墨色框','#2a3031',.6,.4);glass=glass_material();glow=luminous('中庭照明')
    # Replace floating stair treads with continuous flights and solid balustrades.
    for o in list(scene.objects):
        if any(o.name.startswith(n) for n in ['弧形楼梯踏步','弧梯扶手','中庭屋顶格栅','树形柱主干','树形柱分枝']):bpy.data.objects.remove(o,do_unlink=True)
    for side in [-1,1]:
        cx=side*20;cy=-9
        for level in [0,6.8,13.6]:
            n=44;span=math.pi*1.5;theta0=0
            for k in range(n):
                a=theta0+span*(k+.5)/n;z=level+(k+1)*6.8/n
                vs=[]
                for zz in [z-.20,z]:
                    for rr,aa in [(2.8,a-span/n/2),(5.2,a-span/n/2),(5.2,a+span/n/2),(2.8,a+span/n/2)]:vs.append((cx+rr*math.cos(aa),cy+rr*math.sin(aa),zz))
                b.mesh('旋梯整块踏步',vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],white,False)
            for rr in [2.75,5.25]:
                vs=[];fs=[]
                for k in range(129):
                    a=span*k/128;z=level+6.8*k/128
                    for dr,dz in [(-.07,-.3),(.07,-.3),(.07,1.08),(-.07,1.08)]:vs.append((cx+(rr+dr)*math.cos(a),cy+(rr+dr)*math.sin(a),z+dz))
                for k in range(128):
                    for j in range(4):fs.append((k*4+j,k*4+(j+1)%4,(k+1)*4+(j+1)%4,(k+1)*4+j))
                b.mesh('旋梯连续石材侧板',vs,fs,white)
                b.tube('旋梯上沿扶手',[(cx+rr*math.cos(span*k/128),cy+rr*math.sin(span*k/128),level+6.8*k/128+1.12) for k in range(129)],.045,metal,8)
            for k in [0,1]:
                a=span*k;b.box('楼梯接层平台',(cx+4*math.cos(a),cy+4*math.sin(a),level+6.8*k-.15),(3,3,.3),white,.03)
    # Faceted tree columns and triangular daylight structure visible in architect photos.
    for x in [-15,15]:
        beam(b,'树形柱四棱主干',(x,8,0),(x,8,11),1.15,white)
        for dx,dy in [(-12,-12),(12,-12),(-12,12),(12,12)]:
            beam(b,'仿生柱折线分叉',(x,8,8),(x+dx*.45,8+dy*.45,16),.85,white)
            beam(b,'仿生柱上枝',(x+dx*.45,8+dy*.45,16),(x+dx,8+dy,20.1),.55,white)
    for x in [-28,-14,0,14,28]:b.box('天窗主框',(x,0,20.8),(.26,61,.38),white,0)
    for y in [-28,-14,0,14,28]:
        b.box('天窗横框',(0,y,20.8),(59,.26,.38),white,0)
        for x in [-21,-7,7,21]:
            for sign in [-1,1]:beam(b,'天窗斜梁',(x-7,y-7,20.8),(x+7,y+7*sign,20.8),.18,white)
    # Curtain wall fixings, landing edges, floor joints and lifts.
    for x in range(-28,29,2):
        for z in [3.4,10.2,17]:
            b.box('幕墙玻璃分格',(x,-28.85,z),(1.96,.018,6.65),glass,0)
            for zz in [-2.5,2.5]:b.ellipsoid('幕墙点式连接',(x,-28.7,z+zz),(.07,.06,.07),metal,12,8)
    for level in [0,6.8,13.6,20.4]:
        for y in [-24,25]:
            for x in range(-28,29,2):
                b.box('环廊石材接缝',(x,y,level+.006),(.008,10.7,.005),metal,0)
                beam(b,'栏板立柱',(x,y+(5.4 if y<0 else -5.4),level),(x,y+(5.4 if y<0 else -5.4),level+1.1),.045,metal)
    for side in [-1,1]:
        x=side*27
        for level in [-6.8,0,6.8,13.6]:
            # Approximate inclined escalator connection, retaining clear floor labels.
            a=(x,-4,level+.10);z=(x,10,level+6.9)
            beam(b,'扶梯金属承梁',a,z,.72,metal)
            for sign in [-1,1]:
                b.tube('扶梯扶手',[(x+sign*.9,-4,level+1.1),(x+sign*.9,10,level+7.9)],.06,black,8)
                for k in range(29):
                    y=-4+k*.5;zz=level+k/28*6.8+.65
                    b.box('扶梯侧玻璃',(x+sign*.85,y,zz),(.01,.50,1),glass,0)
            for k in range(43):b.box('扶梯阶梯',(x,-4+k/42*14,level+k/42*6.8),(1.65,.38,.16),metal,.015)
        for level in [0,6.8,13.6,20.4]:
            b.box('电梯金属门',(side*24,30.7,level+1.25),(1.8,.06,2.5),metal,.01)
            text(b,('B1' if level<0 else str(int(round(level/6.8))+1)+'F'),(side*24,30.60,level+2.8),.28,black)
    for y in [-24,25]:
        b.box('四层中庭环廊',(0,y,20.4-.18),(58.8,11,.36),white,.01)
        b.box('四层环廊玻璃护栏',(0,y+(5.4 if y<0 else -5.4),20.95),(58.8,.012,1.1),glass,0)
    b.box('观景平台地面',(0,36,20.2),(58,10,.35),gray,.01)
    for y in [31,41]:
        b.box('观景平台玻璃护栏',(0,y,20.95),(58,.012,1.1),glass,0)
        b.tube('观景平台金属扶手',[(-29,y,21.53),(29,y,21.53)],.045,metal,8)
    # Ground arrival desk and seats, deliberately marked digital furniture layout.
    b.box('入口咨询台',(0,-19,.56),(5,1.3,1.12),white,.10)
    text(b,'咨询服务',(0,-19.66,.75),.28,black)
    for x in [-9,9]:
        b.box('入口休息长凳',(x,-19,.42),(3,.75,.13),white,.055)
        for dx in [-1,1]:b.box('长凳支座',(x+dx,-19,.18),(.18,.65,.36),metal,.02)
    for o in b.objects:o['part']='03_Public';o['accuracy']='architect photographs guide form; dimensions, joins and fixtures approximate'
    return c

def enrich_campus(scene):
    c=bpy.data.collections.new('01_Campus_Detail_外观与园林');scene.collection.children.link(c);b=Builder(c)
    stone=mat('外墙拼缝灰','#aaa9a4',0,.8);roof=mat('瓦屋面棱线','#515967',.05,.8);trunk=mat('树干褐灰','#514a3c',0,.95)
    # Existing trees use spheres. Replace their crowns with oriented leaf clusters.
    old=[o for o in scene.objects if o.name.startswith('树干')];locations=[o.location.copy() for o in old]
    for o in list(scene.objects):
        if o.name.startswith('园林阔叶树冠'):bpy.data.objects.remove(o,do_unlink=True)
    foliage=[mat('叶色'+str(i),color,0,.92) for i,color in enumerate(['#273c24','#3e522c','#4c5a34','#657144','#35462c'])]
    rng=random.Random(91);verts=[];faces=[];material_ids=[]
    for center in locations:
        for k in range(7):
            a=rng.random()*math.tau;r=rng.uniform(1,3);end=Vector((center.x+math.cos(a)*r,center.y+math.sin(a)*r,center.z+rng.uniform(5.3,7.3)))
            b.tube('不规则树枝',[tuple(center+Vector((0,0,1))),tuple((center+end)*.5),tuple(end)],.11,trunk,6)
            for _ in range(110):
                p=end+Vector((rng.gauss(0,1.2),rng.gauss(0,1.2),rng.gauss(0,.75)))
                a=rng.random()*math.tau;u=Vector((math.cos(a),math.sin(a),rng.uniform(-.6,.6)))*rng.uniform(.13,.28);v=Vector((-u.y,u.x,rng.uniform(-.06,.1)))*.55
                n=len(verts);verts.extend([tuple(p-u),tuple(p+v),tuple(p+u),tuple(p-v),tuple(p+Vector((0,0,.025)))])
                faces.extend([(n,n+1,n+4),(n+1,n+2,n+4),(n+2,n+3,n+4),(n+3,n,n+4)]);material_ids.extend([rng.randrange(5)]*4)
    leaf=b.mesh('园区阔叶树叶簇',verts,faces,foliage[0],False)
    for m in foliage[1:]:leaf.data.materials.append(m)
    for p,mi in zip(leaf.data.polygons,material_ids):p.material_index=mi
    # Individual tile ridges and stone seams, keeping the source massing intact.
    for cx,cy,w,d,h in [(0,112,72,57,24),(49,87,31,43,12),(-49,87,31,43,12),(-95,82,29,54,12)]:
        for yy in [-1,1]:
            for j in range(int(w*1.12/.65)):
                x=-w*.56+j*.65
                points=[]
                for k in range(13):
                    t=k/12;points.append((cx+x*(1-.55*t),cy+yy*(d*.58-d*.38*t),h+9*t+.10+.30*(1-t)**6))
                b.tube('连续灰瓦瓦垄',points,.045,roof,6)
        for dx in [-1,1]:
            beam(b,'老馆屋脊',(cx+dx*w*.25,cy-d*.2,h+9.12),(cx+dx*w*.25,cy+d*.2,h+9.12),.14,roof)
        for yy in [-1,1]:
            b.box('老馆出檐木构层',(cx,cy+yy*d*.51,h-.3),(w*1.08,.6,.5),roof,0)
            for x in range(int(-w/2)+1,int(w/2),2):b.box('檐下托梁',(cx+x,cy+yy*d*.48,h-.7),(.15,1.5,.48),roof,0)
    for side in [-1,1]:
        cx=side*47.6
        for z in [10,12,14,16,18,20]:
            yy=-32-(z-8)/12.4*3
            b.box('南馆横向石板阴缝',(cx,yy-.012,z),(38+(z-8)/12.4*8,.012,.012),stone,0)
    for o in b.objects:o['part']='01_Campus';o['accuracy']='photo-guided exterior details and approximate vegetation'
    return c
