import streamlit as st
import pandas as pd
import cv2
import numpy as np
import pytesseract
from PIL import Image

st.set_page_config(layout="wide")
st.title("📷→表OCR＋セル修正ツール")

# --- 1. 画像アップロード ---
uploaded = st.file_uploader("1. 表の写真をアップロードしてください", type=["jpg","jpeg","png"])
if not uploaded:
    st.warning("まずは上のボタンから画像を選んでください")
    st.stop()

# --- 2. 画像前処理＋OCRセル抽出関数 ---
@st.cache_data
def ocr_table(img_bytes):
    # OpenCV で読み込み・前処理
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # コントラスト強調＆二値化
    gray = cv2.equalizeHist(gray)
    _, th = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # 縦横線を抽出→テーブルマスク
    vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1,40))
    horz = cv2.getStructuringElement(cv2.MORPH_RECT, (40,1))
    mask = cv2.morphologyEx(th, cv2.MORPH_OPEN, vert) + \
           cv2.morphologyEx(th, cv2.MORPH_OPEN, horz)
    # 輪郭検出→セル矩形
    cnts,_ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.boundingRect(c) for c in cnts if cv2.boundingRect(c)[2]>30 and cv2.boundingRect(c)[3]>20]
    # ソートして行列化（簡易）
    rects = sorted(rects, key=lambda b:(b[1],b[0]))
    texts = []
    for x,y,w,h in rects:
        cell = th[y:y+h, x:x+w]
        txt = pytesseract.image_to_string(cell, lang='jpn', config='--psm 6').strip()
        texts.append((y,x,txt))
    # 行ごとにグルーピング（行間隔閾値で分割）
    rows = []
    current = []
    last_y = None
    for y,x,txt in sorted(texts):
        if last_y is None or abs(y-last_y)<10:
            current.append(txt)
        else:
            rows.append(current)
            current = [txt]
        last_y = y
    if current:
        rows.append(current)
    # DataFrame 化。列数は最大列数に合わせる
    max_cols = max(len(r) for r in rows)
    df = pd.DataFrame([r + [""]*(max_cols-len(r)) for r in rows])
    return df

# OCR実行
img_bytes = uploaded.read()
df = ocr_table(img_bytes)

st.markdown("2. OCR 結果（自動読み取り）")
st.dataframe(df, use_container_width=True)

# --- 3. 編集可能テーブル ---
st.markdown("3. 自動読み取りミスがあるセルだけ直してください")
edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# --- 4. ダウンロード ---
st.markdown("4. 修正後データをダウンロード")
csv = edited.to_csv(index=False, encoding='utf-8-sig').encode()
json_str = edited.to_json(orient="records", force_ascii=False)
col1, col2 = st.columns(2)
with col1:
    st.download_button("📥 CSV でダウンロード", csv, "table.csv", "text/csv")
with col2:
    st.download_button("📥 JSON でダウンロード", json_str, "table.json", "application/json")
