"""Build the source-grounded museum study. Run with Blender 5.2 in background.
All dimensions are metres. Architecture and new artifacts are explicitly approximate.
Original archive files are never opened for writing.
"""
import bpy, math, json, random, sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'models'
sys.path.insert(0,str(ROOT/'scripts'))
from material_export import bake_base_colors
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene['project'] = '湖北省博物馆数字版 / 资料依据下的近似重建'
scene['accuracy'] = '非测绘数字孪生；展览楼层依据馆方，房间边界和物件陈列位置近似'
scene['survey_dimensions_available'] = False
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1500
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('Daylight')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.72,.75,.80,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .6
scene.view_settings.view_transform = 'AgX'
random.seed(7)

def linear_hex(value):
    rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)

palette=[]
def material(name, color, metal=0, rough=.5, emission=0, glass=False):
    if isinstance(color,str):
        palette.append({'material':name,'reference_srgb':color,'role':'photo-guided approximate base colour'})
        color=linear_hex(color)
    m = bpy.data.materials.new(name); m.diffuse_color = (*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    if glass:
        p.inputs['Transmission Weight'].default_value=.92; p.inputs['IOR'].default_value=1.45
    return m

stone=material('南馆浅灰白石材','#e2e0dc',rough=.76)
floor=material('室外中性灰石材','#aca9a3',rough=.78)
interior_floor=material('中庭浅暖灰石材','#c3bfb5',rough=.26)
dark=material('深灰黑窗框与吊顶','#191a1a',rough=.65)
green=material('曾侯乙入口墨绿石材','#354840',rough=.36)
travertine=material('金声玉振米黄石墙','#c4b493',rough=.74)
gallery_floor=material('展厅灰褐色地坪','#92887a',rough=.48)
red=material('楚式朱红漆','#8b201c',rough=.38)
gold=material('标识古铜金','#a68b54',metal=.62,rough=.4)
bronze=material('尊盘暗褐色青铜','#61594c',metal=.45,rough=.72)
sword_metal=material('勾践剑灰金色剑身','#877c56',metal=.6,rough=.46)
sword_dark=material('剑身黑色菱形纹','#303329',metal=.22,rough=.57)
sword_handle=material('剑柄深黑褐色','#242621',metal=.45,rough=.5)
patina=material('局部暗色铜锈','#39453b',metal=.2,rough=.9)
white=material('中庭白色结构','#f0efeb',rough=.43)
steel=material('中庭不锈钢扶手','#a8abad',metal=.82,rough=.28)
glass=material('中性透明玻璃','#f1f4f5',rough=.055,glass=True)
roofmat=material('北馆冷灰色瓦顶','#656973',metal=.02,rough=.86)
grass=material('低饱和草地','#61704d',rough=.95)
foliage=material('园区深绿阔叶树冠','#364d36',rough=.95)
water=material('湖面灰绿色','#6d807c',metal=.18,rough=.26)
lightmat=material('暖白展厅灯带','#fff1d9',emission=2)
blue=material('青花钴蓝','#244967',rough=.3)
porcelain=material('梅瓶淡青白釉','#e0e2cf',rough=.27)
wood=material('竹简浅黄褐色','#b58e59',rough=.88)
lacquer=material('虎座鸟架鼓黑漆','#161b1e',rough=.31)
lacquer.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.35

# Subtle stone variation, baked for the same colour in Blender and the browser.
# These are material studies, not recovered surface scans.
stone_recipes=[(stone,'#d3d2ce','#ebe8e2',False),
               (interior_floor,'#a2a099','#cecbc1',False),
               (travertine,'#ad9c7f','#d6c6a6',True)]
for mat,low,high,bedded in stone_recipes:
    ns=mat.node_tree.nodes;ls=mat.node_tree.links
    coord=ns.new('ShaderNodeTexCoord');scale=ns.new('ShaderNodeVectorMath');scale.operation='MULTIPLY'
    scale.inputs[1].default_value=(1,12,1) if bedded else (1,1,1)
    ls.new(coord.outputs['Generated'],scale.inputs[0])
    noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=9;noise.inputs['Detail'].default_value=3
    ls.new(scale.outputs[0],noise.inputs['Vector'])
    ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*linear_hex(low),1);ramp.color_ramp.elements[1].color=(*linear_hex(high),1)
    ls.new(noise.outputs['Fac'],ramp.inputs[0]);ls.new(ramp.outputs[0],ns['Principled BSDF'].inputs['Base Color'])
