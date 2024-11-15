import os
import sys
from dotenv import load_dotenv
import requests
import json

class KakaoClient:
    """Kakao Mobility API 호출을 담당하는 클래스 
    """
    def __init__(self, api_key:str):
        self.api_key = api_key

    def get_poi(self, keyword:str, region:str = None) -> dict:
        """키워드를 이용해 POI(Point of Interest) 정보를 가져오는 함수.

        Args:
            keyword (str): 검색할 POI 키워드. 예를 들어, "백제문화단지", "남산타워"과 같은 장소 유형.
            region (str, optional): 특정 지역 내에서 검색할 때 사용할 지역 이름. 예를 들어, "서울" 등. 
                기본값은 None이며, 지정하지 않으면 모든 지역에서 검색합니다.

        Returns:
            dict: 검색 결과 중 첫 번째 POI의 정보를 반환. POI 정보가 없을 경우 빈 사전을 반환.
                - 'latitude' (str): POI의 위도 정보.
                - 'longitude' (str): POI의 경도 정보.
                - 'name' (str): POI의 이름.
        
        Raises:
            json.JSONDecodeError: 응답이 JSON 형식이 아닐 경우 발생하는 예외.

        Example:
            ```
            poi_data = get_poi(keyword="백제문화단지", region="서울")
            print(poi_data)
            # Output: {'latitude': '36.30662608', 'longitude': '126.90670093', 'name': '백제문화단지'}
            ```
        """
        # ref. https://developers.kakao.com/docs/latest/ko/local/common
        # 로컬(local) API는 키워드로 특정 장소 정보를 조회하거나, 
        # 좌표를 주소 또는 행정구역으로 변환하는 등 장소에 대한 정보를 제공합니다. 
        # 특정 카테고리로 장소를 검색하는 등 폭넓은 활용이 가능하며, 
        # 지번 주소와 도로명 주소 체계를 모두 지원합니다.            

        url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
        headers = {"Authorization": f"KakaoAK {self.api_key}"}

        search_keyword = f"{region} {keyword}" if region else keyword
        params = {'query': search_keyword, 'page': 1}

        # API 요청
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200: 
            print(f"Error: Received status code {response.status_code} from KAKAO Local API for POI.")
            return {}
        try: 
            # JSON 응답 파싱
            data = response.json()
        except json.JSONDecodeError:
            print("Error: Response is not in JSON format.")
            print("Response content:", response.text)
            return {}
        
        # 결과 확인 및 위도와 경도 추출
        if data['documents']:
            first_poi = data['documents'][0]
            longitude = first_poi['x']  # 경도
            latitude = first_poi['y']  # 위도
            return {
                'name': first_poi['place_name'],
                'latitude': latitude,
                'longitude': longitude
            }
            
        return {}

    def get_route_data(self, start_poi, end_poi, waypoints: list=None):
        # ref. https://developers.kakaomobility.com/docs/navi-api/directions/
        url = "https://apis-navi.kakaomobility.com/v1/directions"

        headers = {
            "Authorization": f"KakaoAK {self.api_key}",
            "Content-Type": "application/json"
        }

        params = {
            "origin": f"{start_poi['longitude']},{start_poi['latitude']}",  # 시작 지점의 경도, 위도
            "destination": f"{end_poi['longitude']},{end_poi['latitude']}",  # 종료 지점의 경도, 위도
            "priority": "RECOMMEND",  # 경로 탐색 우선순위 (TIME: 최단 시간, DISTANCE: 최단 거리, RECOMMEND: 추천 경로 (default))
        }
        
        # 경유지가 존재하는 경우 
        if waypoints:
            # waypoints_str = "|".join([f"{wp['longitude']},{wp['latitude']}" for wp in waypoints])
            # params["waypoints"] = waypoints_str
            waypoints = [
                {
                    'name': wp['name'],
                    'x': float(wp['longitude']),
                    'y': float(wp['latitude']) 
                }
                for wp in waypoints
            ]
        
        response = requests.get(url, headers=headers, params=params)


        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} from KAKAO Mobility API for Route.")
            return {}
        try:
            return response.json()
        except:
            
            print(f"Error: Received status code {response.status_code} from Kakao Mobility API for Route.")
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
        