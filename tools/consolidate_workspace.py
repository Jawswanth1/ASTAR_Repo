"""One-time, checked consolidation; exact duplicate removals recorded in JSON."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parents[1]
log=[]
def safe(p):
    p=p.resolve()
    if not p.is_relative_to(WORK) or p==WORK or p==ROOT:raise ValueError(str(p))
    return p
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for old,new in [('ASTAR','collection'),('ASTAR-Finals','finals'),('ASTAR_LAUNCH','launch-incomplete')]:
    source=safe(WORK/old); target=safe(ROOT/'creative'/new)
    if source.exists():
        if target.exists():raise ValueError(f'Target exists: {target}')
        target.parent.mkdir(exist_ok=True)
        shutil.move(str(source),str(target));log.append(dict(action='move',source=str(source),target=str(target)))
# Remove copied application files only when byte-identical to the active app.
snapshot=ROOT/'creative/launch-incomplete/SOFTWARE/Application'
if snapshot.exists():
    for f in list(snapshot.rglob('*')):
        if not f.is_file():continue
        active=ROOT/f.relative_to(snapshot)
        if active.is_file() and digest(f)==digest(active):
            log.append(dict(action='remove-identical-copy',path=str(f),retained=str(active),sha256=digest(f)))
            safe(f).unlink()
# Keep the old packaged archive only if it contains unique files.
archive=safe(WORK/'ASTAR-Finals-Package.zip')
if archive.exists():
    with zipfile.ZipFile(archive) as z:
        entries=[i for i in z.infolist() if not i.is_dir()]
        identical=all((ROOT/'creative/finals'/Path(i.filename).relative_to('ASTAR-Finals')).is_file() and
            hashlib.sha256(z.read(i)).hexdigest()==digest(ROOT/'creative/finals'/Path(i.filename).relative_to('ASTAR-Finals')) for i in entries)
    if identical:
        log.append(dict(action='remove-verified-duplicate-zip',path=str(archive),entries=len(entries)))
        archive.unlink()
    else:
        target=ROOT/'creative/ASTAR-Finals-Package.zip';shutil.move(str(archive),str(target));log.append(dict(action='move-unique-archive',target=str(target)))
# Eliminate byte-identical historical offline reader copies, retaining explicit pointers.
retained={}
for folder in [ROOT/'creative/collection',ROOT/'creative/finals']:
    for f in folder.rglob('*.html'):
        h=digest(f)
        if h in retained:
            target=retained[h]
            log.append(dict(action='remove-identical-reader',path=str(f),retained=str(target),sha256=h))
            safe(f).unlink()
            f.with_suffix('.location.txt').write_text(f'Identical reader retained at: {target.relative_to(ROOT)}\n',encoding='utf-8')
        else:retained[h]=f
(ROOT/'ORGANIZATION_LOG.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
print(f'Consolidated ASTAR; {len(log)} recorded operations. Unique historical material preserved.')
