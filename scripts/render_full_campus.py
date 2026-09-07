"""Render the current 0.4 campus; do not alter the editable source file."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/hubei-museum.blend'),load_ui=False)
s=bpy.context.scene
assert s.get('version')=='0.4'
s.camera=bpy.data.objects['01_园区鸟瞰']
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1440;s.render.resolution_y=960;s.render.resolution_percentage=100
s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=92
# Interior exhibits do not contribute to this exterior view. Keep them in the saved main file.
for o in s.objects:
    if o.get('gallery_id') or o.get('artifact_id'):o.hide_render=True
s.render.filepath=str(ROOT/'renders/galleries/campus.jpg')
bpy.ops.render.render(write_still=True)
print('CAMPUS_04_RENDERED',flush=True)
