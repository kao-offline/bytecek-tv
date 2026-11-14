"""Build install/source bundles without local caches or Git metadata."""
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
OUT.mkdir(exist_ok=True)
files = sorted(p for p in ROOT.rglob('*') if p.is_file() and not
    any(part in {'.git', 'dist', '__pycache__', '.venv', '.impeccable', '.claude'} for part in p.relative_to(ROOT).parts)
    and p.name != 'preview.png' and p.suffix not in {'.pyc', '.pyo'})
with tarfile.open(OUT / 'bytecek-tv.tar.gz', 'w:gz') as tar, zipfile.ZipFile(
        OUT / 'bytecek-tv-source.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for path in files:
        name = 'bytecek-tv/' + path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        info = tarfile.TarInfo(name)
        info.size = len(data)
        info.mode = 0o755 if path.suffix == '.sh' else 0o644
        tar.addfile(info, io.BytesIO(data))
        zipf.writestr(name, data)
checksums = []
for name in ('bytecek-tv.tar.gz', 'bytecek-tv-source.zip'):
    digest = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
    checksums.append(f'{digest}  {name}\n')
(OUT / 'SHA256SUMS').write_text(''.join(checksums), encoding='utf-8')
print(OUT)
