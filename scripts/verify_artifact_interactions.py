"""Reopen each shipped Blender derivative and verify the saved timeline, not generator state."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
configs=json.loads((ROOT/'web/lib/artifact-experiences.json').read_text())
reports=[]
for slug,config in configs.items():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/interactive'/f'{slug}-interactive.blend'),load_ui=False)
    s=bpy.context.scene;rigs=sorted([o for o in s.objects if 'experience_part' in o],key=lambda o:o['experience_part'])
    s.frame_set(1);rest=[(o.location.copy(),o.rotation_euler.copy()) for o in rigs]
    details=[o for o in s.objects if o.get('experience_detail')]
    if config['mode']=='explode':
        assert details and s['detail_views']==len(details),(slug,'missing detail cameras')
        for o in details:
            assert o.parent in rigs and any(c.type=='CAMERA' for c in o.children),(slug,'detail parenting')
            assert o['view_span']>0 and o['label']
    if slug=='vase':
        body=next(o for o in s.objects if o.type=='MESH')
        inner=[body.matrix_world@body.data.vertices[v].co for p in body.data.polygons if p.material_index==0 for v in p.vertices]
        assert min(v.z for v in inner)<.015 and max(v.z for v in inner)>.38,'inner wall extends through body'
        assert any(.1<v.z<.3 and .06<math.hypot(v.x,v.y)<.1 for v in inner),'body has intermediate inner-wall sections'
    if slug=='manuscript-xiong':
        rig=rigs[0];leaf=next(o for o in rig.children if o.type=='MESH')
        points=[leaf.matrix_world@v.co for v in leaf.data.vertices]
        assert len(points)>3000 and max(v.y for v in points)-min(v.y for v in points)>.002,'curved photo leaf'
    if config['mode']=='explode':
        s.frame_set(61)
        for o,(p,r) in zip(rigs,rest):
            d=o['explode_offset'];target=p+Vector((d[0],-d[2],d[1]))
            assert (o.location-target).length<1e-6,(slug,o.name,'expanded pose')
        s.frame_set(s.frame_end)
        assert all((o.location-p).length<1e-6 for o,(p,r) in zip(rigs,rest)),(slug,'end reset')
    elif config['mode']=='strike':
        if slug=='chimes':assert len(rigs)==32
        tools=sorted([o for o in s.objects if 'experience_tool' in o],key=lambda o:o['experience_tool'])
        assert len(tools)==len(rigs)
        for i,rig in enumerate(rigs):
            s.frame_set(7+i*24);v=rig['strike_point'];point=rest[i][0]+Vector((v[0],-v[2],v[1]))
            assert (tools[i].location-point).length<1e-5 and min(tools[i].scale)>.99,(slug,i,'contact')
            v=rig['strike_normal'];normal=Vector((v[0],-v[2],v[1]))
            assert (tools[i].rotation_euler.to_quaternion()@Vector((0,0,1))).dot(normal)>.99,(slug,i,'head orientation')
            s.frame_set(11+i*24)
            if slug=='chimes':assert .005<abs(rig.rotation_euler.x)<.02
        s.frame_set(s.frame_end)
        assert all(max(t.scale)<1e-5 for t in tools),(slug,'tools hidden at end')
        assert all(o.rotation_euler.to_quaternion().rotation_difference(r.to_quaternion()).angle<1e-5 for o,(p,r) in zip(rigs,rest))
    else:
        assert s.camera.animation_data and s.camera.animation_data.action
        s.frame_set(1);start=s.camera.location.copy();s.frame_set(91)
        assert (s.camera.location-start).length>.001,(slug,'camera tour')
        assert all((o.location-p).length<1e-6 for o,(p,r) in zip(rigs,rest))
    assert all(im.packed_file or Path(bpy.path.abspath(im.filepath)).exists() for im in bpy.data.images if im.source=='FILE')
    reports.append({'id':slug,'mode':config['mode'],'reopened':True,'parts':len(rigs),'detail_views':len(details),'timeline_verified':True,'images_resolved':True})
    print('BLENDER_INTERACTION_VERIFIED',slug,len(rigs),flush=True)
(ROOT/'reports/artifact-interaction-blender-10.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