bake_base_colors([r[0] for r in stone_recipes],512)
textured_stones={r[0] for r in stone_recipes}

def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
campus=collection('01_Campus_园区_近似')
shell=collection('02_South_南馆外立面_近似')
interior=collection('03_Atrium_中庭_近似')
galleries=collection('04_Galleries_展厅归属已核对_位置近似')
roofs=collection('05_Roofs_可隐藏屋顶')
artifacts=collection('06_Artifacts_补建形制示意')
lights=collection('07_Lights_Cameras')
current=campus

def assign(obj,name,mat):
    obj.name=name
    for c in list(obj.users_collection):c.objects.unlink(obj)
    current.objects.link(obj)
    if mat:obj.data.materials.append(mat)
    obj['accuracy']='approximate_reconstruction'
    obj['part']=current.name
    return obj

def box(name,loc,size,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=assign(bpy.context.object,name,mat);o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=2
    return o

def cyl(name,loc,r,depth,mat,vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    return assign(bpy.context.object,name,mat)

def ball(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    o=assign(bpy.context.object,name,mat);o.scale=scale
    for p in o.data.polygons:p.use_smooth=True
    return o

def mesh(name,verts,faces,mat):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(name,d);current.objects.link(o)
    if mat:d.materials.append(mat)
    o['accuracy']='approximate_reconstruction';o['part']=current.name
    return o

def tube(name,points,r,mat):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
    sp=d.splines.new('POLY');sp.points.add(len(points)-1)
    for v,p in zip(sp.points,points):v.co=(*p,1)
    o=bpy.data.objects.new(name,d);current.objects.link(o);d.materials.append(mat)
    o['accuracy']='approximate_reconstruction';o['part']=current.name
    return o

def ring(name,center,r,minor,mat,vertical=False):
    pts=[]
    for i in range(65):
        a=i*math.tau/64
        pts.append((center[0]+r*math.cos(a),center[1]+(0 if vertical else r*math.sin(a)),center[2]+(r*math.sin(a) if vertical else 0)))
    return tube(name,pts,minor,mat)

font=bpy.data.fonts.load(__import__('os').environ.get('MUSEUM_FONT', ''))
def textobj(body,loc,size,mat=gold):
    d=bpy.data.curves.new(body,'FONT');d.body=body;d.font=font;d.size=size;d.align_x='CENTER';d.extrude=.0005
    o=bpy.data.objects.new(body,d);current.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2,0,0);d.materials.append(mat)
    o['part']=current.name;o['accuracy']='interpretive_signage';return o

def lamp(name,loc,energy,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);lights.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def camera(name,loc,target,lens=40):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);lights.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1200;return o

# Campus axes: X east, Y north. Overall geography simplified from the site plan.
box('园区地面',(0,45,-8.3),(290,360,1),grass)
box('南广场',(0,-69,-7.65),(170,72,.3),floor)
mesh('东侧湖面近似',[(95,-135,-7.7),(146,-135,-7.7),(146,190,-7.7),(110,190,-7.7),(104,40,-7.7),(94,-15,-7.7)],[(0,1,2,3,4,5)],water)
for i in range(16): box('南侧台阶',(0,-43+i*.6,-7.45+i*.425),(66,.65,.45),stone)
for side in [-1,1]:
    for y in range(-98,174,16):
        x=side*(83+random.uniform(0,4))
        cyl('树干',(x,y,-4.2),.35,6,wood,12)
        for k in range(7):
            ball('园林阔叶树冠',(x+random.uniform(-2.1,2.1),y+random.uniform(-2.1,2.1),random.uniform(-.2,3.8)),(random.uniform(2,3.3),random.uniform(2,3.3),random.uniform(2,3.2)),foliage)
for x in range(-66,67,12):
    box('广场分缝',(x,-68,-7.475),(.035,63,.005),dark)

def old_building(name,cx,cy,w,d,height):
    global current
    current=campus
    box(name+'基座',(cx,cy,-.7),(w+3,d+3,1.4),stone)
    for xx in [-1,1]:box(name+'侧墙',(cx+xx*w/2,cy,height/2),(.4,d,height),stone)
    for yy in [-1,1]:box(name+'外墙',(cx,cy+yy*d/2,height/2),(w,.4,height),stone)
    for z in range(0,int(height),7):box(name+'楼板',(cx,cy,z-.2),(w,d,.4),floor)
    for z in [3.2,9.5,15.8]:
        if z<height:
            box(name+'窗带',(cx,cy-d/2-.225,z),(w-2,.08,2),dark)
            for x in range(int(-w/2)+2,int(w/2),4):box('立柱',(cx+x,cy-d/2-.27,z),(.3,.3,3),red)
    current=roofs
    verts=[(cx-w*.58,cy-d*.58,height),(cx+w*.58,cy-d*.58,height),(cx+w*.58,cy+d*.58,height),(cx-w*.58,cy+d*.58,height),
           (cx-w*.25,cy-d*.2,height+9),(cx+w*.25,cy-d*.2,height+9),(cx+w*.25,cy+d*.2,height+9),(cx-w*.25,cy+d*.2,height+9)]
    mesh(name+'歇山屋顶简化',verts,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],roofmat)
    for j in range(29):
        x=cx-w*.56+j*w*1.12/28
        tube('瓦垄示意',[(x,cy-d*.58,height+.05),(cx+(x-cx)*.45,cy-d*.2,height+9.06)],.06,roofmat)
