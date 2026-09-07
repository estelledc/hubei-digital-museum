"""Refine the four public spaces from the frozen 0.11 files.
Photo-guided reconstruction, not surveyed dimensions or a navigation map.
Blender --background --python-exit-code 1 --python scripts/refine_public_four.py -- public|campus|assemble
"""
import sys, math, random, json, shutil
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from artifact_geometry import Builder, mat, linear
from full_museum_spaces import text, area, spot, beam, cylinder, luminous, glass_material
from polish_museum_spaces import project_uv
from build_full_museum import optimize_export
from refine_arrival import arc

SOURCE=ROOT/'backups/before-public-12/models'
OUT=ROOT/'renders/public-12';OUT.mkdir(parents=True,exist_ok=True)
VIEWS={
 'campus': [('园区总览',(190,-247,148),(0,53,2),43),('南广场',(54,-102,3),(0,-8,10),32),('北馆庭院',(69,197,15),(0,112,13),34)],
 'arrival':[('入口全景',(10,-24,1.7),(0,-1,2.3),24),('服务台近看',(19,-24,1.65),(12,-15,1.25),26),('下层大厅',(8,-24,-5.12),(0,0,-3.4),24)],
 'atrium':[('树形中庭',(9,-21,9.4),(-8,10,15.2),22),('旋梯近看',(-9,-22,10),(-20,-8,11.8),24),('临窗环廊',(-27,-24,15.25),(17,-15,15.5),25)],
 'connection':[('通道全景',(2,-21,1.65),(0,12,1.8),27),('北馆端',(-2,16,1.65),(0,24,2),26),('南馆端',(2,17,1.65),(0,-22,1.9),27)],
}

def collection(scene,name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return Builder(c)

def material_set(obj,m,scale=3):
 obj.data.materials.clear();obj.data.materials.append(m);project_uv(obj,scale)

def stone(name,color,rough=.42):
 """Low-contrast irregular mineral variation; no periodic checker or sine veins."""
 m=mat('12_'+name,color,0,rough);rng=np.random.default_rng(124)
 n=512;noise=rng.normal(size=(n,n));f=np.fft.fftfreq(n);yy,xx=np.meshgrid(f,f)
 cloud=np.fft.ifft2(np.fft.fft2(noise)/(1+(xx*xx+yy*yy)*14000)**1.2).real
 cloud=(cloud-cloud.mean())/(cloud.std()+1e-9)
 variation=np.clip(cloud*.028+noise*.005,-.13,.10)
 rgb=np.clip(linear(color)[None,None,:]*(1+variation[:,:,None]),0,1)
 encoded=np.where(rgb<=.0031308,rgb*12.92,1.055*rgb**(1/2.4)-.055)
 image=bpy.data.images.new(m.name+'_Albedo',width=n,height=n,alpha=False)
 image.colorspace_settings.name='sRGB';pixels=np.ones((n,n,4),np.float32);pixels[:,:,:3]=encoded
 image.pixels.foreach_set(pixels.ravel());image.pack()
 node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
 m.node_tree.links.new(node.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
 m['reference_srgb']=color;m['accuracy']='Irregular mineral texture study, not a photographed slab';return m

def mark(b,part,context=False):
 for o in b.objects:
  o['part']=part;o['public_revision']='0.12';o['context_only']=context
  o['accuracy']='Photo-guided form; dimensions, furniture and landscape positions approximate'

def cameras(scene,slug):
 result=[]
 for title,loc,target,lens in VIEWS[slug]:
  d=bpy.data.cameras.new('12_'+slug+'_'+title);o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o)
  o.location=loc;d.lens=lens;d.clip_start=.03
  o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();result.append(o)
 scene.camera=result[0];scene['public_views']=json.dumps(VIEWS[slug],ensure_ascii=False);return result

def save(scene,path):
 scene['public_revision']='0.12';scene['space_revision']='0.12'
 scene['accuracy']='Public photographs and sampled video; dimensions and hidden details approximate'
 scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
 scene.render.resolution_x=1440;scene.render.resolution_y=960;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=94
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.2
 for o in scene.objects:
  if o.type=='LIGHT' and o.data.type=='AREA':
   o.data.specular_factor=0;o.visible_glossy=False;o.visible_transmission=False
 for screen in bpy.data.screens:
  for a in screen.areas:
   if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
 bpy.ops.outliner.orphans_purge(do_recursive=True);bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)

