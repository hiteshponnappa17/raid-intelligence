import sqlite3
from pathlib import Path
from config.settings import DB_PATH
SCHEMA="""CREATE TABLE IF NOT EXISTS health_history(id INTEGER PRIMARY KEY,timestamp TEXT,disk_id TEXT,temperature_c REAL,risk_score REAL,read_error_count INTEGER,reallocated_sectors INTEGER,pending_sectors INTEGER,status TEXT);
CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY,timestamp TEXT,disk_id TEXT,risk_score REAL,risk_level TEXT,contributors TEXT,action TEXT,score_type TEXT);
CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY,timestamp TEXT,disk_id TEXT,severity TEXT,category TEXT,description TEXT,action TEXT,acknowledged INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS simulation_events(id INTEGER PRIMARY KEY,timestamp TEXT,event_type TEXT,disk_id TEXT,description TEXT);
CREATE TABLE IF NOT EXISTS recovery_operations(id INTEGER PRIMARY KEY,failed_disk_id TEXT,replacement_disk_id TEXT,started_at TEXT,completed_at TEXT,status TEXT);"""
class Database:
    def __init__(self,path=None):
        self.path=str(path or DB_PATH); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c: c.executescript(SCHEMA)
    def connect(self):
        c=sqlite3.connect(self.path,check_same_thread=False); c.row_factory=sqlite3.Row; return c
    def execute(self,sql,params=()):
        with self.connect() as c: return c.execute(sql,params).lastrowid
    def query(self,sql,params=()):
        with self.connect() as c: return [dict(r) for r in c.execute(sql,params).fetchall()]
    def log_event(self,kind,disk_id,description,timestamp):
        self.execute("INSERT INTO simulation_events(timestamp,event_type,disk_id,description) VALUES(?,?,?,?)",(timestamp,kind,disk_id,description))
    def log_health(self,d,t):
        self.execute("INSERT INTO health_history(timestamp,disk_id,temperature_c,risk_score,read_error_count,reallocated_sectors,pending_sectors,status) VALUES(?,?,?,?,?,?,?,?)",(t,d.disk_id,d.temperature_c,d.risk_score,d.read_error_count,d.reallocated_sectors,d.pending_sectors,d.status))
    def log_prediction(self,d,r):
        self.execute("INSERT INTO predictions(timestamp,disk_id,risk_score,risk_level,contributors,action,score_type) VALUES(?,?,?,?,?,?,?)",(r["timestamp"],d.disk_id,r["risk_score"],r["risk_level"],", ".join(r["contributors"]),r["recommended_action"],r["score_type"]))
    def log_alert(self,disk_id,severity,category,description,action,timestamp):
        self.execute("INSERT INTO alerts(timestamp,disk_id,severity,category,description,action) VALUES(?,?,?,?,?,?)",(timestamp,disk_id,severity,category,description,action))