old_building('北馆',0,112,72,57,24)
old_building('北馆东翼',49,87,31,43,12)
old_building('北馆西翼',-49,87,31,43,12)
old_building('西馆',-95,82,29,54,12)
current=campus
box('新旧馆联系走廊',(0,56,3),(25,48,6),stone)
textobj('湖北省博物馆',(0,-35,7.8),2.1)

# Southern building: white inverted trapezoid wings, dark window bands, glass atrium.
current=shell
for side in [-1,1]:
    cx=side*47.6
    for y in [-32,32]:
        # lower setbacks and large white upper fascia, never presented as surveyed coordinates
        verts=[(cx-19,y,8),(cx+19,y,8),(cx+23,y+(-3 if y<0 else 3),20.4),(cx-23,y+(-3 if y<0 else 3),20.4)]
        mesh('南馆倒梯形石材立面',verts,[(0,1,2,3)],stone)
    for dx in [-1,1]:
        mesh('南馆侧石材立面',[(cx+dx*19,-32,8),(cx+dx*19,32,8),(cx+dx*23,35,20.4),(cx+dx*23,-35,20.4)],[(0,1,2,3)],stone)
    box('底部窗带',(cx,-31,4),(37,.22,6.4),dark)
    box('立面阴缝',(cx,-33,9.3),(40,.24,.15),dark)
    for i in range(22):box('石材竖缝',(cx-20+i*1.9,-35.01,19.2),(.025,.01,2.3),floor)
    current=roofs;box('翼部屋顶',(cx,0,20.6),(46,70,.35),stone);current=shell
for x in range(-28,29,4):
    box('中央入口玻璃',(x,-29,4),(3.8,.15,7.8),glass)
    box('中央入口金属竖框',(x-2,-29,4),(.08,.3,8),dark)
for level in [-6.8,0,6.8,13.6]:
    current=interior
    # Two wings with walkable floor, central void at upper levels.
    for side in [-1,1]:box('侧翼楼板',(side*48,0,level-.18),(40,62,.36),floor)
    if level<=0:box('中庭地坪',(0,0,level-.18),(58.8,62,.36),interior_floor)
    else:
        for y in [-24,25]:
            box('中庭环廊',(0,y,level-.18),(58.8,11,.36),stone)
            box('环廊栏板',(0,y+(5.4 if y<0 else -5.4),level+.55),(58.8,.12,1.1),glass)
            tube('环廊扶手',[(-29.4,y+(5.4 if y<0 else -5.4),level+1.13),(29.4,y+(5.4 if y<0 else -5.4),level+1.13)],.045,steel)