def render(scene,name):
 scene.render.filepath=str(OUT/(name+'.jpg'));bpy.ops.render.render(write_still=True)

def append(path,b,offset=(0,0,0),gallery_only=False):
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=src.objects
 kept=[];rejected=[]
 for o in dst.objects:
  if not o:continue
  keep=o.type in ['MESH','FONT','CURVE','LIGHT'] and not o.get('context_only')
  if gallery_only:keep=keep and bool(o.get('gallery_id'))
  (kept if keep else rejected).append(o)
 rejected_set=set(rejected)
 for o in kept:
  if o.parent in rejected_set:
   transform=o.matrix_world.copy();o.parent=None;o.matrix_world=transform
 # One library remap, instead of scanning every material for every discarded object.
 if rejected:bpy.data.batch_remove(ids=rejected)
 for o in kept:
  b.c.objects.link(o)
  if not o.parent:o.location+=Vector(offset)
 print('APPENDED',path.name,len(kept),'objects',flush=True)

def foliage(b,points,seed=120):
 rng=random.Random(seed);bark=mat('12_树干','#544b3b',0,.9)
 leaves=[mat('12_叶色'+str(i),c,0,.92) for i,c in enumerate(['#294835','#3c5c36','#536d3a','#71834b'])]
 verts=[];faces=[];ids=[]
 for x,y,z,h in points:
  b.tube('12_庭院树干',[(x,y,z),(x+.1,y,z+h*.55),(x,y,z+h*.9)],[.17,.12,.035],bark,8)
  for k in range(7):
   a=k*2.4;end=Vector((x+math.cos(a)*h*.19,y+math.sin(a)*h*.19,z+h+rng.uniform(-.8,.7)))
   b.tube('12_庭院树枝',[(x,y,z+h*.5),tuple(end)],.04,bark,6)
   for j in range(95):
    p=end+Vector((rng.gauss(0,h*.12),rng.gauss(0,h*.12),rng.gauss(0,h*.07)));a=rng.random()*math.tau
    u=Vector((math.cos(a),math.sin(a),rng.uniform(-.35,.35)))*rng.uniform(.17,.32)
    v=Vector((-u.y,u.x,.035))*.65;n=len(verts)
    verts.extend([tuple(p-u),tuple(p+v),tuple(p+u),tuple(p-v)]);faces.append((n,n+1,n+2,n+3));ids.append(rng.randrange(4))
 o=b.mesh('12_庭院细叶冠层',verts,faces,leaves[0],False)
 for m in leaves[1:]:o.data.materials.append(m)
 for p,i in zip(o.data.polygons,ids):p.material_index=i

def window_context(scene,connection=False):
 b=collection(scene,'12_Context_窗外环境示意');paving=stone('窗外石铺地','#b5b4ab',.75);grass=mat('12_窗外绿地','#526341',0,.96)
 level=-13.6 if connection else -7.5
 if connection:
  b.box('12_连接庭院地面',(0,0,level-.2),(70,70,.3),grass,0)
  for side in [-1,1]:b.box('12_连接庭院步道',(side*10,0,level),(3,65,.10),paving,0)
  foliage(b,[(side*x,y,level,18) for side in [-1,1] for x in [15,25] for y in [-14,1,15]])
  # Show receiving halls beyond the doors instead of an empty world background.
  cream=stone('衔接门厅石墙','#d3d0c4',.62)
  for end in [-1,1]:
   b.box('12_门外接续地坪',(0,end*28.5,-.12),(16,9,.24),paving,.01)
   for side in [-1,1]:b.box('12_门外接续侧墙',(side*8,end*28.5,2.75),(.25,9,5.5),cream,.01)
   b.box('12_门外门厅远墙',(0,end*33,2.75),(16,.25,5.5),cream,.01)
   b.box('12_门外门厅顶棚',(0,end*28.5,5.5),(16,9,.2),cream,.01)
   for side in [-1,1]:b.box('12_门外通道暗框',(side*4,end*32.8,1.7),(2.4,.06,3.4),mat('12_接续通道暗色','#68675e',0,.8),.01)
   o=area(b.c,'12_接续门厅天光',(0,end*28.5,5.2),(0,end*28.5,0),650,5);o['context_only']=True

 else:
  b.box('12_窗外南广场',(0,-54,level-.15),(120,45,.3),paving,0)
  for side in [-1,1]:b.box('12_窗外绿带',(side*43,-51,level),(15,43,.12),grass,0)
  foliage(b,[(side*x,y,level,8) for side in [-1,1] for x in [36,47] for y in [-38,-52,-67]])
  b.box('12_远侧湖景',(90,-65,level-.05),(80,120,.05),mat('12_远侧湖水','#617b80',.18,.25),0)
 mark(b,'Context12',True)

