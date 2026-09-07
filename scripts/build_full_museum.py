"""Build eleven independently editable, source-guided galleries and public spaces.
Run with Blender; -- gallery-id builds one gallery, -- integrate assembles the main file.
All room dimensions and display coordinates are approximate; no survey is claimed.
"""
import bpy,sys,json,math,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from full_museum_spaces import *
GALLERIES=json.loads((ROOT/'research/full04/galleries.json').read_text())
OUT=ROOT/'models/galleries';OUT.mkdir(exist_ok=True)
RENDERS=ROOT/'renders/galleries';RENDERS.mkdir(exist_ok=True)
NAMES={'bells':'曾侯乙编钟','chimes':'曾侯乙编磬','zun':'曾侯乙尊盘','sword':'越王勾践剑','drum':'虎座鸟架鼓','bamboo':'睡虎地秦简','vase':'四爱图梅瓶','ding-jian':'曾侯谏铜方鼎','gold-liang':'梁庄王金锭','pottery-bell':'石家河陶铃','drum-chongyang':'崇阳铜鼓','jade-shijiahe':'石家河玉人','carving-wudang':'武当朝圣图','medal-lizuodong':'李作栋勋四位章','manuscript-xiong':'熊秉坤稿本','office-dong':'董必武办公室展陈（近似）'}

def append_objects(path,c,offset=(0,0,0),artifact=None):
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=src.objects
    result=[]
    for o in dst.objects:
        if not o:continue
        if o.type not in ['MESH','FONT','CURVE','LIGHT']:bpy.data.objects.remove(o,do_unlink=True);continue
        c.objects.link(o)
        if not o.parent:o.location+=Vector(offset)
        if artifact:o['artifact_id']=artifact
        result.append(o)
    return result

def setup_render(s,loc,target,name):
    s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
    s.render.resolution_x=1440;s.render.resolution_y=960;s.render.resolution_percentage=100
    s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=92
    s.world=bpy.data.worlds.new('柔和中性环境');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.20,.22,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.20
    s.view_settings.view_transform='AgX'
    d=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,d);s.collection.objects.link(cam);cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=27;d.clip_start=.005;s.camera=cam
    s['camera_blender']=list(loc);s['target_blender']=list(target);s.unit_settings.system='METRIC'
    return cam

def optimize_export(objects,path):
    # Main editable .blend is saved before this destructive, browser-only preparation.
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        if o.type in ['MESH','CURVE','FONT']:o.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in objects if o.select_get())
    bpy.ops.object.convert(target='MESH')
    for o in bpy.context.selected_objects:
        if o.type=='MESH' and o.data.uv_layers.active:o.data.uv_layers.active.name='UVMap'
    groups={}
    for o in list(bpy.context.selected_objects):
        if o.type=='MESH':groups.setdefault((o.get('artifact_id',''),bool(o.get('roof')),any(m and m.use_nodes and m.node_tree.nodes.get('Principled BSDF') and m.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value>.5 for m in o.data.materials)),[]).append(o)
    for (artifact,roof,glass),group in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in group:o.select_set(True)
        bpy.context.view_layer.objects.active=group[0]
        if len(group)>1:bpy.ops.object.join()
        joined=bpy.context.object
        if artifact:joined['artifact_id']=artifact
        if roof:joined['roof']=True
    bpy.ops.object.select_all(action='DESELECT')
    n=0
    for o in sorted(bpy.context.scene.objects,key=lambda o:0 if o.name.startswith('10_') and 'web_intensity' in o else 1 if '展品照明' in o.name else 2 if 'web_intensity' in o else 3):
        if o.type=='MESH':o.select_set(True)
        elif o.type=='LIGHT' and o.data.type in ['SPOT','POINT'] and n<8:o.select_set(True);n+=1
    bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_extras=True,export_lights=True,export_cameras=False,export_apply=True,export_image_format='JPEG',export_jpeg_quality=90)

