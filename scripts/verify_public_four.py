"""Check saved public geometry and preserved gallery meshes, independent of renders."""
import json
from collections import defaultdict
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]

def open_scene(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    return bpy.context.scene

def contents(scene):
    result = {}
    for key in ['gallery_id', 'artifact_id']:
        entries = defaultdict(lambda: {'objects': 0, 'vertices': 0, 'polygons': 0, 'bounds': [float('inf')] * 3 + [float('-inf')] * 3})
        for obj in scene.objects:
            value = obj.get(key)
            if not value:
                continue
            row = entries[value]
            row['objects'] += 1
            if obj.type == 'MESH':
                row['vertices'] += len(obj.data.vertices)
                row['polygons'] += len(obj.data.polygons)
                for corner in obj.bound_box:
                    point = obj.matrix_world @ Vector(corner)
                    for axis in range(3):
                        row['bounds'][axis] = min(row['bounds'][axis], point[axis])
                        row['bounds'][axis + 3] = max(row['bounds'][axis + 3], point[axis])
        for row in entries.values():
            row['bounds'] = [round(v, 3) for v in row['bounds']]
        result[key] = dict(entries)
    return result

baseline = contents(open_scene(ROOT / 'backups/before-public-12/models/hubei-museum.blend'))
results = []
for name in ['public/arrival.blend', 'public/atrium.blend', 'public/connection.blend', 'campus-polished.blend', 'hubei-museum.blend']:
    scene = open_scene(ROOT / 'models' / name)
    assert scene.get('public_revision') == '0.12', name
    row = {'file': name, 'objects': len(scene.objects)}
    if name != 'public/connection.blend':
        floors = [o for o in scene.objects if o.get('arrival_opening_radius')]
        assert len(floors) == 1, (name, len(floors))
        floor = floors[0]
        inverse = floor.matrix_world.inverted()
        evaluated = floor.evaluated_get(bpy.context.evaluated_depsgraph_get())
        hits = {}
        for label, point, expected in [('round_opening', (0, -2, .8), False), ('landing', (12, 0, .8), True), ('west_escalator', (-27, 3, .8), False), ('east_escalator', (27, 3, .8), False)]:
            hit, *_ = evaluated.ray_cast(inverse @ Vector(point), Vector((0, 0, -1)))
            assert hit == expected, (name, label, hit)
            hits[label] = hit
        row['floor_ray_hits'] = hits
        rails = [o for o in scene.objects if o.name.startswith(('环廊栏板', '四层环廊玻璃护栏'))]
        assert rails, name
        for obj in rails:
            assert obj.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value > .85, (name, obj.name)
        skylights = [o for o in scene.objects if o.name.startswith('中庭玻璃顶')]
        roof_z = min((o.matrix_world @ Vector(v)).z for o in skylights for v in o.bound_box)
        assert roof_z > 27, (name, roof_z)
        assert len([o for o in scene.objects if o.name.startswith('12_树冠连续分叉')]) == 8, name
        assert len([o for o in scene.objects if o.name.startswith('12_旋梯四分之一圈平台')]) == 6, name
        row.update({'glass_balustrades': len(rails), 'skylight_bottom_z': roof_z, 'highest_floor_z': 20.4})
    if name in ['campus-polished.blend', 'hubei-museum.blend']:
        assert not any(o.get('context_only') for o in scene.objects), name
        bridge_floors = [o for o in scene.objects if o.name.startswith('12_连廊承重楼板')]
        levels = sorted(round(o.matrix_world.translation.z, 2) for o in bridge_floors)
        assert len(levels) == 2 and abs(levels[1] - levels[0] - 6.8) < .01, (name, levels)
        row['connection_floor_centres'] = levels
    if name == 'hubei-museum.blend':
        assert contents(scene) == baseline, 'Gallery or artifact meshes or placement bounds changed'
        assert len(baseline['gallery_id']) == 11
        row['existing_gallery_and_artifact_mesh_counts'] = 'preserved'
    unpacked = [i.name for i in bpy.data.images if i.source == 'FILE' and i.users and not i.packed_file and not i.packed_files]
    assert not unpacked, (name, unpacked)
    row['referenced_images_packed'] = True
    results.append(row)
    print('PASS', name, flush=True)

(ROOT / 'reports/public-12-blender.json').write_text(json.dumps({'results': results, 'preserved_contents': baseline, 'scope': 'Saved meshes, glass materials, roof headroom, openings, bridge levels and packed images; not survey or browser rendering verification'}, ensure_ascii=False, indent=2))
print('PUBLIC12_VERIFIED', flush=True)
