import os
import json
import requests
from dotenv import load_dotenv
from collections import defaultdict, OrderedDict
import pandas as pd
from itertools import combinations
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TMAPClient:
    """TMAP API 호출을 담당하는 클래스"""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_poi(self, keyword: str, region: str = None) -> dict:
        """키워드를 이용해 POI 정보를 가져옵니다."""
        search_keyword = f"{region} {keyword}" if region else keyword
        url = f'https://apis.openapi.sk.com/tmap/pois?version=1&appKey={self.api_key}&searchKeyword={search_keyword}'
        response = requests.get(url, verify=False)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} from TMAP API for POI.")
            return {}

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Error: Response is not in JSON format.")
            print("Response content:", response.text)  # 응답 내용을 출력해 문제를 확인합니다.
            return {}

        if data and 'searchPoiInfo' in data:
            first_poi = data['searchPoiInfo']['pois']['poi'][0]
            return {
                'latitude': first_poi['noorLat'],
                'longitude': first_poi['noorLon'],
                'name': first_poi['name']
            }
        return {}

    def get_route_data(self, start: dict, end: dict, passList: list=None):
        """TMap API를 이용한 경로 탐색 함수 

        Args:
            start (dict): _description_
            end (dict): _description_
            passList (list, optional): 경유지 좌표 리스트, 최대 5개 지원. Defaults to None.  
                - 형식: 경유지1 X 좌표,경유지1 Y 좌표경유지2 X 좌표,경유지2 Y 좌표_...
        """

        # https://tmap-skopenapi.readme.io/reference/%EC%9E%90%EB%8F%99%EC%B0%A8-%EA%B2%BD%EB%A1%9C%EC%95%88%EB%82%B4
        url = "https://apis.openapi.sk.com/tmap/routes?version=1&callback=function"

        if passList:
            passList = ','.join(passList)
        else:
            passList = None

        payload = {
            "tollgateFareOption": 16,  # 16: 로직판단(기본값)
            "roadType": 32,  # 32:가까운 도로(기본값)
            "endX": end['longitude'],  # 목적지 X좌표 경도 
            "endY": end['latitude'],  # 목적지 Y좌표 위도
            "reqCoordType": "WGS84GEO",
            "startX": start['longitude'],  # 출발지 X좌표 경도 
            "startY": start['latitude'],  # 출발지 Y좌표 위도
            "carType": 0,
            "startName": "출발지",
            "endName": "도착지",
            "passList": passList,
            "resCoordType": "WGS84GEO",
            "sort": "index"
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "appKey": self.api_key
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} from TMAP API for route.")
            return {}

        try:
            return response.json()
        except json.JSONDecodeError:
            print("Error: Response is not in JSON format.")
            print("Response content:", response.text)  # 응답 내용을 출력해 문제를 확인합니다.
            return {}

    def get_optimized_route(self, start_poi:dict, end_poi:dict, via_pois: list = []) -> dict:
        """경유지 최적화 API 호출"""
        routeOptimization = 10
        url = f'https://apis.openapi.sk.com/tmap/routes/routeOptimization{routeOptimization}?version=1&format=json'

        headers = {'appKey': self.api_key}

        data = {
            'reqCoordType': 'WGS84GEO',
            'resCoordType': 'WGS84GEO',
            'startName': '출발',
            'startX': start_poi['longitude'],
            'startY': start_poi['latitude'],
            'startTime': '202410200125',  # 출발시간
            'endName': '도착',
            'endX': end_poi['longitude'],
            'endY': end_poi['latitude'],
            'endPoiId': '',
            'searchOption': '0',
            'carType': '0',  # 톨게이트 요금에 대한 차종 지정 ('0': 승용차)
            'viaPoints': via_pois,
        }

        # api 요청 
        print('############### 경유지 순서 최적화 요청 ###############')
        response = requests.post(url, json=data, headers=headers, verify=False)
        result = response.json()

        return result


