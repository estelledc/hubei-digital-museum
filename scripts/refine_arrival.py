"""South foyer study from observed Bilibili frames and CITIC photographs.
Run in Blender: -- build | integrate. Dimensions/furniture are approximate.
"""
import sys, math, json, random
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from artifact_geometry import Builder,mat
from full_museum_spaces import text,area,spot,cylinder,luminous,beam,glass_material
from polish_museum_spaces import surface,project_uv
from build_full_museum import optimize_export,append_objects
OUT=ROOT/'renders/arrival-11';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'backups/before-arrival-11/models'
TAU=math.tau;CY=-2.;R=8.5
VIEWS={'arrival':((10,-24,1.7),(0,-1,2.3)), 'service':((19,-24,1.65),(12,-15,1.25)), 'lower':((8,-24,-5.12),(0,0,-3.4))}

def camera(s,name,loc,target,lens=24):
 d=bpy.data.cameras.new('11_'+name);o=bpy.data.objects.new('11_'+name,d);s.collection.objects.link(o);o.location=loc;d.lens=lens;d.clip_start=.01
 o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();s.camera=o;return o

def save(s,path):
 s['arrival_revision']='0.11';s['accuracy']='video/photo-guided foyer; dimensions, service counter geometry and equipment positions approximate'
 s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
 s.render.resolution_x=1440;s.render.resolution_y=960;s.render.resolution_percentage=100
 s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=94
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.15
 for screen in bpy.data.screens:
  for a in screen.areas:
   if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_perspective='CAMERA'
 bpy.ops.outliner.orphans_purge(do_recursive=True);bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)

def render(s,name):
 s.render.filepath=str(OUT/(name+'.jpg'));bpy.ops.render.render(write_still=True)

def arc(b,name,ri,ro,z,h,m,start=0,end=TAU,cx=0,cy=CY):
 n=max(16,round((end-start)/TAU*192));v=[];f=[]
 for zz in [z,z+h]:
  for r in [ri,ro]:
   v.extend([(cx+r*math.cos(start+(end-start)*i/n),cy+r*math.sin(start+(end-start)*i/n),zz) for i in range(n+1)])
 k=n+1
 for i in range(n):
  for a,c in [(0,1),(1,3),(3,2),(2,0)]:f.append((a*k+i,c*k+i,c*k+i+1,a*k+i+1))
 f.extend([(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)])
 return b.mesh(name,v,f,m,False)

def cut_circle(o):
 bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=R,depth=2,location=(0,CY,0));c=bpy.context.object
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Real circular floor opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=c
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
 o['arrival_opening_radius']=R;o['arrival_opening_center']=[0,CY,0]
 # The existing escalators connect the lower hall to this landing.
 for x in [-27,27]:
  bpy.ops.mesh.primitive_cube_add(size=1,location=(x,3,0));c=bpy.context.object;c.dimensions=(2.4,16,2)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.context.view_layer.objects.active=o
  mod=o.modifiers.new('Lower escalator opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=c
  bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)

def intervals_outside(lo,hi,holes):
 parts=[(lo,hi)]
 for a,z in holes:
  parts=[piece for l,r in parts for piece in [(l,min(r,a)),(max(l,z),r)] if piece[1]>piece[0]]
 return parts

