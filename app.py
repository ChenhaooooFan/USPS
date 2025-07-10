import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="USPS 批量地址工具", layout="wide")
st.title("📦 USPS 地址批量生成工具（标准格式支持 Apt、City、ZIP 拆分）")

remarks_file = st.file_uploader("📤 上传包含“发货备注”和 Handle 的 CSV 文件", type="csv")

# 固定模板结构
def create_fixed_usps_template(n):
    return pd.DataFrame({
        'Reference ID': [''] * n,
        'Reference ID 2': [''] * n,
        'Shipping Date': [''] * n,
        'Item Description': ['PressOnNails'] * n,
        'Item Quantity': [1] * n,
        'Item Weight (lb)': [0.25] * n,
        'Item Weight (oz)': [0] * n,
        'Item Value': [100] * n,
        'HS Tariff #': [''] * n,
        'Country of Origin': ['US'] * n,
        'Sender First Name': ['Ava'] * n,
        'Sender Middle Initial': [''] * n,
        'Sender Last Name': ['Everly'] * n,
        'Sender Company/Org Name': ['ColorFour LLC'] * n,
        'Sender Address Line 1': ['718 S Hill St'] * n,
        'Sender Address Line 2': [''] * n,
        'Sender Address Line 3': [''] * n,
        'Sender Address Town/City': ['Los Angeles'] * n,
        'Sender State': ['CA'] * n,
        'Sender Country': ['US'] * n,
        'Sender ZIP Code': ['90014'] * n,
        'Sender Urbanization Code': [''] * n,
        'Ship From Another ZIP Code': [''] * n,
        'Sender Email': ['support@colorfour.com'] * n,
        'Sender Cell Phone': ['1234567890'] * n,
        'Recipient Country': ['US'] * n,
        'Recipient First Name': [''] * n,
        'Recipient Middle Initial': [''] * n,
        'Recipient Last Name': [''] * n,
        'Recipient Company/Org Name': [''] * n,
        'Recipient Address Line 1': [''] * n,
        'Recipient Address Line 2': [''] * n,
        'Recipient Address Line 3': [''] * n,
        'Recipient Address Town/City': [''] * n,
        'Recipient Province': [''] * n,
        'Recipient State': [''] * n,
        'Recipient ZIP Code': [''] * n,
        'Recipient Urbanization Code': [''] * n,
        'Recipient Phone': [''] * n,
        'Recipient Email': [''] * n,
        'Service Type': ['First-Class Package International Service'] * n,
        'Package Type': ['Package'] * n,
        'Package Weight (lb)': [0.25] * n,
        'Package Weight (oz)': [0] * n,
        'Length': [6] * n,
        'Width': [4] * n,
        'Height': [1.6] * n,
        'Girth': [''] * n,
        'Insured Value': [100] * n,
        'Contents': ['Merchandise'] * n,
        'Contents Description': ['Press-on nails'] * n,
        'Package Comments': [''] * n,
        'Customs Form Reference #': [''] * n,
        'License #': [''] * n,
        'Certificate #': [''] * n,
        'Invoice #': [''] * n,
    })

# 改进的地址解析函数
def parse_usps_remark(remark, handle):
    first_name = last_name = handle
    addr_line1 = addr_line2 = city = state = zip_code = ""

    if isinstance(remark, str):
        lines = [line.strip() for line in remark.strip().split('\n') if line.strip()]

        # 姓名提取
        if len(lines) > 0 and re.match(r'^[A-Za-z\\-]+\\s+[A-Za-z\\-\\.]+$', lines[0]):
            parts = lines[0].split(' ', 1)
            first_name, last_name = parts[0], parts[1]
            lines = lines[1:]

        # 地址提取
        for i, line in enumerate(lines):
            if re.search(r'\\d+', line):
                if re.search(r'\\b(apt|unit|ste|suite|#)\\b', line.lower()):
                    addr_line2 = line
                else:
                    addr_line1 = line
                lines.pop(i)
                break

        # 公寓行提取（剩余行中找 apt/unit/ste）
        for i, line in enumerate(lines):
            if re.search(r'\\b(apt|unit|ste|suite|#)\\b', line.lower()):
                addr_line2 = line
                break

        # 城市、州、邮编提取
        for line in lines:
            match = re.search(r'([A-Za-z\\s\\.]+),\\s*([A-Z]{2})\\s+(\\d{5})', line)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                zip_code = match.group(3).strip()
                break

    return pd.Series([first_name, last_name, addr_line1, addr_line2, city, state, zip_code])

# 主程序逻辑
if remarks_file:
    remarks_df = pd.read_csv(remarks_file)
    if '发货备注' not in remarks_df.columns or 'Handle' not in remarks_df.columns:
        st.error("❌ 请确保文件包含列：'发货备注' 和 'Handle'")
    else:
        st.success("✅ 文件上传成功，正在解析地址...")

        parsed_df = remarks_df.apply(lambda row: parse_usps_remark(row['发货备注'], row['Handle']), axis=1)
        parsed_df.columns = [
            'Recipient First Name',
            'Recipient Last Name',
            'Recipient Address Line 1',
            'Recipient Address Line 2',
            'Recipient Address Town/City',
            'Recipient State',
            'Recipient ZIP Code'
        ]

        n = len(parsed_df)
        filled_df = create_fixed_usps_template(n)
        filled_df.update(parsed_df)

        filled_df['Shipping Date'] = datetime.today().strftime("%Y-%m-%d")
        filled_df['Reference ID'] = [f'R{100001 + i}' for i in range(n)]
        filled_df['Reference ID 2'] = [f'RR{100001 + i}' for i in range(n)]

        st.dataframe(filled_df.head(10))

        def convert_df(df):
            output = BytesIO()
            df.to_csv(output, index=False)
            return output.getvalue()

        st.download_button(
            label="📥 下载 USPS 地址文件",
            data=convert_df(filled_df),
            file_name="usps_addresses.csv",
            mime="text/csv"
        )
