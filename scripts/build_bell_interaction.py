"""Derive 65 independent bell rigs from the existing browser mesh without altering it."""
import bpy,json,math,struct
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'models/interactive';OUT.mkdir(exist_ok=True)
PERFORMANCE=json.loads((ROOT/'web/lib/bell-performance.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'models/artifacts/bells.glb'))
s=bpy.context.scene;s.unit_settings.system='METRIC';s.render.fps=30
original_faces=sum(len(o.data.polygons) for o in s.objects if o.type=='MESH')
original_bounds=[o.matrix_world@Vector(v) for o in s.objects if o.type=='MESH' for v in o.bound_box]
rigs=[];report=[]
for source,tier,minimum in [('bells_NiuZhong','上层',400),('bells_BoZhong01','中层',2000),('bells_BoZhong02','下层',3000)]:
 o=bpy.data.objects[source];me=o.data;parent=list(range(len(me.vertices)))
 def root(v):
  while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
  return v
 # Weld positional duplicates for analysis only: export split them at UV/normal seams.
 seen={}
 for v in me.vertices:
  key=tuple(round(x,5) for x in v.co)
  if key in seen:parent[root(v.index)]=root(seen[key])
  else:seen[key]=v.index
 for e in me.edges:
  a,b=map(root,e.vertices)
  if a!=b:parent[b]=a
 comps=defaultdict(list)
 for v in me.vertices:comps[root(v.index)].append(v.index)
 coords=np.array([o.matrix_world@v.co for v in me.vertices])
 details={}
 for k,indices in comps.items():
  points=coords[indices];lo=points.min(axis=0);hi=points.max(axis=0)
  details[k]={'center':(lo+hi)/2,'size':hi-lo,'n':len(indices)}
 seeds=[v for v in details.values() if v['n']>=minimum and v['size'][2]>(.15 if tier=='上层' else .25 if tier=='中层' else .3)]
 # Walk the L-shaped rack: short arm front-to-back, then long arm left-to-right.
 seeds.sort(key=lambda v:(0,v['center'][1]) if v['center'][0]<-3.4 else (1,v['center'][0]))
 assert len(seeds)=={'上层':19,'中层':33,'下层':13}[tier],(tier,len(seeds))
 centers=np.array([v['center'] for v in seeds])
 assignment={k:int(np.argmin(((v['center'][:2]-centers[:,:2])**2).sum(axis=1))) for k,v in details.items()}
 face_groups=defaultdict(list)
 for p in me.polygons:
  assert len({root(v) for v in p.vertices})==1
  face_groups[assignment[root(p.vertices[0])]].append(p.index)
 normals=np.empty(len(me.loops)*3,dtype=np.float32);me.corner_normals.foreach_get('vector',normals);normals=normals.reshape(-1,3)
 uv=np.empty(len(me.loops)*2,dtype=np.float32);me.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2)
 for gi,seed in enumerate(seeds):
  polys=[me.polygons[i] for i in face_groups[gi]];vi=sorted({v for p in polys for v in p.vertices});remap={v:i for i,v in enumerate(vi)}
  ps=coords[vi];lo=ps.min(axis=0);hi=ps.max(axis=0);pivot=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,hi[2]))
  num=len(rigs)+1;name=f'Bell_{num:02d}'
  rig=bpy.data.objects.new(name,None);s.collection.objects.link(rig);rig.location=pivot
  rig['bell_id']=num;rig['bell_tier']=tier;rig['animation_note']='Illustrative strike response; not measured vibration or a musical pitch mapping'
  mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata([tuple(Vector(co)-pivot) for co in ps],[],[[remap[v] for v in p.vertices] for p in polys]);mesh.update()
  for mat in me.materials:mesh.materials.append(mat)
  loop_indices=[li for p in polys for li in p.loop_indices]
  layer=mesh.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',uv[loop_indices].ravel())
  for a,b in zip(mesh.polygons,polys):a.material_index=b.material_index;a.use_smooth=b.use_smooth
  mesh.normals_split_custom_set(normals[loop_indices].tolist())
  child=bpy.data.objects.new(name+'_Body',mesh);s.collection.objects.link(child);child.parent=rig;child['bell_id']=num
  # Select a drum-area surface point, fixed to the instrument rather than to the camera.
  # Short-arm players stand outside that arm; modern long-arm short-mallet players stand behind it.
  normal=Vector((-1,0,0)) if pivot.x<-3.4 else Vector((0,-1 if tier=='下层' else 1,0))
  tangent=Vector((0,0,1)).cross(normal)
  bvh=BVHTree.FromPolygons([v.co for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons],all_triangles=True)
  target=Vector((0,0,float(lo[2]+(hi[2]-lo[2])*.24-pivot.z)))
  for zone in ['front','side']:
   direction=normal if zone=='front' else (normal+tangent*.55).normalized()
   hit,_,_,_=bvh.ray_cast(target+direction*2,-direction,4)
   assert hit is not None,(name,zone,'no drum-area intersection')
   # Extras explicitly use glTF Y-up local coordinates; arbitrary extras are not axis-converted by export.
   rig['strike_'+zone]=[float(hit.x),float(hit.z),float(-hit.y)]
   rig['normal_'+zone]=[float(direction.x),float(direction.z),float(-direction.y)]
  rig['strike_note']='Drum-area approximation on supplied mesh, not a verified historical tuning point'
  # Deliberately enlarged demonstration swing; first motion follows mallet contact.
  amplitude={'上层':.12,'中层':.095,'下层':.07}[tier]
  rig['swing_degrees']=math.degrees(amplitude);rig['swing_seconds']=3.0
  for frame,factor in [(1,0),(5,0),(11,1),(23,-.7),(37,.46),(53,-.27),(71,.12),(91,0)]:
   rig.rotation_euler[1 if pivot.x<-3.4 else 0]=amplitude*factor
   rig.keyframe_insert(data_path='rotation_euler',frame=frame)
  action=rig.animation_data.action;action.name=f'Strike_{num:02d}'
  rig.rotation_euler=(0,0,0)
  # Separate actions remain selectable in Blender and are exported as individual clips.
  rig.animation_data.action=None
  track=rig.animation_data.nla_tracks.new();track.name=f'Strike_{num:02d}'
  strip=track.strips.new(action.name,1+(num-1)*20,action);strip.extrapolation='NOTHING'
  rigs.append(rig);report.append({'id':num,'name':name,'tier':tier,'size_m':[float(x) for x in hi-lo],'pivot_m':list(pivot),'triangles':len(polys),'source':source})
 bpy.data.objects.remove(o,do_unlink=True)
