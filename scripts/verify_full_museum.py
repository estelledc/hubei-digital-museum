"""Real Blender reopen and GLB container checks, not a likeness certification."""
import bpy,json,struct,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
galleries=json.loads((ROOT/'research/full04/galleries.json').read_text());report={'galleries':[],'public_spaces':[],'glbs':[]}
for g in galleries:
 p=ROOT/'models/galleries'/(g['id']+'.blend');bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False);s=bpy.context.scene;bpy.context.view_layer.update()
 assert s.camera and s.get('gallery_id')==g['id'] and s.get('space_revision')=='0.10',g['id']
 assert len(g['artifacts'])>0,g['id']
 row={'id':g['id'],'mesh_objects':sum(o.type=='MESH' for o in s.objects),'artifacts':[],'packed_images':sum(bool(im.packed_file) for im in bpy.data.images)}
 for a in g['artifacts']:
  objs=[o for o in s.objects if o.type=='MESH' and o.get('artifact_id')==a['id']];assert objs,(g['id'],a['id'])
  pts=[o.matrix_world@Vector(v) for o in objs for v in o.bound_box];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)];assert all(math.isfinite(x) and x>0 for x in dims)
  polys=sum(len(o.data.polygons) for o in objs);assert polys>=12,(a['id'],polys)
  row['artifacts'].append({'id':a['id'],'dimensions_m':dims,'base_polygons':polys})
 assert (ROOT/'renders/space-10'/(g['id']+'.jpg')).stat().st_size>10000
 for im in bpy.data.images:
  if im.source=='FILE':assert im.packed_file or Path(bpy.path.abspath(im.filepath)).exists(),im.name
 report['galleries'].append(row)
for id in ['atrium','connection','theatre']:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/public'/(id+'.blend')),load_ui=False)
 assert bpy.context.scene.camera
 report['public_spaces'].append({'id':id,'objects':len(bpy.context.scene.objects)})
for p in sorted([*(ROOT/'models/galleries').glob('*.glb'),*(ROOT/'models/public').glob('*.glb'),*(ROOT/'models/artifacts').glob('*.glb'),ROOT/'models/museum-architecture.glb']):
 raw=p.read_bytes();magic,v,size=struct.unpack_from('<4sII',raw);assert magic==b'glTF' and v==2 and size==len(raw),p
 n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a;doc=json.loads(raw[20:20+n]);assert doc.get('meshes'),p
 assert not [x for group in ['images','buffers'] for x in doc.get(group,[]) if x.get('uri') and not x['uri'].startswith('data:')],p
 ids=set(node.get('extras',{}).get('artifact_id') for node in doc.get('nodes',[]))
 if p.parent.name=='galleries':
  expected={a['id'] for a in next(g for g in galleries if g['id']==p.stem)['artifacts']};assert expected<=ids,(p,expected,ids)
 web=ROOT/'web/public/models'/p.relative_to(ROOT/'models') if p.parent.name in ['public','galleries'] else ROOT/'web/public/models'/p.name
 assert web.read_bytes()==raw,web
 report['glbs'].append({'file':str(p.relative_to(ROOT)),'bytes':len(raw),'meshes':len(doc['meshes']),'draw_primitives':sum(len(m['primitives']) for m in doc['meshes'])})
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/hubei-museum.blend'),load_ui=False)
s=bpy.context.scene;assert s.get('version')=='0.10';assert s.get('gallery_count')==11
actual={o.get('gallery_id') for o in s.objects};assert {g['id'] for g in galleries}<=actual
report['main']={'version':s['version'],'objects':len(s.objects),'mesh_objects':sum(o.type=='MESH' for o in s.objects),'gallery_ids':sorted(x for x in actual if x),'packed_images':sum(bool(im.packed_file) for im in bpy.data.images)}
report['limits']='Reopening and resources/structure checked. Visual resemblance, present-day object placement and accurate floor geometry are not certified.'
(ROOT/'reports/space-10-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('SPACE10_VERIFIED',len(report['galleries']),len(report['glbs']),report['main'],flush=True)
