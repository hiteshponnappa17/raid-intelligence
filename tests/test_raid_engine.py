from core.disk import Disk
from core.raid_engine import calculate_raid_state
def make(): return [Disk(f"D{i}") for i in range(4)]
def test_healthy(): assert calculate_raid_state(make()).state=="HEALTHY"
def test_one_failed():
 d=make(); d[0].status="FAILED"; s=calculate_raid_state(d); assert s.state=="DEGRADED" and s.data_accessible
def test_two_failed():
 d=make(); d[0].status=d[1].status="FAILED"; assert calculate_raid_state(d).state=="FAILED"
def test_capacity(): assert calculate_raid_state(make()).usable_capacity_gb==1500
