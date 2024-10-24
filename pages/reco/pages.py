import os
import sys

# 현재 모듈 파일의 디렉터리 경로를 가져옴
module_dir = os.path.dirname(os.path.abspath(__file__))

# CSV 파일의 경로를 모듈 파일 경로를 기준으로 설정
PROJECT__ROOT_PATH = os.path.join(module_dir, '../../..')
sys.path.append(PROJECT__ROOT_PATH)

RECOMMEND_SYS_PATH = os.path.join(module_dir, '../../../recommend')
sys.path.append(RECOMMEND_SYS_PATH)

from func.TMAP_API import get_my_topk_optimized_routes

from collections import defaultdict

# from importlib import reload
from func import search

import streamlit as st
import folium
from streamlit_folium import st_folium

import streamlit as st
import base64

import math

def calculate_distance(coord1, coord2):
    # 유클리드 거리 계산
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)

def load_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

closest_location = 'OD'
PIN_IMG = r"pages\reco\img\location-pin.png"
DEBUG = True

loc_base64 = load_image(PIN_IMG)

def search_page():
    # 페이지 제목
    st.title("OD로 갈까요?")

    # 사용자 입력
    c1, c2 = st.columns([1, 4])
    with c1:
        st.session_state['origin'] = st.text_input("", key="origin_input")

    with c2:
        st.write(".")
        st.write("에서")

    c1, c2 = st.columns([1, 4])
    with c1:
        search_input = st.text_input("", key="destination_input").split()
        if search_input:
            st.session_state["selected_sigungu"] = search_input[0]
            st.session_state["search_query"] = search_input[1:]

    with c2:
        st.write(".")
        st.write("로 여행가기")

    if st.button("seYES!!"):
        st.write("축제 지역 탐색중...")
        st.session_state['page'] = 'select'
        st.rerun()

def select_page():
    global closest_location
    st.session_state['summit'] = True

    # 페이지 제목
    st.title("지도에서 원하는 축제 지역을 선택해주세요")

    # 검색 결과에 따라 마커 추가
    if st.session_state.search_query is not None and st.session_state.search_query != st.session_state.store:

        st.session_state.store = st.session_state.search_query

        search_keyword, st.session_state.map_lat_lon, lat_lon_dict, image, phones = search.get_festival_info(' '.join(st.session_state.search_query))
        locations = {}
        for (place_name, addr), lat_lon in lat_lon_dict.items():
            locations[place_name] = {"coordinates": lat_lon[::-1], "info": addr + '\n', "image":image}
        st.session_state.m = folium.Map(location=list(st.session_state.map_lat_lon), zoom_start=10)
        
        if locations:
            print('검색된 축제 장소')
            for location, data in locations.items():
                print(data["coordinates"])
                folium.Marker(
                    location=data["coordinates"],
                    popup=folium.Popup(

                        html = f"""<div style="text-align: center;">
                                <img src="{data['image']}" width="200" style="margin-bottom: 5px;" />
                                <div style="font-size: 10pt; color: black; font-weight: bold;">{location}</div>
                            </div>""",

                        max_width=300,
                    ),
                    # <a href="https://www.flaticon.com/kr/free-icons/-" title="지도 및 위치 아이콘">지도 및 위치 아이콘 제작자: Slidicon - Flaticon</a>
                    icon=folium.DivIcon(
                        html=f"""<div style="text-align: center;">
                                    <img src="data:image/png;base64,{loc_base64}" width="24" height="24" style="margin-right: 5px;" />

                                    <div style="font-size: 10pt; color: black; font-weight: bold; white-space: nowrap;">{location}</div>
                                </div>""",
                    )
                ).add_to(st.session_state.m)
            st.session_state.locations = locations
        else:
            st.write("No locations found.")

    if st.session_state.m and st.session_state.locations:
        # Folium 지도 출력
        st_data = st_folium(st.session_state.m, width=700, height=500)
        # 검색된 장소 정보를 가로로 나열
        if st.session_state.search_query and st.session_state.locations:
            for idx, (location, data) in enumerate(st.session_state.locations.items()):
                st.subheader(location)
                st.write(data["info"])


        # 사용자가 클릭한 마커의 정보를 출력
        print('last_clicked:', st_data['last_clicked'])
        if st_data['last_clicked'] and (st_data['last_clicked']['lat'], st_data['last_clicked']['lng']) != st.session_state.clicked_location:
            st.session_state.clicked_location = st_data['last_clicked']['lat'], st_data['last_clicked']['lng']
            
            # st.write(f"You clicked on: {clicked_location}")
            
            # 클릭한 좌표에 가장 가까운 장소 정보 표시
            print(st.session_state.locations)
            clicked_location = list(st.session_state.clicked_location)

            closest_distance = float('inf')

            for location, data in st.session_state.locations.items():
                distance = calculate_distance(data["coordinates"], clicked_location)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_location = location

            if closest_location is not None:
                # 클릭한 주소 저장
                print('가장 가까운 장소의 info:', st.session_state.locations[closest_location]['info'])
                st.session_state.dest_addr = st.session_state.locations[closest_location]["info"]
                st.write(f"Info about {closest_location}: {st.session_state.locations[closest_location]['info']}")

            st.rerun()

        elif not st.session_state.clicked_location:
            st.session_state.clicked_location = None
            st.write("지도를 클릭하여 위치를 선택하세요.")


        if st.button(f"{closest_location} 여행가기!", disabled=(st.session_state.clicked_location is None)):
            if st.session_state.clicked_location:
                st.write(f"선택한 위치로 여행을 시작합니다: {location}")
                st.session_state['page'] = 'recommend'
                st.rerun()
            else:
                st.write("먼저 장소를 선택해주세요.")


