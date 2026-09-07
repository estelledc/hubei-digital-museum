"""Build and render the photo-guided revision; integrate only after inspection.
blender --background --python scripts/refine_artifacts.py [-- --integrate]
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from artifact_geometry import build,BUILDERS
OUT=ROOT/'models/refined-03';OUT.mkdir(exist_ok=True)
RENDERS=ROOT/'renders/fidelity-03';RENDERS.mkdir(exist_ok=True)
POSITIONS={'sword':(48,-13,7.7),'zun':(-39,4,.9),'drum':(-48,0,14.5),'vase':(-17,109,14.5),'bamboo':(-40,4,14.5)}
PAGES={'sword':'4694','zun':'6911','drum':'6913','vase':'4696','bamboo':'6912'}
if '--integrate' not in sys.argv:
    report=[]
    chosen=[a for a in sys.argv[sys.argv.index('--')+1:] if a in BUILDERS] if '--' in sys.argv else []
    previous=json.loads((ROOT/'reports/fidelity-03-models.json').read_text()) if chosen else []
    for slug in chosen or BUILDERS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
        c=bpy.data.collections.new('06_Artifacts_照片依据补建');s.collection.children.link(c)
        objects=build(slug,c)
        for o in objects:o['source_url']='https://www.hbww.org.cn/zgzb/p/'+PAGES[slug]+'.html'
        bpy.context.view_layer.update()
        points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
        lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
        center=(lo+hi)*.5;dims=hi-lo;r=max(dims)
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(slug+'.blend')),compress=True)
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()
        objects=[bpy.context.object]
        bpy.ops.export_scene.gltf(filepath=str(OUT/(slug+'.glb')),use_selection=True,export_format='GLB',export_extras=True,export_image_format='JPEG',export_jpeg_quality=92)
        deps=bpy.context.evaluated_depsgraph_get()
        triangles=sum(len(o.evaluated_get(deps).data.polygons) for o in objects if o.type=='MESH')
        report.append({'id':slug,'dimensions_m':list(dims),'objects':len(objects),'evaluated_polygons':triangles,'image_count':len(bpy.data.images),'glb_bytes':(OUT/(slug+'.glb')).stat().st_size})
        s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
        s.render.resolution_x=1200;s.render.resolution_y=1200;s.render.resolution_percentage=100
        s.world=bpy.data.worlds.new('Neutral studio');s.world.use_nodes=True
        s.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.19,.20,1)
        s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
        s.view_settings.view_transform='AgX'
        def lamp(name,pos,power,size):
            d=bpy.data.lights.new(name,'AREA');d.energy=power*r*r;d.shape='DISK';d.size=size*r
            o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=center+Vector(pos)*r
            o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
        lamp('Large softbox',(-1.5,-2.0,2.1),190,2.2)
        lamp('Neutral fill',(1.2,-1.5,.2),60,1.8)
        lamp('Edge light',(.9,1.5,1.3),260,1.7)
        d=bpy.data.cameras.new('Artifact detail');cam=bpy.data.objects.new('Artifact detail',d);s.collection.objects.link(cam)
        angle={'sword':(.1,-2.2,.20),'zun':(.55,-1.7,.95),'drum':(.1,-2.2,.22),'vase':(.1,-2.2,.15),'bamboo':(.05,-2.2,.1)}[slug]
        cam.location=center+Vector(angle)*r;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=52;d.clip_start=.001;s.camera=cam
        s.render.image_settings.file_format='PNG';s.render.filepath=str(RENDERS/(slug+'.png'))
        bpy.ops.render.render(write_still=True)
        print('ARTIFACT_REFINED',slug,report[-1],flush=True)
    report=[r for r in previous if r['id'] not in chosen]+report
    (ROOT/'reports/fidelity-03-models.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
else:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/hubei-museum.blend'),load_ui=False)
    s=bpy.context.scene
    for o in list(s.objects):
        if o.get('artifact_id') in set(BUILDERS)|{'bells','chimes'}:bpy.data.objects.remove(o,do_unlink=True)
    c=bpy.data.collections.get('06_Artifacts_补建形制示意')
    for slug in BUILDERS:
        with bpy.data.libraries.load(str(OUT/(slug+'.blend')),link=False) as (src,dst):dst.objects=src.objects
        for o in dst.objects:
            if o and o.type=='MESH':c.objects.link(o);o.location+=Vector(POSITIONS[slug])
    for slug,pos in [('bells',(-51,-5,0)),('chimes',(-41,-4,0))]:
        c=bpy.data.collections.get('Archive_'+slug+'_用户存档_非扫描')
        with bpy.data.libraries.load(str(OUT/(slug+'.blend')),link=False) as (src,dst):dst.objects=src.objects
        for o in dst.objects:
            if o and o.type=='MESH':c.objects.link(o);o.location+=Vector(pos);o['artifact_id']=slug;o['part']='archival_artifact'
    bpy.data.orphans_purge(do_recursive=True)
    s['fidelity_revision']='0.3 photo-guided geometry and registered high-resolution photography; not a scan'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/hubei-museum.blend'),compress=True)
    for slug in BUILDERS:
        bpy.ops.object.select_all(action='DESELECT')
        objs=[o for o in s.objects if o.get('artifact_id')==slug]
        for o in objs:o.select_set(True)
        bpy.context.view_layer.objects.active=objs[0]
        bpy.ops.object.convert(target='MESH')
        if len(objs)>1:bpy.ops.object.join()
    bpy.ops.object.select_all(action='DESELECT')
    for o in s.objects:
        if o.type not in ['LIGHT','CAMERA'] and o.get('artifact_id') not in ['bells','chimes']:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'models/museum-architecture.glb'),use_selection=True,export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,export_image_format='JPEG',export_jpeg_quality=92)
    print('FIDELITY_INTEGRATED',flush=True)
