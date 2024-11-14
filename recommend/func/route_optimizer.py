from itertools import permutations
import re
import pandas as pd
from collections import OrderedDict, defaultdict
from sklearn.preprocessing import MinMaxScaler

from recommend.func.tmap_client import TMAPClient  # new 
from recommend.func.place_data_manager import PlaceDataManager  # new

# from tmap_route_optimizer import PlaceDataManager, TMAPClient  # old 


class RouteOptimizer:
    """경로 최적화를 수행하고 상위 경로를 반환하는 클래스"""
    def __init__(self, tmap_client: TMAPClient, place_data_manager: PlaceDataManager):
        self.tmap_client = tmap_client
        self.place_data_manager = place_data_manager

    def calculate_place_score(self, place_list: list, region: str) -> float:
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

  

    def add_start_and_festival_places(self, places, start, festival_place):
        places = [{'name': start, 'category': '출발지', 'latitude': None, 'longitude': None}] \
            + places \
            + [{'name': festival_place, 'category': '축제장소', 'latitude': None, 'longitude': None}]

        return places   
    

    def fetch_route_data(self, start, end):
        if start['latitude'] == None and start['longitude'] == None:
            start = self.tmap_client.get_poi(start['name'])
        if end['latitude'] == None and end['longitude'] == None:
            end = self.tmap_client.get_poi(end['name'])

        response = self.tmap_client.get_route_data(start=start, end=end)
        return response 
    
    
    def get_scaled_properties(self, routes: dict):
        """
        TMap API를 통해 얻어온 경로 정보에서 거리, 소요 시간, 비용을 정규화하고,
        각 경로의 상대적 점수를 계산하여 추가하는 함수.

        Args:
            routes (dict): 각 경로의 정보를 담고 있는 데이터.

        Returns:
            dict: 정규화된 점수 정보가 추가된 경로 데이터.
        """
        # 모든 경로의 'totalDistance', 'totalTime', 'totalFare'만 추출
        selected_properties_data = [
            {
                'totalDistance': route['features'][0]['properties']['totalDistance'],
                'totalTime': route['features'][0]['properties']['totalTime'],
                'totalFare': route['features'][0]['properties']['totalFare']
            }
            for route in routes.values()
        ]

        # DataFrame 변환 및 정규화
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(pd.DataFrame(selected_properties_data))

        # 정규화된 데이터를 바탕으로 scaledProperties 생성
        scaled_properties = [
            {
                'scaledDistance': round(1 - scaled[0], 2),
                'scaledTime': round(1 - scaled[1], 2),
                'scaledFare': round(1 - scaled[2], 2),
                'scaledDTFScore': round(1 - scaled[0] + 1 - scaled[1] + 1 - scaled[2], 2)
            }
            for scaled in scaled_data
        ]

        # 원본 데이터에 정규화된 점수 추가
        for route, scaled_property in zip(routes.values(), scaled_properties):
            route['features'][0]['properties']['scaledProperties'] = scaled_property

        return routes
    
    
    def calculate_route_score(self, route, routes_data, weight_distance=0.4, weight_time=0.4, weight_fare=0.2):
        # print(route)
        score = 0
        for i in range(len(route) - 1):
            route_info = routes_data[(route[i], route[i + 1])]
            # print(0000)
            # print(type(route_info))
            # route_info = get_scaled_properties(route_info)
            route_features = route_info['features'][0]
            # print_json(route_info)0
            route_properties = route_features['properties']
            route_scaled_properties = route_properties['scaledProperties']
            # print(route_info_scaled_properties)
            score += route_scaled_properties['scaledDTFScore']
        return score
    
    # 출발지에서 시작하여 모든 장소를 방문 후 출발지로 돌아오는 최적 경로 탐색
    def find_optimal_route(self, places, routes_data):
        num_places = len(places)
        all_routes = list(permutations(range(1, num_places)))  # 출발지를 제외한 경유지들의 순열 생성
        best_score = 0
        best_route = None

        # print(f'출발지 제외 경유지 순열: {list(all_routes)}')   

        for route in all_routes:
            route = (0,) + route + (0,)  # 출발지(0)를 추가해 순환 경로 형성
            score = round(self.calculate_route_score(route, routes_data), 4)
            # print(f'{route}: {score}')
            if score > best_score:
                best_score = score
                best_route = route
                
        return best_route, best_score

    
    def get_top_k_routes_tsp(self, start_place: str, end_place: str, region: str, festival_place: str, 
                         comb: int = 2, comb_k: int = 5, top_k: int = 3) -> list:
        """자체 TSP 알고리즘을 활용한 축제 중심 여행 경로 추천 함수.

        Args:
            start_place (str): _description_
            end_place (str): _description_  (unused @241113)
            region (str): _description_
            festival_place (str): _description_
            comb (int, optional): _description_. Defaults to 2.
            comb_k (int, optional): _description_. Defaults to 5.
            top_k (int, optional): _description_. Defaults to 3.

        Returns:
            list: _description_
        """
        place_combinations = self.place_data_manager.generate_place_combinations(region, comb, comb_k)
        
        # 각 장소 조합 별 최적 경로를 담는 리스트
        best_routes_for_each_place_comb = []

        # 장소 조합 별 경유지 순서 최적화 진행 
        for p, places in enumerate(place_combinations):

            places = self.add_start_and_festival_places(places=places, start=start_place, festival_place=festival_place)
        
            routes_for_place_comb = dict()

            for i, src in enumerate(places):
                for j, dst in enumerate(places):
                    if i != j:
                        routes_for_place_comb[(i, j)] = self.fetch_route_data(start=src, end=dst)
            
            # 정규화된 Properties를 추가
            routes_for_place_comb = self.get_scaled_properties(routes=routes_for_place_comb)

            # 출발지에서 시작하여 모든 장소를 방문 후 출발지로 돌아오는 최적 경로 탐색 
            best_route, best_score = self.find_optimal_route(places=places, routes_data=routes_for_place_comb)

            start = places[best_route[0]]
            end = places[best_route[-1]]
            passList = [places[pl] for pl in best_route[1:-1]]
            optimal_route = self.tmap_client.get_route_data(start=start, end=end, passList=passList)
            
            # print_json(optimal_route)

            
            _properties = optimal_route['features'][0]['properties']
            properties = {
                'totalDistance': _properties['totalDistance'],
                'totalTime': _properties['totalTime'],
                'totalFare': _properties['totalFare'],
                'routeScore': best_score
            }

            points = []
            coordinates = []

            # 장소 안내 지점 유형
            # pointType_list = ['S', 'E', 'B1', 'B2', 'B3']
            pointType_pattern = r'^(S|E|B\d*)$'  # S(출발지), E(경유지), B*(경유지)

            pointName_index = 0
            for _feature in optimal_route['features']:
                if ('description' not in _feature['properties'].keys()) or _feature['properties']['description'] == '경유지와 연결된 가상의 라인입니다':
                    continue
                _geometry = _feature['geometry']
                if _geometry['type'] == 'Point' and re.match(pointType_pattern, _feature['properties']['pointType']):
                    point = defaultdict(str)
                    point['pointId'] = _feature['properties']['pointIndex']
                    point['pointName'] =  places[pointName_index % len(places)]['name']  # 장소명 
                    point['pointLatitude'] = _geometry['coordinates'][1]  # 위도
                    point['pointLongitude'] = _geometry['coordinates'][0]  # 경도 
                    points.append(point)
                    pointName_index += 1

                elif _geometry['type'] == 'LineString':
                    coordinates.extend(_geometry['coordinates'])


            # 현재 장소 조합에 대한 경유지 순서 최적화 경로 데이터
            best_route_dict = {
                'properties': properties,
                'points': points,
                'lineCoordinates': coordinates
            }
            
            best_routes_for_each_place_comb.append(best_route_dict)

        # route_score 기준 내림차순 정렬
        best_routes_for_each_place_comb.sort(key=lambda x: x['properties']['routeScore'], reverse=True)

        return best_routes_for_each_place_comb[:top_k]


    
    def get_top_k_routes(self, start_place: str, end_place: str, region: str, festival_place: str, 
                         comb: int = 2, comb_k: int = 5, top_k: int = 3) -> list:
        """TMAP 경유지 순서 최적화 API를 활용한 여행 경로 추천 함수.

        Args:
            start_place (str): _description_
            end_place (str): _description_
            region (str): _description_
            festival_place (str): _description_
            comb (int, optional): _description_. Defaults to 2.
            comb_k (int, optional): _description_. Defaults to 5.
            top_k (int, optional): _description_. Defaults to 3.

        Returns:
            list: _description_
        """
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
            # print(place_combination)
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
            # places = []
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
                    # places.append(_point['pointName'])

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
            properties['routeScore'] = self.calculate_place_score(place_combination[:-1], region)

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
    
