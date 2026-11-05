from pathlib import Path
import sys,shutil
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
from test_structure import StructureTests
from astar_app.storage import atomic_json
fixture=StructureTests();fixture.setUp()
try:
    target=root/'test-results/structure-library'/('a'*32)
    shutil.copytree(fixture.directory,target,dirs_exist_ok=True)
    shutil.copy2(fixture.source,target/'source.pdf')
    atomic_json(target/'course.json',fixture.course)
    print(target)
finally:fixture.tearDown()
