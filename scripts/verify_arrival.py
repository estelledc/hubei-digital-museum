"""Check saved foyer geometry and preservation of existing gallery contents."""
import json
from collections import Counter
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'reports/arrival-11-blender.json'

def content(scene):
    return {
        'galleries': dict(Counter(o.get('gallery_id') for o in scene.objects if o.get('gallery_id'))),
        'artifacts': dict(Counter(o.get('artifact_id') for o in scene.objects if o.get('artifact_id'))),
    }

def open_scene(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    return bpy.context.scene

baseline = content(open_scene(ROOT / 'backups/before-arrival-11/models/hubei-museum.blend'))
results = []
for name in ['public/arrival.blend', 'public/atrium.blend', 'campus-polished.blend', 'hubei-museum.blend']:
    scene = open_scene(ROOT / 'models' / name)
    assert scene.get('arrival_revision') == '0.11', name
    floors = [o for o in scene.objects if o.get('arrival_opening_radius')]
    assert len(floors) == 1, (name, len(floors))
    floor = floors[0]
    inverse = floor.matrix_world.inverted()
    # Test the actual evaluated floor mesh, independently of its metadata.
    floor_eval = floor.evaluated_get(bpy.context.evaluated_depsgraph_get())
    hits = {}
    for label, point, expected in [
        ('round_opening', (0, -2, .8), False),
        ('landing', (12, 0, .8), True),
        ('west_escalator', (-27, 3, .8), False),
        ('east_escalator', (27, 3, .8), False),
    ]:
        hit, loc, normal, index = floor_eval.ray_cast(inverse @ Vector(point), Vector((0, 0, -1)))
        assert hit == expected, (name, label, hit)
        hits[label] = hit
    for prefix in ['11_弧形夹胶玻璃', '11_连续深色扶手', '11_灯幕暗蓝底盘', '11_咨询台石材柜身', '11_自助导览终端']:
        assert any(o.name.startswith(prefix) for o in scene.objects), (name, prefix)
    assert not any(o.name.startswith('入口咨询台') for o in scene.objects), name
    if name.startswith('public/'):
        assert len([o for o in scene.objects if o.type == 'LIGHT' and 'web_intensity' in o]) == 8
        for camera in ['11_arrival', '11_service', '11_lower']:
            assert camera in scene.objects
    if name == 'hubei-museum.blend':
        assert content(scene) == baseline, 'Existing gallery or artifact membership changed'
        assert len(baseline['galleries']) == 11
    unpacked = [i.name for i in bpy.data.images if i.source == 'FILE' and i.users and not i.packed_file and not i.packed_files]
    assert not unpacked, (name, unpacked)
    results.append({'file': name, 'objects': len(scene.objects), 'floor_ray_hits': hits, 'referenced_images_packed': True, 'camera': scene.camera.name if scene.camera else None})
    print('PASS', name, flush=True)

RESULT.write_text(json.dumps({'results': results, 'preserved_contents': baseline, 'scope': 'Saved Blender geometry, camera presence, packed images and existing gallery/artifact membership; not survey or browser rendering validation'}, ensure_ascii=False, indent=2))
print('ARRIVAL11_VERIFIED', flush=True)
