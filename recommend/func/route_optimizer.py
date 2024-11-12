import pandas as pd
from collections import OrderedDict, defaultdict
from sklearn.preprocessing import MinMaxScaler

# from tmap_client import TMAPClient  # new 
# from place_data_manager import PlaceDataManager  # new

from tmap_route_optimizer import PlaceDataManager, TMAPClient  # old 


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