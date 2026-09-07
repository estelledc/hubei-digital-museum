"""Sanitize a local Blender project into an independently editable public copy.
blender -b --python scripts/prepare_blender_release.py -- /path/to/project
"""
from pathlib import Path
import json, re, sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
COLORS=json.loads((ROOT/'scripts/public-materials.json').read_text())
SOURCE=Path(sys.argv[sys.argv.index('--')+1])
OUTPUT=ROOT/'.release';OUTPUT.mkdir(exist_ok=True)

def base_name(name): return re.sub(r'\.(?:jpg|jpeg|png)$','',re.sub(r'\.\d{3}$','',name))
def sanitize(source,destination):
    bpy.ops.wm.open_mainfile(filepath=str(source))
    changed=[]
    for im in list(bpy.data.images):
        name=base_name(im.name)
        if name in COLORS:
            replacement=bpy.data.images.new('Public approximate material: '+name,width=1,height=1,alpha=False)
            rgb=COLORS[name]; encoded=[12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055 for x in rgb]
            replacement.pixels[:]=[*encoded,1];replacement.pack();im.user_remap(replacement)
            bpy.data.images.remove(im);changed.append(name)
    # Convert labels to geometry and remove all embedded system font binaries.
    for obj in list(bpy.context.scene.objects):
        if obj.type=='FONT':
            bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
            bpy.ops.object.convert(target='MESH')
    bpy.data.batch_remove(ids=[f for f in bpy.data.fonts if f.name!='Bfont'])
    bpy.data.batch_remove(ids=list(bpy.data.texts))
    for collection in [bpy.data.objects,bpy.data.scenes,bpy.data.materials,bpy.data.images,bpy.data.collections,bpy.data.actions]:
        for block in collection:
            for key in list(block.keys()):
                value=block[key]
                if isinstance(value,str):
                    block[key]=re.sub(r'(?:/Users/|/var/folders/|/private/var/)[^\s"\n]*','[local research path omitted]',value)
    for block in bpy.data.user_map():
        if block.library_weak_reference:
            block.library_weak_reference.filepath='//sources/'+Path(block.library_weak_reference.filepath).name
    for im in bpy.data.images:
        if im.packed_file:
            im.filepath='//textures/'+im.name
            for packed in im.packed_files: packed.filepath=im.filepath
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type=='FILE_BROWSER' and space.params:
                    space.params.directory=b'//'
                    space.params.filename=''

    for scene in bpy.data.scenes:
        scene.render.filepath='//renders/public-preview.jpg'
        scene['public_release']='0.13; restricted reference photos replaced by approximate colors; see RIGHTS.md'
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
    return {'file':destination.name,'objects':len(bpy.context.scene.objects),'replaced_images':sorted(set(changed)),'bytes':destination.stat().st_size,'fonts':len(bpy.data.fonts),'text_blocks':len(bpy.data.texts)}

reports=[sanitize(SOURCE/'models/hubei-museum.blend',OUTPUT/'hubei-museum-public.blend')]
for slug in ['bells','chimes','zun','sword','drum','bamboo','vase','ding-jian','gold-liang','pottery-bell','carving-wudang','drum-chongyang','jade-shijiahe','manuscript-xiong','medal-lizuodong','office-dong']:
    source=SOURCE/'models/interactive'/(slug+'-interactive.blend')
    if source.exists(): reports.append(sanitize(source,OUTPUT/(slug+'-interactive.blend')))
(ROOT/'reports/public-blender.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
print('PUBLIC_BLENDER_COMPLETE',len(reports),flush=True)
