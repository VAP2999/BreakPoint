"""Build a self-contained source download, excluding credentials and local runtime files."""
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
files=[root/name for name in ['README.md','package.json','playwright.config.js','.gitignore','.env.example']]
for folder,pattern in [('docs','*.md'),('.github/workflows','*.yml'),('worker','*.py'),('worker','*.txt'),('tests','*.py'),('tests','*.js'),('scripts','*.py'),('dist','*.html'),('dist','*.js')]:
    files.extend((root/folder).glob(pattern))
for folder in ['dist/runs','dist/policy-runs']:
    files.extend(p for p in (root/folder).rglob('*') if p.is_file())
with zipfile.ZipFile(root/'dist/worker-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        archive.write(path,str(Path('breakpoint')/path.relative_to(root)))
print('Source archive rebuilt')