from recommend.func.TMAP_API import get_my_topk_optimized_routes

def recommend_page():
    # 페이지 제목
    st.title("이렇게 가볼까요?")

    # 경로 저장 리스트 (세션 상태에 경로를 저장)
    if 'route' not in st.session_state:
        st.session_state.route = []

    import json
    if DEBUG:
        with open(r'..\recommend\data\my_route_sample.json', 'r') as f:
            data = json.load(f)
    else:
        if len(st.session_state['route']) == 0:
            start_place = "유성구 덕명동 515-3"
            end_place = "유성구 덕명동 515-3"
            selected_sigungu = '부여'
            selected_festival_place = "백제문화단지"
            print(st.session_state["selected_sigungu"], st.session_state["dest_addr"],)
            data = get_my_topk_optimized_routes(
                start_place=st.session_state['origin'],
                end_place=st.session_state['origin'],
                selected_region=st.session_state["selected_sigungu"],
                selected_festival_place=st.session_state["dest_addr"],
                comb=2,
                comb_k=5,
                topk=3
            )
            with open(r'..\recommend\data\my_route_sample2.json', 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    st.session_state['route'] = data

    # 경로의 모든 노드 좌표 수집
    all_points = []
    colors = ["blue", "green", "red", "purple", "orange"]  # 각 경로에 대한 색상 리스트

    for route in st.session_state['route']:
        route_points = route['points']
        all_points.extend([(point['pointLatitude'], point['pointLongitude']) for point in route_points])

    # 기본 지도 생성
    st.session_state.m = folium.Map(location=[0, 0], zoom_start=2)  # 기본 위치 및 줌 레벨 설정

    # 경로 선택을 위한 드롭다운 생성
    selected_route_index = st.selectbox("경로 선택", range(len(st.session_state['route'])))

    selected_route = st.session_state['route'][selected_route_index]
    route_points = selected_route['points']
    points = [(point['pointLatitude'], point['pointLongitude']) for point in route_points]
    color = colors[selected_route_index % len(colors)]

    folium.PolyLine(
        locations=points,
        color=color,
        weight=5,
        opacity=0.8,
        smooth_factor=10
    ).add_to(st.session_state.m)
    # 선택된 경로의 각 점에 마커 추가
    for order, point in enumerate(route_points):
        folium.Marker(
            location=(point['pointLatitude'], point['pointLongitude']),
            icon=folium.DivIcon(
                html=f"""<div style="width: 40px; height: 40px; background-color: {color}; 
                        border-radius: 20px; display: flex; align-items: center; justify-content: center; 
                        color: white; font-weight: bold; font-size: 12pt; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);">
                        {order + 1}
                        </div>""",
            )
        ).add_to(st.session_state.m)

    # 모든 노드의 경계를 계산하여 지도 조정
    if all_points:
        lats, lons = zip(*all_points)
        bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
        st.session_state.m.fit_bounds(bounds)  # 모든 노드를 포함하도록 줌 조정

    # Folium 지도 출력
    st_folium(st.session_state.m, width=700, height=500)

    # 선택된 경로에 대한 정보 표시
    selected_route = st.session_state['route'][selected_route_index]
    st.subheader(f"선택한 경로: {selected_route_index + 1}")
    for order, point in enumerate(selected_route['points']):
        st.write(f"{order + 1}. {point['pointName']}")