for x in [-15,15]:
    tube('树形柱主干',[(x,8,0),(x,8,8),(x,8,10)],.65,white)
    for dx,dy in [(-12,-12),(12,-12),(-12,12),(12,12)]:
        tube('树形柱分枝',[(x,8,7),(x+dx*.4,8+dy*.4,15),(x+dx,8+dy,20.1)],.4,white)
current=roofs
box('中庭玻璃顶',(0,0,21),(59,61,.15),glass)
for x in range(-28,29,4):box('中庭屋顶格栅',(x,0,20.8),(.13,61,.23),white)
for y in range(-28,29,4):box('中庭屋顶格栅',(0,y,20.8),(59,.13,.23),white)
current=interior
for side in [-1,1]:
    box('中庭北侧浅色围护',(side*16.7,31,10),(25.4,.35,20),stone)
box('中庭北侧通道上方围护',(0,31,12.7),(8,.35,14.6),stone)
# Paired curved stair studies. Radius and treads are design approximations.
for side in [-1,1]:
    cx=side*20; cy=-9
    for k in range(46):
        a=k/45*math.pi*1.5
        o=box('弧形楼梯踏步',(cx+4*math.cos(a),cy+4*math.sin(a),k*6.8/46),(2.5,.6,.17),stone)
        o.rotation_euler.z=a
    for r in [2.8,5.2]:
        tube('弧梯扶手',[(cx+r*math.cos(k/92*math.pi*1.5),cy+r*math.sin(k/92*math.pi*1.5),k/92*6.8+1) for k in range(93)],.055,steel)
ring('入口圆形天顶白边',(0,-17,6.4),8,.18,white)
for i in range(28):
    a=i*math.tau/28
    ball('二十八宿构图点_非原屏幕',(7.6*math.cos(a),-17+7.6*math.sin(a),6.4),(.09,.09,.09),lightmat)

# Exhibitions: official floor allocation, approximate subdivisions. Empty evidence stays explicit.
gallery_data=[
 ('zeng','曾侯乙','南馆一、二层',(-48,0,0),'4676','3D 编钟、编磬、尊盘；具体陈列位置近似'),
 ('sword','越王勾践剑特展','南馆二层',(48,-13,6.8),'7387','剑形制示意；纹饰未扫描'),
 ('family','曾世家','南馆二层',(48,17,6.8),'7386','展览入口与归属，藏品模型待补'),
 ('chu','楚国八百年','南馆三层',(-48,0,13.6),'7385','虎座鸟架鼓、秦简形制示意；未沿用 2018 展厅'),
 ('liang','梁庄王珍藏','南馆三层',(48,0,13.6),'4698','展览入口与归属，藏品模型待补'),
 ('music','天籁','楼层待复核',(48,0,-6.8),'12832','数字导览临时定位；不宣称此处为现馆准确房间'),
 ('craft','巧夺天工','西馆二层',(-95,82,6.8),'10718','展览入口与归属，藏品模型待补'),
 ('ancient','极目楚天 · 古代文明','北馆二层',(0,98,6.8),'10715','展览入口与归属，藏品模型待补'),
 ('ceramics','荆楚陶雅 瓷韵江夏','北馆三层',(-17,112,13.6),'10716','四爱梅瓶形制示意；具体展位未核实'),
 ('modern','极目楚天 · 近代风云','北馆三层',(17,112,13.6),'10714','展览入口与归属，藏品模型待补'),
 ('people','极目楚天 · 现当代英杰','北馆四层',(0,112,20.4),'10713','展览入口与归属，藏品模型待补'),
]
current=galleries
for slug,title,level,(x,y,z),pid,note in gallery_data:
    w=36 if abs(x)<70 and y<40 else 25
    depth=26 if slug in ['sword','family'] else 42
    wallmat=travertine if slug in ['zeng','family','music'] else (stone if slug=='liang' else dark)
    box(title+'背墙',(x,y+depth/2,z+2.8),(w,.35,5.6),wallmat)
    for side in [-1,1]:
        box(title+'侧墙',(x+side*w/2,y,z+2.8),(.3,depth,5.6),wallmat)
        box(title+'入口侧墙',(x+side*(w/4+1.5),y-depth/2,z+2.8),(w/2-3,.3,5.6),wallmat)
    box(title+'深色展厅地坪',(x,y,z+.014),(w,depth,.028),gallery_floor)
    # The room ceiling is independently hideable for the browser cutaway.
    current=roofs;box(title+'展厅吊顶',(x,y,z+5.9),(w,depth,.18),dark);current=galleries
    textobj(title,(x,y+depth/2-.22,z+3.5),.9)
    textobj('资料依据下的近似展陈',(x,y+depth/2-.23,z+2.4),.29,white)
    for s in [-1,1]:box('灯带',(x+s*(w/2-.6),y,z+5.6),(.08,35,.035),lightmat)
    if slug not in ['zeng','chu','sword','ceramics']:
        textobj('展览入口 · 藏品三维资源待补',(x,y+depth/2-.23,z+1.55),.3,white)
    lamp(title+'照明',(x,y,z+5.3),2500 if slug=='zeng' else 1700,8,(x,y,z))
    if slug=='zeng':
        box('曾侯乙入口绿石屏风',(x,y-depth/2+.22,z+2.6),(8,.25,5.2),green)
        textobj('曾侯乙',(x,y-depth/2+.07,z+3.1),.85)
        for k in range(30):box('黑色吊顶格栅',(x-w/2+.6+k*w/30,y,z+5.65),(.06,depth,.23),dark)

