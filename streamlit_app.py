import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="TikTok Shop店铺数据分析", layout="wide")
st.title("🏪 TikTok Shop英国店铺数据罗盘分析")
st.markdown("上传Seller Center数据罗盘导出CSV，自动计算转化率、退款率、渠道拆解")

upload_file = st.file_uploader("上传店铺罗盘CSV报表", type=["csv","xlsx"])
if upload_file:
    df = None
    # 依次尝试常用编码，解决TikTok导出csv编码报错
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            if upload_file.name.endswith(".csv"):
                df = pd.read_csv(upload_file, encoding=enc)
            else:
                df = pd.read_excel(upload_file)
            break
        except Exception:
            upload_file.seek(0) # 重置文件指针，下一个编码重试
            continue
    if df is None:
        st.error("❌ 所有编码尝试失败，文件无法读取")
    else:
        st.success("✅ 文件读取成功！")
        st.subheader("📌 你的文件里面所有表头（复制发给我）")
        st.write(df.columns.tolist())
        st.subheader("📌 前5行预览")
        st.dataframe(df.head())
        st.info("上面就是你这份报表真实的字段名称，把这一段复制给我，我改成适配你报表的正式分析代码！")
else:
    st.info("⬆️ 上传【Seller Center数据罗盘】导出报表，不是广告后台报表！")