def public():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'public/arrival.blend'),load_ui=False);s=bpy.context.scene
 b=collection(s,'12_Public_中庭及入口深化')
 floor=stone('公共石地坪','#cfcec7',.34);wall=stone('浅米灰石墙','#d7d5ca',.53)
 paint=mat('12_白色结构涂层','#e7e8e4',0,.55);dark=mat('12_深灰收口','#3e4240',.5,.36);steel=mat('12_金属扶手','#a7aaa5',.8,.24)
 glass=glass_material();glass.name='12_中庭低反射玻璃'
 sky=mat('12_天窗夹胶玻璃','#e3e9ec',0,.16);p=sky.node_tree.nodes['Principled BSDF'];p.inputs['Transmission Weight'].default_value=.9;p.inputs['IOR'].default_value=1.46
 for o in list(s.objects):
  if o.name.startswith(('树形柱四棱主干','仿生柱折线分叉','仿生柱上枝')):bpy.data.objects.remove(o,do_unlink=True);continue
  if o.type!='MESH':continue
  if o.name.startswith(('中庭玻璃顶','天窗主框','天窗横框','天窗斜梁')):o.location.z+=6.8
  if o.name.startswith(('环廊栏板','四层环廊玻璃护栏')):material_set(o,glass)
  elif o.name.startswith('中庭玻璃顶'):material_set(o,sky);o['roof']=True
  elif any(k in o.name for k in ['中庭地坪','中庭环廊','四层中庭环廊','11_门厅顶板','旋梯整块踏步','楼梯接层平台']):
   material_set(o,floor,3.5)
   o.data.materials.append(paint)
   for poly in o.data.polygons:
    if poly.normal.z<-.5:poly.material_index=1
  elif any(k in o.name for k in ['中庭北侧','旋梯连续石材侧板','11_门厅侧墙','11_下层大厅后墙','11_入口石材方柱','11_咨询台石材柜身']):material_set(o,wall,4)
  elif o.name.startswith('11_灯幕暗蓝底盘'):
   material_set(o,luminous('12_灯幕浅蓝光底','#85b6cc',.22))
 # Continuous branching shapes terminate at the skylight grid rather than crossing it.
 for x in [-15,15]:
  b.box('12_树形柱主干',(x,8,12.8),(1.30,1.30,12),paint,.11)
  for dx,dy in [(-12,-12),(12,-12),(-12,12),(12,12)]:
   points=[];radii=[]
   for i in range(19):
    t=i/18;horizontal=t*t*(2-t);points.append((x+dx*horizontal,8+dy*horizontal,18.0+9.4*t));radii.append(.78*(1-t)+.29*t)
   b.tube('12_树冠连续分叉',points,radii,paint,8)
   end=points[-1];grid_x=min([-28,-14,0,14,28],key=lambda a:abs(a-end[0]))
   beam(b,'12_树冠天窗接合梁',end,(grid_x,end[1],27.55),.42,paint)
 # Four gallery levels need headroom above the highest landing at 20.4 m.
 # Extend the public enclosure and top glazing to the consistent 27.6 m roof.
 for side in [-1,1]:
  for y,d in [(-4.5,53),(28.5,5)]:b.box('12_中庭上部侧围护',(side*29.5,y,17),(.25,d,20.4),wall,.015)
  for level in [6.8,13.6,20.4]:b.box('12_侧廊入口门楣',(side*29.5,24,level+5.35),(.25,4,2.9),wall,.015)
  b.box('12_中庭北墙上部',(side*16.7,31,23.65),(25.4,.35,7.3),wall,.015)
 b.box('12_中庭北墙上部中央',(0,31,23.65),(8,.35,7.3),wall,.015)
 for x in range(-28,29,2):
  b.box('12_最高层幕墙玻璃',(x,-28.85,23.8),(1.96,.018,6.7),glass,0)
  for z in [21.5,26.1]:b.ellipsoid('12_幕墙点式连接',(x,-28.7,z),(.07,.06,.07),steel,12,8)
 # Glazing joints, thin floor fascias and anti-slip tread inserts add human-scale detail.
 for level in [6.8,13.6,20.4]:
  for y in [-18.6,19.6]:
   b.box('12_平台铝合金边槽',(0,y,level+.035),(58.8,.07,.075),steel,.005)
  for side in [-1,1]:
   x=side*20
   arc(b,'12_旋梯四分之一圈平台',2.8,5.2,level-.18,.36,floor,math.pi*1.5,math.tau,cx=x,cy=-9)
   arc(b,'12_旋梯平台弧形玻璃',5.2,5.217,level+.06,1.02,glass,math.pi*1.5+.1,math.tau-.1,cx=x,cy=-9)
   b.box('12_旋梯接层过渡',(x,-16.5,level-.18),(3.2,5.2,.36),floor,.02)
   for dx in [-1.63,1.63]:
    b.box('12_接层玻璃护栏',(x+dx,-16.5,level+.57),(.014,4.9,1.1),glass,0)
    b.tube('12_接层金属扶手',[(x+dx,-18.9,level+1.13),(x+dx,-14.1,level+1.13)],.025,steel,8)
 for side in [-1,1]:
  for level in [0,6.8,13.6]:
   for i in range(44):
    a=math.pi*1.5*(i+.88)/44;z=level+(i+1)*6.8/44+.008
    b.tube('12_踏步防滑嵌条',[(side*20+r*math.cos(a),-9+r*math.sin(a),z) for r in [2.91,5.07]],.007,dark,6)
 # Regular slab joints replace a highly repetitive checker texture.
 for level in [-6.8,0,6.8,13.6]:
  for z in [1.25,2.5,3.75,5.0]:
   for side in [-1,1]:b.box('12_墙面石板横缝',(side*16.7,30.806,level+z),(25.3,.006,.008),dark,0)
  for side in [-1,1]:
   for x in range(5,30,3):b.box('12_墙面石板错缝',(side*x,30.802,level+3),(.007,.006,5.95),dark,0)
 for level in [-6.8,0]:
  for x in [-19,19]:
   for y in [-25,16]:
    for dx in [-.42,.42]:b.box('12_石柱金属护角',(x+dx,y-.424,level+3.15),(.025,.025,6.25),steel,.004)
  # Return walls and framed glazing give the formerly empty north opening depth.
  for side in [-1,1]:b.box('12_北向过渡门厅侧墙',(side*4,34,level+2.6),(.16,6,5.2),wall,.01)
  b.box('12_北向过渡门厅地面',(0,34,level-.10),(8,6,.2),floor,.01)
  b.box('12_北向过渡门厅顶棚',(0,34,level+5.3),(8,6,.18),paint,.01)
  for x in [-3,-1,1,3]:
   b.box('12_过渡门金属框',(x-1,31.3,level+2.1),(.05,.1,4.2),dark,.004)
   b.box('12_过渡门玻璃',(x,31.3,level+2.08),(1.94,.015,4.1),glass,0)
  b.box('12_过渡门顶框',(0,31.3,level+4.22),(8,.13,.14),dark,.008)
  area(b.c,'12_门厅纵深照明',(0,34,level+4.9),(0,31,level+1.5),700,4)
 for x in [-14,14]:
  for dx in [-1.5,1.5]:
   b.box('12_服务台键盘',(x+dx,-18.32,1.155),(.36,.13,.02),dark,.009)
  b.box('12_服务台侧面开缝',(x+3.11,-18,.62),(.005,.66,.012),dark,0)
  for y in [-18.5,-17.5]:b.box('12_服务台侧收边',(x+3.112,y,.54),(.01,.009,.84),steel,0)
 # Add visible downlight apertures around the daylight ceiling.
 for x in [-27,27]:
  for y in range(-24,28,4):
   cylinder(b,'12_天窗边筒灯',(x,y,27.19),.09,.018,luminous('12_白色筒灯','#f2ede1',1.5),20)
 mark(b,'03_Public12');window_context(s)
 # Skylight lamps stay out of glass reflections.
 for o in s.objects:
  if o.type=='LIGHT' and o.name.startswith(('11_中庭天光','11_中庭采光')):o.location.z+=6.8
  if o.type=='LIGHT' and o.name.startswith('11_中庭天光'):o.data.energy=6500
 s.world.node_tree.nodes['Background'].inputs[0].default_value=(.64,.75,.86,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 ac=cameras(s,'arrival');save(s,ROOT/'models/public/arrival.blend');render(s,'arrival')
 s.camera=ac[1];render(s,'arrival-service')
 tc=cameras(s,'atrium');save(s,ROOT/'models/public/atrium.blend');render(s,'atrium')
 s.camera=tc[1];render(s,'atrium-stairs')
 optimize_export(list(s.objects),ROOT/'models/public/atrium.glb');shutil.copy2(ROOT/'models/public/atrium.glb',ROOT/'models/public/arrival.glb')
 print('PUBLIC12_ATRIUM_DONE',flush=True)
 connection()

def connection():
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;b=collection(s,'12_Connection_连接廊与两端门厅')
 floor=stone('连接廊石地坪','#c8c7bf',.32);wall=stone('连接廊浅米石','#d7d4c7',.56)
 white=mat('12_连接廊白顶','#e6e5df',0,.72);metal=mat('12_连接廊暖灰金属','#737972',.65,.3);dark=mat('12_连接廊深色框','#353d3d',.55,.34)
 red=mat('12_北馆楚红门套','#683a32',0,.6);glass=glass_material();glass.name='12_连接廊通透玻璃'
 b.box('12_连廊承重楼板',(0,0,-.20),(12.4,48,.4),floor,.02)
 b.box('12_连廊白色顶棚',(0,0,4.6),(12.4,48,.25),white,.02)['roof']=True
 for y in range(-24,25,2):b.box('12_连廊横向铺地接缝',(0,y,.006),(12,.007,.004),metal,0)
 for x in [-4,-2,0,2,4]:b.box('12_连廊纵向铺地接缝',(x,0,.007),(.007,48,.004),metal,0)
 for side in [-1,1]:
  x=side*6
  for y in range(-12,15,3):
   b.box('12_连廊窗边石台',(x,y,.30),(.24,2.98,.60),wall,.012)
   b.box('12_连廊分格玻璃',(x,y,2.5),(.015,2.95,3.7),glass,0)
   b.box('12_连廊竖向框',(x-side*.02,y-1.5,2.3),(.08,.065,4.6),metal,.006)
   b.box('12_连廊通风窗横框',(x-side*.02,y,3.6),(.09,3,.045),metal,.005)
  b.tube('12_连廊临窗扶手',[(x-side*.18,-13.5,1.05),(x-side*.18,13.5,1.05)],.03,metal,10)
  for y in [-19,19]:
   b.box('12_端部门厅石墙',(x,y,2.3),(.25,10,4.6),wall,.02)
   for z in [1.15,2.3,3.45]:b.box('12_门厅横缝',(x-side*.132,y,z),(.006,9.95,.009),metal,0)
  for y in [-14,14]:b.box('12_新旧结构交界石柱',(x-side*.15,y,2.3),(.6,.65,4.6),wall,.01)
  b.box('12_地脚通风线槽',(x-side*.2,0,.1),(.025,27,.12),dark,.004)
 for y in [-24,24]:
  for side in [-1,1]:b.box('12_端部入口侧墙',(side*4.25,y,2.3),(3.5,.22,4.6),wall,.015)
  b.box('12_端部入口门楣',(0,y,4.0),(5,.3,1.2),red if y>0 else dark,.025)
  for x in [-2.55,2.55]:b.box('12_入口门套',(x,y,1.7),(.20,.3,3.4),red if y>0 else dark,.012)
  for x in [-1.85,-.62,.62,1.85]:
   b.box('12_端部门扇',(x,y,1.67),(1.20,.015,3.3),glass,0)
   b.box('12_端部门扇窄框',(x-.61,y,1.67),(.035,.08,3.34),metal,.005)
  title=text(b,'北馆' if y>0 else '南馆',(0,y+(-.18 if y>0 else .18),3.92),.4,white)
  if y<0:title.rotation_euler.z=math.pi
  b.box('12_伸缩缝盖板',(0,y*.59,.013),(12,.16,.024),metal,.002)
 for side in [-1,1]:
  x=side*4.9
  b.box('12_连廊休息凳',(x,17,.44),(.63,2.8,.16),wall,.04)
  for y in [16,18]:b.box('12_座凳支脚',(x,y,.21),(.42,.09,.42),dark,.009)
 for y in [-20,-12,-4,4,12,20]:
  for side in [-1,1]:
   x=side*4.8;b.box('12_顶棚纵向灯槽',(x,y,4.45),(.04,5,.025),luminous('12_廊道线性灯','#fff3da',1.6),.004)
   b.box('12_顶棚风口',(x-side*.36,y,4.445),(.055,1.6,.025),dark,0)
  area(b.c,'12_连廊柔光',(0,y,4.35),(0,y,0),420,5)
  o=spot(b.c,'12_连廊照明',(0,y,4.3),(0,y,0),55,115);o['web_intensity']=50.;o['web_shadow']=False
 mark(b,'Public_connection')
 for o in b.c.objects:
  o['part']='Public_connection';o['public_revision']='0.12'
 window_context(s,True)
 s.world=bpy.data.worlds.new('12_连廊日光');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.78,.9,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 for side in [-1,1]:area(b.c,'12_连接廊窗侧日光',(side*6.6,0,3.5),(0,0,1),1800,16)
 cs=cameras(s,'connection');s['assembly_levels']=[6.8,13.6];s['assembly_offset']=[0,56,13.6]
 save(s,ROOT/'models/public/connection.blend');render(s,'connection');s.camera=cs[1];render(s,'connection-north')
 optimize_export(list(s.objects),ROOT/'models/public/connection.glb');print('PUBLIC12_CONNECTION_DONE',flush=True)

def campus():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'campus-polished.blend'),load_ui=False);s=bpy.context.scene
 for o in list(s.objects):
  if str(o.get('part','')).startswith(('03_','Public_connection')) or o.name.startswith(('中庭玻璃顶','11_','12_')):bpy.data.objects.remove(o,do_unlink=True)
 # Raise the southern roof to clear the existing fourth-floor galleries.
 # Stretch its upper stone fascias and joints from the retained 8 m setback.
 for o in s.objects:
  if o.type!='MESH':continue
  if o.name.startswith(('南馆倒梯形石材立面','南馆侧石材立面','南馆横向石板阴缝','10_立面分格竖缝','石材竖缝','立面阴缝','翼部屋顶')):
   inverse=o.matrix_world.inverted()
   for v in o.data.vertices:
    w=o.matrix_world@v.co
    if w.z>8:w.z=8+(w.z-8)*(19.2/12.4)
    v.co=inverse@w
 b=collection(s,'12_Campus_铺地地形与构件');paving=stone('园区浅灰花岗岩','#b8b8ae',.73);wall=stone('基座石材','#a2a298',.76)
 roof=stone('旧馆屋面青灰瓦','#535d65',.81);metal=mat('12_室外深色金属','#454d4a',.6,.48);wood=mat('12_老馆深色檐下','#473b31',0,.76)
 facade=stone('馆舍浅色石板','#d9d8d0',.62)
 for o in s.objects:
  if o.type=='MESH' and any(k in o.name for k in ['石材立面','外墙','侧墙','翼部屋顶']):material_set(o,facade,4)
 # The architect's facade photographs show shallow, stepped white relief strips.
 # These repeat their depth and rhythm, not an invented transcription of the motifs.
 for side in [-1,1]:
  cx=side*47.6
  for front in [-1,1]:
   for base in [12.0,17.5,23.0]:
    for x,length,dz in [(-15,5,0),(-10,3,.55),(-6,6,.95),(0,4,.40),(5,5,.95),(11,3,.55),(15,3,0)]:
     z=base+dz;t=(z-8)/19.2
     b.box('12_南馆浅浮雕石条',(cx+x,front*(32+3*t+.13),z),(length,.18,.24),facade,.025)
     if x in [-10,0,11]:b.box('12_南馆浮雕折接',(cx+x-length*.5,front*(32+3*t+.14),z-.27),(.25,.19,.78),facade,.02)
 # The old museum is on the higher northern ground in the architect's section.
 b.box('12_北侧高地基体',(-15,115,-4.65),(210,162,6.6),wall,.04)
 b.box('12_北馆庭院铺地',(-2,167,-1.325),(116,48,.05),paving,.015)
 b.box('12_新旧馆间庭院铺地',(0,57,-1.325),(148,43,.05),paving,.015)
 for side in [-1,1]:
  b.box('12_沿馆侧步道',(side*73,73,-1.31),(4.5,118,.07),paving,.02)
  b.box('12_南广场侧步道',(side*75,-66,-7.46),(4.5,77,.08),paving,.02)
 for x in range(-58,58,4):b.box('12_北广场纵缝',(x,167,-1.293),(.009,48,.008),metal,0)
 for y in range(144,192,4):b.box('12_北广场横缝',(-2,y,-1.291),(116,.009,.008),metal,0)
 # Continuous lake-edge walking line and retaining edge, derived from the simplified site boundary.
 for a,z in [((90,-108,-7.42),(96,-10,-7.42)),((96,-10,-7.42),(103,148,-7.42))]:
  delta=Vector(z)-Vector(a);o=b.box('12_滨湖步道',(Vector(a)+Vector(z))*.5,(3.8,delta.length,.18),paving,.02);o.rotation_euler.z=-math.atan2(delta.x,delta.y)
  b.tube('12_湖岸深色压顶',[(a[0]+2,a[1],a[2]),(z[0]+2,z[1],z[2])],.14,wall,6)
 for x in [-24,0,24]:
  points=[(x,-43+i*.6,-6.38+i*.425) for i in range(16)]
  b.tube('12_南台阶连续扶手',points,.04,metal,12)
  for i in [0,5,10,15]:beam(b,'12_南台阶扶手立柱',(x,-43+i*.6,-7.35+i*.425),points[i],.05,metal)
 for x in [-31,31]:
  b.box('12_南入口侧石台',(x,-30.8,-.3),(4.2,5.2,.6),paving,.02)
  b.box('12_入口石台排水边',(x,-33.3,.015),(4.2,.10,.03),metal,.005)
 # The old simplified roofs ended in broad flat caps. Add their raised hipped crowns.
 for cx,cy,w,d,h in [(0,112,72,57,24),(49,87,31,43,12),(-49,87,31,43,12),(-95,82,29,54,12)]:
  base=h+9.03;rise=3.6 if w>60 else 2.2
  vs=[(cx-w*.25,cy-d*.2,base),(cx+w*.25,cy-d*.2,base),(cx+w*.25,cy+d*.2,base),(cx-w*.25,cy+d*.2,base),(cx-w*.12,cy,base+rise),(cx+w*.12,cy,base+rise)]
  o=b.mesh('12_老馆上层屋冠',vs,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],roof,False);o['roof']=True
  b.tube('12_老馆正脊',[(cx-w*.125,cy,base+rise+.12),(cx+w*.125,cy,base+rise+.12)],.13,roof,10)['roof']=True
  for side in [-1,1]:
   for j in range(int(w*.5/.7)):
    x=-w*.25+j*.7
    b.tube('12_上层瓦垄',[(cx+x,cy+side*d*.2,base+.04),(cx+x*.48,cy,base+rise+.04)],.035,roof,6)['roof']=True
   y=cy+side*d*.505
   b.box('12_檐下连续阴影层',(cx,y,h-.15),(w*1.1,.55,.24),wood,.02)
  # Stone foundation and the low entry stair are coherent with the raised terrain.
  for j in range(8):b.box('12_旧馆基座台阶',(cx,cy+d/2+3.8-j*.35,-1.25+j*.16),(w*.5,.38,.18),paving,.01)
  # Historical north-facing photograph: horizontal dark glazing, pale piers and
  # layered overhanging eaves. Reconstruct those visible forms at approximate scale.
  glazing=mat('12_旧馆窗带深灰玻璃','#344348',.38,.2)
  red=mat('12_旧馆窗檐暗红','#5f3d32',0,.58)
  levels=[3.2,10.0,16.8] if h>20 else [3.2,9.0]
  for z in levels:
   y=cy+d/2+.24
   b.box('12_旧馆北向连续窗带',(cx,y,z),(w-2,.12,2.9),glazing,.01)
   for j in range(int(w/4)):
    x=cx-w/2+2+j*4
    b.box('12_旧馆北向石柱',(x,y+.11,z),(.35,.35,3.5),facade,.02)
    b.box('12_旧馆窗格竖梃',(x+2,y+.08,z),(.055,.09,2.85),metal,.004)
   b.box('12_旧馆窗带横枋',(cx,y+.1,z+1.5),(w,.25,.2),red,.01)
   for end in [-1,1]:
    x=cx+end*(w/2+.24)
    b.box('12_旧馆侧向窗带',(x,cy,z),(.12,d-2,2.9),glazing,.01)
    for j in range(int(d/4)):b.box('12_旧馆侧向石柱',(x+end*.1,cy-d/2+2+j*4,z),(.35,.35,3.5),facade,.02)
   lower=z+2.4;upper=lower+1.35
   vs=[(cx-w/2-2.1,cy-d/2-2.1,lower),(cx+w/2+2.1,cy-d/2-2.1,lower),(cx+w/2+2.1,cy+d/2+2.1,lower),(cx-w/2-2.1,cy+d/2+2.1,lower),(cx-w/2,cy-d/2,upper),(cx+w/2,cy-d/2,upper),(cx+w/2,cy+d/2,upper),(cx-w/2,cy+d/2,upper)]
   b.mesh('12_旧馆层叠挑檐',vs,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],roof,False)['roof']=True
   for end in [-1,1]:b.box('12_旧馆檐口浅色收边',(cx,cy+end*(d/2+2.1),lower),(w+4.2,.18,.18),facade,.015)['roof']=True
  for dx in [-3,-1,1,3]:
   y=cy+d/2+.38
   b.box('12_旧馆北入口门扇',(cx+dx,y,1.65),(1.9,.1,3.3),glazing,.015)
   b.box('12_旧馆北入口门梃',(cx+dx-.95,y+.06,1.65),(.055,.08,3.3),metal,.005)
   b.tube('12_旧馆入口门拉手',[(cx+dx+.7,y+.2,1.1),(cx+dx+.7,y+.2,1.75)],.025,metal,10)
 # Hand-scale furniture belongs at the path edge, leaving the main axis clear.
 for side in [-1,1]:
  for y in [-90,-60]:
   x=side*67;b.box('12_广场休息长凳',(x,y,-7.0),(3,.64,.16),wood,.03)
   for dx in [-1,1]:b.box('12_广场凳脚',(x+dx,y,-7.28),(.09,.43,.55),metal,.01)
  x=side*60;b.box('12_园区导览牌',(x,-52,-5.8),(1.15,.13,2.8),metal,.02)
  text(b,'湖北省博物馆',(x,-52.08,-5.2),.105,mat('12_导览牌字','#e4e2d7',0,.8))
 # Additional low canopy softens the edge of the broad south square.
 foliage(b,[(side*x,y,-7.45,5.5) for side in [-1,1] for x in [67,82] for y in [-97,-80,-61]],122)
 mark(b,'01_Campus12')
 public=collection(s,'12_IntegratedPublic');append(ROOT/'models/public/atrium.blend',public)
 for level in [6.8,13.6]:
  cb=collection(s,'12_连接廊_'+str(level));append(ROOT/'models/public/connection.blend',cb,(0,56,level))
 s.world.node_tree.nodes['Background'].inputs[0].default_value=(.63,.77,.91,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 cs=cameras(s,'campus');s['version']='0.12';save(s,ROOT/'models/campus-polished.blend');render(s,'campus')
 s.camera=cs[1];render(s,'campus-south');s.camera=cs[2];render(s,'campus-north')
 optimize_export(list(s.objects),ROOT/'models/museum-architecture.glb');print('PUBLIC12_CAMPUS_DONE',flush=True)

def assemble():
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/campus-polished.blend'),load_ui=False);s=bpy.context.scene
 g=collection(s,'12_PreservedGalleries');append(SOURCE/'hubei-museum.blend',g,gallery_only=True)
 t=collection(s,'12_PreservedTheatre');append(ROOT/'models/public/theatre.blend',t,(-48,0,-6.8))
 s['version']='0.12';s['gallery_count']=11;s['artifact_count']=16
 save(s,ROOT/'models/hubei-museum.blend');print('PUBLIC12_ASSEMBLED',flush=True)

def lighting():
 # Refine Cycles-only light visibility without rebuilding or exporting geometry.
 # Area lights must illuminate the glass, not appear as giant white panels behind it.
 for slug, path, names in [
  ('connection','public/connection.blend',['connection','connection-north']),
  ('arrival','public/arrival.blend',['arrival','arrival-service']),
  ('atrium','public/atrium.blend',['atrium','atrium-stairs']),
  ('campus','campus-polished.blend',['campus','campus-south','campus-north']),
 ]:
  bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models'/path),load_ui=False);s=bpy.context.scene
  s.camera=bpy.data.objects['12_'+slug+'_'+VIEWS[slug][0][0]];save(s,ROOT/'models'/path)
  for index,name in enumerate(names):
   s.camera=bpy.data.objects['12_'+slug+'_'+VIEWS[slug][index][0]];render(s,name)
  print('PUBLIC12_LIGHTING_'+slug,flush=True)

if __name__=='__main__':
 if 'assemble' in sys.argv:assemble()
 elif 'lighting' in sys.argv:lighting()
 elif 'campus' in sys.argv:campus()
 elif 'connection' in sys.argv:connection()
 else:public()
