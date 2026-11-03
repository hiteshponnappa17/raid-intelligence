from datetime import datetime,timezone
from prediction.feature_engineering import validate,disk_features
def score_features(row):
    f=validate(row)
    parts={"Temperature":min(1,max(0,(f["temperature_c"]-30)/30))*15,
    "Reallocated sectors":min(1,f["reallocated_sectors"]/20)*22,"Pending sectors":min(1,f["pending_sectors"]/10)*18,
    "Uncorrectable errors":min(1,f["uncorrectable_errors"]/5)*18,"Read errors":min(1,f["read_error_count"]/100)*8,
    "Write errors":min(1,f["write_error_count"]/100)*5,"Power-on hours":min(1,f["power_on_hours"]/60000)*6,
    "Latency":min(1,f["latency_ms"]/50)*8}
    score=round(min(100,sum(parts.values())),1)
    level="LOW" if score<30 else "MEDIUM" if score<60 else "HIGH" if score<80 else "CRITICAL"
    actions={"LOW":"Continue routine monitoring.","MEDIUM":"Increase monitoring frequency.","HIGH":"Inspect disk and prepare a replacement.","CRITICAL":"Review disk immediately and verify backups."}
    return {"risk_score":score,"risk_level":level,"contributors":[k for k,v in sorted(parts.items(),key=lambda x:x[1],reverse=True) if v>=5][:3],"recommended_action":actions[level],"timestamp":datetime.now(timezone.utc).isoformat(),"score_type":"Heuristic score, not calibrated failure probability."}
def score_disk(d):
    r=score_features(disk_features(d)); d.risk_score=r["risk_score"]; d.risk_level=r["risk_level"]; return r