def install_character(b,g,ink):
    """Different installations follow visible hall materials and motifs, not invented artifacts."""
    id=g['id'];w,d=g['size'];white=mat('展墙浅暖灰','#d2cfc5',0,.85);dark=mat('窄框黑','#222625',.35,.42)
    if id=='liang':
        wood=aged('梁庄王圆门深木色','#422b20',0,.65)
        # Ring extruded in depth; the opening is real geometry.
        vs=[];fs=[];n=144
        for y in [4.8,5.15]:
            for r in [2.55,2.85]:
                for i in range(n):a=i*math.tau/n;vs.append((math.cos(a)*r,y,2.85+math.sin(a)*r))
        for j in range(4):
            nxt={0:1,1:3,3:2,2:0}[j]
            for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,nxt*n+(i+1)%n,nxt*n+i))
        b.mesh('梁庄王月洞门_真实圆孔',vs,fs,wood)
        for x in [-6,6]:b.box('圆门两侧浅色展墙',(x,5,2.6),(6,.2,5.2),white,.02)
    elif id=='craft':
        teal=luminous('青绿灯箱','#3bb2b0',1.5)
        for x in [-3.7,3.7]:
            b.box('工艺厅灰色方柱',(x,3,2.6),(.85,.85,5.2),white,.02)
            b.box('青绿竖向灯箱',(x,2.55,2.2),(.57,.04,3.8),teal,.01)
            area(b.c,'灯箱柔光',(x,2.4,2.5),(0,0,1),100,2)
    elif id=='ancient':
        green=mat('弧形深绿展墙','#283e33',0,.84)
        for x in [-4.8,4.8]:
            cylinder(b,'古代厅弧形柱墙',(x,3,2.6),.78,5.2,green,96)
            b.box('弧墙浅色腰带',(x,2.22,1.4),(1.1,.06,.65),white,.005)
    elif id=='modern':
        blue=mat('近代蓝色分段展板','#204969',0,.8)
        for x in [-4.5,0,4.5]:
            b.box('蓝白图文展墙',(x,4,2.2),(4,.20,4.4),white,.008)
            b.box('蓝色竖向叙事板',(x,3.86,2.25),(1.25,.04,3.85),blue,.003)
    elif id=='people':
        for x in [-4.7,4.7]:b.box('历史展陈外围木饰墙',(x,3,2.2),(2,.22,4.4),white,.01)
        # Glass boundary around reconstructed office, not a claim of original furniture.
        for x in [-2.5,2.5]:b.box('办公室展陈侧护栏',(x,.8,.5),(.018,4,1),glass_material(),0)
        b.box('办公室展陈前护栏',(0,-1.25,.5),(5,.018,1),glass_material(),0)
    elif id=='music':
        brass=mat('天籁入口金色竖饰','#a88b49',.6,.5)
        for i in range(42):
            x=-5.5+i*.26;h=2.5+.4*math.sin(x*1.1)
            b.box('天籁波浪下缘隔片',(x,5,1+h/2),(.035,.25,h),brass,.005)
        text(b,'天 籁',(0,4.75,4.15),.64,ink)
    elif id in ['family','sword-hall','chu']:
        brown=aged('青铜褐色叙事屏风','#3c3229',0,.84)
        b.box('入口折角展墙',(-4.5,3,2.3),(2.8,.2,4.6),brown,.02).rotation_euler.z=-.28
        if id=='sword-hall':
            b.box('剑厅独立背景',(0,1.55,2.2),(4.8,.20,4.4),brown,.015)
            text(b,'越王勾践剑',(0,1.43,3.3),.40,ink)
    # Source photographs are placed as clearly titled comparison boards, not extra 3D exhibits.
    if g['photo']:
        file=ROOT/'research/full04'/g['photo'];im=bpy.data.images.load(str(file),check_existing=True)
        width=3.6;height=width*im.size[1]/im.size[0];y=d/2-.3
        b.box('实景对照照片背板',(-w*.24,y+.035,2.3),(width+.12,.08,height+.12),dark,.01)
        picture(b,'馆方实景参考照片',file,(-w*.24,y-.015,2.3),width,height)
        text(b,'现馆实景照片 · 用于对照',(-w*.24,y-.025,2.4-height/2-.25),.17,ink)
    # Narrow information ledges provide furniture scale without empty cases or fake vessels.
    for x in [-w*.34,w*.34]:
        b.box('解说阅读台',(x,-2,.95),(1.8,.7,.08),white,.014)
        b.box('阅读台支柱',(x,-2,.47),(.12,.50,.90),dark,.02)
        text(b,'代表展品 · 资料依据重建',(x,-2.36,.85),.105,ink)

