import pandas as pd 
import os 
import sys
from dotenv import load_dotenv
import json 
import requests 
import warnings
from tqdm import tqdm
from collections import defaultdict

from .tools import *

load_dotenv()

warnings.filterwarnings("ignore")

#################### CONST VAR ####################
SK_API_KEY = os.getenv("SK_OPEN_API_KEY")  # 재환 - 241021 할당량 끝
# SK_API_KEY = os.getenv("SK_OPEN_API_KEY2")  # 제후 - 10(50/50) 20(25/50)
# SK_API_KEY = os.getenv("SK_OPEN_API_KEY3")  # 기범 - 10(50/50)
# SK_API_KEY = os.getenv("SK_OPEN_API_KEY4")  # 영희 - 10(25/50)
routeOptimization = 20  # 10 or 20
###################################################
print(SK_API_KEY)
# SK_API_KEY = ''

def get_poi_by_keyword(keyword: str, return_full: bool = False, **kwargs):
    """TMAP poi 정보 반환 함수입니다.

    Args:
        keyword (str): 검색 키워드.
        return_full (bool): api 요청 응답 전체 반환 여부. Defaults to False
        region (str): 지역명 (시군구 단위).

    Returns:
        result: json
    """

    region = kwargs.get("region", None)
    if region:
        search_keyword = region + ' ' + keyword
        url = f'https://apis.openapi.sk.com/tmap/pois?version=1&appKey={SK_API_KEY}&searchKeyword={search_keyword}'
    else:
        url = f'https://apis.openapi.sk.com/tmap/pois?version=1&appKey={SK_API_KEY}&searchKeyword={keyword}'

    try:
        response = requests.get(url, verify=False)
        # 상태 코드 확인
        if response.status_code == 204:
            print("No content available for this request (204).")
            return None
        
        # 상태 코드가 200이 아닌 경우 에러 처리
        response.raise_for_status()

        result = response.json()

        if return_full:
            return result

        first_poi = result['searchPoiInfo']['pois']['poi'][0]
        latitude = first_poi['noorLat']
        longitude = first_poi['noorLon']
        name = first_poi['name']
        poi = {
            'latitude': latitude,
            'longitude': longitude,
            'name': name
        }
        return poi

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        print(f"An error occurred: {err}")
        return None



def get_route(start_poi, end_poi):
    """_summary_

    Args:
        start_poi (_type_): _description_
        end_poi (_type_): _description_

    Returns:
        _type_: _description_
    """
    url = f'https://apis.openapi.sk.com/tmap/routes?version=1&appKey={SK_API_KEY}'
    data = {
        'startX': start_poi['longitude'],
        'startY': start_poi['latitude'],
        'endX': end_poi['longitude'],
        'endY': end_poi['latitude'] 
    }
    response = requests.post(url, json=data, verify=False)
    result = response.json()
    return result


def get_optimized_route(src_keyword:str, 
                        dst_keyword:str, 
                        region:str, 
                        via_points:list):
    """TMAP API 기반 경유지 순서 최적화 루트 반환 함수입니다. 

    Args:
        src_keyword (str): 출발지 키워드
        dst_keyword (str): 목적지 키워드
        region (str): 사용자가 선택한 지역 (시군구 단위)
        via_points (list): 경유지 키워드 목록
    """

    # use headers
    
    url = f'https://apis.openapi.sk.com/tmap/routes/routeOptimization{routeOptimization}?version=1&format=json'

    headers = {
        # 'Content-Type': 'application/json',
        'appKey': SK_API_KEY
    }

    # 출발지 Poi
    start_poi = get_poi_by_keyword(keyword=src_keyword)
    print(f"출발지명: {src_keyword}")

    # 목적지 poi 
    end_poi = get_poi_by_keyword(keyword=dst_keyword)
    print(f"도착지명: {dst_keyword}")

    viaPoints = []
    for i, via_point_keyword in tqdm(enumerate(via_points)):
        print(f"경유지 명: {via_point_keyword}")
        via_poi = get_poi_by_keyword(keyword=via_point_keyword, region=region)
        if not via_poi: continue

        viaPoint = {
            'viaPointId': str(i+1),
            'viaPointName': via_point_keyword,
            'viaDetailAddress': '',
            'viaX': via_poi['longitude'],
            'viaY': via_poi['latitude'],
            'viaPoiId': '',
            'viaTime': 600,
            'wishStartTime': '',
            'wishEndTime': ''
        }
        viaPoints.append(viaPoint)

    data = {
        'reqCoordType': 'WGS84GEO',
        'resCoordType': 'WGS84GEO',
        'startName': "출발",
        'startX': start_poi['longitude'],
        'startY': start_poi['latitude'],
        'startTime': '202410200125',  # 출발시간
        'endName': "도착",
        'endX': end_poi['longitude'],
        'endY': end_poi['latitude'],
        'endPoiId': '',
        'searchOption': '0',
        'carType': '0',  # 톨게이트 요금에 대한 차종 지정 ('0': 승용차)
        'viaPoints': viaPoints,
    }
   
    # api 요청 
    print("############### 경유지 순서 최적화 요청 ###############")
    response = requests.post(url, json=data, headers=headers, verify=False)
    result = response.json()

    return result


