from prediction.risk_engine import score_features
from prediction.synthetic_data import generate_synthetic_dataset
from prediction.ml_model import train_model
def test_score_bounds():
 f=dict(temperature_c=32,reallocated_sectors=0,pending_sectors=0,uncorrectable_errors=0,read_error_count=0,write_error_count=0,power_on_hours=1000,latency_ms=2)
 assert 0<=score_features(f)["risk_score"]<=100
def test_reproducible(): assert generate_synthetic_dataset(50).equals(generate_synthetic_dataset(50))
def test_train(): assert train_model(generate_synthetic_dataset(250))[1]["test_records"]>0