def pedestal(label,loc,size=(1.1,1.1,.9)):
    x,y,z=loc
    current_saved=current
    box(label+'展台',(x,y,z+size[2]/2),size,dark,.025)
    box(label+'铜边',(x,y,z+size[2]-.03),(size[0]+.02,size[1]+.02,.025),gold)
    textobj(label,(x,y-size[1]/2-.008,z+size[2]*.53),.11,white)
    textobj('照片依据 · 非扫描',(x,y-size[1]/2-.009,z+size[2]*.3),.065,gold)
    return z+size[2]

from artifact_geometry import build as build_refined

new_defs=[('sword','越王勾践剑',(48,-13,6.8),'4694'),('zun','曾侯乙尊盘',(-39,4,0),'6911'),('drum','虎座鸟架鼓',(-48,0,13.6),'6913'),('vase','四爱梅瓶',(-17,109,13.6),'4696'),('bamboo','云梦睡虎地秦简',(-40,4,13.6),'6912')]
new_objects={}
for slug,title,pos,pid in new_defs:
    current=artifacts
    before=set(scene.objects);build_refined(slug,artifacts);objs=list(set(scene.objects)-before)
    for o in objs:o['artifact_id']=slug;o['source_url']='https://www.hbww.org.cn/zgzb/p/'+pid+'.html';o['accuracy']='照片依据补建，非扫描；深度、装饰拓扑与环向拼接仍有近似'
    # Export standalone at true size and origin before placing it in the gallery.
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'artifacts'/f'{slug}.glb'),use_selection=True,export_format='GLB',export_extras=True)
    z=pedestal(title,pos,(1.5,1.5,.9) if slug=='drum' else (1.1,1.1,.9))
    for o in objs:o.location+=Vector((pos[0],pos[1],z))
    new_objects[slug]=objs

# Append the corrected archival copies, preserving their full detail and materials.
archive_objects=[]
for slug,pos in [('bells',(-51,-5,0)),('chimes',(-41,-4,0))]:
    c=collection('Archive_'+slug+'_用户存档_非扫描')
    with bpy.data.libraries.load(str(OUT/'artifacts'/f'{slug}.blend'),link=False) as (src,dst):dst.objects=src.objects
    objs=[o for o in dst.objects if o and o.type=='MESH']
    for o in objs:
        c.objects.link(o);o.location+=Vector(pos);o['artifact_id']=slug;o['part']='archival_artifact'
    archive_objects+=objs
current=galleries
textobj('曾侯乙编钟',(-51,-8.1,.3),.25,white)
textobj('65 件 · 用户考据校正版存档',(-51,-8.12,.07),.13,gold)
for y in [-9,0]:lamp('编钟展陈灯',(-51,y,5.2),1200,4,(-51,-3,1))

