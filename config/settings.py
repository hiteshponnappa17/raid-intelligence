from pathlib import Path
import os
BASE_DIR=Path(__file__).resolve().parents[1]
DATA_DIR=BASE_DIR/'data'; MODEL_DIR=BASE_DIR/'models'
DATA_DIR.mkdir(exist_ok=True); MODEL_DIR.mkdir(exist_ok=True)
DB_PATH=Path(os.getenv('RAID_DB_PATH',str(DATA_DIR/'raid_simulator.db')))
if not DB_PATH.is_absolute(): DB_PATH=BASE_DIR/DB_PATH
