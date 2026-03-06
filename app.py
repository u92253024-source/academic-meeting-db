import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

# 1. 網頁基本設定
st.set_page_config(page_title="教務會議歷史查詢", layout="wide")
st.title("🎓 教務會議歷史查詢系統")
st.markdown("請導入會議記錄 PDF 檔，系統將透過 AI 幫您精確查詢提案資訊。")

# 2. 側邊欄：設定 API Key (從 Google AI Studio 取得)
with st.sidebar:
    st.header("系統設定")
    api_key = st.text_input("請輸入您的 Gemini API Key:", type="password")
    st.info("您可以到 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請 Key。")

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
            model = genai.GenerativeModel('gemini-1.5-flash')

            all_results = []
            
            with st.spinner('AI 正在翻閱會議紀錄中，請稍候...'):
                for uploaded_file in uploaded_files:
                    # 讀取 PDF 內容 (Gemini 1.5 系列支援直接處理 PDF 數據)
                    pdf_data = uploaded_file.read()
                    
                    # 建立 AI 指令 (Prompt)
                    prompt = f"""
                    你是一個專業的校務助理，現在請在提供的會議紀錄文件中，
                    尋找與關鍵字「{query}」相關的所有提案。
                    
                    請整理成以下格式的 JSON 列表：
                    [
                      {{"會議名稱": "例如：112學年度第1次教務會議", "提案單位": "單位名稱", "提案內容": "簡述內容", "提案結果": "決議結果"}}
                    ]
                    若找不到相關內容，請回傳空的列表 []。
                    請只回傳 JSON 格式內容，不要有額外解釋。
                    """
                    
                    # 發送給 AI (傳送 PDF 檔案與指令)
                    response = model.generate_content([
                        prompt,
                        {'mime_type': 'application/pdf', 'data': pdf_data}
                    ])
                    
                    # 解析 AI 回傳的文字
                    try:
                        # 清理可能的 markdown 標籤
                        clean_text = response.text.replace('```json', '').replace('```', '').strip()
                        import json
                        data = json.loads(clean_text)
                        if isinstance(data, list):
                            all_results.extend(data)
                    except:
                        continue

                # 5. 呈現結果
                if all_results:
                    st.success(f"找到 {len(all_results)} 筆相關提案！")
                    df = pd.DataFrame(all_results)
                    # 重新排序與顯示表格
                    st.table(df)
                    
                    # 提供下載 CSV 功能
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("下載查詢結果表格 (CSV)", data=csv, file_name="search_results.csv", mime="text/csv")
                else:
                    st.info("查無相關提案資訊，請更換關鍵字試試看。")
        except Exception as e:
            st.error(f"發生錯誤: {e}")

st.markdown("---")
st.caption("註：本系統使用 Google Gemini AI 技術，查詢結果僅供參考，請以原始公文為準。")
