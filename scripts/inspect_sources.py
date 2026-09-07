"""Read the supplied Blender archive without saving into it."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
source_root, output = map(Path, args)
rows = []
for path in sorted((source_root / 'models' / 'blend').glob('*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(p) for o in objects for p in o.bound_box]
    rows.append({
        'file': path.name, 'blender_version': bpy.app.version_string,
        'mesh_objects': len(objects),
        'vertices': sum(len(o.data.vertices) for o in objects),
        'polygons': sum(len(o.data.polygons) for o in objects),
        'unit_scale': bpy.context.scene.unit_settings.scale_length,
        'bounds': {'min': [min(p[i] for p in pts) for i in range(3)],
                   'max': [max(p[i] for p in pts) for i in range(3)]},
        'file_images': [{'name': im.name, 'size': list(im.size),
                         'packed': bool(im.packed_file), 'has_data': im.has_data}
                        for im in bpy.data.images if im.source == 'FILE'],
        'materials': len(bpy.data.materials),
        'scene_properties': {k: str(v) for k, v in bpy.context.scene.items()},
        'largest_meshes': [{'name': o.name, 'vertices': len(o.data.vertices),
                            'dimensions': list(o.dimensions),
                            'location': list(o.location)}
                           for o in sorted(objects, key=lambda o: len(o.data.vertices), reverse=True)[:18]],
    })
    print('INSPECTED', path.name, len(objects), flush=True)
output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print('REPORT', output, flush=True)
