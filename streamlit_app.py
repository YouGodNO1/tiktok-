import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="TikTok广告数据分析", layout="wide")
st.title("📊 TikTok英国广告报表分析工具")
st.markdown("支持后台直接导出CSV上传，自动计算ROAS/ACOS/CTR/CVR")

# 上传文件
upload_file = st.file_uploader("上传TikTok广告CSV报表", type="csv")
if upload_file:
    df = pd.read_csv(upload_file)
    st.success("✅ 文件上传成功！")

    # 字段适配（TikTok后台标准字段）
    needed_cols = ["Date", "Campaign name", "Ad group name", "Ad name", "Impressions", "Clicks", "Spend", "Orders", "Revenue"]
    check_ok = all(c in df.columns for c in needed_cols)
    if not check_ok:
        st.warning("⚠️ 字段不匹配！请确认报表包含：Date, Campaign name, Ad group name, Ad name, Impressions, Clicks, Spend, Orders, Revenue")
    else:
        # 清洗
        df = df[df["Impressions"] > 0].copy()
        # 计算指标
        df["CTR"] = df["Clicks"] / df["Impressions"]
        df["CVR"] = df["Orders"] / df["Clicks"]
        df["ACOS"] = df["Spend"] / df["Revenue"]
        df["ROAS"] = df["Revenue"] / df["Spend"]

        # 大盘汇总卡片
        total_spend = df["Spend"].sum()
        total_rev = df["Revenue"].sum()
        total_orders = df["Orders"].sum()
        avg_roas = total_rev / total_spend if total_spend>0 else 0
        avg_acos = total_spend / total_rev if total_rev>0 else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("总花费", f"£{total_spend:.2f}")
        col2.metric("总GMV", f"£{total_rev:.2f}")
        col3.metric("总订单", f"{total_orders:.0f}")
        col4.metric("整体ROAS", f"{avg_roas:.2f}")
        col5.metric("整体ACOS", f"{avg_acos:.2%}")

        # 侧边筛选
        st.sidebar.header("🔍 筛选条件")
        camp_list = ["全部"] + sorted(df["Campaign name"].unique().tolist())
        sel_camp = st.sidebar.selectbox("选择广告系列", camp_list)
        if sel_camp != "全部":
            df = df[df["Campaign name"] == sel_camp]

        # 阈值告警设置
        acos_threshold = st.sidebar.number_input("ACOS告警阈值(例：0.3=30%)", min_value=0.0, max_value=2.0, value=0.3)
        df["告警标记"] = df["ACOS"].apply(lambda x: "🔴超标" if x>acos_threshold else "🟢正常")

        st.subheader("📋 明细数据表（带指标）")
        st.dataframe(df, use_container_width=True)

        st.subheader("📈 每日ROAS & ACOS趋势")
        day_group = df.groupby("Date").agg({"ROAS":"mean","ACOS":"mean","Spend":"sum","Revenue":"sum"}).reset_index()
        fig1 = px.line(day_group, x="Date", y=["ROAS","ACOS"], title="每日ROAS / ACOS")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("📊 广告组ROAS对比")
        adgroup_sum = df.groupby("Ad group name").agg({"ROAS":"mean","ACOS":"mean","Spend":"sum","Revenue":"sum"}).reset_index()
        fig2 = px.bar(adgroup_sum, x="Ad group name", y="ROAS", color="ACOS", title="各广告组ROAS")
        st.plotly_chart(fig2, use_container_width=True)

        # 导出处理好的文件
        @st.cache_data
        def convert_df(out_df):
            return out_df.to_csv(index=False).encode('utf-8')
        csv_down = convert_df(df)
        st.download_button("💾 下载分析后CSV", csv_down, "tiktok_analyzed.csv", "text/csv")

else:
    st.info("⬆️ 上传报表后开始分析，报表直接从TikTok广告后台导出即可，不用修改")
