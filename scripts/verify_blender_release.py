"""Reopen public Blender files and verify photo/font removal and model presence."""
from pathlib import Path
import json,re
import bpy
ROOT=Path(__file__).resolve().parents[1]
restricted=json.loads((ROOT/'scripts/public-materials.json').read_text())
results=[]
for path in sorted((ROOT/'.release').glob('*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    assert len(bpy.context.scene.objects)>0
    for image in bpy.data.images:
        name=re.sub(r'\.(?:jpg|jpeg|png)$','',re.sub(r'\.\d{3}$','',image.name))
        assert name not in restricted,(path.name,name)
        if image.source=='FILE': assert image.packed_file,(path.name,name,'unpacked image')
    assert not bpy.data.texts
    assert all(f.name=='Bfont' for f in bpy.data.fonts)
    if path.name=='hubei-museum-public.blend': assert len(bpy.context.scene.objects)==14404
    if path.name=='bells-interactive.blend':
        assert sum(a.name.startswith('Strike_') for a in bpy.data.actions)==65
        assert sum(a.name.startswith('ToolDemo_') for a in bpy.data.actions)==65
    results.append({'file':path.name,'objects':len(bpy.context.scene.objects),'actions':len(bpy.data.actions),'images':len(bpy.data.images),'restricted_images':0,'embedded_system_fonts':0})
(ROOT/'reports/blender-release-verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('PASS reopened public Blender files',len(results))
