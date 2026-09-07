"""Repair the confirmed legacy sRGB encoding error in saved artifact derivatives.

Blender runs this file with -- blends. Bundled Python with Pillow runs -- glb.
GLB geometry, UVs, hierarchy and animation bytes are preserved exactly.
"""
from pathlib import Path
import sys, json, shutil, struct, io, re

ROOT=Path(__file__).resolve().parents[1]
BACKUP=ROOT/'backups/before-space-polish-10'


def backup(p):
    target=BACKUP/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copy2(p,target)


def glb():
    from PIL import Image
    lut=[round((c/255*12.92 if c/255<=.0031308 else 1.055*(c/255)**(1/2.4)-.055)*255) for c in range(256)]
    records=[]
    for directory in ['artifacts','interactive']:
        for p in sorted((ROOT/'models'/directory).glob('*.glb')):
            raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n])
            binary=bytearray(raw[28+n:]);oldlen=len(binary);images=set();changed=[]
            for m in doc.get('materials',[]):
                extra=m.get('extras',{})
                if not str(extra.get('surface_accuracy','')).startswith('procedural micro-surface') or extra.get('albedo_encoding')=='srgb-byte-v1':continue
                texture=m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
                if not texture:continue
                image=doc['textures'][texture['index']]['source'];images.add(image);changed.append(m['name'])
                extra['albedo_encoding']='srgb-byte-v1'
            if not images:continue
            backup(p)
            for index in images:
                image=doc['images'][index];view=doc['bufferViews'][image['bufferView']]
                start=view.get('byteOffset',0);content=bytes(binary[start:start+view['byteLength']])
                im=Image.open(io.BytesIO(content)).convert('RGB').point(lut*3)
                output=io.BytesIO();im.save(output,format='PNG')
                while len(binary)%4:binary.append(0)
                image['bufferView']=len(doc['bufferViews']);image['mimeType']='image/png'
                doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(output.getvalue())})
                binary.extend(output.getvalue())
            # Old buffer ranges, including every accessor's source, remain untouched.
            assert bytes(binary[:oldlen])==raw[28+n:]
            doc['buffers'][0]['byteLength']=len(binary)
            while len(binary)%4:binary.append(0)
            payload=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
            payload+=b' '*((-len(payload))%4)
            result=struct.pack('<4sII',b'glTF',2,28+len(payload)+len(binary))+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary
            tmp=p.with_suffix('.glb.tmp');tmp.write_bytes(result);tmp.replace(p)
            public=ROOT/'web/public/models'/directory/p.name
            if public.parent.exists():shutil.copy2(p,public)
            records.append({'file':p.relative_to(ROOT).as_posix(),'materials':changed,'images':len(images),'geometry_and_animation_bytes_unchanged':True,'bytes':len(result)})
            print('REPAIRED_GLB',p.name,len(images),flush=True)
    (ROOT/'reports/space-10-artifact-colour-glb.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))


def blends():
    import bpy
    sys.path.insert(0,str(ROOT/'scripts'))
    from repair_procedural_colour import repair
    records=[]
    for directory in ['artifacts','interactive']:
        for p in sorted((ROOT/'models'/directory).glob('*.blend')):
            bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False)
            changes=repair(bpy.data.materials)
            if not changes:continue
            backup(p)
            scene=bpy.context.scene;scene['procedural_colour_revision']='srgb-byte-v1'
            for screen in bpy.data.screens:
                for a in screen.areas:
                    if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL'
            tmp=p.with_name(p.stem+'-colour10.blend')
            bpy.ops.wm.save_as_mainfile(filepath=str(tmp),compress=True);tmp.replace(p)
            records.append({'file':p.relative_to(ROOT).as_posix(),'repairs':changes})
            print('REPAIRED_BLEND',p.name,len(changes),flush=True)
    (ROOT/'reports/space-10-artifact-colour-blender.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))


if __name__=='__main__':
    if 'blends' in sys.argv:blends()
    elif 'glb' in sys.argv:glb()
    else:raise SystemExit('Choose blends or glb')
