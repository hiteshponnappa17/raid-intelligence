import pandas as pd
import streamlit as st
def render_events(db,limit=30):
    rows=db.query("SELECT timestamp,event_type,disk_id,description FROM simulation_events ORDER BY id DESC LIMIT ?",(limit,))
    if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    else: st.info("No events recorded yet.")
