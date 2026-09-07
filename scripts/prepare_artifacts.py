"""Create centered, editable copies and smaller GLBs from the supplied archive."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from material_export import bake_base_colors

archive, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
output.mkdir(parents=True, exist_ok=True)
report = []
for slug, title in [('bells', '曾侯乙编钟'), ('chimes', '曾侯乙编磬')]:
    bpy.ops.wm.open_mainfile(filepath=str(archive / 'models/blend' / (title + '_考据校正版.blend')), load_ui=False)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.update()
    worlds = {o: o.matrix_world.copy() for o in meshes}
    points = [worlds[o] @ Vector(v) for o in meshes for v in o.bound_box]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for obj in meshes:
        world = worlds[obj]
        obj.parent = None
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.data = obj.data.copy()
        obj.data.transform(Matrix.Translation(-offset) @ world)
        obj.matrix_world = Matrix.Identity(4)
    for obj in meshes:
        obj.name = slug + '_' + obj.name
        obj['provenance'] = 'user_supplied_archive_2026-07-28'
        obj['accuracy'] = 'archive_corrected_not_a_scan'
    for obj in list(bpy.context.scene.objects):
        if obj not in meshes: bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1
    bpy.context.scene['artifact_title'] = title
    bpy.context.scene['source_archive'] = archive.name
    # The modern red cloth is a property of the source display, not the bells.
    # Museum catalogue photographs show a neutral taupe floor beneath the set.
    if slug == 'bells':
        cloth=bpy.data.materials.get('BuWen')
        if cloth:
            p=next(n for n in cloth.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            for link in list(p.inputs['Base Color'].links):cloth.node_tree.links.remove(link)
            p.inputs['Base Color'].default_value=(.16,.135,.105,1)
            p.inputs['Roughness'].default_value=.9
            cloth['colour_reference']='hbww.org.cn/zgzb/p/4695.html; display-floor approximation'
    baked=bake_base_colors(list(bpy.data.materials),2048)
    bpy.context.view_layer.update()
    actual = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
    dimensions = [max(p[i] for p in actual) - min(p[i] for p in actual) for i in range(3)]
    assert all(abs(dimensions[i] - (hi-lo)[i]) < 0.002 for i in range(3)), dimensions
    assert max(dimensions) < 12, dimensions
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / (slug + '.blend')), compress=True)
    before = sum(len(o.data.polygons) for o in meshes)
    for obj in meshes:
        if len(obj.data.polygons) > 6000:
            bpy.context.view_layer.objects.active = obj
            mod = obj.modifiers.new('Web viewing copy', 'DECIMATE')
            mod.ratio = 0.22 if slug == 'bells' else 0.85
            bpy.ops.object.modifier_apply(modifier=mod.name)
    for im in bpy.data.images:
        if im.source == 'FILE' and im.has_data and max(im.size) > 2048:
            factor = 2048 / max(im.size)
            im.scale(max(1, int(im.size[0] * factor)), max(1, int(im.size[1] * factor)))
    bpy.ops.export_scene.gltf(filepath=str(output / (slug + '.glb')), export_format='GLB',
                              export_yup=True, export_extras=True, export_cameras=False,
                              export_lights=False, export_image_format='AUTO')
    report.append({'id': slug, 'title': title, 'high_detail_polygons': before,
                   'web_polygons': sum(len(o.data.polygons) for o in meshes),
                   'dimensions_m': list(hi - lo), 'original_archive_modified': False})
    report[-1]['baked_base_colors']=baked
    print('PREPARED', slug, flush=True)
(output / 'preparation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
