import numpy as np
import pandas as pd
from prediction.feature_engineering import FEATURES
def generate_synthetic_dataset(n=1200,seed=42):
    r=np.random.default_rng(seed)
    df=pd.DataFrame({"temperature_c":r.normal(35,8,n).clip(20,75),"reallocated_sectors":r.poisson(2,n),"pending_sectors":r.poisson(1,n),"uncorrectable_errors":r.poisson(.4,n),"read_error_count":r.poisson(8,n),"write_error_count":r.poisson(5,n),"power_on_hours":r.integers(100,70000,n),"latency_ms":r.gamma(2,4,n).clip(.2,100)})
    risk=(df.temperature_c.gt(48)*1.1+df.reallocated_sectors.ge(8)*1.6+df.pending_sectors.ge(3)*1.8+df.uncorrectable_errors.ge(2)*1.8+df.latency_ms.gt(20)*.7+df.power_on_hours.gt(50000)*.5+r.normal(0,.7,n))
    df["failure_label"]=(risk>=2).astype(int)
    return df[FEATURES+["failure_label"]]