def lighting(s,c):
 # Neutral-warm area lighting for Blender; the eight public lights also survive GLB export.
 for o in list(s.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 for level in [-6.8,0]:
  for x in [-16,16]:
   for y in [-18,15]:
    area(c,'11_门厅柔光',(x,y,level+5.9),(x,y,level),3000,8)
    if y==15:continue
    o=spot(c,'11_门厅照明',(x,y,level+5.9),(x,y,level),250,110);o.data.color=(1,.94,.85);o['web_intensity']=230.;o['web_shadow']=True;o['part']='03_Arrival11';o['arrival_revision']='0.11'
 area(c,'11_入口日光',(0,-30,2),(0,-7,1),1800,14)
 # Light the tree-column atrium independently above the entrance ceiling.
 for x in [-16,16]:
  for y in [-12,16]:
   area(c,'11_中庭天光',(x,y,19.8),(x,y,7),5500,14)
   o=spot(c,'11_中庭采光',(x,y,19.8),(x,y,7),500,115);o.data.color=(.94,.97,1);o['web_intensity']=450.;o['web_shadow']=True;o['part']='03_Arrival11';o['arrival_revision']='0.11'
 s.world.node_tree.nodes['Background'].inputs[1].default_value=.35

def build():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'public/atrium.blend'),load_ui=False);s=bpy.context.scene
 # Source scene has no opening and a thin floating ring; replace those exact studies.
 for o in list(s.objects):
  if o.name.startswith(('入口圆形天顶','二十八宿构图点','入口咨询台','咨询服务','入口休息长凳','长凳支座','10_中庭纵向石缝','10_中庭横向石缝')):bpy.data.objects.remove(o,do_unlink=True)
 for o in list(s.objects):
  if (o.name.startswith('栏板立柱') and o.location.z<1.2) or (o.name.startswith('环廊石材接缝') and o.location.z<.1):bpy.data.objects.remove(o,do_unlink=True)
 for o in s.objects:
  if o.name.startswith('中庭地坪') and abs(o.location.z+.18)<.1:cut_circle(o)
 c=bpy.data.collections.new('11_Arrival_南入口与服务区');s.collection.children.link(c);b=Builder(c)
 stone=surface('11入口灰色细纹石材','#b9b8b0','marble',.3)
 cream=surface('11入口米白石墙','#dedbd0','stone',.48)
 white=mat('11_白色天花','#e5e4df',0,.7);black=mat('11_深灰金属收口','#303536',.65,.3)
 steel=mat('11_拉丝不锈钢','#999e9b',.8,.31);red=surface('11楚红门框','#652a27','stone',.56)
 glass=glass_material();soft=luminous('11_暖白灯带','#fff2d9',2.2);blue=luminous('11_光纤冷白','#b7dbff',2.8)
 for o in s.objects:
  if o.name.startswith('中庭北侧') and o.type=='MESH':o.data.materials.clear();o.data.materials.append(cream);project_uv(o,4)
  if o.name.startswith('中庭地坪') and o.type=='MESH':o.data.materials.clear();o.data.materials.append(stone);project_uv(o,5)
 # Floor joints stop at the actual opening; no floating lines span it.
 for x in range(-28,29,2):
  h=math.sqrt(max(0,R*R-x*x)) if abs(x)<R else 0
  holes=([(CY-h,CY+h)] if h else [])+([(-5,11)] if abs(abs(x)-27)<1.2 else [])
  for a,z in intervals_outside(-31,31,holes):b.box('11_地坪纵缝',(x,(a+z)/2,.004),(.005,z-a,.002),black,0)
 for y in range(-30,32,2):
  h=math.sqrt(max(0,R*R-(y-CY)**2)) if abs(y-CY)<R else 0
  holes=([(-h,h)] if h else [])+([(-28.2,-25.8),(25.8,28.2)] if -5<y<11 else [])
  for a,z in intervals_outside(-29.4,29.4,holes):b.box('11_地坪横缝',((a+z)/2,y,.005),(z-a,.005,.002),black,0)
 # Deep fascia, curved glass panels, metal shoes and continuous rail.
 arc(b,'11_挑空石材板边',R,R+.24,-.46,.46,cream)
 arc(b,'11_挑空黑色基槽',R+.035,R+.12,.01,.095,black)
 for i in range(48):
  a=i*TAU/48+.003;z=(i+1)*TAU/48-.003
  arc(b,'11_弧形夹胶玻璃',R+.045,R+.060,.105,1.02,glass,a,z)
  x=(R+.055)*math.cos(a);y=CY+(R+.055)*math.sin(a)
  cylinder(b,'11_栏杆金属立柱',(x,y,.59),.024,1.08,steel,16)
  for h in [.26,.88]:b.ellipsoid('11_玻璃固定夹',(x,y,h),(.038,.038,.03),steel,12,6)
 b.tube('11_连续深色扶手',[( (R+.055)*math.cos(i*TAU/256),CY+(R+.055)*math.sin(i*TAU/256),1.16) for i in range(257)],.045,black,12)
 # Solid ceiling with a recessed circular optical-fibre feature, not a floating torus.
 ceiling=b.box('11_门厅顶板',(0,0,6.5),(58.8,62,.5),white,.025);ceiling['roof']=True
 # Open the ceiling around the existing spirals and escalators, preserving circulation.
 for x in [-20,20]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=5.65,depth=2,location=(x,-9,6.5));cut=bpy.context.object
  bpy.context.view_layer.objects.active=ceiling;mod=ceiling.modifiers.new('Stair opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
  bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 for x in [-27,27]:
  bpy.ops.mesh.primitive_cube_add(size=1,location=(x,3,6.5));cut=bpy.context.object;cut.dimensions=(2.4,16,2)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.context.view_layer.objects.active=ceiling
  mod=ceiling.modifiers.new('Escalator opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
  bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 # Place the star disc below the ceiling; sparse stars are an optical study, not an invented star chart.
 arc(b,'11_灯幕外围暗槽',9.10,9.24,6.08,.10,black)
 arc(b,'11_灯幕石膏跌级',8.92,9.12,6.04,.22,white)
 arc(b,'11_环形柔光槽',8.86,8.93,6.07,.04,soft)
 disc=cylinder(b,'11_灯幕暗蓝底盘',(0,CY,6.20),8.86,.07,mat('11_星空底色','#162c43',0,.7),192)
 disc['accuracy']='Optical-fibre appearance study; original phoenix and 28 mansion programme not reconstructed'
 rng=random.Random(711);vs=[];fs=[]
 for i in range(3600):
  a=rng.random()*TAU;r=math.sqrt(rng.random())*8.8;x=r*math.cos(a);y=CY+r*math.sin(a);z=6.12-rng.uniform(0,.16);q=rng.uniform(.008,.021);k=len(vs)
  vs.extend([(x-q,y,z),(x,y-q,z-.009),(x+q,y,z),(x,y+q,z+.009)]);fs.append((k,k+1,k+2,k+3))
 dots=b.mesh('11_光纤端点_分布近似',vs,fs,blue,False)
 for i in range(72):
  a=i*TAU/72
  b.tube('11_光纤垂线',[(8.7*math.cos(a),CY+8.7*math.sin(a),6.1),(8.7*math.cos(a),CY+8.7*math.sin(a),5.76)],.006,blue,6)
 # Downlights, narrow ventilation slots, stone-clad piers.
 for level in [-6.8,0]:
  for x in [-23,-13,13,23]:
   for y in [-22,-10,10,24]:
    if level==0 and x in [-13,13] and y==-10:continue
    b.box('11_顶棚风口',(x,y,level+6.2),(1.1,.08,.025),black,0)
    cylinder(b,'11_筒灯深色灯杯',(x+.85,y,level+6.19),.085,.04,black,24)
    cylinder(b,'11_筒灯发光面',(x+.85,y,level+6.16),.058,.015,soft,24)
  for x in [-19,19]:
   for y in [-25,16]:
    b.box('11_入口石材方柱',(x,y,level+3.15),(.82,.82,6.3),cream,.015)
    for z in [1.2,2.4,3.6,4.8]:b.box('11_石柱横缝',(x,y-.416,level+z),(.8,.003,.007),black,0)
 # Side return walls and red-black gallery portals identify an occupied museum foyer.
 for level in [-6.8,0]:
  for side in [-1,1]:
   x=side*29.2
   b.box('11_门厅侧墙',(x,0,level+3.15),(.2,62,6.3),cream,.02)
   # Return-facing public doors. Position and unobserved equipment remain approximate.
   for xx in [side*22]:
    b.box('11_通道深色门洞',(xx,28.8,level+1.55),(3.8,.12,3.1),black,.01)
    for dx in [-2.0,2.0]:b.box('11_楚红门套',(xx+dx,28.65,level+1.7),(.22,.2,3.4),red,.01)
    b.box('11_楚红门楣',(xx,28.65,level+3.4),(4.22,.2,.24),red,.01)
  # Two source-guided service desks at the front sides; coordinates are digital approximations.
  if level==0:
   for side in [-1,1]:
    x=side*14;y=-18
    b.box('11_咨询台石材柜身',(x,y,.53),(6.2,1.22,1.06),cream,.16)
    b.box('11_服务台深色台面',(x,y-.035,1.095),(6.35,1.35,.095),black,.11)
    b.box('11_服务台内凹踢脚',(x,y,.09),(5.9,1.04,.16),black,.05)
    for dx in [-2,0,2]:b.box('11_台身细竖缝',(x+dx,y-.613,.53),(.007,.004,.8),black,0)
    text(b,'咨询服务' if side>0 else '导览服务',(x,y-.628,.69),.30,black)
    text(b,'INFORMATION' if side>0 else 'AUDIO GUIDE',(x,y-.629,.34),.13,black)
    for dx in [-1.5,1.5]:
     b.box('11_柜台显示器',(x+dx,y+.05,1.45),(.5,.055,.34),black,.022)
     b.box('11_显示器支架',(x+dx,y+.09,1.25),(.04,.05,.3),steel,.01)
     b.box('11_显示器底座',(x+dx,y,1.145),(.26,.2,.025),black,.015)
    b.box('11_导览折页托盘',(x,y-.25,1.17),(.42,.25,.06),steel,.012)
    for dx in [-.10,0,.10]:b.box('11_导览折页',(x+dx,y-.25,1.207),(.09,.20,.012),white,.003)
   for x in [-24,24]:
    b.box('11_自助导览终端',(x,-20,.81),(.65,.43,1.62),black,.05)
    b.box('11_终端屏幕',(x,-20.23,1.18),(.52,.012,.67),mat('11_终端蓝灰屏','#38535e',0,.5),.012)
    text(b,'馆内导览',(x,-20.245,1.3),.12,white)
    text(b,'服务位置示意',(x,-20.246,1.04),.075,white)
    b.box('11_休息凳台面',(x,-12,.45),(.8,3.0,.13),cream,.07)
    for dy in [-1,1]:b.box('11_休息凳支脚',(x,-12+dy,.21),(.55,.09,.42),black,.01)
 # Glazed entrance pairs and pull handles at the south line, with a broad clear central route.
 for level in [-6.8,0]:
  for x in [-9,-6,-3,0,3,6,9]:
   for dx in [-1.46,1.46]:b.box('11_玻璃门竖框',(x+dx,-29.15,level+1.65),(.055,.12,3.3),black,.007)
   b.box('11_玻璃门楣',(x,-29.15,level+3.3),(2.96,.12,.075),black,.006)
   for dx in [-.74,.74]:
    b.box('11_门扇玻璃',(x+dx,-29.15,level+1.62),(1.40,.015,3.17),glass,0)
    b.tube('11_不锈钢门拉手',[(x+dx*.16,-28.99,level+.95),(x+dx*.16,-28.99,level+1.58)],.021,steel,12)
   b.box('11_门槛',(x,-29.15,level+.015),(3,.3,.03),steel,.005)
  b.box('11_入口除尘地垫',(0,-27.8,level+.009),(21,2,.018),surface('11除尘地垫'+str(level),'#3b3d3a','fabric',.96),.006)
 # Lower level soffit is painted, rather than a duplicate marble floor texture.
 for o in s.objects:
  if o.name.startswith('中庭地坪') and o.type=='MESH' and abs(o.location.z+.18)<.1:
   o.data.materials.append(white)
   for poly in o.data.polygons:
    if poly.normal.z<-.5:poly.material_index=len(o.data.materials)-1
 b.box('11_下层大厅后墙',(0,30,-3.5),(58.8,.3,6.6),cream,.015)
 # Lower level remains a public hall; no fabricated reproduction of the large wall artwork.
 for x in [-12,12]:
  t=text(b,'公共服务' if x>0 else '编钟演奏厅',(x,27.5,-3.7),.4,black)
  t['accuracy']='Digital wayfinding; not a facsimile of on-site signage'
 # Remove ground-floor visual lines inside the new void and close ceiling texture correctly.
 for o in b.objects:
  o['part']='03_Arrival11';o['arrival_revision']='0.11'
  if 'accuracy' not in o:o['accuracy']='Observed architectural vocabulary; dimensions, fixtures and coordinates approximate'
  if o.type=='MESH' and not o.name.startswith('11_光纤'):project_uv(o,4)
 lighting(s,c)
 s['arrival_views']=json.dumps(VIEWS)
 for name,(loc,target) in VIEWS.items():camera(s,name,loc,target)
 s.camera=bpy.data.objects['11_arrival'];save(s,ROOT/'models/public/arrival.blend');render(s,'arrival')
 for name in ['service','lower']:s.camera=bpy.data.objects['11_'+name];render(s,name)
 # Atrium uses the upper level, above the foyer ceiling, retaining the tree-column architecture.
 camera(s,'atrium',(11,-18,8.5),(-5,7,13.5));save(s,ROOT/'models/public/atrium.blend');render(s,'atrium')
 optimize_export(list(s.objects),ROOT/'models/public/atrium.glb')
 import shutil
 shutil.copy2(ROOT/'models/public/atrium.glb',ROOT/'models/public/arrival.glb')
 print('ARRIVAL11_BUILT',flush=True)

def relight():
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/public/arrival.blend'),load_ui=False);s=bpy.context.scene
 lighting(s,bpy.data.collections['11_Arrival_南入口与服务区'])
 s.camera=bpy.data.objects['11_arrival'];save(s,ROOT/'models/public/arrival.blend');render(s,'arrival')
 for name in ['service','lower']:s.camera=bpy.data.objects['11_'+name];render(s,name)
 camera(s,'atrium',(11,-18,8.5),(-5,7,13.5));save(s,ROOT/'models/public/atrium.blend');render(s,'atrium')
 optimize_export(list(s.objects),ROOT/'models/public/atrium.glb')
 import shutil
 shutil.copy2(ROOT/'models/public/atrium.glb',ROOT/'models/public/arrival.glb')
 print('ARRIVAL11_RELIT',flush=True)

def integrate():
 # The public model is one coherent volume. Remove the old public interior before appending it.
 for filename in ['campus-polished.blend','hubei-museum.blend']:
  bpy.ops.wm.open_mainfile(filepath=str(SOURCE/filename),load_ui=False);s=bpy.context.scene
  for o in list(s.objects):
   if str(o.get('part','')).startswith('03_') or o.name.startswith('中庭玻璃顶'):bpy.data.objects.remove(o,do_unlink=True)
  c=bpy.data.collections.new('11_Public_入口及中庭');s.collection.children.link(c);append_objects(ROOT/'models/public/atrium.blend',c)
  s['version']='0.11';save(s,ROOT/'models'/filename)
  if filename=='campus-polished.blend':optimize_export(list(s.objects),ROOT/'models/museum-architecture.glb')
 print('ARRIVAL11_INTEGRATED',flush=True)

if __name__=='__main__':
 if 'integrate' in sys.argv:integrate()
 elif 'relight' in sys.argv:relight()
 else:build()
