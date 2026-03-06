import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# 網頁設定
st.set_page_config(page_title="教務會議歷史查詢", layout="wide")
st.title("🎓 教務會議歷史查詢系統")

# 側邊欄
with st.sidebar:
    st.header("系統設定")
    api_key = st.text_input("請輸入您的 Gemini API Key:", type="password")
    st.info("申請處: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    
    # 新增：診斷按鈕 (如果出錯可以按)
    if st.button("診斷：檢查可用模型"):
        if api_key:
            genai.configure(api_key=api_key)
            models = [m.name for m in genai.list_models()]
            st.write("您的 API 目前支援：", models)
        else:
            st.warning("請先輸入 API Key")

# 檔案上傳
uploaded_files = st.file_uploader("導入會議記錄 PDF", type="pdf", accept_multiple_files=True)
query = st.text_input("輸入查詢關鍵字")

if st.button("進行 AI 檢索"):
    if not api_key or not uploaded_files or not query:
        st.error("請確認 Key、檔案與關鍵字皆已輸入。")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # 【修正重點】使用更具相容性的模型名稱格式
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

            all_results = []
            progress_bar = st.progress(0)
            
            for index, uploaded_file in enumerate(uploaded_files):
                pdf_data = uploaded_file.read()
                
                # 建立指令
                prompt = f"請在文件中找關於『{query}』的提案，以 JSON 格式回傳列表：[{{'會議名稱': '...','提案單位': '...','提案內容': '...','提案結果': '...'}}]"
                
                # 呼叫 AI
                response = model.generate_content([
                    prompt,
                    {'mime_type': 'application/pdf', 'data': pdf_data}
                ])
                
                # 處理回傳
                try:
                    txt = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(txt)
                    if isinstance(data, list):
                        all_results.extend(data)
                except:
                    continue
                
                progress_bar.progress((index + 1) / len(uploaded_files))

            if all_results:
                st.success("查詢成功！")
                st.table(pd.DataFrame(all_results))
            else:
                st.info("未找到相關提案。")

        except Exception as e:
            st.error(f"發生錯誤: {e}")
            st.info("嘗試建議：請確認 GitHub 上的 requirements.txt 是否已改為 google-generativeai>=0.8.3")
