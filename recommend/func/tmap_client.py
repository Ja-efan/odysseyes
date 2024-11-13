from dotenv import load_dotenv
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TMAPClient:
    """TMAP API 호출을 담당하는 클래스"""
    def __init__(self, api_key: str):
        """_summary_

        Args:
            api_key (str): _description_
        """
        self.api_key = api_key


    def get_poi(self, keyword: str, region: str = None) -> dict:
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
            ```python
            poi_data = get_poi(keyword="백제문화단지", region="서울")
            print(poi_data)
            # Output: {'latitude': '36.30662608', 'longitude': '126.90670093', 'name': '백제문화단지'}
            ```
        """
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
        """TMap API를 이용한 경로 탐색 함수.

            주어진 출발지와 도착지 사이의 최적 경로를 TMap API를 통해 탐색하고, 
            필요에 따라 최대 5개의 경유지를 지정할 수 있습니다.

            Args:
                start (dict): 출발지 정보로, 다음과 같은 키를 포함하는 사전 형식입니다.
                    - 'longitude' (float): 출발지 경도.
                    - 'latitude' (float): 출발지 위도.
                
                end (dict): 도착지 정보로, 다음과 같은 키를 포함하는 사전 형식입니다.
                    - 'longitude' (float): 도착지 경도.
                    - 'latitude' (float): 도착지 위도.

                passList (list, optional): 경유지 좌표 리스트로, 최대 5개의 경유지를 지원합니다. Defaults to None.
                    - 형식: 각 경유지는 {'longitude': 경도, 'latitude': 위도} 형식의 사전으로 구성.
                    - 예시: [{"longitude": 127.0, "latitude": 37.0}, {"longitude": 128.0, "latitude": 38.0}]

            Returns:
                dict: TMap API로부터 반환된 경로 탐색 결과. API 응답을 그대로 반환하며, 응답이 없거나 
                오류가 발생한 경우 빈 사전을 반환합니다.
            
            Raises:
                json.JSONDecodeError: 응답이 JSON 형식이 아닐 경우 발생하는 예외.

            Example:
                ```python
                start = {"longitude": 126.98217734415019, "latitude": 37.56468648536046}
                end = {"longitude": 129.07579349764512, "latitude": 35.17883196265564}
                passList = [{"longitude": 127.38454163183215, "latitude": 36.35127257501252}]
                
                route_data = get_route_data(start, end, passList)
                ```
        """
        # 출발지 위/경도 데이터가 없는 경우 
        if start['latitude'] == None and start['longitude'] == None:
            start = self.get_poi(start['name'])
        
        # 최종 도착지 위/경도 데이터가 없는 경우
        if end['latitude'] == None and end['longitude'] == None:
            end = self.get_poi(end['name'])

        # https://tmap-skopenapi.readme.io/reference/%EC%9E%90%EB%8F%99%EC%B0%A8-%EA%B2%BD%EB%A1%9C%EC%95%88%EB%82%B4
        url = "https://apis.openapi.sk.com/tmap/routes?version=1&callback=function"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "appKey": self.api_key
        }

        payload = {
            "tollgateFareOption": 16,  # 16: 로직판단(default)
            "roadType": 32,  # 32:가까운 도로(default)
            "endX": float(end['longitude']),  # 목적지 X좌표 (경도)
            "endY": float(end['latitude']),  # 목적지 Y좌표 (위도)
            "reqCoordType": "WGS84GEO",
            "startX": float(start['longitude']),  # 출발지 X좌표 (경도) 
            "startY": float(start['latitude']),  # 출발지 Y좌표 (위도)
            "carType": 0,
            "startName": start['name'],
            "endName": end['name'],
            "resCoordType": "WGS84GEO",
            "sort": "index"
        }

        # 경유지가 존재하는 경우 
        if passList:
            passList_lst = []
            for pl in passList:
                if pl['latitude'] == None and pl['longitude'] == None:
                    pl = self.get_poi(keyword=pl['name'])
                
                passList_lst.append(f"{str(pl['longitude'])},{str(pl['latitude'])}")

            passList_str = "_".join(passList_lst)
            payload["passList"] = passList_str

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} from TMAP API for route.")
            return response.json()

        try:
            return response.json()
        except json.JSONDecodeError:
            print("Error: Response is not in JSON format.")
            print("Response content:", response.text)  # 응답 내용을 출력해 문제를 확인합니다.
            return {}


    def get_optimized_route(self, start_poi:dict, end_poi:dict, via_pois: list = []) -> dict:
        """경유지 순서 최적화 API 호출"""
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
    

    def extract_polyline_points(self, route_data:json, has_passLists: bool=False):
        """API를 통해 얻어온 경로 정보(Json)에서 PolyLine(경로 좌표)를 추출하는 함수.

        Args:
            route_data (json): TMAP Mobility Api를 통해 수집한 경로 데이터
            has_passLists (bool, optional):  경유지 존재 여부. Defaults to False.

        Returns:
            list[tuple]: 경로 좌표 정보(PolyLine) 리스트 
        """

        polyline_points = []
        _features = route_data['features']
        for _feature in _features:
            _geometry = _feature['geometry']
            if _geometry['type'] == 'LineString':
                polyline_points.extend([(coords[0], coords[1]) for coords in _geometry['coordinates']])

        return polyline_points