"""Export one run to the local demo viewer: python -m worker.export PATH/report.json."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile


def export(report_path, destination=Path('dist/live-run')):
    report_path=Path(report_path).resolve()
    root=report_path.parent
    report=json.loads(report_path.read_text())
    if report.get('schema_version') != 1 or 'verdict' not in report:
        raise ValueError('Unsupported report')
    files={'report.json','actions.json'}
    if report.get('regression'):files.add(report['regression'])
    for name,phase in report.get('phases',{}).items():
        if name not in {'exploration','replay'}:raise ValueError('Unknown phase')
        files.add(name+'/events.json')
        files.update(phase.get('screenshots',[]))
        if phase.get('trace'):files.add(phase['trace'])
    checked=[]
    for item in files:
        if not isinstance(item,str) or Path(item).is_absolute() or '..' in Path(item).parts:
            raise ValueError('Unsafe artifact path')
        src=(root/item).resolve()
        if not src.is_relative_to(root) or not src.is_file():
            raise ValueError('Missing or unsafe artifact')
        checked.append((src,item))
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        temp=Path(staging)/'run';temp.mkdir()
        for src,name in checked:
            target=temp/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,target)
        if destination.exists():shutil.rmtree(destination)
        shutil.move(str(temp),destination)
    return report['verdict']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    try:
        result=export(args.report)
    except (ValueError,OSError) as exc:
        parser.exit(2,f'Export failed: {exc}\n')
    print(f'Exported {result}. Start the local static server and open /report.html')

if __name__=='__main__':main()
