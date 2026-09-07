"""Decode shipped GLB textures and compare them with their intended sRGB palette.
Run with Python + Pillow. This checks colour transport, not browser lighting or likeness.
"""
from pathlib import Path
import json, struct, io
from PIL import Image, ImageStat

ROOT=Path(__file__).resolve().parents[1]
rows=[]
paths=[ROOT/'models/museum-architecture.glb']+sorted((ROOT/'models/galleries').glob('*.glb'))+sorted((ROOT/'models/public').glob('*.glb'))
for path in paths:
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
    assert all('uri' not in x for x in doc.get('images',[])+doc['buffers'])
    checked=[]
    for m in doc.get('materials',[]):
        extra=m.get('extras',{});reference=extra.get('reference_srgb')
        if not reference:continue
        pbr=m['pbrMetallicRoughness'];texture=doc['textures'][pbr['baseColorTexture']['index']]
        image=doc['images'][texture['source']];view=doc['bufferViews'][image['bufferView']]
        start=view.get('byteOffset',0)
        im=Image.open(io.BytesIO(binary[start:start+view['byteLength']])).convert('RGB')
        mean=ImageStat.Stat(im).mean;target=[int(reference[k:k+2],16) for k in [1,3,5]]
        error=max(abs(a-b) for a,b in zip(mean,target))
        assert error<10,(path.name,m['name'],mean,target)
        assert 'normalTexture' in m and 'metallicRoughnessTexture' in pbr,(path.name,m['name'],'missing surface maps')
        checked.append({'material':m['name'],'reference':reference,'mean_srgb':[round(v,2) for v in mean],'max_channel_error':round(error,2)})
    assert checked,(path,'no calibrated material maps')
    light_nodes=[x for x in doc.get('nodes',[]) if 'KHR_lights_punctual' in x.get('extensions',{})]
    assert light_nodes and all('web_intensity' in x.get('extras',{}) for x in light_nodes),(path,'light metadata')
    if path.parent.name=='galleries' or path.name=='museum-architecture.glb':
        assert any(x.get('extras',{}).get('roof') for x in doc['nodes']),(path,'roof cutaway lost')
    rows.append({'file':path.relative_to(ROOT).as_posix(),'materials':checked,'lights':len(light_nodes),'bytes':len(raw)})
    print('SPACE_COLOUR_OK',path.name,len(checked),'materials',len(light_nodes),'lights')

# Every old geometry and animation buffer remains byte-identical in corrected artifact GLBs.
repairs=json.loads((ROOT/'reports/space-10-artifact-colour-glb.json').read_text())
for r in repairs:
    path=ROOT/r['file'];old=ROOT/'backups/before-space-polish-10'/r['file']
    before=old.read_bytes();after=path.read_bytes()
    n0=struct.unpack_from('<I',before,12)[0];n1=struct.unpack_from('<I',after,12)[0]
    a=json.loads(before[20:20+n0]);b=json.loads(after[20:20+n1])
    assert after[28+n1:28+n1+len(before)-28-n0]==before[28+n0:],path
    for key in ['accessors','meshes','nodes','scenes','animations','skins']:
        assert a.get(key)==b.get(key),(path,key)

report={'spaces':rows,'artifact_files_with_preserved_geometry_and_animation':len(repairs),'scope':'Decoded albedo pixels, material maps, light metadata and structural bytes; no browser GPU/DOM or measured appearance certification'}
(ROOT/'reports/space-10-colour-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
