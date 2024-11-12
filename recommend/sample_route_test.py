import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from recommend.func.archive.TMAP_API import get_route

# # Tmap API 키 설정
import os
from dotenv import load_dotenv
load_dotenv()
TMAP_API_KEY = os.getenv("SK_OPEN_API_KEY")


def get_route(start_x, start_y, end_x, end_y):
    url = f'https://apis.openapi.sk.com/tmap/routes?version=1&appKey={TMAP_API_KEY}'
    data = {
        'startX': start_x,
        'startY': start_y,
        'endX': end_x,
        'endY': end_y 
    }
    response = requests.post(url, json=data, verify=False)
    result = response.json()
    return result


def draw_route_on_map(route_data):
    # 경로의 중심점 계산
    _features = route_data['features']
    _line_strings = []
    for _feature in _features:
        _geometry = _feature['geometry']

        if _geometry['type'] == "LineString":
            _line_strings.append(_geometry['coordinates'])

    _coordinates = []

    for _line_string in _line_strings:

        _coordinates.extend(_line_string)
    
    print("###################### 좌표 리스트 ######################")
    print(*_coordinates)
    center_lat = sum(coord[1] for coord in _coordinates) / len(_coordinates)
    center_lon = sum(coord[0] for coord in _coordinates) / len(_coordinates)
    
    # 지도 생성
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 경로 그리기
    route_coords = [(coord[1], coord[0]) for coord in _coordinates]
    folium.PolyLine(route_coords, color="red", weight=2.5, opacity=1).add_to(m)
    
    # 시작점과 끝점 마커 추가
    folium.Marker(route_coords[0], popup="Start").add_to(m)
    folium.Marker(route_coords[-1], popup="End").add_to(m)
    
    return m

# Streamlit 앱
st.title("Tmap 경로 표시")

# 사용자 입력
start_x = st.number_input("출발지 경도", value=126.985)
start_y = st.number_input("출발지 위도", value=37.566)
end_x = st.number_input("도착지 경도", value=127.015)
end_y = st.number_input("도착지 위도", value=37.576)

if st.button("경로 찾기"):
    route_data = get_route(start_x, start_y, end_x, end_y)
    print(route_data)
    map = draw_route_on_map(route_data)
    folium_static(map)