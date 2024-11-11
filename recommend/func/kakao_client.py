import os
import sys
from dotenv import load_dotenv
import requests
import json

class KakaoMobilityClient:
    """Kakao Mobility API 호출을 담당하는 클래스 
    """
    def __init__(self, api_key:str):
        self.api_key = api_key

    def get_route_data(self, start_poi, end_poi, waypoints: list=None):
        url = "https://apis-navi.kakaomobility.com/v1/directions"

        headers = {
            "Authorization": f"KakaoAK {self.api_key}",
            "Content-Type": "application/json"
        }

        params = {
            "origin": f"{start_poi['longitude']},{start_poi['latitude']}",  # 시작 지점의 경도, 위도
            "destination": f"{end_poi['longitude']},{end_poi['latitude']}",  # 종료 지점의 경도, 위도
            "priority": "RECOMMEND",  # 경로 탐색 우선순위 (TIME: 최단 시간, DISTANCE: 최단 거리, RECOMMEND: 추천 경로 (default))
            "waypoints": waypoints
        }
        
        # 경유지가 존재하는 경우 
        if waypoints:
            waypoints_str = "|".join([f"{wp['longitude']},{wp['latitude']}" for wp in waypoints])
            params["waypoints"] = waypoints_str
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            route_data = response.json()
            return route_data
        else:
            print(f"Error: Received status code {response.status_code} from Kakao Mobility API for route.")
            return None
        
    
    def extract_polyline_points(self, route_data:json, has_waypoints: bool=False):
        """API를 통해 얻어온 경로 정보(Json)에서 PolyLine(경로 좌표)를 추출하는 함수.

        Args:
            route_data (json): Kakao Mobility Api를 통해 수집한 경로 데이터
            has_waypoints (bool, optional): 경유지 존재 여부. Defaults to False.

        Returns:
            list: 경로 좌표 정보(PolyLine) 리스트 
        """
        polyline_points = list()
        for section in route_data['routes'][0]['sections']:
            for road in section['roads']:
                vertexes = road['vertexes']
                # vertexes를 [위도, 경도] 리스트로 변환하여 PolyLine을 생성
                polyline_points.extend([(vertexes[i+1], vertexes[i]) for i in range(0, len(vertexes), 2)])

        return polyline_points
        