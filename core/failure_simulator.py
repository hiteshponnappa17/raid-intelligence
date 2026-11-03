from datetime import datetime,timezone
from core.disk import DiskStatus
from core.raid_engine import calculate_raid_state
class FailureSimulator:
    def __init__(self,event_callback=None,alert_callback=None):
        self.event_callback=event_callback or (lambda *a:None); self.alert_callback=alert_callback or (lambda *a:None)
    def fail_disk(self,disks,disk_id):
        d=next((x for x in disks if x.disk_id==disk_id),None)
        if d is None: raise ValueError("Disk not found.")
        if d.status=="FAILED": raise ValueError("Disk has already failed.")
        d.status="FAILED"; d.last_updated=datetime.now(timezone.utc).isoformat()
        s=calculate_raid_state(disks)
        self.event_callback("DISK_FAILURE",disk_id,f"Failure injected; RAID is {s.state}.")
        self.alert_callback(disk_id,"CRITICAL","ACTUAL_FAILURE",f"{disk_id} was marked failed.","Replace the disk if array remains recoverable.")
        return s
