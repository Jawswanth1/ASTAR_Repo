from pathlib import Path
import sys,json,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astar_app.storage import portable_course,install_portable,atomic_json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'benchmarks/representative-book'
COURSE=OUT/'11111111111111111111111111111111'
package=portable_course(COURSE)
payload=json.dumps(package,ensure_ascii=False)
(OUT/'textbook.astar.json').write_text(payload,encoding='utf-8')
with tempfile.TemporaryDirectory(dir=OUT) as tmp:
    assert Path(tmp).resolve().is_relative_to(ROOT)
    installed=install_portable(json.loads(payload),Path(tmp))
    assert installed['structure']['evidenceHash']==package['structure']['evidenceHash']
    assert installed['structure']['objects']==package['structure']['objects']
    assert len(installed['structure']['evidence']['pages'])==374
result=dict(passed=True,sourcePages=374,embeddedImages=len(package['assets']),packageBytes=len(payload.encode('utf-8')),objectCount=len(package['structure']['objects']),checks=['full-book export','all referenced PNGs decoded and verified on import','source evidence hash unchanged','all structured objects and relationships unchanged'])
atomic_json(OUT/'package-validation.json',result)
print(json.dumps(result))
