"""End-to-end acceptance checks against a running controlled fixture."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-url', default='http://localhost:8000')
    p.add_argument('--fixture-directory')
    p.add_argument('--output', default='artifacts/acceptance')
    args=p.parse_args()
    reports=[]
    for mode, expected in [('buggy','confirmed'),('fixed','passed')]:
        extra=['--fixture-directory',args.fixture_directory] if args.fixture_directory else []
        proc=subprocess.run([sys.executable,'-m','worker.run','--base-url',args.base_url,'--mode',mode,'--output',args.output]+extra,capture_output=True,text=True,timeout=100)
        if proc.returncode:
            raise RuntimeError(proc.stdout+proc.stderr)
        path=Path(json.loads(proc.stdout)['report'])
        report=json.loads(path.read_text())
        assert report['verdict']==expected, report
        first,replay=(report['phases'][n] for n in ['exploration','replay'])
        assert first['context_id']!=replay['context_id']
        for phase in [first,replay]:
            assert phase['initial']['quantity']==1
            assert phase['final']['quantity']==0
            assert len(phase['screenshots'])==2
            for artifact in phase['screenshots']+[phase['trace']]:
                assert (path.parent/artifact).stat().st_size>0
        regression=subprocess.run([sys.executable,str(path.parent/'regression.py')],capture_output=True,text=True,timeout=30,env={**os.environ, **({'BREAKPOINT_FIXTURE_DIR':str(Path(args.fixture_directory).resolve())} if args.fixture_directory else {})})
        if mode=='buggy':
            assert regression.returncode!=0 and 'AssertionError' in regression.stderr, regression.stderr
        else:
            assert regression.returncode==0, regression.stderr
        reports.append({'fixture':mode,'verdict':expected,'report':str(path),'regression':'expected assertion failure' if mode=='buggy' else 'pass'})
    print(json.dumps({'acceptance':'passed','runs':reports},indent=2))

if __name__=='__main__':main()
