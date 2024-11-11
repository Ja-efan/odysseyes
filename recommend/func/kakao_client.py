import os
import sys
from dotenv import load_dotenv
import requests

class KakaoMobilityClient:
    """Kakao Mobility API 호출을 담당하는 클래스 
    """
    def __init__(self, api_key:str):
        self.api_key = api_key

    def get_route_data(self, start_poi, end_poi):
        url = "https://apis-navi.kakaomobility.com/v1/directions"
        headers = {
            "Authorization": f"KakaoAK {self.api_key}"
        }
        params = {
            "origin": f"{start_poi['longitude']},{start_poi['latitude']}",  # 시작 지점의 경도, 위도
            "destination": f"{end_poi['longitude']},{end_poi['latitude']}",  # 종료 지점의 경도, 위도
            "priority": "DISTANCE"  # 최단 거리 우선으로 경로 설정 (TIME: 최단 시간 우선)
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            route_data = response.json()
            return route_data
        else:
            print(f"Error: {response.status_code}")
            return None