def build_gallery(g):
    print('BUILD_GALLERY',g['id'],flush=True)
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
    c=bpy.data.collections.new('Gallery_'+g['id']);s.collection.children.link(c);b=Builder(c)
    ink=gallery_shell(b,g);install_character(b,g,ink)
    for item in g['artifacts']:
        id=item['id'];x=item['x'];y=item['y'];base=item['base']
        if item['case']:
            case(b,NAMES[id],x,y,*item['case'],base=base)
            if id not in ['bells','chimes']:base+=.045
            if id not in ['bells','chimes']:text(b,NAMES[id],(x,y-item['case'][1]/2-.035,base-.22),.095,ink)
        path=ROOT/'models/refined-04'/(id+'.blend')
        if not path.exists():path=ROOT/'models/artifacts'/(id+'.blend')
        append_objects(path,c,(x,y,base),id)
    for o in c.objects:
        o['gallery_id']=g['id'];o['part']='Gallery_'+g['id'];o['gallery_source']=g['url']
        if not o.get('accuracy'):o['accuracy']=g['accuracy']
    loc=g['camera'];target=g['target']
    setup_render(s,loc,target,'GalleryCamera_'+g['id'])
    s['gallery_id']=g['id'];s['representative_artifacts']=','.join(a['id'] for a in g['artifacts']);s['accuracy']=g['accuracy']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(g['id']+'.blend')),compress=True)
    s.render.filepath=str(RENDERS/(g['id']+'.jpg'));bpy.ops.render.render(write_still=True)
    export_gallery(g)

def export_gallery(g):
    s=bpy.context.scene
    # Archive full meshes remain in .blend; use established browser LOD for these two groups.
    for item in g['artifacts']:
        if item['id'] in ['bells','chimes']:
            id=item['id']
            for o in list(s.objects):
                if o.get('artifact_id')==id:bpy.data.objects.remove(o,do_unlink=True)
            before=set(s.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'models/artifacts'/(id+'.glb')))
            for o in set(s.objects)-before:
                if not o.parent:o.location+=Vector((item['x'],item['y'],item['base']))
                o['artifact_id']=id;o['gallery_id']=g['id']
    optimize_export(list(s.objects),OUT/(g['id']+'.glb'))
    print('GALLERY_DONE',g['id'],flush=True)

def build_connection():
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;c=bpy.data.collections.new('Public_connection');s.collection.children.link(c);b=Builder(c)
    stone=aged('联系空间浅灰石','#c8c5ba',0,.42);metal=mat('联系廊铝框','#7a8385',.65,.35);white=mat('联系廊暖白','#dfded8',0,.6)
    b.box('连接廊地面',(0,0,-.15),(12,38,.3),stone,.02)
    for side in [-1,1]:
        for y in range(-18,19,3):
            b.box('连接廊玻璃',(side*6,y,2.65),(.012,2.96,5.3),glass_material(),0)
            b.box('玻璃金属分格',(side*6,y-1.5,2.65),(.08,.08,5.3),metal,0)
        for y in [-12,0,12]:b.box('走廊休息座椅',(side*4.5,y,.42),(.65,2.4,.15),white,.04)
    b.box('联系廊顶棚',(0,0,5.35),(12,38,.15),white,.01)['roof']=True
    for y in range(-18,19,3):
        b.box('联系廊线灯',(0,y,5.22),(9,.035,.018),luminous('廊道光带'),0)
        area(c,'廊道采光',(0,y,5),(0,y,0),400,5)
    text(b,'北馆  /  南馆',(0,16,3.5),.6,metal)
    for o in b.objects:o['part']='Public_connection';o['accuracy']='approximate visitor connection; architectural circulation, not measured corridor'
    setup_render(s,(2,-14,1.65),(0,10,2),'ConnectionCamera')
    return s,c

