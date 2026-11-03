import pytest
from core.disk import Disk
from core.recovery_engine import RecoveryEngine
def test_rebuild():
 d=[Disk(f"D{i}") for i in range(4)]; d[0].status="FAILED"; e=RecoveryEngine(); op=e.start_rebuild(d,"D0",Disk("D4"))
 for _ in range(10): e.advance(d,op,10)
 assert op.status=="COMPLETED" and op.progress==100
def test_capacity():
 d=[Disk(f"D{i}") for i in range(4)]; d[0].status="FAILED"
 with pytest.raises(ValueError): RecoveryEngine().start_rebuild(d,"D0",Disk("D4",capacity_gb=100))
