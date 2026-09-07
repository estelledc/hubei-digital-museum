"""Build and render the photo-guided revision; integrate only after inspection.
blender --background --python scripts/refine_artifacts.py [-- --integrate]
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from full_museum_artifacts import build,BUILDERS
OUT=ROOT/'models/refined-04';OUT.mkdir(exist_ok=True)
RENDERS=ROOT/'renders/fidelity-04';RENDERS.mkdir(exist_ok=True)
POSITIONS={'sword':(48,-13,7.7),'zun':(-39,4,.9),'drum':(-48,0,14.5),'vase':(-17,109,14.5),'bamboo':(-40,4,14.5)}
SOURCES={'pottery-bell':'https://3dvr4.marslanding.com.cn/','ding-jian':'https://www.hbww.org.cn/xwdt/p/7400.html','gold-liang':'https://www.hbww.org.cn/xwdt/p/6897.html','drum-chongyang':'https://www.hbww.org.cn/zgzb/p/6916.html','jade-shijiahe':'https://www.hbww.org.cn/zgzb/p/6915.html','carving-wudang':'https://www.hbww.org.cn/p/9380.html','medal-lizuodong':'https://www.hbww.org.cn/xwdt/p/9632.html','manuscript-xiong':'https://www.hbww.org.cn/xwdt/p/9632.html','office-dong':'https://www.hbww.org.cn/cszl/p/10713.html'}
if __name__=='__main__':
    report=[]
    chosen=[a for a in sys.argv[sys.argv.index('--')+1:] if a in BUILDERS] if '--' in sys.argv else []
    previous=json.loads((ROOT/'reports/fidelity-04-models.json').read_text()) if chosen and (ROOT/'reports/fidelity-04-models.json').exists() else []
    for slug in chosen or BUILDERS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
        c=bpy.data.collections.new('06_Artifacts_04_照片依据补建');s.collection.children.link(c)
        objects=build(slug,c)
        for o in objects:o['source_url']=SOURCES[slug]
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
        angle={'ding-jian':(.8,-2,.8),'drum-chongyang':(1,-1.8,.4),'office-dong':(.1,-1.7,.5)}.get(slug,(.08,-2.2,.15))
        cam.location=center+Vector(angle)*r;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=52;d.clip_start=.001;s.camera=cam
        s.render.image_settings.file_format='PNG';s.render.filepath=str(RENDERS/(slug+'.png'))
        bpy.ops.render.render(write_still=True)
        print('ARTIFACT_REFINED',slug,report[-1],flush=True)
    report=[r for r in previous if r['id'] not in chosen]+report
    (ROOT/'reports/fidelity-04-models.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