def build_theatre():
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;c=bpy.data.collections.new('Public_theatre');s.collection.children.link(c);b=Builder(c)
    red=aged('演奏厅深红木饰','#682c25',0,.72);black=mat('剧场炭灰','#181919',0,.75);fabric=aged('座椅暗红织物','#5e2423',0,.97);metal=mat('椅架黑金属','#272a2a',.5,.5)
    b.box('演奏厅地坪',(0,0,-.2),(23,27,.4),black,.01)
    for x in [-11.5,11.5]:
        b.box('演奏厅红色侧墙',(x,0,4),(.3,27,8),red,.01)
        for y in range(-12,13):b.box('声学竖向木饰缝',(x*.988,y,4),(.025,.04,8),black,0)
    b.box('舞台',(0,9,.45),(20,7,.9),red,.035)
    b.box('舞台黑色背景',(0,12.3,4),(23,.2,8),black,.01)
    b.box('演奏厅顶棚',(0,0,8.1),(23,27,.2),black,.01)['roof']=True
    for row in range(9):
        y=4-row*1.38;z=row*.16
        b.box('观众席阶梯',(0,y-.18,z/2),(22,1.4,z+.10),black,.02)
        for col in range(16):
            x=(col-7.5)*.64+(-.65 if col<8 else .65)
            b.box('软包座面',(x,y,z+.49),(.49,.47,.13),fabric,.06)
            o=b.box('软包椅背',(x,y-.28,z+.85),(.51,.12,.67),fabric,.065);o.rotation_euler.x=-.12
            for side in [-1,1]:
                b.box('座椅扶手',(x+side*.27,y,z+.69),(.055,.53,.045),metal,.015)
                b.box('椅腿',(x+side*.2,y,z+.25),(.035,.3,.45),metal,.015)
    # Performance copy is explicitly separate from the original Zeng display.
    append_objects(ROOT/'models/artifacts/bells.blend',c,(0,8,.9),'bells-performance-copy')
    text(b,'编钟乐舞 · 数字演奏场景',(0,12.1,5.8),.52,mat('舞台标题','#d4b493',0,.8))
    for x in [-7,0,7]:area(c,'舞台柔光',(x,5,7),(x,8,1.8),900,4)
    for y in [-9,-3,3]:area(c,'观众区柔光',(0,y,6),(0,y,0),220,5)
    for o in c.objects:o['part']='Public_theatre';o['accuracy']='red-black architectural palette; stage, seats and copy instrument placement approximate; not current performance setup'
    setup_render(s,(2,-9,2.65),(0,8,2.8),'TheatreCamera');return s,c

def public_file(id,factory,offset):
    s,c=factory();pub=ROOT/'models/public';pub.mkdir(exist_ok=True)
    s['public_id']=id;s['assembly_offset']=list(offset)
    bpy.ops.wm.save_as_mainfile(filepath=str(pub/(id+'.blend')),compress=True)
    s.render.filepath=str(RENDERS/(id+'.jpg'));bpy.ops.render.render(write_still=True)
    if id=='theatre':
        for o in list(s.objects):
            if o.get('artifact_id')=='bells-performance-copy':bpy.data.objects.remove(o,do_unlink=True)
        before=set(s.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'models/artifacts/bells.glb'))
        for o in set(s.objects)-before:
            if not o.parent:o.location+=Vector((0,8,.9))
            o['artifact_id']='bells-performance-copy'
    optimize_export(list(s.objects),pub/(id+'.glb'))

