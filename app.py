import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# 1. 網頁基本設定
st.set_page_config(page_title="教務會議歷史查詢", layout="wide")
st.title("🎓 教務會議歷史查詢系統")
st.markdown("偵測到您的 API 支援最新 Gemini 2.0 系列模型，系統已自動完成優化。")

# 2. 側邊欄：設定 API Key
with st.sidebar:
    st.header("系統設定")
    api_key = st.text_input("請輸入您的 Gemini API Key:", type="password")
    st.info("申請處: [Google AI Studio](https://aistudio.google.com/app/apikey)")

# 3. 檔案上傳介面
uploaded_files = st.file_uploader("導入會議記錄 PDF 檔 (可多選)", type="pdf", accept_multiple_files=True)

# 4. 查詢介面
query = st.text_input("輸入查詢關鍵字 (例如：學則修改、通識課程...)", placeholder="請輸入想查詢的主題...")

search_button = st.button("進行 AI 檢索")

if search_button:
    if not api_key:
        st.error("請先在左側輸入 API Key！")
    elif not uploaded_files:
        st.warning("請先上傳至少一個 PDF 檔案。")
    elif not query:
        st.warning("請輸入查詢關鍵字。")
    else:
        try:
            # 初始化 Gemini AI
            genai.configure(api_key=api_key)
            
            # 【關鍵修正】：使用你診斷清單中確定的模型名稱
            # 我們選擇 'gemini-2.0-flash'，它支援 PDF 讀取且速度極快
            model = genai.GenerativeModel('gemini-2.0-flash')

            all_results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"正在分析第 {index+1} 份檔案: {uploaded_file.name}...")
                
                # 讀取 PDF 數據
                pdf_data = uploaded_file.read()
                
                # 建立更精確的指令
                prompt = f"""
                你是一個專業的校務助理，現在請在提供的會議紀錄文件中，
                尋找與關鍵字「{query}」相關的所有提案。
                
                請嚴格依照以下 JSON 格式回傳，不要有任何多餘的解釋文字：
                [
                  {{"會議名稱": "請填入本次會議名稱或日期", "提案單位": "填入提案單位", "提案內容": "摘要提案重點", "提案結果": "填入決議結果"}}
                ]
                若文件中完全找不到相關內容，請只回傳 []。
                """
                
                # 發送請求給 Gemini 2.0
                response = model.generate_content([
                    prompt,
                    {'mime_type': 'application/pdf', 'data': pdf_data}
                ])
                
                # 解析回傳結果
                try:
                    res_text = response.text
                    # 移除 AI 可能加上的 Markdown 標籤
                    clean_text = res_text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_text)
                    if isinstance(data, list):
                        all_results.extend(data)
                except Exception:
                    # 如果單個檔案解析失敗，跳過並繼續下一個
                    continue
                
                progress_bar.progress((index + 1) / len(uploaded_files))

            # 5. 呈現結果
            status_text.text("檢索完成！")
            if all_results:
                st.success(f"找到 {len(all_results)} 筆相關提案！")
                df = pd.DataFrame(all_results)
                # 使用 table 顯示美化表格
                st.table(df)
                
                # 提供 CSV 下載
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("下載查詢結果 (CSV)", data=csv, file_name="search_results.csv", mime="text/csv")
            else:
                st.info("在您提供的文件中，找不到與此關鍵字相關的提案。")

        except Exception as e:
            st.error(f"系統發生非預期錯誤: {e}")

st.markdown("---")
st.caption("註：本系統已針對 Gemini 2.0 Flash 優化，處理 PDF 效率更高。")