def get_my_route_info(src_keyword:str, 
                      dst_keyword:str, 
                      region:str, 
                      via_points:list):
    """_summary_

    Args:
        src_keyword (str): 출발지 키워드
        dst_keyword (str): 도착지 키워드 
        region (str): 사용자가 선택한 지역 (시군구 단위)
        viapoints (list): 추천 장소와 축제 장소를 포함하는 장소 리스트 
                        (마지막 요소가 축제 장소, 축제 장소는 '지역 장소명' 형식으로 입력)

    Returns:
        json: 경유지 순서 최적화 경로 정보 

        return format
        
        ```
        {
            'properties': {
                'totalTime',  # 전체 경로 소요시간
                'totalDistance',  # 전체 경로 이동거리
                'totalFare',  # 전체 경로 비용
                'routeScore',  # 경로 점수 (자체 산정)
            },

            'points': [
                {
                    'pointId',  # 장소 id
                    'pointName',  # 장소 이름
                    'pointLatitude',  # 장소 위도
                    'pointLongitude',  # 장소 경도
                },
                ...
            ],
            'paths': [
                {
                    'pathId',  # 경로 id
                    'time',  # 경로 소요시간
                    'distance',  # 경로 길이 
                    'fare'  # 경로 비용
                },
                ...
            ]
        }
        ```
    """
    
    route = get_optimized_route(src_keyword=src_keyword, dst_keyword=dst_keyword, region=region,  via_points=via_points)
    properties = route["properties"]
    features = route["features"]

    # result = dict{}
    points = []  # 장소 정보 리스트 
    paths = []  # 경로 정보 리스트 
    places = []
    for feature in features:
        type = feature["geometry"]['type']
        if type == "Point":
            _point = defaultdict(str)
            _point["pointId"] = feature["properties"]["index"]  # 장소 id (방문 순서)
            _point["pointName"] = feature["properties"]["viaPointName"].split()[-1]  # 장소 명 
            _point["pointLatitude"] = feature["geometry"]["coordinates"][1]  # 위도
            _point["pointLongitude"]= feature["geometry"]["coordinates"][0]  # 경도 
            points.append(_point)
            places.append(_point["pointName"])

        elif type == "LineString":
            _path = defaultdict(str)
            _path["pathId"] = feature["properties"]["index"]
            _path["pathTime"] = feature["properties"]["time"]
            _path["pathDistance"] = feature["properties"]["distance"]
            _path["pathFare"] = feature["properties"]["Fare"]
            paths.append(_path)

    # festival_place = via_points[-1].split()[0]
    
    # 축제 장소 제외한 추천 장소 리스트 
    recommended_places = via_points[:-1]
    route_score = get_route_score(recommended_places, region)
    
    properties["routeScore"] = route_score

    result = {
        "properties": properties,
        "points": points,
        "paths": paths
    }
    
    return result


def get_my_topk_optimized_routes(start_place:str, 
                                 end_place:str, 
                                 selected_region:str,
                                 selected_festival_place:str, 
                                 comb:int=2, 
                                 comb_k:int=5, 
                                 topk:int=3) ->list:
    """_summary_

    Args:
        start_place (str): _description_
        end_place (str): _description_
        selected_region (str): _description_
        selected_festival_place (str): _description_
        comb (str, optional): _description_. Defaults to 2.
        comb_k (int, optional): _description_. Defaults to 5.
        topk (int, optional): _description_. Defaults to 3.

    Returns:
        list: _description_
    """
    place_comb_list = get_place_comb_list(region=selected_region, n=comb, k=comb_k)

    route_list = []
    for place_comb in place_comb_list:
        place_comb = place_comb + [selected_festival_place]
        route = get_my_route_info(start_place, end_place, selected_region, place_comb)
        route_list.append(route)

    new_route_list = get_scaled_score(route_list)

    top_3_routes = get_topk_optimized_route(route_list=new_route_list, k=topk)
    return top_3_routes