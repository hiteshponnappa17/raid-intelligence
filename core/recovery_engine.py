from dataclasses import dataclass
from datetime import datetime,timezone
from core.disk import DiskStatus
@dataclass
class RecoveryOperation:
    failed_disk_id:str; replacement_disk_id:str; started_at:str
    progress:float=0; status:str="REBUILDING"
class RecoveryEngine:
    def start_rebuild(self,disks,failed_disk_id,replacement):
        failed=next((d for d in disks if d.disk_id==failed_disk_id),None)
        if failed is None or failed.status!="FAILED": raise ValueError("Select a failed disk.")
        if any(d.status=="FAILED" and d.disk_id!=failed_disk_id for d in disks): raise ValueError("A second failed disk prevents rebuild.")
        if replacement.capacity_gb<failed.capacity_gb: raise ValueError("Replacement capacity is insufficient.")
        if any(d.disk_id==replacement.disk_id for d in disks): raise ValueError("Replacement ID already exists.")
        replacement.status="REBUILDING"; replacement.is_replacement=True
        disks.remove(failed); disks.append(replacement)
        return RecoveryOperation(failed_disk_id,replacement.disk_id,datetime.now(timezone.utc).isoformat())
    def advance(self,disks,op,step=10):
        if op.status!="REBUILDING": raise ValueError("No active rebuild.")
        if any(d.status=="FAILED" for d in disks): op.status="FAILED"; raise ValueError("Rebuild stopped because another disk failed.")
        op.progress=min(100,op.progress+max(.1,step))
        if op.progress>=100:
            next(d for d in disks if d.disk_id==op.replacement_disk_id).status="HEALTHY"; op.status="COMPLETED"
        return op