class PlaceDataManager:
    """장소 데이터를 로드하고 조합을 생성하는 클래스"""
    def __init__(self, file_name=None):

        # 현재 모듈 파일의 디렉터리 경로를 가져옴
        self.module_dir = os.path.dirname(os.path.abspath(__file__))

        if file_name is None:
            # CSV 파일의 경로를 모듈 파일 경로를 기준으로 설정
            default_file_name = '추천장소통합리스트.csv'
            data_path = os.path.join(self.module_dir, '..', 'data', f'{default_file_name}')
        else:
            data_path = os.path.join(self.module_dir, '..', 'data', f'{file_name}')

        self.data_path = data_path
        self.place_data = pd.read_csv(data_path)
    
    def get_filtered_places(self, region: str, category: str, top_k: int = 5) -> pd.DataFrame:
        """특정 지역과 카테고리에 맞는 상위 장소 필터링"""
        filtered_data = self.place_data[(self.place_data['지역'] == region) & (self.place_data['분류'] == category)]
        return filtered_data.nlargest(top_k, '최종점수')
    
    def generate_place_combinations(self, region: str, n: int = 3, k: int = 5) -> list:
        """카페와 식당에서 각각 1개, 나머지는 관광지에서 선택하여 조합 생성"""
        cafe_list = self.get_filtered_places(region, '카페', k)['목적지명'].values
        res_list = self.get_filtered_places(region, '식당', k)['목적지명'].values
        land_list = self.get_filtered_places(region, '관광지', k)['목적지명'].values

        combinations_list = []
        for cafe in cafe_list:
            for res in res_list:
                for land_comb in combinations(land_list, n - 2):
                    combinations_list.append([cafe, res] + list(land_comb))
        return combinations_list

    
    def search_poi(self, keyword: str, region: str):
        """추천장소통합리스트에 찾고자 하는 장소의 POI 반환

        Args:
            keyword (str): 장소명
            region (str): 지역명

        Returns:
            _type_: dict
        """

        if region:
            filtered_data = self.place_data[self.place_data['지역'] == region]
        
        try:
            poi_dict = filtered_data[filtered_data['목적지명'] == keyword].to_dict(orient='records')[0]
            keys_to_extract = ['목적지명', '위도', '경도']

            new_poi_dict = {key: poi_dict[key] for key in keys_to_extract if key in poi_dict}

            return new_poi_dict
            
        except IndexError:
            raise ValueError(f"Keyword '{keyword}' not found in '목적지명'.")
        except KeyError as e:
            raise KeyError(f"Key '{e.args[0]}' not found in the data for keyword '{keyword}'.")


    def __str__(self):
        return self.data_path

