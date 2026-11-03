from dataclasses import dataclass
from enum import Enum
from core.disk import Disk,DiskStatus
class RAIDState(str,Enum):
    HEALTHY="HEALTHY"; DEGRADED="DEGRADED"; REBUILDING="REBUILDING"; FAILED="FAILED"
@dataclass
class RAIDSummary:
    state:str; total_raw_capacity_gb:float; usable_capacity_gb:float; failed_disks:int
    available_disks:int; data_accessible:bool; redundancy_available:bool; rebuild_possible:bool
def calculate_raid_state(disks,rebuilding=False):
    disks=list(disks)
    if len(disks)<3: raise ValueError("RAID 5 requires at least three disks.")
    failed=sum(d.status==DiskStatus.FAILED.value for d in disks)
    raw=sum(d.capacity_gb for d in disks); usable=max(0,(len(disks)-1)*min(d.capacity_gb for d in disks))
    state="FAILED" if failed>=2 else "REBUILDING" if rebuilding else "DEGRADED" if failed==1 else "HEALTHY"
    return RAIDSummary(state,raw,usable,failed,len(disks)-failed,failed<2,failed==0 and not rebuilding,failed==1)
