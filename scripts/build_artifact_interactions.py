"""Derive presentation rigs from existing artifacts; never edit the static sources.
Offsets and inspection views are shared with the web viewer in glTF Y-up coordinates.
"""
import bpy, json, math, sys, shutil, struct
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from artifact_detail_geometry import refine, detail_anchors
OUT = ROOT / 'models/interactive'
WEB = ROOT / 'web/public/models/interactive'
CONFIG = json.loads((ROOT / 'web/lib/artifact-experiences.json').read_text())
REPORT = ROOT / 'reports/artifact-interaction-models-09.json'
OUT.mkdir(exist_ok=True); WEB.mkdir(exist_ok=True)

def y_up(v): return [float(v.x), float(v.z), float(-v.y)]
def z_up(v): return Vector((v[0], -v[2], v[1]))
def bounds(objects):
    bpy.context.view_layer.update()
    ps = [o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    return (Vector([min(p[i] for p in ps) for i in range(3)]),
            Vector([max(p[i] for p in ps) for i in range(3)]))

def classify(slug, o):
    n = o.name; lo, hi = bounds([o]); c = (lo + hi) / 2
    if slug == 'sword':
        return 0 if n.startswith('剑身') else 1 if n.startswith('剑格') else 2 if n.startswith('剑茎') else 3
    if slug == 'bamboo': return int(n.split('第')[1].split('枚')[0]) - 1
    if slug == 'zun':
        if n.startswith(('多层蟠虺', '口沿外层')): return 3 if c.z > .30 else 1
        if n.startswith(('盘四抠手', '抠手')): return 1
        if n.startswith('蟠螭'):
            return 0 if math.hypot(c.x, c.y) > .18 else 2
        if n.startswith(('尊', '反首豹', '豹')): return 2
        return 0
    if slug == 'drum':
        if n.startswith(('缺损鼓腔', '残鼓框', '残框')): return 4
        tiger = n.startswith(('卧虎', '虎')) or (n.startswith(('圆眼',)) and c.z < .35)
        return (0 if c.x < 0 else 1) + (0 if tiger else 2)
    if slug == 'ding-jian':
        return 1 if n.startswith('竖向环耳') else 2 if n.startswith(('四柱足', '柱足')) else 3 if n.startswith(('鼎角', '扉棱')) else 0
    if slug == 'carving-wudang': return 0 if n.startswith('武当') else 1 if n.startswith('独山玉') else 2
    if slug == 'manuscript-xiong': return 0 if n.startswith('稿本微曲') else 2 if n.startswith('稿本封底') else 1
    if slug == 'office-dong':
        if n.startswith(('写字台', '书桌', '抽屉', '台灯', '绿色台灯', '案头')): return 1
        if n.startswith('木椅'): return 2 if c.x < .5 else 5
        if n.startswith(('书架', '木书架')): return 3
        if n.startswith(('圆茶几', '茶几', '茶杯')): return 4
        return 0
    return 0

def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1: bpy.ops.object.join()
    result = bpy.context.object; result.name = name
    return result

def rig_group(objects, index, part, pivot=None):
    lo, hi = bounds(objects); center = pivot if pivot is not None else (lo + hi) / 2
    child = join(objects, f'Part_{index+1:02d}_Mesh')
    matrix = child.matrix_world.copy()
    rig = bpy.data.objects.new(f'Part_{index+1:02d}', None)
    bpy.context.scene.collection.objects.link(rig); rig.location = center
    bpy.context.view_layer.update()
    child.parent = rig; child.matrix_world = matrix
    rig['experience_part'] = index
    rig['label'] = part['label']; rig['detail'] = part['detail']
    rig['explode_offset'] = part.get('offset', [0, 0, 0])
    return rig, child

def action_nla(obj, name, start=1):
    action = obj.animation_data.action; action.name = name
    obj.animation_data.action = None
    track = obj.animation_data.nla_tracks.new(); track.name = name
    strip = track.strips.new(name, start, action); strip.extrapolation = 'HOLD'
    return action

def studio(scene, lo, hi):
    center = (lo+hi)/2; r = max(hi-lo)
    data = bpy.data.cameras.new('交互展示相机'); cam = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(cam); scene.camera = cam
    cam.location = center + Vector((.32, -2.3, .6)) * r
    cam.rotation_euler = (center-cam.location).to_track_quat('-Z','Y').to_euler()
    data.lens = 48; data.clip_start = .0005; data.clip_end = 1000
    scene.world = bpy.data.worlds.new('中性柔光'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.12,.13,.14,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
    for pos, power in [((-.8,-1.5,2),210),((1.5,-.4,.8),90),((0,1,1.5),180)]:
        light = bpy.data.lights.new('展品柔光','AREA'); light.energy = power*r*r; light.shape='DISK'; light.size=r*1.8
        o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o)
        o.location=center+Vector(pos)*r;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.view_settings.view_transform='AgX';scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    fill=bpy.data.lights.new('观察视角补光','AREA');fill.energy=25*r*r;fill.size=r*.8
    lamp=bpy.data.objects.new(fill.name,fill);scene.collection.objects.link(lamp);lamp.parent=cam;lamp.location=(0,0,0)
    return cam

def strike(rig, child, index, slug):
    lo, hi = bounds([child]); dim = hi-lo
    verts = [child.matrix_world @ v.co for v in child.data.vertices]
    bvh = BVHTree.FromPolygons(verts,[list(p.vertices) for p in child.data.polygons])
    normal = Vector((1,0,0)) if slug == 'drum-chongyang' else Vector((0,-1,0))
    target = Vector((hi.x,0,.39)) if slug == 'drum-chongyang' else Vector(((lo.x+hi.x)/2+dim.x*.20,lo.y,lo.z+dim.z*.25))
    contact, _, _, _ = bvh.ray_cast(target + normal*2, -normal, 4)
    if contact is None: contact, _, _, _ = bvh.find_nearest(target)
    assert contact is not None
    rig['strike_point'] = y_up(contact-rig.location); rig['strike_normal'] = y_up(normal)
    rig['view_direction'] = y_up(normal)
    # Scale chosen for legibility; no claim of a measured historical beater.
    length = .20 if slug == 'drum-chongyang' else max(.10, min(.22, max(dim)*.38))
    rig['tool_length'] = length
    wood=bpy.data.materials.get('演示木槌') or bpy.data.materials.new('演示木槌')
    wood.use_nodes=True;p=wood.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.16,.065,.025,1);p.inputs['Roughness'].default_value=.8
    tool=bpy.data.objects.new(f'Tool_{index+1:02d}',None);bpy.context.scene.collection.objects.link(tool)
    tool['experience_tool']=index;tool.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
    for radius, depth, location, rotation in [(length*.12,length,(0,0,length/2),(0,0,0)),(length*.052,length*1.8,(0,-length*.9,length/2),(math.pi/2,0,0))]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth)
        mesh=bpy.context.object;mesh.name=tool.name+'_Wood';mesh.parent=tool;mesh.location=location;mesh.rotation_euler=rotation;mesh.data.materials.append(wood);mesh['experience_tool_mesh']=True
        for face in mesh.data.polygons:face.use_smooth=len(face.vertices)==4
        bevel=mesh.modifiers.new('木槌细圆角','BEVEL');bevel.width=radius*.14;bevel.segments=3
        bevel.harden_normals=True;bpy.context.view_layer.objects.active=mesh;bpy.ops.object.modifier_apply(modifier=bevel.name)
    # Keep the beater in one animated mesh. A zero-scale parent makes child
    # inverse transforms singular during glTF export, collapsing its geometry.
    bpy.context.view_layer.update();tool_matrix=tool.matrix_world.copy();name=tool.name
    mesh=join(list(tool.children),name+'_Mesh')
    mesh.data.transform(tool_matrix.inverted()@mesh.matrix_world)
    mesh.parent=None;mesh.matrix_world=tool_matrix
    bpy.data.objects.remove(tool,do_unlink=True);tool=mesh;tool.name=name
    tool['experience_tool']=index;tool['experience_tool_mesh']=True;tool['tool_length']=length
    tool.rotation_mode='XYZ'
    for frame, distance, visible in [(1,1.3,0),(2,1.3,1),(7,0,1),(14,.9,1),(23,1.3,1),(25,1.3,0),(46,1.3,0)]:
        tool.location=contact+normal*distance*length;tool.scale=(visible,)*3
        tool.keyframe_insert(data_path='location',frame=frame);tool.keyframe_insert(data_path='scale',frame=frame)
        # Key orientation explicitly: zero-scale export poses cannot preserve a decomposed rotation.
        tool.keyframe_insert(data_path='rotation_euler',frame=frame)
    action_nla(tool,f'ToolStrike_{index+1:02d}',1+index*24);tool.scale=(0,0,0)
    if slug == 'chimes':
        for frame,factor in [(1,0),(7,0),(11,1),(19,-.55),(28,.3),(38,-.12),(46,0)]:
            rig.rotation_euler.x=.012*factor;rig.keyframe_insert(data_path='rotation_euler',frame=frame)
        action_nla(rig,f'Strike_{index+1:02d}',1+index*24);rig.rotation_euler=(0,0,0)
    return {'part':index,'contact':y_up(contact),'normal':y_up(normal),'contact_frame':7,'tool':tool.name}

