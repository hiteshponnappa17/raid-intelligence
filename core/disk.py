from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
class DiskStatus(str,Enum):
    HEALTHY="HEALTHY"; WARNING="WARNING"; FAILED="FAILED"; REBUILDING="REBUILDING"; RECOVERED="RECOVERED"
@dataclass
class Disk:
    disk_id:str
    model:str="Virtual SATA Drive"
    capacity_gb:float=500
    temperature_c:float=32
    power_on_hours:int=12000
    reallocated_sectors:int=0
    pending_sectors:int=0
    uncorrectable_errors:int=0
    read_error_count:int=2
    write_error_count:int=1
    io_operations:int=1000
    latency_ms:float=4
    status:str="HEALTHY"
    risk_score:float=0
    risk_level:str="LOW"
    is_replacement:bool=False
    last_updated:str=""
    def __post_init__(self):
        if not self.last_updated: self.last_updated=datetime.now(timezone.utc).isoformat()
        if not self.disk_id or self.capacity_gb<=0: raise ValueError("Disk ID and positive capacity are required.")
        for k in ("temperature_c","power_on_hours","reallocated_sectors","pending_sectors","uncorrectable_errors","read_error_count","write_error_count","io_operations","latency_ms"):
            if getattr(self,k)<0: raise ValueError(f"{k} cannot be negative.")
        if self.status not in {s.value for s in DiskStatus}: raise ValueError("Invalid disk status.")
