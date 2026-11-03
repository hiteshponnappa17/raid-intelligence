FEATURES=["temperature_c","reallocated_sectors","pending_sectors","uncorrectable_errors","read_error_count","write_error_count","power_on_hours","latency_ms"]
def disk_features(d): return {k:float(getattr(d,k)) for k in FEATURES}
def validate(row):
    missing=set(FEATURES)-set(row)
    if missing: raise ValueError("Missing features: "+", ".join(sorted(missing)))
    f={k:float(row[k]) for k in FEATURES}
    if any(v<0 for v in f.values()): raise ValueError("Features cannot be negative.")
    return f
