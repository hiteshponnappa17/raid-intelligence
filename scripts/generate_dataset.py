import argparse
from prediction.synthetic_data import generate_synthetic_dataset
p=argparse.ArgumentParser(); p.add_argument("--rows",type=int,default=1200); p.add_argument("--output",default="data/sample_disk_data.csv"); a=p.parse_args()
generate_synthetic_dataset(a.rows).to_csv(a.output,index=False); print(f"Wrote dataset to {a.output}")
