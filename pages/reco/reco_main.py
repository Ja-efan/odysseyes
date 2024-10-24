import sys
import os 
# sys.path.append(r"C:\Users\SSAFY\Desktop\2024_big_contest\odesseyes\pages\reco")

module_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(module_dir)
DATA_PATH = os.path.join(module_dir, '../..')
sys.path.append(DATA_PATH)

# from importlib import reload
from func import search


import streamlit as st
import folium
from pages import search_page, select_page, recommend_page

PAGE_PATH = "."
RECO_PATH = PAGE_PATH + "/reco"

if 'page' not in st.session_state:
    st.session_state['page'] = 'search'

# if 'is_refreshed' not in st.session_state:
#     st.session_state['is_refreshed'] = False

# # 새로고침 반영
# if st.session_state['is_refreshed']:
#     st.session_state['origin'] = False
#     st.session_state['store'] = False
#     st.session_state['locations'] = False
#     st.session_state['m'] = False
#     st.session_state['summit'] = False
#     st.session_state['search_query'] = ''
#     st.session_state['bnt_press'] = False
#     st.session_state['map_lat_lon'] = False
#     st.rerun()

st.session_state['is_refreshed'] = True

if 'origin' not in st.session_state:
    st.session_state['origin'] = False
if 'store' not in st.session_state:
    st.session_state['store'] = False
if 'locations' not in st.session_state:
    st.session_state['locations'] = False
if 'm' not in st.session_state:
    st.session_state['m'] = False
if 'summit' not in st.session_state:
    st.session_state['summit'] = False
if 'search_query' not in st.session_state:
    st.session_state['search_query'] = ''
if 'bnt_press' not in st.session_state:
    st.session_state['bnt_press'] = False
if 'map_lat_lon' not in st.session_state:
    st.session_state['map_lat_lon'] = False
if 'dest_addr' not in st.session_state:
    st.session_state['dest_addr'] = False
if 'clicked_location' not in st.session_state:
    st.session_state['clicked_location'] = False


if st.session_state['page'] == 'search':
    search_page()
elif st.session_state['page'] == 'select':
    select_page()
elif st.session_state['page'] == 'recommend':
    recommend_page()