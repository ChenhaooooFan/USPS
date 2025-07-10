
import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.title("📦 USPS 地址批量生成工具")
st.markdown("只需上传包含“发货备注”的表格，系统将自动提取地址并生成 USPS 模板格式的文件。")

remarks_file = st.file_uploader("📤 上传包含“发货备注”的 CSV 文件", type="csv")

# 内嵌 USPS 模板结构（可根据实际字段微调）
def create_usps_template(n):
    return pd.DataFrame({
        'Reference ID': [''] * n,
        'Reference ID2': [''] * n,
        'Shipping Date': [''] * n,
        'Item Description': ['PressOnNails'] * n,
        'Item Quantity': [1] * n,
        'Item Weight (lb)': [0.25] * n,
        'Item Weight (oz)': [0] * n,
        'Item Value': [100] * n,
        'HS Tariff #': [''] * n,
        'Country of Origin': ['US'] * n,
        'Recipient First Name': [''] * n,
        'Recipient Last Name': [''] * n,
        'Recipient Company': [''] * n,
        'Recipient Address Line 1': [''] * n,
        'Recipient Address Line 2': [''] * n,
        'Recipient Address Town/City': [''] * n,
        'Recipient State': [''] * n,
        'Recipient ZIP Code': [''] * n,
        'Recipient Country': ['US'] * n,
    })

def parse_remark(remark, handle):
    first_name = last_name = handle
    address1 = address2 = city = state = zip_code = ""

    if isinstance(remark, str):
        parts = remark.strip().split('\n')
        parts = [p.strip() for p in parts if p.strip()]
        name_pattern = re.compile(r'^[A-Za-z]+\s+[A-Za-z]+$')

        for part in parts:
            if name_pattern.match(part):
                first_name, last_name = part.split(' ', 1)
                break

        city_zip_match = re.search(r'([A-Za-z\s]+),?\s*([A-Z]{2})\s+(\d{5})', remark)
        if city_zip_match:
            city = city_zip_match.group(1).strip()
            state = city_zip_match.group(2)
            zip_code = city_zip_match.group(3)

        address_lines = [line for line in parts if not name_pattern.match(line) and not re.search(r'\d{5}', line)]
        if len(address_lines) >= 1:
            address1 = address_lines[0]
        if len(address_lines) >= 2:
            address2 = address_lines[1]

    return pd.Series([first_name, last_name, address1, address2, city, state, zip_code])

if remarks_file:
    remarks_df = pd.read_csv(remarks_file)
    if '发货备注' not in remarks_df.columns or 'Handle' not in remarks_df.columns:
        st.error("❌ 请确保文件包含列：'发货备注' 和 'Handle'")
    else:
        st.success("📄 文件上传成功，正在处理...")

        parsed_data = remarks_df.apply(lambda row: parse_remark(row['发货备注'], row['Handle']), axis=1)
        parsed_data.columns = [
            'Recipient First Name',
            'Recipient Last Name',
            'Recipient Address Line 1',
            'Recipient Address Line 2',
            'Recipient Address Town/City',
            'Recipient State',
            'Recipient ZIP Code'
        ]

        # 创建模板
        n = len(remarks_df)
        usps_df = create_usps_template(n)

        # 更新模板内容
        usps_df.update(parsed_data)
        today_str = datetime.today().strftime("%Y-%m-%d")
        usps_df['Shipping Date'] = today_str
        usps_df['Reference ID'] = [f'R{100001 + i}' for i in range(n)]
        usps_df['Reference ID2'] = [f'RR{100001 + i}' for i in range(n)]

        st.dataframe(usps_df.head(10))

        # 导出功能
        def to_csv_download(df):
            output = BytesIO()
            df.to_csv(output, index=False)
            return output.getvalue()

        csv_bytes = to_csv_download(usps_df)

        st.download_button(
            label="📥 下载 USPS 导出文件",
            data=csv_bytes,
            file_name="usps_output.csv",
            mime="text/csv"
        )