def build(slug, config):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if slug == 'chimes': bpy.ops.import_scene.gltf(filepath=str(ROOT/'models/artifacts/chimes.glb'))
    else: bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/artifacts'/f'{slug}.blend'),load_ui=False)
    scene=bpy.context.scene;scene.render.fps=30;scene.unit_settings.system='METRIC'
    for o in list(scene.objects):
        if o.type not in ['MESH','EMPTY']:bpy.data.objects.remove(o,do_unlink=True)
    refinement=refine(slug)
    objects=[o for o in scene.objects if o.type=='MESH']
    # Apply existing modifiers once; geometry and material data come from the saved source.
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH')
    objects=[o for o in scene.objects if o.type=='MESH']
    lo,hi=bounds(objects)
    for o in objects:o.data.calc_loop_triangles()
    triangles=sum(len(o.data.loop_triangles) for o in objects)
    rigs=[];contacts=[];details=[]
    if config['mode']=='inspect':
        join(objects,'Artifact_Body')
        glo=Vector((lo.x,lo.z,-hi.y));ghi=Vector((hi.x,hi.z,-lo.y))
        for i,view in enumerate(config['views']):
            o=bpy.data.objects.new(f'Part_{i+1:02d}',None);scene.collection.objects.link(o)
            point=glo+(ghi-glo)*Vector(view['point']);o.location=z_up(point)
            o['experience_part']=i;o['label']=view['label'];o['detail']=view['detail']
            o['view_direction']=view['direction'];o['view_span']=view['span']*max(hi-lo);rigs.append(o)
    else:
        groups=defaultdict(list)
        if slug=='chimes':
            for o in objects:
                if o.name.startswith('chimes_BianQin'):groups[int(o.name.split('BianQin')[1])].append(o)
            assert len(groups)==32
            config=dict(config);config['parts']=[{'label':f'第 {i+1:02d} 枚磬','detail':'外击与小幅回振示意；磬架与挂钩保持固定。','offset':[0,0,0]} for i in range(32)]
        else:
            for o in objects:groups[classify(slug,o)].append(o)
        assert set(groups)==set(range(len(config['parts']))),(slug,sorted(groups))
        for i,part in enumerate(config['parts']):
            anchors=detail_anchors(slug,groups[i],bounds)
            a,b=bounds(groups[i]);pivot=Vector(((a.x+b.x)/2,(a.y+b.y)/2,b.z)) if slug=='chimes' else None
            rig,child=rig_group(groups[i],i,part,pivot);rigs.append(rig)
            for j,(label,point,span,direction) in enumerate(anchors):
                anchor=bpy.data.objects.new(f'Detail_{i+1:02d}_{j+1:02d}',None);scene.collection.objects.link(anchor)
                anchor.parent=rig;anchor.location=point-rig.location;anchor['experience_detail']=True
                anchor['label']=label;anchor['view_span']=span;anchor['view_direction']=list(direction)
                anchor['detail']='依据当前模型及参考照片观察；隐藏形态与细小连接仍为近似。'
                details.append(anchor)
            if config['mode']=='explode':
                rest=rig.location.copy();offset=z_up(part['offset'])
                for frame,factor in [(1,0),(61,1),(91,1),(151,0)]:
                    rig.location=rest+offset*factor;rig.keyframe_insert(data_path='location',frame=frame)
                action_nla(rig,f'Expand_{i+1:02d}');rig.location=rest
            else:contacts.append(strike(rig,child,i,slug))
    scene.frame_start=1;scene.frame_end=151 if config['mode']=='explode' else (len(rigs)-1)*24+46 if config['mode']=='strike' else len(rigs)*90+1
    scene.frame_set(1);bpy.context.view_layer.update()
    after=[o for o in scene.objects if o.type=='MESH' and not o.get('experience_tool_mesh')]
    alo,ahi=bounds(after)
    assert (alo-lo).length<1e-5 and (ahi-hi).length<1e-5,(slug,'rest bounds changed')
    for o in after:o.data.calc_loop_triangles()
    assert sum(len(o.data.loop_triangles) for o in after)==triangles,(slug,'geometry changed')
    bpy.ops.object.select_all(action='DESELECT')
    for o in scene.objects:
        if o.type in ['MESH','EMPTY']:o.select_set(True)
    path=OUT/f'{slug}-interactive.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_extras=True,export_cameras=False,export_lights=False,
        export_animations=config['mode']!='inspect',export_animation_mode='ACTIONS',export_merge_animation='ACTION',
        export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_image_format='JPEG',export_jpeg_quality=92)
    shutil.copy2(path,WEB/path.name)
    # Camera and guides belong to the editable demonstration, not to the original artifact.
    camera=studio(scene,lo,hi)
    for anchor in details:
        data=bpy.data.cameras.new(anchor['label']+'特写');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam)
        cam.parent=anchor;data.lens=48;data.clip_start=.0001;data.clip_end=1000
        distance=anchor['view_span']/(2*math.tan(data.angle_y/2))*1.3
        cam.location=z_up(anchor['view_direction']).normalized()*distance
        cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    if config['mode']=='inspect':
        for i,rig in enumerate(rigs+rigs[:1]):
            direction=z_up(rig['view_direction']).normalized();span=rig['view_span']
            distance=span/(2*math.tan(camera.data.angle_y/2))*1.25
            camera.location=rig.location+direction*distance
            camera.rotation_euler=(rig.location-camera.location).to_track_quat('-Z','Y').to_euler()
            for frame in [i*90+1,min(i*90+46,scene.frame_end)]:
                camera.keyframe_insert(data_path='location',frame=frame);camera.keyframe_insert(data_path='rotation_euler',frame=frame)
    elif config['mode']=='explode':
        scene.frame_set(61);elo,ehi=bounds(after);scene.frame_set(1)
        center=(elo+ehi+lo+hi)/4;r=max(ehi-elo,hi-lo,key=lambda v:max(v));radius=max(r)
        camera.location=center+Vector((.25,-2.4,.5))*radius
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene['interaction_revision']='0.9';scene['interaction_mode']=config['mode'];scene['interaction_note']=config['note']
    scene['detail_views']=len(details)
    scene['static_source']=f'models/artifacts/{slug}.blend';scene['part_count']=len(rigs)
    scene.frame_set(1)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{slug}-interactive.blend'),compress=True)
    data=path.read_bytes();doc=json.loads(data[20:20+struct.unpack_from('<I',data,12)[0]])
    report={'id':slug,'mode':config['mode'],'parts':len(rigs),'triangles':triangles,'rigging_preserves_refined_bounds':True,'geometry_refinement':refinement,'detail_views':len(details),'bytes':len(data),'clips':len(doc.get('animations',[])),'contacts':contacts}
    print('ARTIFACT_INTERACTION_BUILT',json.dumps(report,ensure_ascii=False),flush=True)
    return report

chosen=[s for s in sys.argv[sys.argv.index('--')+1:] if s in CONFIG] if '--' in sys.argv else list(CONFIG)
reports=json.loads(REPORT.read_text()) if REPORT.exists() else []
for slug in chosen:
    report=build(slug,CONFIG[slug]);reports=[r for r in reports if r['id']!=slug]+[report]
    REPORT.write_text(json.dumps(reports,ensure_ascii=False,indent=2))
