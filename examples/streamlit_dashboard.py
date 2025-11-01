"""Streamlit dashboard for exploring BioNeuron outputs in real time.

This example provides:
* incremental inference via manual inputs or uploaded batch files
* novelty score trend chart updated after each inference step
* simulated security module sweep progress for the production modules

Run locally with ``streamlit run examples/streamlit_dashboard.py``.
"""

from __future__ import annotations

import io
import time
from typing import List, Tuple

import numpy as np
import streamlit as st

from bioneuronai.core import BioNet

MODULE_NAMES = [
    "SQL Injection Module",
    "IDOR Detection Module",
    "Enhanced Auth Module",
]

st.set_page_config(page_title="BioNeuron Dashboard", layout="wide")
st.title("BioNeuron AI Dashboard")

if "net" not in st.session_state:
    st.session_state.net = BioNet()
    st.session_state.novelty_history: List[float] = []
    st.session_state.output_log: List[Tuple[List[float], List[float], float]] = []


def run_inference(inputs: Tuple[float, float]) -> Tuple[List[float], float]:
    outputs, _ = st.session_state.net.forward(inputs)
    st.session_state.net.learn(inputs)
    novelty = st.session_state.net.average_novelty()
    st.session_state.novelty_history.append(novelty)
    st.session_state.output_log.append((list(inputs), list(outputs), novelty))
    return list(outputs), novelty


with st.sidebar:
    st.header("輸入控制")
    a_value = st.number_input("輸入 a", value=0.5, format="%.3f")
    b_value = st.number_input("輸入 b", value=0.2, format="%.3f")
    if st.button("執行推論", type="primary"):
        outputs, novelty = run_inference((a_value, b_value))
        st.toast(
            f"輸出: {[round(o, 3) for o in outputs]}  | 新穎性: {novelty:.3f}",
            icon="✅",
        )

    uploaded_file = st.file_uploader("或上傳批次檔", type=["txt", "csv"]) 
    if uploaded_file is not None and st.button("批次處理"):
        text = io.TextIOWrapper(uploaded_file, encoding="utf-8")
        for line in text:
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            try:
                tokens = [token for token in cleaned.replace(",", " ").split() if token]
                values = tuple(float(tok) for tok in tokens)
                if len(values) != 2:
                    raise ValueError("需要兩個數值")
            except Exception as exc:  # noqa: BLE001
                st.toast(f"忽略行 '{cleaned}': {exc}", icon="⚠️")
                continue
            run_inference((values[0], values[1]))
        st.toast("批次輸入處理完成", icon="📦")

    if st.button("啟動安全模組掃描"):
        status_placeholder = st.empty()
        progress = st.progress(0, text="初始化掃描...")
        total = len(MODULE_NAMES)
        for idx, module in enumerate(MODULE_NAMES, start=1):
            progress.progress(idx / total, text=f"{module} 掃描中...")
            status_placeholder.info(f"{module} 正在分析最新的輸入樣本...")
            time.sleep(0.6)
        progress.progress(1.0, text="掃描完成")
        status_placeholder.success("所有安全模組已完成掃描！")


col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("即時輸出紀錄")
    if st.session_state.output_log:
        table_rows = [
            {
                "Input": f"{values[0]:.3f}, {values[1]:.3f}",
                "Layer2 Output": ", ".join(f"{o:.3f}" for o in outputs),
                "Novelty": f"{novelty:.3f}",
            }
            for values, outputs, novelty in st.session_state.output_log[-50:]
        ]
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.caption("尚未有推論資料。請在側欄輸入數值或上傳批次檔。")

    st.subheader("新穎性趨勢")
    novelty_placeholder = st.empty()
    if st.session_state.novelty_history:
        novelty_array = np.array(st.session_state.novelty_history)
        novelty_placeholder.line_chart(novelty_array, height=240)
    else:
        st.caption("等待首次推論以建立趨勢圖。")

with col2:
    st.subheader("模型狀態")
    weights = st.session_state.net.collect_weights()
    st.metric(
        "平均新穎性",
        f"{st.session_state.net.average_novelty():.3f}",
    )
    for idx, vector in enumerate(weights, start=1):
        st.write(f"神經元 {idx} 權重")
        st.progress(min(1.0, float(np.mean(vector))), text=", ".join(f"{w:.3f}" for w in vector))

    st.caption(
        "此範例會在每次推論後即時更新權重平均值與新穎性計算，"
        "並模擬後端安全模組的掃描進度。"
    )
