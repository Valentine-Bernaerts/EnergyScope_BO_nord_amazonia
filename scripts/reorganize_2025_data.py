from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1] / 'Data'
old = root / '2025'
old_reality = root / '2025_reality'
new_suff = old / 'sufficiency'
new_reality = old / 'reality'

new_suff.mkdir(parents=True, exist_ok=True)
new_reality.mkdir(parents=True, exist_ok=True)

print('Moving Data/2025 items to Data/2025/sufficiency...')
for item in sorted(old.iterdir(), key=lambda p: p.name):
    if item.name in {'sufficiency', 'reality'}:
        continue
    target = new_suff / item.name
    print(f'  {item.relative_to(root)} -> {target.relative_to(root)}')
    shutil.move(str(item), str(target))

print('Moving Data/2025_reality items to Data/2025/reality...')
for item in sorted(old_reality.iterdir(), key=lambda p: p.name):
    target = new_reality / item.name
    print(f'  {item.relative_to(root)} -> {target.relative_to(root)}')
    shutil.move(str(item), str(target))

if old_reality.exists() and not any(old_reality.iterdir()):
    old_reality.rmdir()
    print('Removed empty Data/2025_reality directory')

print('Done')
