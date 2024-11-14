import streamlit as st

##################### word net #####################

help_str = """
- 같은 문서에서 많이 등장한 만큼 간선이 굵어집니다.
- Greedy Modularity Communities를 활용하여 군집화하고 색상으로 표현하였습니다.
- 노드를 선택하여 해당 노드에 연결된 노드와 간선만 볼 수 있습니다.
"""
st.title("대백제전 Word Network", help=help_str)

# HTML 파일 수동으로 작성
html_file_path = "data/word_network.html"

# Streamlit에서 HTML 임베딩
with open(html_file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=700, scrolling=True)

st.write('---')

##################### word cloud #####################

st.title("대백제전 Word Cloud")

st.image('data/word_cloud.png')