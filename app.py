import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# 1. ここに OCR で取り込んだデータを貼り付け
data = [
    {
        "艇": 1, "登番": 3947, "氏名": "寺本 昇平", "支部/出身地": "群馬 神奈川", "登録期/年齢": "82期 49歳",
        "FL": 0, "級別": "B1", "平均ST": 0.17, "勝率": 4.57, "全国2連率": 20.1, "全国近況2連率": 23.1, "当地2連率": 15.7,
        "モーター番号": 29, "モーター2連率": 28.5, "ボート番号": 72, "ボート2連率": 37.7
    },
    # 2～6号艇分を同様に追加…
]

df = pd.DataFrame(data)

st.title("OCR結果 手動修正ツール")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True)
grid_options = gb.build()

st.markdown("#### 誤りがあるセルをクリックして修正できます")
grid_response = AgGrid(df, gridOptions=grid_options, update_mode="MODEL_CHANGED",
                        height=300, fit_columns_on_grid_load=True)

edited_df = pd.DataFrame(grid_response["data"])
st.markdown("#### 修正後のデータプレビュー")
st.dataframe(edited_df)

csv_bytes = edited_df.to_csv(index=False, encoding='utf-8-sig').encode()
json_str = edited_df.to_json(orient="records", force_ascii=False)

st.download_button("CSVでダウンロード", csv_bytes, "corrected_data.csv", "text/csv")
st.download_button("JSONでダウンロード", json_str, "corrected_data.json", "application/json")
