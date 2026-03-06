import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import time # 加入時間延遲功能

# 1. 網頁基本設定
st.set_page_config(page_title="教務會議歷史查詢", layout="wide")
st.title("🎓 教務會議歷史查詢系統")

# 2. 側邊欄：設定 API Key
with st.sidebar:
    st.header("系統設定")
    api_key = st.text_input("請輸入您的 Gemini API Key:", type="password")
    st.info("申請處: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    st.warning("提示：如果遇到 429 錯誤，請稍候一分鐘再試，這是免費版的頻率限制。")

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
            
            # 【關鍵修正】：切換回最穩定的 1.5-flash，並確保免費額度可用
            model = genai.GenerativeModel('gemini-1.5-flash')

            all_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"正在分析第 {index+1} 份檔案: {uploaded_file.name}...")
                
                # 讀取 PDF 數據
                pdf_data = uploaded_file.read()
                
                # 建立指令
                prompt = f"""
                請在文件中尋找與關鍵字「{query}」相關的所有提案。
                
                請嚴格依照以下 JSON 格式回傳列表，不要有額外解釋：
                [
                  {{"會議名稱": "會議名稱", "提案單位": "單位", "提案內容": "內容摘要", "提案結果": "決議"}}
                ]
                若找不到請回傳 []。
                """
                
                # 呼叫 AI
                response = model.generate_content([
                    prompt,
                    {'mime_type': 'application/pdf', 'data': pdf_data}
                ])
                
                # 解析結果
                try:
                    res_text = response.text
                    clean_text = res_text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_text)
                    if isinstance(data, list):
                        all_results.extend(data)
                except Exception:
                    pass
                
                # 更新進度
                progress_bar.progress((index + 1) / len(uploaded_files))
                
                # 【防 429 關鍵】：每處理完一個檔案，強制暫停 3 秒，避免衝撞免費版頻率限制
                if len(uploaded_files) > 1:
                    time.sleep(3)

            # 5. 呈現結果
            status_text.text("檢索完成！")
            if all_results:
                st.success(f"找到 {len(all_results)} 筆相關提案！")
                df = pd.DataFrame(all_results)
                st.table(df)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("下載查詢結果 (CSV)", data=csv, file_name="search_results.csv", mime="text/csv")
            else:
                st.info("查無相關提案。")

        except Exception as e:
            if "429" in str(e):
                st.error("錯誤 429：請求太頻繁了。Google 免費版限制每分鐘只能處理少量檔案。請等一分鐘後，改為一次只上傳 1-2 個檔案試試看。")
            else:
                st.error(f"發生錯誤: {e}")

st.markdown("---")
st.caption("提示：若檔案很大或很多，請分批上傳以符合免費版 API 規範。")
