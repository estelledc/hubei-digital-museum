"""Correct QA-observed area-light reflections and exported UV names in saved galleries."""
import sys,bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build_full_museum import *
for g in GALLERIES:
    path=OUT/(g['id']+'.blend');bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);s=bpy.context.scene
    for o in s.objects:
        if o.type=='LIGHT' and o.data.type=='AREA':o.data.specular_factor=0
    if g['id'] in ['ceramics','liang','music','people']:
        ink=mat('浅墙深色说明','#5d5545',0,.84)
        for o in s.objects:
            if o.type=='FONT' and o.location.z>3:o.data.materials.clear();o.data.materials.append(ink)
    for o in s.objects:
        if o.type=='MESH' and any(m and '展柜低反射玻璃' in m.name for m in o.data.materials):o.visible_camera=False
    s.render.filepath=str(RENDERS/(g['id']+'.jpg'));s.view_settings.exposure=-.45
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    bpy.ops.render.render(write_still=True)
    export_gallery(g)
# Connection missing bench supports, and softbox reflections hide the glazing.
p=ROOT/'models/public/connection.blend';bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False);s=bpy.context.scene;c=bpy.data.collections.get('Public_connection');b=Builder(c)
m=mat('座椅支座灰','#767772',.4,.5)
if not any(o.name.startswith('休息座椅支座') for o in s.objects):
    for side in [-1,1]:
        for y in [-12,0,12]:
            for dy in [-.8,.8]:b.box('休息座椅支座',(side*4.5,y+dy,.19),(.5,.09,.38),m,.015)
for o in s.objects:
    if o.type=='LIGHT' and o.data.type=='AREA':o.data.specular_factor=0
for o in s.objects:
    if o.type=='MESH' and any(m and '展柜低反射玻璃' in m.name for m in o.data.materials):o.visible_camera=False
s.render.filepath=str(RENDERS/'connection.jpg');bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True);bpy.ops.render.render(write_still=True)
optimize_export(list(s.objects),ROOT/'models/public/connection.glb')

integrate()
