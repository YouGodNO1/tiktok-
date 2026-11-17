import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="TikTok Shop店铺数据分析", layout="wide")
st.title("🏪 TikTok Shop英国店铺数据罗盘分析")
st.markdown("上传Seller Center数据罗盘导出CSV，自动计算转化率、退款率、渠道拆解")

upload_file = st.file_uploader("上传店铺罗盘CSV报表", type=["csv","xlsx"])
if upload_file:
    # 先读取，打印全部表头用来调试
    if upload_file.name.endswith(".csv"):
        df = pd.read_csv(upload_file)
    else:
        df = pd.read_excel(upload_file)
    st.success("✅ 文件读取成功！")
    st.subheader("📌 你的文件里面所有表头（复制发给我）")
    st.write(df.columns.tolist())
    st.subheader("📌 前5行预览")
    st.dataframe(df.head())

    # 先暂停原来的字段校验，我们先拿到你的表头
    st.info("上面就是你这份报表真实的字段名称，把这一段复制给我，我改成适配你报表的代码！")

else:
    st.info("⬆️ 上传【Seller Center数据罗盘】导出报表，不是广告后台报表！")
