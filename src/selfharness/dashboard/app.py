"""Streamlit viewer for saved attempts and rule-gate decisions."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
ROOT=Path(__file__).resolve().parents[3]
RUNS=ROOT/"runs"
def read_rows(path):
    if not path.exists():return []
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:continue
    return rows
st.set_page_config(page_title="SelfHarness",layout="wide")
st.title("SelfHarness evaluation dashboard")
st.caption("Explore attempts, validation comparisons, cost, and audit flags. Demo values are synthetic.")
dirs=sorted((p for p in RUNS.iterdir() if p.is_dir()),key=lambda p:p.stat().st_mtime,reverse=True) if RUNS.exists() else []
if not dirs:st.info("No runs found. Start with selfharness demo.");st.stop()
selected=st.selectbox("Run",[p.name for p in dirs]);folder=RUNS/selected
if selected=="demo":
    report=json.loads((folder/"demo-report.json").read_text(encoding="utf-8"));st.warning(report["note"]);st.json(report)
else:
    attempts=read_rows(folder/"attempts.jsonl")
    if attempts:
        frame=pd.DataFrame(attempts);valid=frame[frame.status.isin(["passed","failed_tests"])]
        cols=st.columns(4);cols[0].metric("Valid attempts",len(valid));cols[1].metric("Pass rate",f"{valid.passed.mean():.1%}" if len(valid) else "n/a")
        cols[2].metric("Estimated cost",f"${frame.estimated_cost_usd.sum():.4f}");cols[3].metric("Flagged attempts",int(frame.audit_flags.map(bool).sum()))
        st.dataframe(frame,use_container_width=True)
    gate=folder/"gate-summary.json"
    if gate.exists():
        data=json.loads(gate.read_text(encoding="utf-8"));st.subheader("Validation gate");st.metric(data["decision"],data["reason"])
        st.json({k:data[k] for k in ("baseline","candidate","paired_delta","paired_outcomes","critical_audit_flags")})
        st.dataframe(pd.DataFrame(data.get("per_task_pairs",[])),use_container_width=True)
