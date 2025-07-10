import streamlit as st
import pandas as pd
import re
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="USPS 地址生成工具", layout="wide")
st.title("📦 USPS 地址批量生成工具（智能拆分 Apt、City、ZIP + 电话提取）")

remarks_file = st.file_uploader("📤 上传包含“发货备注”和 Handle 的 CSV 文件", type="csv")

# ✅ 州名映射表（全称转缩写）
STATE_ABBR = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
    'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
    'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND',
    'ohio': 'OH', 'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI',
    'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
    'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
    'wisconsin': 'WI', 'wyoming': 'WY'
}

def normalize_state(state_str):
    state_str = state_str.strip().lower()
    return STATE_ABBR.get(state_str, state_str.upper()[:2])

# ✅ 智能解析发货备注
def smart_parse_remark(remark, handle):
    first_name = last_name = handle
    addr1 = addr2 = city = state = zip_code = phone = ""
    error = ""

    if isinstance(remark, str):
        remark = remark.replace('\r', '\n')
        lines = [line.strip() for line in remark.split('\n') if line.strip()]
        combined = " ".join(lines)

        # 📞 手机号提取
        phone_match = re.search(r'\+?1?[-\s\.]?\(?\d{3}\)?[-\s\.]?\d{3}[-\s\.]?\d{4}', combined)
        if phone_match:
            phone = phone_match.group(0)

        # 🙋 姓名提取
        name_match = re.match(r'^([A-Z][a-zA-Z\-]+)\s+([A-Z][a-zA-Z\-\.]+)', lines[0])
        if name_match:
            first_name = name_match.group(1)
            last_name = name_match.group(2)
            lines = lines[1:]

        # 🏙️ 城市+州+ZIP 提取（限制不能包含街道）
        for i in reversed(range(len(lines))):
            match = re.search(r'([A-Za-z\s]+?),\s*([A-Za-z]{2,})\s*(\d{5})$', lines[i])
            if match:
                city = match.group(1).strip()
                state = normalize_state(match.group(2))
                zip_code = match.group(3)
                lines.pop(i)
                break
        else:
            error = "⚠️ 缺失城市/州/邮编"

        # 🏠 地址识别
        for line in lines:
            if re.search(r'\d+', line):
                if re.search(r'\b(apt|unit|ste|suite|#)\b', line.lower()):
                    addr2 = line
                elif not addr1:
                    addr1 = line

    return pd.Series([
        first_name, last_name,
        addr1, addr2, city, state, zip_code,
        phone, error
    ])

# 📦 固定 USPS 模板结构
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
        '解析备注': [''] * n
    })

# 🚀 主程序
if remarks_file:
    remarks_df = pd.read_csv(remarks_file)
    if '发货备注' not in remarks_df.columns or 'Handle' not in remarks_df.columns:
        st.error("❌ 文件中必须包含列：'发货备注' 和 'Handle'")
    else:
        st.success("✅ 文件上传成功，正在解析地址中...")

        parsed_df = remarks_df.apply(lambda row: smart_parse_remark(row['发货备注'], row['Handle']), axis=1)
        parsed_df.columns = [
            'Recipient First Name',
            'Recipient Last Name',
            'Recipient Address Line 1',
            'Recipient Address Line 2',
            'Recipient Address Town/City',
            'Recipient State',
            'Recipient ZIP Code',
            'Recipient Phone',
            '解析备注'
        ]

        n = len(parsed_df)
        result_df = create_fixed_usps_template(n)
        result_df.update(parsed_df)
        result_df['Shipping Date'] = datetime.today().strftime("%Y-%m-%d")
        result_df['Reference ID'] = [f'R{100001 + i}' for i in range(n)]
        result_df['Reference ID 2'] = [f'RR{100001 + i}' for i in range(n)]

        st.dataframe(result_df.head(10))

        def convert_df(df):
            output = BytesIO()
            df.to_csv(output, index=False)
            return output.getvalue()

        st.download_button(
            label="📥 下载 USPS 地址文件",
            data=convert_df(result_df),
            file_name="usps_final_output.csv",
            mime="text/csv"
        )
