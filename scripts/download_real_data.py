"""Fetch PUBLIC Kaggle data into data/real, leaving synthetic demo data untouched.
Requires internet access, `pip install kagglehub>=1.0.3`, and acceptance
of any dataset-specific access terms. Not run in this artifact environment.
"""
from pathlib import Path
import sys
try:
    import kagglehub
except ImportError:
    sys.exit('Install the downloader first: python -m pip install "kagglehub>=1.0.3"')
BASE=Path(__file__).resolve().parents[1]
DEST=BASE/'data/real'
DEST.mkdir(exist_ok=True)
try:
    folder=Path(kagglehub.dataset_download('olistbr/brazilian-ecommerce',output_dir=str(DEST)))
except Exception as exc:
    sys.exit(f'Download failed: {exc}\nUse the source link in README to download manually.')
missing=[]
for name in ['olist_orders_dataset.csv', 'olist_customers_dataset.csv']:
    matches=list(DEST.rglob(name))
    if not matches and folder.exists(): matches=list(folder.rglob(name))
    if not matches:missing.append(name)
    else: print(f'Found {name}: {matches[0]}')
if missing:
    sys.exit('Missing expected files: '+', '.join(missing)+'; check dataset contents in '+str(DEST))
print('Real data ready. From this project folder, run:')
print('python scripts/analyze.py --orders data/real/olist_orders_dataset.csv --customers data/real/olist_customers_dataset.csv')
