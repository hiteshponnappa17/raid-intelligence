from database.db_manager import Database
def test_db(tmp_path):
 d=Database(tmp_path/"test.db"); d.log_event("TEST","D1","hello","now")
 assert d.query("SELECT * FROM simulation_events")[0]["event_type"]=="TEST"
