import bpy,json
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'models/artifacts/bells.glb'))
rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 me=o.data;parent=list(range(len(me.vertices)))
 def root(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 seen={}
 for v in me.vertices:
  key=tuple(round(x,5) for x in v.co)
  if key in seen:parent[root(v.index)]=root(seen[key])
  else:seen[key]=v.index
 for e in me.edges:
  a,b=map(root,e.vertices)
  if a!=b:parent[b]=a
 groups=defaultdict(list)
 for v in me.vertices:groups[root(v.index)].append(v.index)
 chunks=[]
 for vs in groups.values():
  ps=[o.matrix_world@me.vertices[v].co for v in vs];lo=Vector([min(p[i] for p in ps) for i in range(3)]);hi=Vector([max(p[i] for p in ps) for i in range(3)])
  chunks.append({'vertices':len(vs),'center':list((lo+hi)*.5),'size':list(hi-lo)})
 chunks.sort(key=lambda c:-c['vertices'])
 rows.append({'name':o.name,'verts':len(me.vertices),'components':len(chunks),'largest':chunks[:90]})
(ROOT/'reports/bell-components.json').write_text(json.dumps(rows,indent=2))
for r in rows:print(r['name'],r['verts'],r['components'],r['largest'][:3],flush=True)
