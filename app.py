import streamlit as st
import pandas as pd
import re
import datetime

# --- 州缩写映射表 ---
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
ALL_STATES = {**STATE_ABBR, **{v: v for v in STATE_ABBR.values()}}

# --- 智能解析函数 ---
def extract_address_parts(text, handle=""):
    lines = [l.strip() for l in text.strip().replace('\r', '\n').split('\n') if l.strip()]
    result = {
        'Recipient First Name': handle,
        'Recipient Last Name': handle,
        'Recipient Address Line 1': '',
        'Recipient Address Line 2': '',
        'Recipient Address Line 3': '',
        'Recipient Address Town/City': '',
        'Recipient State': '',
        'Recipient ZIP Code': '',
        'Recipient Phone': '',
        '解析备注错误': ''
    }

    # 手机号
    combined = " ".join(lines)
    phone_match = re.search(r'(\+?1?[-\s\.]?\(?\d{3}\)?[-\s\.]?\d{3}[-\s\.]?\d{4})', combined)
    if phone_match:
        result['Recipient Phone'] = phone_match.group(1)

    # 姓名（第一行）
    if lines:
        name_parts = re.findall(r'\b[\w\-]+\b', lines[0])
        if len(name_parts) >= 2:
            result['Recipient First Name'] = name_parts[0]
            result['Recipient Last Name'] = name_parts[-1]
        else:
            result['Recipient First Name'] = result['Recipient Last Name'] = lines[0]

    # 查找城市/州/ZIP结尾片段，并分割前面为街道
    city_state_zip = None
    for idx, line in enumerate(reversed(lines)):
        match = re.search(r'([A-Za-z .\-]+),?\s*([A-Za-z]{2}|[A-Za-z .\-]+)\s+(\d{5})(?!\d)', line)
        if match:
            city = match.group(1).strip().title()
            state_raw = match.group(2).strip().lower()
            zip_code = match.group(3).strip()
            state = ALL_STATES.get(state_raw.lower(), state_raw.upper()[:2])
            result['Recipient Address Town/City'] = city
            result['Recipient State'] = state
            result['Recipient ZIP Code'] = zip_code
            city_state_zip = line
            break

    # 提取 address1、address2
    addr_lines = []
    for line in lines[1:]:
        # 跳过已被识别为 city/state/zip 的行
        if line == city_state_zip:
            continue
        if re.search(r'\b(apt|unit|suite|ste|#)\b', line.lower()):
            result['Recipient Address Line 2'] = line
        elif re.search(r'\d+', line):
            addr_lines.append(line)
    if addr_lines:
        result['Recipient Address Line 1'] = addr_lines[0]

    return result

# --- USPS 模板 ---
def create_fixed_usps_template(n):
    return pd.DataFrame({
        'Reference ID': [f"R{i+1}" for i in range(n)],
        'Reference ID 2': [f"RR{i+1}" for i in range(n)],
        'Shipping Date': [datetime.date.today().strftime('%Y-%m-%d')] * n,
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

# --- Streamlit 主程序 ---
st.title("USPS 地址批量解析工具（严格格式修复版）")
uploaded = st.file_uploader("上传水单 CSV（含 '发货备注' 和 Handle）", type="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    if '发货备注' not in df.columns or 'Handle' not in df.columns:
        st.error("缺少 '发货备注' 或 'Handle' 列")
    else:
        parsed = df.apply(lambda row: extract_address_parts(row['发货备注'], str(row['Handle'])), axis=1)
        parsed_df = pd.DataFrame(list(parsed))
        usps_df = create_fixed_usps_template(len(df))
        for col in parsed_df.columns:
            if col in usps_df.columns:
                usps_df[col] = parsed_df[col]
        st.success("🎉 地址识别成功，结果如下：")
        st.dataframe(usps_df)
        st.download_button("📥 下载 USPS 地址文件", usps_df.to_csv(index=False).encode('utf-8-sig'), "usps_filled.csv")
