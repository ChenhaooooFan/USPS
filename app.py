import streamlit as st
import pandas as pd
import re
import datetime

# === 精确地址解析函数 ===
def extract_address_parts(text, handle=""):
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    full_text = " ".join(lines)

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
        'Recipient Email': '',
        'Recipient Country': 'US',
        '解析备注错误': ''
    }

    # 手机号识别
    phone_match = re.search(r'(\+?1?[-\s.]?\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4})', full_text)
    if phone_match:
        result['Recipient Phone'] = phone_match.group(1).strip()

    # 城市、州、邮编识别（倒序）
    zip_state_city_match = re.search(r'(.+?),\s*([A-Za-z]{2})[, ]+\s*(\d{5})(?!\d)', full_text)
    if zip_state_city_match:
        city = zip_state_city_match.group(1).strip().title()
        state = zip_state_city_match.group(2).strip().upper()
        zip_code = zip_state_city_match.group(3).zfill(5)

        result['Recipient Address Town/City'] = city
        result['Recipient State'] = state
        result['Recipient ZIP Code'] = zip_code

        # 城市之前为地址部分
        address_section = full_text[:zip_state_city_match.start()].strip()

        # Line 2：有 Apt/Unit/Suite
        apt_match = re.search(r'(.*?)(?:\s+)?(apt|unit|suite|#)[\s\-\.]*\w*', address_section, re.IGNORECASE)
        if apt_match:
            result['Recipient Address Line 2'] = apt_match.group(0).strip()

        # Line 1：数字+街道名结构
        address1_match = re.search(r'\d{1,5}[^,\\n]*\s+(Street|St\.?|Rd\.?|Road|Ave\.?|Avenue|Blvd\.?|Drive|Dr\.?|Ln\.?|Way)', address_section, re.IGNORECASE)
        if address1_match:
            result['Recipient Address Line 1'] = address1_match.group(0).strip()
        else:
            result['Recipient Address Line 1'] = address_section
    else:
        result['解析备注错误'] += ' 城市/州/邮编解析失败；'

    # 姓名识别（第一行）
    if lines:
        name_line = lines[0]
        name_parts = re.findall(r'\b[\w\-]+\b', name_line)
        if len(name_parts) >= 2:
            result['Recipient First Name'] = name_parts[0]
            result['Recipient Last Name'] = name_parts[-1]
        else:
            result['Recipient First Name'] = result['Recipient Last Name'] = handle

    return result

# === USPS 模板构造 ===
def create_fixed_usps_template(n):
    return pd.DataFrame({
        'Reference ID': [f"{i+1}" for i in range(n)],
        'Reference ID 2': [f"{i+8}" for i in range(n)],
        'Shipping Date': [datetime.date.today().strftime('%-m/%-d/%y')] * n,
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
        'Sender Address Line 2': ['STE310'] * n,
        'Sender Address Line 3': [''] * n,
        'Sender Address Town/City': ['Los Angeles'] * n,
        'Sender State': ['CA'] * n,
        'Sender Country': ['US'] * n,
        'Sender ZIP Code': ['90014'] * n,
        'Sender Urbanization Code': [''] * n,
        'Ship From Another ZIP Code': [''] * n,
        'Sender Email': ['contact@nailvesta.com'] * n,
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

# === Streamlit App ===
st.title("📦 USPS 标签生成器（精确模板匹配）")

uploaded = st.file_uploader("📤 上传水单文件（包含“发货备注”列）", type="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    if '发货备注' not in df.columns:
        st.error("❌ 缺少“发货备注”列，请检查 CSV 文件格式。")
    else:
        parsed = df['发货备注'].fillna('').apply(lambda x: extract_address_parts(x))
        parsed_df = pd.DataFrame(list(parsed))
        usps_df = create_fixed_usps_template(len(parsed_df))

        for col in parsed_df.columns:
            if col in usps_df.columns:
                usps_df[col] = parsed_df[col]

        st.success("✅ 地址已解析并填入 USPS 模板。")
        st.dataframe(usps_df)

        st.download_button("📥 下载 USPS 标签 CSV", usps_df.to_csv(index=False).encode('utf-8-sig'), "usps_filled.csv")