s.frame_start=1;s.frame_end=(len(rigs)-1)*20+91;s.frame_set(0)
assert sum(len(o.data.polygons) for o in s.objects if o.type=='MESH')==original_faces
bpy.context.view_layer.update()
current_bounds=[o.matrix_world@Vector(v) for o in s.objects if o.type=='MESH' for v in o.bound_box]
for axis in range(3):
 assert abs(min(p[axis] for p in current_bounds)-min(p[axis] for p in original_bounds))<.00001
 assert abs(max(p[axis] for p in current_bounds)-max(p[axis] for p in original_bounds))<.00001
s['interaction_revision']='0.7';s['bell_count']=65;s['animation_scope']='Reference-based tool demonstration; reduced swing is not a measured physical reconstruction'
# A useful saved view and timeline preview for the editable derivative.
camdata=bpy.data.cameras.new('编钟互动预览');cam=bpy.data.objects.new('编钟互动预览',camdata);s.collection.objects.link(cam)
cam.location=(1,-12,4);cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=40;s.camera=cam
s.world=bpy.data.worlds.new('中性环境');s.world.color=(.18,.18,.18)
for pos,power,size in [((0,-5,6),1800,7),((-5,2,4),900,5)]:
 d=bpy.data.lights.new('编钟柔光','AREA');d.energy=power;d.shape='DISK';d.size=size
 lamp=bpy.data.objects.new('编钟柔光',d);s.collection.objects.link(lamp);lamp.location=pos;lamp.rotation_euler=(Vector((0,0,1.2))-lamp.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.samples=24;s.view_settings.view_transform='AgX'
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.object.select_all(action='DESELECT')
for obj in s.objects:
 if obj.type in ['MESH','EMPTY']:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'bells-interactive.glb'),use_selection=True,export_extras=True,export_animations=True,export_animation_mode='ACTIONS',export_merge_animation='ACTION',export_force_sampling=True,export_frame_range=False,export_image_format='JPEG',export_jpeg_quality=92)
