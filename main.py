import streamlit as st

PAGE_PATH = "pages"
RECO_PATH = PAGE_PATH + "/reco"
VIS_PATH = PAGE_PATH + "/vis"

reco_page = st.Page(f"{RECO_PATH}/reco_main.py", title="OD로 갈까요?", icon=":material/add_circle:")
vis_page = st.Page(f"{VIS_PATH}/vis_main.py", title="OD를 볼까요?", icon=":material/map:")

pages = [
        reco_page,
        vis_page
    ]
pg = st.navigation(pages)
pg.run()