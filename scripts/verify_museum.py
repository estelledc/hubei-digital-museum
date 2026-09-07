"""Verify reopening, archival world extents, packed resources and web GLB structure."""
import bpy, json, struct, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/hubei-museum.blend'),load_ui=False)
scene=bpy.context.scene
report={'blender_version':bpy.app.version_string,'reopened':True,'mesh_objects':sum(o.type=='MESH' for o in scene.objects),'camera_names':[o.name for o in scene.objects if o.type=='CAMERA'],'archive_bounds':{},'unresolvable_images':[],'glb_files':[]}
for slug in ['bells','chimes']:
 objs=[o for o in scene.objects if o.get('artifact_id')==slug and o.type=='MESH']
 pts=[o.matrix_world@Vector(v) for o in objs for v in o.bound_box]
 dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
 expected=[9.240858,4.882427,2.828298] if slug=='bells' else [2.4,.65,1.17]
 assert objs and all(abs(a-b)<.003 for a,b in zip(dims,expected)),(slug,dims)
 report['archive_bounds'][slug]={'dimensions_m':dims,'polygons':sum(len(o.data.polygons) for o in objs)}
for im in bpy.data.images:
 if im.source=='FILE':
  available=bool(im.packed_file) or Path(bpy.path.abspath(im.filepath)).is_file()
  if not available and not im.has_data:report['unresolvable_images'].append(im.name)
assert not report['unresolvable_images'],report['unresolvable_images']
assert any(f.packed_file for f in bpy.data.fonts if f.name!='Bfont Regular'), 'Chinese font must be packed'
expected_cameras=json.loads((ROOT/'reports/build.json').read_text())['cameras']
assert len(report['camera_names'])==len(expected_cameras)
for p in sorted([ROOT/'models/museum-architecture.glb', *(ROOT/'models/artifacts').glob('*.glb')]):
 data=p.read_bytes();magic,version,length=struct.unpack_from('<4sII',data)
 assert magic==b'glTF' and version==2 and length==len(data),p
 n,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
 g=json.loads(data[20:20+n]);assert g.get('meshes') and g.get('scenes'),p
 if p.name=='chimes.glb':
  stones=[m for m in g['materials'] if m['name'].startswith('CQ_Stone_')]
  assert len(stones)==4
  assert all('baseColorTexture' in m['pbrMetallicRoughness'] for m in stones), 'Stone colour graph was lost in export'
 if p.name=='bells.glb':
  cloth=next(m for m in g['materials'] if m['name']=='BuWen')['pbrMetallicRoughness']
  assert 'baseColorFactor' in cloth and max(cloth['baseColorFactor'][:3])<.2, 'Display floor reverted to bright red'
 external=[x['uri'] for group in ['buffers','images'] for x in g.get(group,[]) if 'uri' in x and not x['uri'].startswith('data:')]
 assert not external,(p,external)
 for accessor in g.get('accessors',[]):
  for key in ['min','max']:
   assert all(math.isfinite(x) for x in accessor.get(key,[])),p
 report['glb_files'].append({'file':str(p.relative_to(ROOT)),'bytes':len(data),'meshes':len(g['meshes']),'external_dependencies':external})
report['version']=scene.get('version','unknown')
report['retained_fidelity_revision']=scene.get('fidelity_revision','unknown')
report['refined_artifacts_03']=json.loads((ROOT/'reports/fidelity-03-models.json').read_text())
report['added_artifacts_04']=json.loads((ROOT/'reports/fidelity-04-models.json').read_text())
report['limits']='File and structural verification, plus original instrument world dimensions. Does not certify historical identity, visual likeness, exact room layout, or browser interaction.'
report['colour_revision']={
 'source_graph_baked':True,
 'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),
 'render_samples':scene.cycles.samples,
 'blender_view_transform':scene.view_settings.view_transform,
 'baked_colour_images':[im.name for im in bpy.data.images if im.name.startswith('Baked_Albedo_')],
}
(ROOT/'reports/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('VERIFIED',json.dumps(report,ensure_ascii=False),flush=True)
