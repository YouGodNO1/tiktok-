import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="TikTok Shop店铺数据看板", layout="wide")
st.title("🏪 TikTok Shop 店铺数据罗盘分析")
st.markdown("自动识别后台导出的【关键指标】报表，支持 xlsx / csv")

upload_file = st.file_uploader("上传 Shop Analytics_Key metrics 报表", type=["xlsx", "csv"])

if upload_file:
    raw = None
    if upload_file.name.endswith(".xlsx"):
        raw = pd.read_excel(upload_file, header=None)
    else:
        for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                raw = pd.read_csv(upload_file, header=None, encoding=enc)
                break
            except:
                upload_file.seek(0)
                continue

    if raw is None:
        st.error("文件读取失败")
        st.stop()

    # 找【日期】所在行作为表头
    header_row_idx = None
    for i in range(min(len(raw), 30)):
        cell_val = str(raw.iloc[i, 0]).strip()
        if cell_val == "日期":
            header_row_idx = i
            break

    if header_row_idx is None:
        st.error("没找到'日期'列，请确认上传的是数据罗盘【关键指标】导出报表")
        st.dataframe(raw.head(20))
        st.stop()

    headers = raw.iloc[header_row_idx].tolist()
    # ✅ 重点修复：过滤空表头，把空名字替换成临时名称，避免报错
    clean_headers = []
    for idx, h in enumerate(headers):
        if pd.isna(h) or str(h).strip() == "":
            clean_headers.append(f"temp_col_{idx}")
        else:
            clean_headers.append(str(h).strip())

    df = raw.iloc[header_row_idx+1:].copy()
    df.columns = clean_headers
    # 只保留日期不为空的行
    df = df.dropna(subset=["日期"])
    df = df[df["日期"].astype(str).str.strip() != ""]

    # 数值列转换，跳过临时空列
    num_cols = [c for c in df.columns if c not in ["日期"] and not c.startswith("temp_col_")]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # 日期解析
    df["日期"] = pd.to_datetime(df["日期"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期")

    st.success(f"✅ 成功读取 {len(df)} 天数据：{df['日期'].min().strftime('%Y-%m-%d')} ~ {df['日期'].max().strftime('%Y-%m-%d')}")

    # 计算衍生指标（先判断列是否存在，防止缺少字段报错）
    if "商品曝光次数" in df.columns and "商品点击量" in df.columns:
        df["点击率CTR"] = df["商品点击量"] / df["商品曝光次数"]
    if "商品点击量" in df.columns and "订单数" in df.columns:
        df["转化率CVR"] = df["订单数"] / df["商品点击量"]
    if "GMV" in df.columns and "退款金额" in df.columns:
        df["退款率"] = df["退款金额"] / df["GMV"]
    if "GMV" in df.columns and "订单数" in df.columns:
        df["客单价"] = df["GMV"] / df["订单数"]

    # 大盘汇总
    total_gmv = df["GMV"].sum() if "GMV" in df.columns else 0
    total_orders = df["订单数"].sum() if "订单数" in df.columns else 0
    total_refund = df["退款金额"].sum() if "退款金额" in df.columns else 0
    total_visitors_click = df["商品点击量"].sum() if "商品点击量" in df.columns else 0
    total_imp = df["商品曝光次数"].sum() if "商品曝光次数" in df.columns else 0
    total_customer = df["客户数"].sum() if "客户数" in df.columns else 0

    avg_refund_rate = total_refund / total_gmv if total_gmv > 0 else 0
    avg_ctr = total_visitors_click / total_imp if total_imp > 0 else 0
    avg_cvr = total_orders / total_visitors_click if total_visitors_click > 0 else 0
    avg_aov = total_gmv / total_orders if total_orders > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("总GMV", f"£{total_gmv:.2f}")
    c2.metric("总订单", f"{total_orders:.0f}")
    c3.metric("总退款率", f"{avg_refund_rate:.1%}")
    c4.metric("点击率CTR", f"{avg_ctr:.2%}")
    c5.metric("转化率CVR", f"{avg_cvr:.2%}")

    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric("客单价", f"£{avg_aov:.2f}")
    c7.metric("总曝光", f"{total_imp:,.0f}")
    c8.metric("总点击", f"{total_visitors_click:,.0f}")
    c9.metric("退款金额", f"£{total_refund:.2f}")
    c10.metric("总客户数", f"{total_customer:.0f}")

    st.divider()

    # 趋势图
    st.subheader("📈 每日 GMV / 订单 / 退款 趋势")
    fig1 = go.Figure()
    if "GMV" in df.columns:
        fig1.add_trace(go.Bar(x=df["日期"], y=df["GMV"], name="GMV (£)", marker_color="#00c3ff"))
    if "订单数" in df.columns:
        fig1.add_trace(go.Scatter(x=df["日期"], y=df["订单数"], name="订单数", yaxis="y2", mode="lines+markers", line=dict(color="#ff6b6b", width=3)))
    if "退款金额" in df.columns:
        fig1.add_trace(go.Scatter(x=df["日期"], y=df["退款金额"], name="退款金额", mode="lines+markers", line=dict(color="#ffd93d", width=2, dash="dot")))
    fig1.update_layout(
        yaxis=dict(title="GMV (£)"),
        yaxis2=dict(title="订单数", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 流量漏斗
    st.subheader("🔻 每日流量转化漏斗")
    fig2 = go.Figure()
    if "商品曝光次数" in df.columns:
        fig2.add_trace(go.Scatter(x=df["日期"], y=df["商品曝光次数"], name="商品曝光", mode="lines+markers"))
    if "商品点击量" in df.columns:
        fig2.add_trace(go.Scatter(x=df["日期"], y=df["商品点击量"], name="商品点击", mode="lines+markers"))
    if "订单数" in df.columns:
        fig2.add_trace(go.Scatter(x=df["日期"], y=df["订单数"], name="订单", mode="lines+markers"))
    fig2.update_layout(legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig2, use_container_width=True)

    # 渠道占比
    st.subheader("📊 各渠道 GMV 占比")
    channel_cols = {
        "直播": "直播归因 GMV",
        "商品卡": "商品卡 GMV",
        "短视频": "视频归因 GMV",
    }
    channel_data = {}
    for label, col in channel_cols.items():
        if col in df.columns:
            channel_data[label] = df[col].sum()
    if channel_data:
        ch_df = pd.DataFrame(list(channel_data.items()), columns=["渠道", "GMV"])
        fig3 = px.pie(ch_df, values="GMV", names="渠道", color_discrete_sequence=["#ff6b6b", "#00c3ff", "#ffd93d"])
        st.plotly_chart(fig3, use_container_width=True)

    # 退款监控
    if "退款率" in df.columns:
        st.subheader("⚠️ 每日退款率监控")
        refund_threshold = st.slider("退款率告警阈值", 0.0, 0.5, 0.15, 0.01)
        df["退款告警"] = df["退款率"].apply(lambda x: "🔴 超标" if x > refund_threshold else "🟢 正常")
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=df["日期"], y=df["退款率"]*100, name="退款率%",
                              marker_color=df["退款率"].apply(lambda x: "#ff4444" if x > refund_threshold else "#00c3ff")))
        fig4.add_hline(y=refund_threshold*100, line_dash="dash", line_color="red", annotation_text=f"阈值 {refund_threshold:.0%}")
        fig4.update_layout(yaxis_title="退款率 (%)")
        st.plotly_chart(fig4, use_container_width=True)

    # 明细表
    st.subheader("📋 每日明细数据")
    show_cols = ["日期","GMV","订单数","客户数","客单价","商品曝光次数","商品点击量","点击率CTR","转化率CVR","退款金额","退款率"]
    show_cols = [c for c in show_cols if c in df.columns]
    st.dataframe(df[show_cols].style.format({
        "日期": lambda x: x.strftime("%m-%d"),
        "GMV": "£{:.2f}", "退款金额": "£{:.2f}", "客单价": "£{:.2f}",
        "点击率CTR": "{:.2%}", "转化率CVR": "{:.2%}", "退款率": "{:.2%}",
        "商品曝光次数": "{:,.0f}", "商品点击量": "{:,.0f}"
    }), use_container_width=True)

    # 下载
    csv_out = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("💾 下载分析后CSV", csv_out, "shop_daily_analyzed.csv", "text/csv")

else:
    st.info("⬆️ 上传数据罗盘导出的 xlsx 报表（文件名类似 Shop Analytics_Key metrics_日期范围.xlsx）")
