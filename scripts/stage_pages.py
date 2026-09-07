"""Package the static Vite output and verify GitHub Pages asset references."""
from pathlib import Path
import os, re, shutil
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'web/dist/client';out=ROOT/'.pages'
base=os.environ.get('MUSEUM_BASE_PATH','/hubei-digital-museum').rstrip('/')
assert (source/'index.html').is_file(), 'Static index.html missing; do not publish an empty export'
if out.exists():shutil.rmtree(out)
shutil.copytree(source,out)
if base and (out/base.lstrip('/')).is_dir():
    nested=out/base.lstrip('/')
    for p in nested.iterdir():
        target=out/p.name
        assert not target.exists(),f'Duplicate generated output: {p.name}'
        shutil.move(str(p),target)
    nested.rmdir()
(out/'.nojekyll').touch()
html=(out/'index.html').read_text()
for ref in re.findall(r'(?:href|src)="([^"#]+)"',html):
    if ref.startswith(base+'/'):
        local=ref[len(base)+1:].split('?')[0]
        if local: assert (out/local).exists(),f'Missing static resource: {ref}'
assert sum(f.stat().st_size for f in out.rglob('*') if f.is_file())<1_000_000_000
print('Pages artifact ready:',len(list(out.rglob('*'))),'entries')