class RouteOptimizer:
    """경로 최적화를 수행하고 상위 경로를 반환하는 클래스"""
    def __init__(self, tmap_client: TMAPClient, place_data_manager: PlaceDataManager):
        self.tmap_client = tmap_client
        self.place_data_manager = place_data_manager

    def calculate_route_score(self, place_list: list, region: str) -> float:
        """경로 점수 계산"""
        scores = [float(self.place_data_manager.place_data[(self.place_data_manager.place_data['지역'] == region) &
                                                           (self.place_data_manager.place_data['목적지명'] == place)]['최종점수'].values[0]) 
                  for place in place_list]
        return sum(scores)

    def get_scaled_scores(self, route_list: list) -> list:
        """경로 리스트의 점수를 스케일링하여 총 점수 계산"""
        properties_data = [route['properties'] for route in route_list]
        scaler = MinMaxScaler()
        scaled_properties = scaler.fit_transform(pd.DataFrame(properties_data))
        scaled_scores = []
        for i in range(len(scaled_properties[0])):
            scaled_score = []
            for j in range(len(scaled_properties)):
                scaled_score.append(round(float(scaled_properties[j][i]), 3))
            scaled_scores.append(scaled_score)
                
        scaledProperties = []
        totalRouteScores = []
        for i in range(len(scaled_scores[0])):
            scaledProperty = {
                'scaledDistance': round(1 - scaled_scores[0][i], 2),
                'scaledTime': round(1 - scaled_scores[1][i], 2),
                'scaledFare': round(1 - scaled_scores[2][i], 2),
                'scaledPlaceScore': scaled_scores[3][i],
            }
            
            scaledProperties.append(scaledProperty)

            totalRouteScore = round(sum(scaledProperty.values()), 2)
            totalRouteScores.append(totalRouteScore)

        for i, route in enumerate(route_list):
            # 기존 route 정보와 새로운 속성 추가 후 정렬
            ordered_route = OrderedDict([
                ('properties', route.get('properties')),
                ('scaledProperties', scaledProperties[i]),
                ('totalRouteScore', totalRouteScores[i]),
                ('points', route.get('points')),
                ('paths', route.get('paths')),
                ('lineCoordinates', route.get('lineCoordinates'))
            ])
            route_list[i] = ordered_route
        
        return route_list

    def get_top_k_routes(self, start_place: str, end_place: str, region: str, festival_place: str, 
                         comb: int = 2, comb_k: int = 5, top_k: int = 3) -> list:
        """상위 k개의 최적 경로를 반환"""
        place_combinations = self.place_data_manager.generate_place_combinations(region, comb, comb_k)
        
        # place_data_manager.search_poi() 로직 추가 
        search_poi_result_start_place = self.place_data_manager.search_poi(start_place, region)
        if search_poi_result_start_place:
            start_poi = search_poi_result_start_place
        else:
            start_poi = self.tmap_client.get_poi(start_place, region)


        if start_place == end_place:
            end_poi = search_poi_result_start_place
        else:
            search_poi_result_end_place = self.place_data_manager.search_poi(end_place, region)
            if search_poi_result_end_place:
                end_poi = search_poi_result_end_place
            else:
                end_poi = self.tmap_client.get_poi(end_place, region)


        route_list = []
        for place_combination in place_combinations:
            via_pois = []
            place_combination = place_combination + [festival_place]
            print(place_combination)
            for j, via_point_name in enumerate(place_combination):
                via_poi = self.tmap_client.get_poi(via_point_name, region)
                if not via_poi: continue 
                via_point = {
                    'viaPointId': str(j+1),
                    'viaPointName': via_point_name,
                    'viaDetailAddress': '',
                    'viaX': via_poi['longitude'],
                    'viaY': via_poi['latitude'],
                    'viaPoiId': '',
                    'viaTime': 600,
                    'wishStartTime': '',
                    'wishEndTime': ''
                }
                via_pois.append(via_point)
        

            # route = self.tmap_client.get_route(start_poi, end_poi, via_points)

            # 경유지 순서 최적화 요청 
            via_optimized_route = self.tmap_client.get_optimized_route(start_poi, end_poi, via_pois)

            properties = via_optimized_route['properties']
            features = via_optimized_route['features']

            result = dict()
            points = []  # 장소 정보 리스트 
            paths = []  # 경로 정보 리스트 
            places = []
            coordinates = []
            for feature in features:
                _geometry = feature['geometry']
                # type = _geometry['type']
                if _geometry['type'] == 'Point':
                    _point = defaultdict(str)
                    _point['pointId'] = feature['properties']['index']  # 장소 id (방문 순서)
                    _point['pointName'] = feature['properties']['viaPointName'].split()[-1]  # 장소 명 
                    _point['pointLatitude'] = feature['geometry']['coordinates'][1]  # 위도
                    _point['pointLongitude']= feature['geometry']['coordinates'][0]  # 경도 
                    points.append(_point)
                    places.append(_point['pointName'])

                elif _geometry['type'] == 'LineString':
                    _path = defaultdict(str)
                    _path['pathId'] = feature['properties']['index']
                    _path['pathTime'] = feature['properties']['time']
                    _path['pathDistance'] = feature['properties']['distance']
                    _path['pathFare'] = feature['properties']['Fare']
                    paths.append(_path)
                    
                    # 경로(Line의 좌표 정보)
                    coordinates.extend(_geometry['coordinates'])

            # 축제 장소 제외한 추천 장소 리스트 
            # recommended_places = place_combination[:-1]
            properties['routeScore'] = self.calculate_route_score(place_combination[:-1], region)

            result = {
                'properties': properties,
                'points': points,
                'paths': paths,
                'lineCoordinates': coordinates
            }
            route_list.append(result)
        
        route_list = self.get_scaled_scores(route_list)
        route_list.sort(key=lambda x: x['totalRouteScore'], reverse=True)
        return route_list[:top_k]