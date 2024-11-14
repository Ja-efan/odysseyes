import os
import sys
import streamlit as st
import folium
from streamlit_folium import st_folium
import base64
import math
from dotenv import load_dotenv


##################################### project modules ###################################   
# 현재 모듈 파일의 디렉터리 경로를 가져옴
module_dir = os.path.dirname(os.path.abspath(__file__))

# CSV 파일의 경로를 모듈 파일 경로를 기준으로 설정
PROJECT_ROOT_PATH = os.path.join(module_dir, '../..')
sys.path.append(PROJECT_ROOT_PATH)

RECOMMEND_SYS_PATH = os.path.join(module_dir, '../../recommend')
sys.path.append(RECOMMEND_SYS_PATH)

from recommend.func.tmap_client import TMAPClient
from recommend.func.place_data_manager import PlaceDataManager
from recommend.func.route_optimizer import RouteOptimizer
from recommend.func.tools import *
from func import search
#########################################################################################

load_dotenv()
api_key = os.getenv('SK_OPEN_API_KEY')

################################ route optimizer instances ##############################
tmap_client = TMAPClient(api_key)
place_data_manager = PlaceDataManager(file_name="추천장소통합리스트.csv")
route_optimizer = RouteOptimizer(tmap_client, place_data_manager)
#########################################################################################

DEBUG = True

def calculate_distance(coord1, coord2):
    # 유클리드 거리 계산
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)

def load_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

closest_location = 'OD'
# PIN_IMG = r"./pages/reco/img/location-pin.png"
PIN_IMG = os.path.join(module_dir, 'img', 'location-pin.png')

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
    
    st.warning("본 버전은 데모 버전입니다. '대전 서구 월평동 1216'에서 '부여 백제문화제'로 가는 경로만 탐색 가능합니다.", icon="⚠️")

def select_page():
    global closest_location
    st.session_state['summit'] = True

    # 페이지 제목
    st.title("지도에서 원하는 축제 지역을 선택해주세요")

    # 검색 결과에 따라 마커 추가
    if st.session_state.search_query is not None and st.session_state.search_query != st.session_state.store:

        st.session_state.store = st.session_state.search_query

        if DEBUG:
            search_keyword, st.session_state.map_lat_lon, lat_lon_dict, image, phones = '백제문화제', (36.4702917892, 127.1275545162), {('미르섬', '충청남도 공주시 금벽로 368 '): [127.128418890171, 36.4674920688043], ('백제문화단지', ' 충청남도 부여군 규암면 백제문로 455 백제문화단지'): [126.906673511388, 36.3063152681079]}, "http://tong.visitkorea.or.kr/cms/resource/46/2953046_image2_1.jpg", []
        else:
            search_keyword, st.session_state.map_lat_lon, lat_lon_dict, image, phones = search.get_festival_info(' '.join(st.session_state.search_query))
            print('get_festival_info -', ' '.join(st.session_state.search_query), ':', search_keyword, st.session_state.map_lat_lon, lat_lon_dict, image, phones)

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
                st.write(f"선택한 위치로 여행을 시작합니다: {st.session_state.locations}")
                st.session_state['page'] = 'recommend'
                st.rerun()
            else:
                st.write("먼저 장소를 선택해주세요.")


def recommend_page():
    # 페이지 제목
    st.title("이렇게 가볼까요?")

    # 경로 저장 리스트 (세션 상태에 경로를 저장)
    if 'route' not in st.session_state:
        st.session_state.route = []

    import json
    if DEBUG:
        # sample_file_name = 'sample_top3_optimized_routes.json'
        sample_file_name = 'tsp_top_routes.json'
        sample_data_path = os.path.join(RECOMMEND_SYS_PATH, 'data', sample_file_name)
        with open(sample_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        if len(st.session_state['route']) == 0:
            print(st.session_state["selected_sigungu"], st.session_state["dest_addr"],)

            data = route_optimizer.get_top_k_routes_tsp(
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
        '''
        route = {
            'properties': properties,
            'points': points,
            'paths': paths,
            'lineCoordinates': coordinates
        }
        '''
        route_points = route['points']
        all_points.extend([(point['pointLatitude'], point['pointLongitude']) for point in route_points])

    # 경로 선택을 위한 드롭다운 생성
    selected_route_index = st.selectbox("경로 선택", range(1, len(st.session_state['route'])+1)) -1

    selected_route = st.session_state['route'][selected_route_index]
    route_points = selected_route['points']

    # 장소 좌표 (출발지 - (축제장소, 추천장소) - 도착지(출발지)) 
    points_coordinates = [(point['pointLatitude'], point['pointLongitude']) for point in route_points]

    # 경로 시각화를 위한 좌표 추출
    line_coordinates = [(coord[1], coord[0]) for coord in selected_route['lineCoordinates']]
    color = colors[selected_route_index % len(colors)]

    if points_coordinates:

        ################################ ver 1. 축제 지역 포커싱 ##################################
        inner_points = points_coordinates[1:-1]
        center_lat = round(sum([lat for lat, _ in inner_points]) / len(inner_points), 8)
        center_lon = round(sum([lon for _, lon in inner_points]) / len(inner_points), 8)
        #######################################################################################

        ################################ ver 2. 전체 경로 표시  ##################################
        # center_lat = sum([lat for lat, _ in points_coordinates]) / len(points_coordinates)
        # center_lon = sum([lon for _, lon in points_coordinates]) / len(points_coordinates)
        #######################################################################################

        print("######## center ########")
        print(center_lat, center_lon)
        st.session_state.m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    else:
        st.session_state.m = folium.Map(location=[0, 0], zoom_start=2)
    
    # 경로 시각화
    if line_coordinates:
        folium.PolyLine(
            locations=line_coordinates,
            color=color,
            weight=2.5,
            opacity=1
        ).add_to(st.session_state.m)
    else:
        st.warning("유효한 경로 좌표가 없습니다.")
    

    # 선택된 경로의 각 점에 마커 추가 (index 값을 기준으로 정렬하여 표시)
    for order, point in sorted(enumerate(route_points), key=lambda x: x[1].get('index', x[0])):
        print(point['pointName'], point['pointId'], order+1)
        folium.Marker(
            location=(point['pointLatitude'], point['pointLongitude']),
            icon=folium.DivIcon(
                html=f"""<div style="width: 25px; height: 25px; background-color: {color}; 
                        border-radius: 20px; display: flex; align-items: center; justify-content: center; 
                        color: white; font-weight: bold; font-size: 10pt; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);">
                        {order + 1}
                        </div>""",
            )
        ).add_to(st.session_state.m)


    # Folium 지도 출력
    st_folium(st.session_state.m, width=700, height=500)

    
    ############################# 선택된 경로에 대한 정보 표시  #############################
    st.subheader(f"선택한 경로: {selected_route_index + 1}")

    # # 경로 정보 (거리, 시간, 요금) 출력
    st.write(f"- 총 이동 거리 :  {round(selected_route['properties']['totalDistance'] / 1e3, 2)} km")
    st.write(f"- 총 이동 시간 :  {format_time(selected_route['properties']['totalTime'])}")
    st.write(f"- 총 이동 비용 :  {selected_route['properties']['totalFare']} 원")

    st.markdown(f"---")
    
    for order, point in enumerate(route_points):
        if order == 0 :
            point_type = '출발지'
        elif order == len(selected_route['points'])-1:
            point_type = '도착지'
        else: 
            point_type = '경유지'
        
        st.write(f"{order + 1}. {point_type}: {point['pointName']}")