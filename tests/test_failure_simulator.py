import pytest
from core.disk import Disk
from core.failure_simulator import FailureSimulator
def test_failure(): 
 d=[Disk(f"D{i}") for i in range(4)]; FailureSimulator().fail_disk(d,"D0"); assert d[0].status=="FAILED"
def test_duplicate():
 d=[Disk(f"D{i}") for i in range(4)]; s=FailureSimulator(); s.fail_disk(d,"D0")
 with pytest.raises(ValueError): s.fail_disk(d,"D0")