# Southern entrance theatre location only, confirmed B1 west. Interior remains a study.
current=galleries
textobj('编钟演奏厅 · B1 西侧',(-48,-20,-3.8),.75)
box('演奏台近似',(-48,7,-6.3),(17,8,.8),dark)
for j in range(5):
    for i in range(13):box('观众席示意',(-59+i*1.8,-17+j*2,-6+j*.18),(.65,.65,.8),red,.07)

sun_data=bpy.data.lights.new('日光','SUN');sun_data.energy=2.5;sun_data.angle=.15
sun=bpy.data.objects.new('日光',sun_data);lights.objects.link(sun);sun.rotation_euler=(.45,-.4,-.6)
lamp('中庭补光',(0,-5,18),22000,28,(0,3,0))
lamp('入口自然补光',(0,-26,12),16000,25,(0,10,5))
cams={
 'campus':camera('01_园区鸟瞰',(180,-245,159),(0,38,5),43),
 'atrium':camera('02_中庭',(0,-27,3),(0,12,10),19),
 'bells':camera('03_曾侯乙编钟',(-42,-16,3.8),(-51,-3.5,1.2),40),
    'sword':camera('04_越王勾践剑',(48,-14.9,7.99),(48,-13,7.98),55),
    'vase':camera('05_四爱梅瓶',(-16.94,107.65,14.72),(-17,109,14.69),60),
    'chimes':camera('06_曾侯乙编磬',(-38.8,-7.8,1.6),(-41,-4,.7),48),
}
scene.camera=cams['campus']
(ROOT/'reports/colour-palette.json').write_text(json.dumps(palette,ensure_ascii=False,indent=2))
bpy.context.view_layer.update()
# Assign a metre-scaled projection to stone surfaces, including custom facade meshes.
for obj in scene.objects:
    if obj.type!='MESH' or not any(m in textured_stones for m in obj.data.materials):continue
    uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='StoneProjection')
    for face in obj.data.polygons:
        normal=(obj.matrix_world.to_3x3()@face.normal).normalized()
        axis=max(range(3),key=lambda i:abs(normal[i]))
        axes=(0,1) if axis==2 else ((0,2) if axis==1 else (1,2))
        for li in face.loop_indices:
            v=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv=(v[axes[0]]/2.4,v[axes[1]]/2.4)
font.pack()
scene['colour_revision']='2026-09-07 photo-guided sRGB palette, neutral lighting, source material baking'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hubei-museum.blend'),compress=True)

# Separate small architecture GLB; detailed archival instruments remain lazy-loaded assets.
bpy.ops.object.select_all(action='DESELECT')
for c in [campus,shell,interior,galleries,roofs,artifacts]:
    for o in c.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'museum-architecture.glb'),use_selection=True,export_format='GLB',export_extras=True,export_cameras=False,export_lights=False)

report={'generated_artifacts':[x[0] for x in new_defs],'archive_artifacts':['bells','chimes'],'gallery_count':len(gallery_data),'objects':len(scene.objects),'polygons':sum(len(o.data.polygons) for o in scene.objects if o.type=='MESH'),'floor_height_m_approx':6.8,'source_grounded_atrium_width_m':58.8,'missing_images':[im.name for im in bpy.data.images if im.source=='FILE' and not im.has_data and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()],'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'limitations':['建筑近似；无 CAD 与测绘','北馆、西馆室内未实测','五件补建文物为形制示意','部分展览仅入口与资料，未建藏品','天籁楼层在当前文本中未确认'],'cameras':list(cams)}
(ROOT/'reports'/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(ROOT/'research'/'galleries.json').write_text(json.dumps([{'id':s,'title':t,'floor':f,'position':p,'url':'https://www.hbww.org.cn/cszl/p/'+pid+'.html','coverage':n} for s,t,f,p,pid,n in gallery_data],ensure_ascii=False,indent=2))
for slug in ['campus','atrium','bells','sword','vase','chimes']:
    scene.camera=cams[slug];scene.render.filepath=str(ROOT/'renders'/f'{slug}.jpg');scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=92
    bpy.ops.render.render(write_still=True)
    print('RENDERED',slug,flush=True)
print('BUILD_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)
