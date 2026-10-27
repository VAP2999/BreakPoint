"""Offline policy integration acceptance. Never makes model API requests."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    results=[]
    for mode,steps,expected in [('buggy',8,'confirmed'),('fixed',8,'passed'),('buggy',1,'inconclusive')]:
        run=subprocess.run([sys.executable,'-m','worker.run','--provider','offline','--fixture-directory','dist','--mode',mode,'--max-steps',str(steps),'--output','artifacts/policy'],capture_output=True,text=True,timeout=100)
        assert run.returncode==0,run.stdout+run.stderr
        path=Path(json.loads(run.stdout)['report'])
        report=json.loads(path.read_text())
        assert report['verdict']==expected,report
        assert report['autonomous_discovery'] is False
        assert report['policy']['api_requests']==0
        first,second=(report['phases'][p] for p in ['exploration','replay'])
        assert first['context_id']!=second['context_id']
        assert [a['action'] for a in second['actions']]==report['actions']
        assert len(first['actions'])<=steps
        for decision in first['decisions']:
            assert set(decision['observation'])=={'quantity','total_cents','displayed_total','enabled_buttons'}
        if expected in ['confirmed','passed']:
            exported=subprocess.run([sys.executable,str(path.parent/'regression.py')],capture_output=True,text=True,timeout=30)
            assert (exported.returncode==0)==(expected=='passed')
            if expected=='confirmed':assert 'AssertionError' in exported.stderr
        results.append({'mode':mode,'max_steps':steps,'verdict':expected,'report':str(path)})
    env={**os.environ,'OPENAI_API_KEY':''}
    missing=subprocess.run([sys.executable,'-m','worker.run','--provider','openai','--model','test-model'],env=env,capture_output=True,text=True)
    assert missing.returncode==2 and 'no offline fallback' in missing.stderr
    print(json.dumps({'acceptance':'passed','live_model_tested':False,'runs':results},indent=2))

if __name__=='__main__':main()
