"""Create public GLB derivatives without redistributing restricted photographs.

Usage: python3 scripts/package_public_models.py PATH_TO_LOCAL_PROJECT
Geometry, animation accessors and the object hierarchy are copied byte for byte.
Only listed image buffer views and local-path metadata are replaced.
"""
from pathlib import Path
import gzip, json, re, struct, sys, zlib
ROOT = Path(__file__).resolve().parents[1]
COLORS = json.loads((ROOT / 'scripts/public-materials.json').read_text())

def clean(value):
    if isinstance(value, dict): return {k:clean(v) for k,v in value.items()}
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, str):
        return re.sub(r'(?:/Users/|/var/folders/|/private/var/)[^\s"\n]*', '[local research path omitted]', value)
    return value

def solid_png(rgb):
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    # Explicit approximate material, not a reconstruction of the photograph.
    encoded=[12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055 for x in rgb]
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+bytes(round(x*255) for x in encoded)))+chunk(b'IEND',b'')

def sanitize(raw):
    n=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+n]); binary=raw[28+n:]
    replacement={}; changed=[]
    for im in doc.get('images',[]):
        name=im.get('name','')
        if name in COLORS:
            replacement[im['bufferView']]=solid_png(COLORS[name])
            im['mimeType']='image/png'; im['name']='Public approximate material: '+name
            im['extras']={'public_material':'Solid approximate color; reference photograph not distributed'}
            changed.append(name)
    packed=bytearray()
    for i,view in enumerate(doc.get('bufferViews',[])):
        old=view.get('byteOffset',0); length=view['byteLength']
        payload=replacement.get(i,binary[old:old+length])
        packed.extend(b'\0'*((-len(packed))%4)); view['byteOffset']=len(packed);view['byteLength']=len(payload)
        packed.extend(payload)
    packed.extend(b'\0'*((-len(packed))%4));doc['buffers'][0]['byteLength']=len(packed)
    doc=clean(doc);doc['asset']['copyright']='See research/fidelity-credits.md and RIGHTS.md. Non-official approximate reconstruction.'
    header=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();header+=b' '*((-len(header))%4)
    result=struct.pack('<4sII',b'glTF',2,28+len(header)+len(packed))+struct.pack('<I4s',len(header),b'JSON')+header+struct.pack('<I4s',len(packed),b'BIN\0')+packed
    return result,changed

if __name__=='__main__':
    source=Path(sys.argv[1])/'web/public/models'; out=ROOT/'web/public/models'; report=[]
    paths=[source/'museum-architecture.glb',*sorted((source/'public').glob('*.glb')),*sorted((source/'galleries').glob('*.glb')),*sorted((source/'interactive').glob('*.glb'))]
    for path in paths:
        dest=out/(str(path.relative_to(source))+'.gz');dest.parent.mkdir(parents=True,exist_ok=True)
        result,changed=sanitize(path.read_bytes()); compressed=gzip.compress(result,compresslevel=9,mtime=0);dest.write_bytes(compressed)
        report.append({'file':str(dest.relative_to(ROOT)), 'original_bytes':path.stat().st_size,'public_glb_bytes':len(result),'download_bytes':len(compressed),'replaced_photographs':changed})
        print(path.relative_to(source),round(len(compressed)/2**20,2),'MiB',flush=True)
    (ROOT/'reports/public-assets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