def integrate():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'backups/before-full-museum-04/models/hubei-museum.blend'))
    s=bpy.context.scene
    for o in list(s.objects):
        part=str(o.get('part',''))
        if o.get('artifact_id') or part.startswith(('04_','06_')) or o.name.endswith('展厅吊顶') or any(o.name==g['title']+'照明' for g in GALLERIES):bpy.data.objects.remove(o,do_unlink=True)
    enrich_public(s);enrich_campus(s)
    # The old connection was a solid mass; replace with an accessible glazed corridor.
    for o in list(s.objects):
        if o.name.startswith('新旧馆联系走廊'):bpy.data.objects.remove(o,do_unlink=True)
    for id,offset in [('connection',(0,56,0)),('theatre',(-48,0,-6.8))]:
        c=bpy.data.collections.new('FullPublic_'+id);s.collection.children.link(c);append_objects(ROOT/'models/public'/(id+'.blend'),c,offset)
    for g in GALLERIES:
        c=bpy.data.collections.new('FullGallery_'+g['id']);s.collection.children.link(c)
        append_objects(OUT/(g['id']+'.blend'),c,g['position'])
    s['version']='0.4';s['scope']='11 permanent exhibition themes plus representative exhibits and public visitor spaces; approximate geometry, not survey'
    s['gallery_count']=len(GALLERIES);s['artifact_count']=len(NAMES)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/hubei-museum.blend'),compress=True)
    # Public atrium separate file, preserving full editable source.
    for o in list(s.objects):
        if o.get('gallery_id') or o.get('artifact_id') or str(o.get('part','')).startswith('Public_'):bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in s.objects:
        if o.type in ['MESH','FONT','CURVE']:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'models/museum-architecture.glb'),use_selection=True,export_extras=True,export_apply=True,export_image_format='JPEG',export_jpeg_quality=90)
    for o in list(s.objects):
        part=str(o.get('part',''))
        if o.type in ['MESH','FONT','CURVE'] and not (part.startswith('03_') or o.name.startswith('中庭玻璃顶')):bpy.data.objects.remove(o,do_unlink=True)
    setup_render(s,(0,-26,2.1),(0,9,12),'AtriumCamera04')
    area(s.collection,'中庭天光',(0,0,24),(0,0,0),6500,24)
    area(s.collection,'入口日光',(0,-30,12),(0,15,8),3800,15)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/public/atrium.blend'),compress=True)
    s.render.filepath=str(RENDERS/'atrium.jpg');bpy.ops.render.render(write_still=True)
    optimize_export(list(s.objects),ROOT/'models/public/atrium.glb')
    print('FULL_MUSEUM_INTEGRATED',flush=True)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if 'export-only' in args:
        for g in GALLERIES:
            bpy.ops.wm.open_mainfile(filepath=str(OUT/(g['id']+'.blend')),load_ui=False);export_gallery(g)
        for id in ['connection','theatre']:
            bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/public'/(id+'.blend')),load_ui=False)
            if id=='theatre':
                for o in list(bpy.context.scene.objects):
                    if o.get('artifact_id')=='bells-performance-copy':bpy.data.objects.remove(o,do_unlink=True)
                before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'models/artifacts/bells.glb'))
                for o in set(bpy.context.scene.objects)-before:
                    if not o.parent:o.location+=Vector((0,8,.9))
                    o['artifact_id']='bells-performance-copy'
            optimize_export(list(bpy.context.scene.objects),ROOT/'models/public'/(id+'.glb'))
    elif 'integrate' in args:integrate()
    elif 'public' in args:
        public_file('connection',build_connection,(0,56,0));public_file('theatre',build_theatre,(-48,0,-6.8))
    else:
        for g in GALLERIES:
            if not args or g['id'] in args:build_gallery(g)
