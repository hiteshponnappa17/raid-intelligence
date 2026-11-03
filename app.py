from datetime import datetime, timezone
import random

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.disk import Disk
from core.raid_engine import calculate_raid_state
from core.failure_simulator import FailureSimulator
from core.recovery_engine import RecoveryEngine
from database.db_manager import Database
from prediction.risk_engine import score_disk
from prediction.synthetic_data import generate_synthetic_dataset
from prediction.ml_model import train_model, predict_with_model
from prediction.feature_engineering import disk_features
from config.settings import MODEL_DIR, DB_PATH

st.set_page_config(
    page_title="RAID Intelligence | Storage Monitoring",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------- Design system ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --bg:#080d18; --panel:#101827; --panel2:#131f31; --line:#26344a; --muted:#8fa1b8; --text:#eaf1fb; --cyan:#55d6d0; --blue:#6e9cff; --green:#48d597; --amber:#f3bd62; --red:#ff6b7d; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:radial-gradient(ellipse at 80% 0%, #15243b 0%, var(--bg) 42%); color:var(--text); }
[data-testid="stHeader"] { background:rgba(8,13,24,.82); }
[data-testid="stSidebar"] { background:#0a1220; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { padding-top:1.4rem; padding-bottom:2.4rem; max-width:1500px; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif!important; letter-spacing:-.035em; color:var(--text); }
h1 { font-size:2.25rem!important; }
h2 { font-size:1.55rem!important; }
h3 { font-size:1.12rem!important; }
p, label, .stMarkdown { color:var(--text); }
small,.muted { color:var(--muted)!important; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#121e30,#0e1726); border:1px solid var(--line); border-radius:15px; padding:17px 18px; }
[data-testid="stMetricLabel"] { color:var(--muted)!important; font-size:.82rem!important; }
[data-testid="stMetricValue"] { color:var(--text)!important; font-family:'Space Grotesk',sans-serif; }
[data-testid="stMetricDelta"] { font-size:.78rem!important; }
.stButton>button, .stDownloadButton>button { border-radius:9px; border:1px solid #30435e; background:#16243a; color:#edf4ff; font-weight:600; min-height:2.55rem; }
.stButton>button:hover, .stDownloadButton>button:hover { border-color:var(--cyan); color:white; background:#1b3048; }
.stButton>button[kind="primary"] { background:linear-gradient(90deg,#1b9d9a,#377be5); border:0; color:white; }
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stSlider { border-radius:9px; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line)!important; border-radius:15px!important; background:rgba(16,24,39,.76); }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
hr { border-color:var(--line); }
.hero { padding:26px 28px; border:1px solid #2b415c; border-radius:20px; background:linear-gradient(115deg,rgba(27,157,154,.14),rgba(55,123,229,.12) 55%,rgba(17,27,44,.9)); margin-bottom:22px; }
.eyebrow { color:var(--cyan); text-transform:uppercase; letter-spacing:.15em; font-size:.72rem; font-weight:700; margin-bottom:8px; }
.hero-title { font-family:'Space Grotesk',sans-serif; font-size:2.05rem; line-height:1.15; font-weight:700; letter-spacing:-.04em; color:#f4f8ff; }
.hero-copy { color:#a9bad0; margin-top:10px; max-width:820px; line-height:1.6; }
.section-label { color:var(--muted); font-size:.75rem; text-transform:uppercase; letter-spacing:.13em; font-weight:700; margin:4px 0 12px; }
.disk-card { border:1px solid var(--line); background:linear-gradient(155deg,#121f32,#0e1726); border-radius:15px; padding:16px; height:100%; }
.disk-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:13px; }
.disk-name { font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.03rem; }
.pill { display:inline-block; padding:4px 9px; border-radius:20px; font-size:.68rem; font-weight:700; letter-spacing:.04em; }
.pill-green { background:rgba(72,213,151,.13); color:var(--green); border:1px solid rgba(72,213,151,.3); }
.pill-amber { background:rgba(243,189,98,.13); color:var(--amber); border:1px solid rgba(243,189,98,.3); }
.pill-red { background:rgba(255,107,125,.13); color:var(--red); border:1px solid rgba(255,107,125,.3); }
.pill-blue { background:rgba(110,156,255,.13); color:var(--blue); border:1px solid rgba(110,156,255,.3); }
.disk-shell { height:48px; border-radius:9px; border:1px solid #354a65; background:linear-gradient(180deg,#24364d,#111b2b); position:relative; margin:12px 0 15px; overflow:hidden; }
.disk-shell:before { content:''; position:absolute; width:32px; height:32px; border:3px solid #66819d; border-radius:50%; left:12px; top:7px; box-shadow:inset 0 0 0 5px #18263a; }
.disk-shell:after { content:''; position:absolute; height:5px; left:56px; right:12px; top:21px; border-radius:5px; background:linear-gradient(90deg,#55d6d0,#6e9cff); opacity:.8; }
.disk-stats { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.stat-label { font-size:.72rem; color:var(--muted); }
.stat-value { font-family:'Space Grotesk',sans-serif; font-size:1.02rem; font-weight:600; margin-top:2px; }
.raid-node { border:1px solid var(--line); border-radius:12px; background:#111c2c; padding:14px 10px; text-align:center; }
.raid-node-title { font-weight:700; font-size:.9rem; }
.raid-node-sub { color:var(--muted); font-size:.72rem; margin-top:4px; }
.raid-link { color:#49617d; text-align:center; padding-top:18px; font-size:1.3rem; }
.callout { border-left:3px solid var(--cyan); background:rgba(85,214,208,.07); padding:12px 15px; border-radius:0 10px 10px 0; color:#b9c9db; margin:10px 0 16px; }
.footer-note { color:#7588a2; font-size:.75rem; padding-top:22px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------ Data setup ------------------------------
db = Database()
now = lambda: datetime.now(timezone.utc).isoformat()


def defaults():
    specs = [
        ("DISK-01", 31, 0, 0, 0, 3, 1, 12000, 4),
        ("DISK-02", 34, 0, 0, 0, 5, 2, 19000, 5),
        ("DISK-03", 44, 8, 3, 1, 42, 18, 47000, 21),
        ("DISK-04", 32, 0, 0, 0, 2, 1, 9000, 3),
    ]
    result = []
    for disk_id, temp, realloc, pending, uncorr, read_err, write_err, hours, latency in specs:
        disk = Disk(
            disk_id=disk_id, model="Virtual SATA Drive", capacity_gb=500,
            temperature_c=temp, reallocated_sectors=realloc,
            pending_sectors=pending, uncorrectable_errors=uncorr,
            read_error_count=read_err, write_error_count=write_err,
            power_on_hours=hours, latency_ms=latency, io_operations=1200,
        )
        score_disk(disk)
        result.append(disk)
    return result

if "disks" not in st.session_state:
    st.session_state.disks = defaults()
if "recovery" not in st.session_state:
    st.session_state.recovery = None
if "model" not in st.session_state:
    st.session_state.model = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "last_action" not in st.session_state:
    st.session_state.last_action = "System initialized with four virtual disks."


def log_event(kind, disk_id, description):
    db.log_event(kind, disk_id, description, now())
    st.session_state.last_action = description


def log_alert(disk_id, severity, category, description, action):
    db.log_alert(disk_id, severity, category, description, action, now())


def record_disk(disk):
    db.log_health(disk, now())


def run_prediction(disk):
    result = score_disk(disk)
    db.log_prediction(disk, result)
    record_disk(disk)
    if result["risk_level"] in ("HIGH", "CRITICAL"):
        log_alert(disk.disk_id, result["risk_level"], "PREDICTION_WARNING",
                  f"Calculated score {result['risk_score']}/100", result["recommended_action"])
    return result


def status_pill(status):
    if status in ("HEALTHY", "RECOVERED"):
        cls = "pill-green"
    elif status == "WARNING":
        cls = "pill-amber"
    elif status == "FAILED":
        cls = "pill-red"
    else:
        cls = "pill-blue"
    return f'<span class="pill {cls}">{status}</span>'


def risk_color(level):
    return {"LOW": "#48d597", "MEDIUM": "#f3bd62", "HIGH": "#ff9b65", "CRITICAL": "#ff6b7d"}.get(level, "#6e9cff")


def render_disk_card(disk):
    st.markdown(f"""
    <div class="disk-card">
      <div class="disk-top"><div class="disk-name">{disk.disk_id}</div>{status_pill(disk.status)}</div>
      <div class="disk-shell"></div>
      <div class="disk-stats">
        <div><div class="stat-label">Capacity</div><div class="stat-value">{disk.capacity_gb:g} GB</div></div>
        <div><div class="stat-label">Temperature</div><div class="stat-value">{disk.temperature_c:g} °C</div></div>
        <div><div class="stat-label">Risk score</div><div class="stat-value" style="color:{risk_color(disk.risk_level)}">{disk.risk_score:g}/100</div></div>
        <div><div class="stat-label">Latency</div><div class="stat-value">{disk.latency_ms:g} ms</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_raid_diagram(disks, summary):
    state_color = {"HEALTHY": "#48d597", "DEGRADED": "#f3bd62", "REBUILDING": "#6e9cff", "FAILED": "#ff6b7d"}.get(summary.state, "#8fa1b8")
    st.markdown(f"<div class='section-label'>Virtual array / RAID 5</div><div class='callout'>Array state: <b style='color:{state_color}'>{summary.state}</b> &nbsp; · &nbsp; {summary.available_disks}/{len(disks)} members available &nbsp; · &nbsp; Data {'accessible' if summary.data_accessible else 'unavailable'}</div>", unsafe_allow_html=True)
    cols = st.columns([1, .18, 1, .18, 1, .18, 1])
    for i, disk in enumerate(disks[:4]):
        with cols[i * 2]:
            color = risk_color(disk.risk_level) if disk.status != "FAILED" else "#ff6b7d"
            st.markdown(f"<div class='raid-node' style='border-top:3px solid {color}'><div class='raid-node-title'>{disk.disk_id}</div><div style='margin:9px auto;width:32px;height:32px;border-radius:50%;border:3px solid {color};display:flex;align-items:center;justify-content:center;color:{color};font-size:.65rem;font-weight:700'>{'X' if disk.status == 'FAILED' else 'OK'}</div>{status_pill(disk.status)}<div class='raid-node-sub'>{disk.capacity_gb:g} GB · {disk.temperature_c:g}°C</div></div>", unsafe_allow_html=True)
        if i < 3:
            with cols[i * 2 + 1]:
                st.markdown("<div class='raid-link'>↔</div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Raw capacity", f"{summary.total_raw_capacity_gb:g} GB")
    m2.metric("Usable capacity", f"{summary.usable_capacity_gb:g} GB")
    m3.metric("Parity overhead", f"{summary.total_raw_capacity_gb-summary.usable_capacity_gb:g} GB")


def render_events(limit=8):
    rows = db.query("SELECT timestamp,event_type,disk_id,description FROM simulation_events ORDER BY id DESC LIMIT ?", (limit,))
    if rows:
        frame = pd.DataFrame(rows)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True).dt.strftime("%d %b %H:%M:%S")
        st.dataframe(frame, use_container_width=True, hide_index=True)
    else:
        st.info("No events recorded yet. Use the simulator controls to create the first event.")

# ------------------------------ Sidebar ---------------------------------
with st.sidebar:
    st.markdown("<div class='eyebrow'>STORAGE SYSTEMS / 01</div><div style='font-family:Space Grotesk;font-size:1.35rem;font-weight:700;color:#f4f8ff'>RAID Intelligence</div><div style='font-size:.78rem;color:#8fa1b8;margin:4px 0 18px'>Intelligent Storage Monitoring &amp; Recovery</div>", unsafe_allow_html=True)
    page = st.radio("WORKSPACE", [
        "Command Center", "Disk Simulator", "Disk Health", "Failure Risk Analysis",
        "RAID Array Management", "Recovery Operations", "Analytics & History", "Model & Dataset", "System Information"
    ], label_visibility="visible")
    st.divider()
    st.markdown("<div class='section-label'>Environment</div>", unsafe_allow_html=True)
    st.markdown("**Mode:** Virtual simulation")
    st.markdown("**Array:** RAID 5 · 4 members")
    st.markdown("**Data source:** Simulated telemetry")
    st.divider()
    if st.button("Reset simulation environment", use_container_width=True):
        st.session_state.disks = defaults()
        st.session_state.recovery = None
        st.session_state.last_action = "Simulation reset to initial demo state."
        log_event("RESET", None, "Simulation reset to initial demo state.")
        st.rerun()

# ----------------------------- State ------------------------------------
disks = st.session_state.disks
recovery = st.session_state.recovery
summary = calculate_raid_state(disks, bool(recovery and recovery.status == "REBUILDING"))
failed_count = sum(d.status == "FAILED" for d in disks)
healthy_count = sum(d.status in ("HEALTHY", "RECOVERED") for d in disks)
warning_count = sum(d.status == "WARNING" or d.risk_level in ("HIGH", "CRITICAL") for d in disks if d.status != "FAILED")

# ----------------------------- Pages ------------------------------------
if page == "Command Center":
    st.markdown("<div class='hero'><div class='eyebrow'>Storage observability / live simulation</div><div class='hero-title'>Intelligent RAID Failure<br>Prediction & Recovery</div><div class='hero-copy'>Monitor virtual drive health, simulate faults, analyze failure risk, and rebuild a RAID 5 array in a controlled virtual storage environment.</div></div>", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Array status", summary.state, help="Calculated from simulated member-disk states")
    b.metric("Healthy disks", f"{healthy_count}/{len(disks)}")
    c.metric("High-risk members", warning_count)
    d.metric("Failed disks", failed_count)
    st.markdown("### Array topology")
    render_raid_diagram(disks, summary)
    st.markdown("### Disk fleet overview")
    cards = st.columns(4)
    for col, disk in zip(cards, disks[:4]):
        with col:
            render_disk_card(disk)
    left, right = st.columns([1.15, .85])
    with left:
        st.markdown("### Risk profile")
        chart = go.Figure(go.Bar(x=[x.disk_id for x in disks], y=[x.risk_score for x in disks], marker_color=[risk_color(x.risk_level) for x in disks], text=[f"{x.risk_score:g}" for x in disks], textposition="outside"))
        chart.update_layout(height=280, margin=dict(l=10,r=10,t=20,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#dce8f7", yaxis=dict(range=[0,110],gridcolor="#26344a",title="Risk score / 100"), xaxis=dict(title="Virtual disk"), showlegend=False)
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown("### Latest system action")
        st.markdown(f"<div class='callout'>{st.session_state.last_action}</div>", unsafe_allow_html=True)
        st.markdown("**Quick actions**")
        qa, qb = st.columns(2)
        with qa:
            if st.button("Run health scan", type="primary", use_container_width=True):
                for disk in disks:
                    run_prediction(disk)
                log_event("HEALTH_SCAN", None, "Health scan completed for all virtual disks.")
                st.rerun()
        with qb:
            if st.button("Open disk simulator", use_container_width=True):
                st.session_state._unused = True
                st.info("Choose Disk Simulator from the left navigation.")
        st.markdown("### Recent events")
        render_events(5)

elif page == "Disk Simulator":
    st.markdown("<div class='eyebrow'>Virtual Storage Environment</div>", unsafe_allow_html=True)
    st.title("Disk Simulator")
    st.caption("Select a virtual disk, change its health telemetry, run workload, or inject a failure. All changes are simulated and remain in this session.")
    render_raid_diagram(disks, summary)
    st.markdown("### Select a drive")
    selected_id = st.selectbox("Virtual disk", [x.disk_id for x in disks], key="disk_simulator_selected")
    disk = next(x for x in disks if x.disk_id == selected_id)
    left, right = st.columns([.92, 1.08], gap="large")
    with left:
        render_disk_card(disk)
        st.markdown("#### Live telemetry")
        g1, g2 = st.columns(2)
        g1.metric("Read errors", disk.read_error_count)
        g2.metric("Write errors", disk.write_error_count)
        g1.metric("Pending sectors", disk.pending_sectors)
        g2.metric("Reallocated sectors", disk.reallocated_sectors)
        g1.metric("Power-on hours", f"{disk.power_on_hours:,}")
        g2.metric("I/O latency", f"{disk.latency_ms:g} ms")
    with right:
        st.markdown("#### Adjust virtual disk conditions")
        st.write("Adjust these values to test how the risk engine responds.")
        with st.form("disk_telemetry_form"):
            temp = st.slider("Temperature (°C)", 15, 85, int(min(85, max(15, disk.temperature_c))), key=f"sim_temp_{disk.disk_id}")
            read_errors = st.number_input("Read errors", min_value=0, max_value=10000, value=int(disk.read_error_count), step=1, key=f"sim_read_{disk.disk_id}")
            write_errors = st.number_input("Write errors", min_value=0, max_value=10000, value=int(disk.write_error_count), step=1, key=f"sim_write_{disk.disk_id}")
            reallocated = st.number_input("Reallocated sectors", min_value=0, max_value=1000, value=int(disk.reallocated_sectors), step=1, key=f"sim_realloc_{disk.disk_id}")
            pending = st.number_input("Pending sectors", min_value=0, max_value=1000, value=int(disk.pending_sectors), step=1, key=f"sim_pending_{disk.disk_id}")
            uncorrectable = st.number_input("Uncorrectable errors", min_value=0, max_value=1000, value=int(disk.uncorrectable_errors), step=1, key=f"sim_uncorrectable_{disk.disk_id}")
            latency = st.slider("I/O latency (ms)", 1, 100, int(min(100, max(1, disk.latency_ms))), key=f"sim_latency_{disk.disk_id}")
            apply = st.form_submit_button("Apply telemetry & recalculate risk", type="primary", use_container_width=True)
        if apply:
            disk.temperature_c = temp
            disk.read_error_count = int(read_errors)
            disk.write_error_count = int(write_errors)
            disk.reallocated_sectors = int(reallocated)
            disk.pending_sectors = int(pending)
            disk.uncorrectable_errors = int(uncorrectable)
            disk.latency_ms = latency
            disk.power_on_hours += 1
            result = run_prediction(disk)
            if disk.status not in ("FAILED", "REBUILDING") and result["risk_level"] in ("HIGH", "CRITICAL"):
                disk.status = "WARNING"
            elif disk.status == "WARNING" and result["risk_level"] in ("LOW", "MEDIUM"):
                disk.status = "HEALTHY"
            log_event("TELEMETRY_EDIT", disk.disk_id, f"Manual telemetry applied; risk {result['risk_score']}/100 ({result['risk_level']}).")
            st.success(f"Risk recalculated: {result['risk_score']}/100 — {result['risk_level']}")
            st.rerun()
    st.markdown("### Workload & fault controls")
    x1, x2, x3, x4 = st.columns(4)
    with x1:
        if st.button("Run read workload", use_container_width=True, disabled=disk.status == "FAILED"):
            disk.io_operations += random.randint(80, 220)
            disk.read_error_count += random.choice([0, 0, 1, 2])
            disk.temperature_c = min(85, disk.temperature_c + random.choice([0, 1, 2]))
            disk.latency_ms = min(100, disk.latency_ms + random.choice([0, 1, 3]))
            result = run_prediction(disk)
            if result["risk_level"] in ("HIGH", "CRITICAL"): disk.status = "WARNING"
            log_event("READ_WORKLOAD", disk.disk_id, f"Read workload executed; {disk.io_operations} cumulative I/O operations.")
            st.rerun()
    with x2:
        if st.button("Run write workload", use_container_width=True, disabled=disk.status == "FAILED"):
            disk.io_operations += random.randint(60, 180)
            disk.write_error_count += random.choice([0, 0, 1])
            disk.temperature_c = min(85, disk.temperature_c + random.choice([1, 1, 2, 3]))
            disk.latency_ms = min(100, disk.latency_ms + random.choice([1, 2, 4]))
            result = run_prediction(disk)
            if result["risk_level"] in ("HIGH", "CRITICAL"): disk.status = "WARNING"
            log_event("WRITE_WORKLOAD", disk.disk_id, f"Write workload executed; {disk.io_operations} cumulative I/O operations.")
            st.rerun()
    with x3:
        if st.button("Simulate gradual wear", use_container_width=True, disabled=disk.status == "FAILED"):
            disk.temperature_c = min(85, disk.temperature_c + 4)
            disk.read_error_count += 8
            disk.write_error_count += 4
            disk.reallocated_sectors += 2
            disk.pending_sectors += 1
            disk.latency_ms = min(100, disk.latency_ms + 7)
            result = run_prediction(disk)
            if result["risk_level"] in ("HIGH", "CRITICAL"): disk.status = "WARNING"
            log_event("WEAR_SIMULATION", disk.disk_id, f"Wear simulated; risk is {result['risk_score']}/100.")
            st.rerun()
    with x4:
        if st.button("Inject disk failure", type="primary", use_container_width=True, disabled=disk.status == "FAILED"):
            try:
                FailureSimulator(log_event, log_alert).fail_disk(disks, disk.disk_id)
                record_disk(disk)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    st.markdown("### Simulator event log")
    render_events(10)

elif page == "Disk Health":
    st.title("Disk Health Monitoring")
    st.caption("Review the current condition and history of each virtual disk.")
    selected_id = st.selectbox("Select disk", [x.disk_id for x in disks], key="health_page_disk")
    disk = next(x for x in disks if x.disk_id == selected_id)
    c1, c2 = st.columns([.8, 1.2])
    with c1:
        render_disk_card(disk)
        if st.button("Run health assessment", type="primary"):
            result = run_prediction(disk)
            if disk.status not in ("FAILED", "REBUILDING"):
                disk.status = "WARNING" if result["risk_level"] in ("HIGH", "CRITICAL") else "HEALTHY"
            log_event("HEALTH_ASSESSMENT", disk.disk_id, f"Health assessment: {result['risk_level']} risk.")
            st.success(result["recommended_action"])
            st.rerun()
    with c2:
        rows = db.query("SELECT timestamp,temperature_c,risk_score,read_error_count,reallocated_sectors,pending_sectors,status FROM health_history WHERE disk_id=? ORDER BY id DESC LIMIT 100", (disk.disk_id,))
        if rows:
            hist = pd.DataFrame(rows).sort_values("timestamp")
            hist["timestamp"] = pd.to_datetime(hist["timestamp"], errors="coerce", utc=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.timestamp, y=hist.risk_score, mode="lines+markers", name="Risk score", line=dict(color="#55d6d0", width=3)))
            fig.add_trace(go.Scatter(x=hist.timestamp, y=hist.temperature_c, mode="lines+markers", name="Temperature °C", yaxis="y2", line=dict(color="#f3bd62", width=2)))
            fig.update_layout(height=330, margin=dict(l=5,r=5,t=25,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#dce8f7", yaxis=dict(title="Risk score",gridcolor="#26344a"), yaxis2=dict(title="Temperature °C",overlaying="y",side="right",showgrid=False), legend=dict(orientation="h",y=1.15), xaxis=dict(showgrid=False))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.info("No health history for this disk yet. Run an assessment or use the Disk Simulator.")
    st.markdown("### Telemetry snapshot")
    telemetry = pd.DataFrame([{"Metric":"Temperature (°C)","Value":disk.temperature_c},{"Metric":"Read errors","Value":disk.read_error_count},{"Metric":"Write errors","Value":disk.write_error_count},{"Metric":"Reallocated sectors","Value":disk.reallocated_sectors},{"Metric":"Pending sectors","Value":disk.pending_sectors},{"Metric":"Uncorrectable errors","Value":disk.uncorrectable_errors},{"Metric":"Power-on hours","Value":disk.power_on_hours},{"Metric":"Latency (ms)","Value":disk.latency_ms},{"Metric":"Cumulative I/O operations","Value":disk.io_operations}])
    st.dataframe(telemetry, use_container_width=True, hide_index=True)

elif page == "Failure Risk Analysis":
    st.title("Failure Risk Analysis")
    st.markdown("<div class='callout'>Risk scores are rule-based indicators, not calibrated failure probabilities. The Random Forest uses synthetic data and is not validated for physical storage devices.</div>", unsafe_allow_html=True)
    selected_id = st.selectbox("Disk to evaluate", [x.disk_id for x in disks], key="prediction_page_disk")
    disk = next(x for x in disks if x.disk_id == selected_id)
    p1, p2 = st.columns([.75, 1.25])
    with p1:
        gauge = go.Figure(go.Indicator(mode="gauge+number", value=disk.risk_score, number={"suffix":"/100","font":{"color":"#eaf1fb","size":34}}, title={"text":f"{disk.disk_id} risk score","font":{"color":"#8fa1b8","size":15}}, gauge={"axis":{"range":[0,100],"tickcolor":"#8fa1b8"},"bar":{"color":risk_color(disk.risk_level)},"bgcolor":"#101827","bordercolor":"#26344a","steps":[{"range":[0,30],"color":"rgba(72,213,151,.15)"},{"range":[30,60],"color":"rgba(243,189,98,.15)"},{"range":[60,80],"color":"rgba(255,155,101,.15)"},{"range":[80,100],"color":"rgba(255,107,125,.15)"}] }))
        gauge.update_layout(height=280, margin=dict(l=15,r=15,t=35,b=5), paper_bgcolor="rgba(0,0,0,0)", font_color="#eaf1fb")
        st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar":False})
        st.markdown(f"Current level: {status_pill(disk.risk_level)}", unsafe_allow_html=True)
        if st.button("Run heuristic prediction", type="primary", use_container_width=True):
            result = run_prediction(disk)
            st.success(f"{result['risk_level']} risk — {result['risk_score']}/100")
            st.write(result["recommended_action"])
            if result["contributors"]: st.write("Main contributors: " + ", ".join(result["contributors"]))
    with p2:
        st.markdown("### Model training")
        st.write("Train a Random Forest on generated virtual-disk health records, then inspect its test metrics and feature importance.")
        if st.button("Train / evaluate Random Forest", use_container_width=True):
            with st.spinner("Training model on synthetic examples..."):
                model, metrics = train_model(model_path=MODEL_DIR / "raid_rf.joblib")
                st.session_state.model, st.session_state.metrics = model, metrics
        if st.session_state.metrics:
            metrics = st.session_state.metrics
            metcols = st.columns(3)
            metcols[0].metric("Precision", f"{metrics.get('precision',0):.2f}")
            metcols[1].metric("Recall", f"{metrics.get('recall',0):.2f}")
            metcols[2].metric("F1 score", f"{metrics.get('f1',0):.2f}")
            importance = pd.DataFrame({"Feature":st.session_state.model.feature_names_in_,"Importance":st.session_state.model.feature_importances_}).sort_values("Importance")
            fig = go.Figure(go.Bar(x=importance.Importance, y=importance.Feature, orientation="h", marker_color="#55d6d0"))
            fig.update_layout(height=310, margin=dict(l=5,r=5,t=15,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#dce8f7", xaxis=dict(gridcolor="#26344a"), yaxis=dict(title=""))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            if st.button("Predict selected disk with ML", use_container_width=True):
                result = predict_with_model(st.session_state.model, disk_features(disk))
                st.metric("Model output", "Failure label" if result["label"] else "No failure label", f"Synthetic-model score: {result['score']:.1%}")
        else:
            st.info("Train the model to display evaluation metrics and feature importance.")

elif page == "RAID Array Management":
    st.title("RAID Array Management")
    st.caption("Inject controlled failures and observe how array availability changes.")
    render_raid_diagram(disks, summary)
    if summary.state == "FAILED":
        st.error("The array is failed in this simplified simulation. Reset the demo to start again.")
    else:
        choices = [d.disk_id for d in disks if d.status != "FAILED"]
        selected = st.selectbox("Select member disk to fail", choices, key="raid_page_failure_disk") if choices else None
        confirm = st.checkbox("Confirm fault injection")
        if st.button("Inject selected disk failure", type="primary", disabled=not confirm or not selected):
            try:
                disk = next(d for d in disks if d.disk_id == selected)
                FailureSimulator(log_event, log_alert).fail_disk(disks, selected)
                record_disk(disk)
                st.rerun()
            except ValueError as exc: st.error(str(exc))
        st.markdown("#### Failure rules")
        st.write("- One failed member: RAID 5 becomes degraded; data remains accessible in this model.")
        st.write("- Two failed members: array data becomes unavailable in this model.")
        st.write("- Recovery is possible only when no other member is failed and a sufficiently large replacement is supplied.")
    st.markdown("### Fault event history")
    render_events(12)

elif page == "Recovery Operations":
    st.title("Recovery Operations")
    st.caption("Simulate replacement and rebuild. Rebuild progress advances in controlled steps so it can be demonstrated live.")
    failed = [d for d in disks if d.status == "FAILED"]
    op = st.session_state.recovery
    if failed and not (op and op.status == "REBUILDING"):
        selected = st.selectbox("Failed member", [d.disk_id for d in failed], key="recovery_target")
        old = next(d for d in failed if d.disk_id == selected)
        c1, c2 = st.columns(2)
        with c1: cap = st.number_input("Replacement capacity (GB)", min_value=1.0, value=float(old.capacity_gb), step=50.0, key="replacement_capacity")
        with c2: replacement_id = st.text_input("Replacement disk ID", f"REPL-{selected}", key="replacement_id")
        if st.button("Install replacement & begin rebuild", type="primary"):
            try:
                replacement = Disk(replacement_id.strip(), "Virtual Replacement Drive", cap, is_replacement=True)
                operation = RecoveryEngine().start_rebuild(disks, selected, replacement)
                st.session_state.recovery = operation
                db.execute("INSERT INTO recovery_operations(failed_disk_id,replacement_disk_id,started_at,status) VALUES(?,?,?,?)", (operation.failed_disk_id, operation.replacement_disk_id, operation.started_at, "REBUILDING"))
                log_event("REBUILD_STARTED", replacement_id, f"Rebuild started for failed member {selected}.")
                st.rerun()
            except ValueError as exc: st.error(str(exc))
    elif not failed and not (op and op.status in ("REBUILDING", "COMPLETED")):
        st.success("No failed disks. Use Disk Simulator or RAID Array to inject a failure first.")
    op = st.session_state.recovery
    if op and op.status == "REBUILDING":
        st.markdown("### Rebuild in progress")
        st.progress(int(op.progress), text=f"Rebuild progress · {op.progress:.0f}%")
        st.write(f"Failed member: **{op.failed_disk_id}** · Replacement: **{op.replacement_disk_id}**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Advance rebuild by 10%", type="primary", use_container_width=True):
                try:
                    RecoveryEngine().advance(disks, op, 10)
                    log_event("REBUILD_PROGRESS", op.replacement_disk_id, f"Rebuild progress {op.progress:.0f}%.")
                    if op.status == "COMPLETED":
                        db.execute("UPDATE recovery_operations SET completed_at=?,status='COMPLETED' WHERE replacement_disk_id=?", (now(), op.replacement_disk_id))
                        log_event("REBUILD_COMPLETED", op.replacement_disk_id, "Rebuild completed; replacement disk is healthy.")
                    st.rerun()
                except ValueError as exc:
                    db.execute("UPDATE recovery_operations SET completed_at=?,status='FAILED' WHERE replacement_disk_id=?", (now(), op.replacement_disk_id))
                    log_event("REBUILD_FAILED", op.replacement_disk_id, str(exc))
                    st.error(str(exc))
        with c2:
            if st.button("Complete rebuild instantly", use_container_width=True):
                try:
                    RecoveryEngine().advance(disks, op, 100)
                    db.execute("UPDATE recovery_operations SET completed_at=?,status='COMPLETED' WHERE replacement_disk_id=?", (now(), op.replacement_disk_id))
                    log_event("REBUILD_COMPLETED", op.replacement_disk_id, "Rebuild completed; replacement disk is healthy.")
                    st.rerun()
                except ValueError as exc: st.error(str(exc))
    elif op and op.status == "COMPLETED":
        st.success("Rebuild completed. The replacement disk is healthy; the failed virtual disk remains failed.")
        render_raid_diagram(disks, calculate_raid_state(disks))
    elif op and op.status == "FAILED":
        st.error("Rebuild failed. Reset the simulation before starting another scenario.")
    st.markdown("### Recovery history")
    rows = db.query("SELECT * FROM recovery_operations ORDER BY id DESC LIMIT 50")
    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else: st.info("No rebuild operations recorded yet.")

elif page == "Analytics & History":
    st.title("Analytics & History")
    st.caption("Review the event trail, prediction records, health snapshots, alerts, and rebuild history.")
    tables = ["simulation_events", "health_history", "predictions", "alerts", "recovery_operations"]
    tabs = st.tabs([x.replace("_", " ").title() for x in tables])
    for tab, table in zip(tabs, tables):
        with tab:
            rows = db.query(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 1000")
            if rows:
                frame = pd.DataFrame(rows)
                st.dataframe(frame, use_container_width=True, hide_index=True)
                st.download_button(f"Export {table} as CSV", frame.to_csv(index=False), file_name=f"{table}.csv", mime="text/csv", key=f"export_{table}")
            else: st.info("No records in this table yet.")

elif page == "Model & Dataset":
    st.title("Model & Dataset")
    df = generate_synthetic_dataset()
    st.markdown("<div class='callout'>This prototype generates synthetic examples for demonstration. Model scores and test metrics do not establish real-world disk-failure accuracy.</div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Generated rows", f"{len(df):,}")
    m2.metric("Features", len(df.columns)-1)
    m3.metric("Label", "failure_label")
    st.markdown("### Preview training data")
    st.dataframe(df.head(30), use_container_width=True, hide_index=True)
    st.download_button("Download synthetic dataset CSV", df.to_csv(index=False), file_name="synthetic_disk_health.csv", mime="text/csv")
    uploaded = st.file_uploader("Upload labeled CSV", type=["csv"])
    if uploaded:
        try:
            custom = pd.read_csv(uploaded)
            missing = set(df.columns) - set(custom.columns)
            if missing: st.error("Missing required columns: " + ", ".join(sorted(missing)))
            else:
                st.success(f"Dataset schema accepted: {len(custom)} rows.")
                if st.button("Train on uploaded dataset", type="primary"):
                    model, metrics = train_model(custom, MODEL_DIR / "uploaded_rf.joblib")
                    st.session_state.model, st.session_state.metrics = model, metrics
                    st.json(metrics)
        except Exception as exc: st.error(f"Dataset error: {exc}")

elif page == "System Information":
    st.title("System Information")
    st.markdown("""
    RAID Intelligence provides a virtual storage environment for monitoring disk health, analyzing failure risk, managing a RAID 5 array, and reviewing recovery activity.

    **Available capabilities**
    - Virtual disk telemetry and simulated read/write workloads.
    - Rule-based health-risk scoring and synthetic-data model evaluation.
    - RAID 5 healthy, degraded, rebuilding, and failed states.
    - Replacement capacity validation and incremental rebuild progress.
    - SQLite event/history records and CSV export.

    **Operating boundaries**
    - Disk telemetry, failure injection, and recovery operations are simulated; no physical storage devices are controlled.
    - Synthetic training labels are not evidence of real-world predictive accuracy.
    - The score is not a calibrated probability of disk failure.
    - RAID redundancy does not replace backups.
    """)
    st.markdown("### Architecture")
    st.code("Streamlit dashboard → Disk simulator → RAID / failure / recovery engines → Risk engine + Random Forest → SQLite event history", language="text")
    st.caption(f"Database location: {DB_PATH}")

st.markdown("<div class='footer-note'>RAID Intelligence · Storage Monitoring &amp; Recovery Platform</div>", unsafe_allow_html=True)
