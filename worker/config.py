"""Minimal literal .env reader: two allowed keys, no shell evaluation."""
import os
from pathlib import Path


def load_env(path='.env'):
    file=Path(path)
    if not file.is_file(): return
    values={}
    for number,line in enumerate(file.read_text().splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'):continue
        key,sep,value=line.partition('=')
        if not sep or key.strip() not in {'OPENAI_API_KEY','OPENAI_MODEL'}:
            raise ValueError(f'Unsupported .env entry on line {number}')
        value=value.strip()
        if len(value)>=2 and value[0]==value[-1] and value[0] in {'"',"'"}:
            value=value[1:-1]
        values[key.strip()]=value
    for key,value in values.items():
        if value:os.environ.setdefault(key,value)
