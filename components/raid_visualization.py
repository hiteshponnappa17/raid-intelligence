import streamlit as st
def render_raid_summary(s):
    color={"HEALTHY":"#22c55e","DEGRADED":"#f59e0b","REBUILDING":"#3b82f6","FAILED":"#ef4444"}.get(s.state,"#aaa")
    st.markdown(f"<div style='padding:16px;border-radius:12px;border:1px solid {color}'><h2 style='color:{color}'>RAID 5 — {s.state}</h2><p>Data accessible: <b>{s.data_accessible}</b> | Redundancy: <b>{s.redundancy_available}</b></p><p>Raw: {s.total_raw_capacity_gb:.0f} GB | Usable: {s.usable_capacity_gb:.0f} GB</p></div>",unsafe_allow_html=True)
