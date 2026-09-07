"""Read back the exported chimes, where the old GLB silently defaulted to white."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'models/artifacts/chimes.glb'))
records=[]
for material in bpy.data.materials:
 if not material.name.startswith('CQ_Stone_'):continue
 bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 socket=bsdf.inputs['Base Color'];assert socket.is_linked,material.name
 node=socket.links[0].from_node
 assert node.type=='TEX_IMAGE' and node.image,material.name
 image=node.image;w,h=image.size;assert w==1024 and h==1024
 samples=[]
 for fy in [.2,.4,.6,.8]:
  for fx in [.2,.4,.6,.8]:
   p=4*(int(h*fy)*w+int(w*fx));samples.append(list(image.pixels[p:p+3]))
 mean=[sum(p[c] for p in samples)/len(samples) for c in range(3)]
 assert max(mean)<.8 and min(mean)>.005,(material.name,mean)
 records.append({'material':material.name,'gltf_texture_readback':True,'sample_mean_image_buffer_rgb':mean,'image_color_space':image.colorspace_settings.name,'default_white':False})
assert len(records)==4
(root/'reports/export-colour-readback.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps(records,ensure_ascii=False),flush=True)