b=(OUT/'bells-interactive.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);assert len(j['animations'])==65,len(j['animations'])
for a in j['animations']:
 targets={j['nodes'][c['target']['node']]['name'] for c in a['channels']};assert len(targets)==1,(a['name'],targets)
(ROOT/'reports/bell-interaction-model.json').write_text(json.dumps({'bell_count':len(rigs),'original_triangles':original_faces,'output_triangles':sum(len(o.data.polygons) for o in s.objects if o.type=='MESH'),'bell_triangles':sum(x['triangles'] for x in report),'clips':len(j['animations']),'bytes':len(b),'bells':report},ensure_ascii=False,indent=2))
print('INTERACTIVE_BELLS_BUILT',len(rigs),len(j['animations']),len(b),flush=True)

# Editable tool demonstration in Blender; browser creates the same tools using the shared dimensions.
# Add these after the bell-only GLB export to avoid shipping 65 redundant copies of two small tools.
wood=bpy.data.materials.new('示范木槌与撞棒');wood.diffuse_color=(.16,.065,.025,1);wood.use_nodes=True
wood.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.16,.065,.025,1)
wood.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
def cylinder(parent,radius,length,location,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=length)
 obj=bpy.context.object;obj.name=parent.name+'_Wood';obj.parent=parent;obj.location=location;obj.rotation_euler=rotation
 obj.data.materials.append(wood);obj['performance_demo']=True
 return obj
for rig in rigs:
 strip=rig.animation_data.nla_tracks[0].strips[0];strip.use_animated_influence=True;strip.influence=PERFORMANCE['referenceWeight']
 num=rig['bell_id'];is_rod=rig['bell_tier']=='下层'
 point=Vector(rig['strike_front']);point=Vector((point.x,-point.z,point.y))+rig.location
 direction=Vector(rig['normal_front']);direction=Vector((direction.x,-direction.z,direction.y))
 tool=bpy.data.objects.new(f'DemoTool_{num:02d}',None);s.collection.objects.link(tool);tool['performance_demo']=True;tool['tool_type']='long_rod' if is_rod else 'short_mallet'
 # Local Z points away from the bell; local Y is the vertical axis of the handle.
 tool.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
 if is_rod:
  p=PERFORMANCE['rod'];cylinder(tool,p['radius'],p['length'],(0,0,p['length']/2))
 else:
  p=PERFORMANCE['mallet'];cylinder(tool,p['headRadius'],p['headLength'],(0,0,p['headLength']/2))
  cylinder(tool,p['handleRadius'],p['handleLength'],(0,-p['handleLength']/2,p['headLength']/2),(math.pi/2,0,0))
 for frame,distance,lift,visible in [(1,.3,.06,0),(2,.3,.06,1),(6,0,0,1),(12,.16,.025,1),(19,.3,.06,1),(20,.3,.06,0)]:
  tool.location=point+direction*distance+Vector((0,0,lift if not is_rod else 0))
  tool.scale=(visible,)*3
  tool.keyframe_insert(data_path='location',frame=frame);tool.keyframe_insert(data_path='scale',frame=frame)
 action=tool.animation_data.action;action.name=f'ToolDemo_{num:02d}';tool.animation_data.action=None
 track=tool.animation_data.nla_tracks.new();track.name=action.name
 strip=track.strips.new(action.name,1+(num-1)*20,action);strip.extrapolation='HOLD'
 tool.scale=(0,0,0)
s.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bells-interactive.blend'),compress=True)
print('REFERENCE_TOOL_DEMO_SAVED',len(rigs),flush=True)
