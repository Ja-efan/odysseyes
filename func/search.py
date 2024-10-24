import os
import requests
from dotenv import load_dotenv

load_dotenv()
KAKAO_API_KEY = os.environ['KAKAO_KEY']
API_KEY = os.environ['API_KEY']

def get_lon_lat(search: str):
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

    # 그냥 검색
    search = ' '.join(search.split('/'))
    params = {'query': search, 'page': 1}
    # API 요청
    response = requests.get(url, headers=headers, params=params)
    # JSON 응답 파싱
    data = response.json()
    
    # print(search, data)
    # 결과 확인 및 위도와 경도 추출
    if data['documents']:
        
        address_info = data['documents'][0]
        longitude = address_info['x']
        latitude = address_info['y']

        # print('latlon', address_info["place_name"], (longitude, latitude))

        # 경도: x, 위도: y
        return address_info["place_name"], (longitude, latitude)
        
    return None, None

"""
{'addr1': '충청남도 공주시 금벽로 368 (신관동)',
 'addr2': '공주 금강신관공원, 충청남도 부여군 규암면 백제문로 455 백제문화단지',
 'areacode': '34',
 'booktour': '',
 'cat1': 'A02',
 'cat2': 'A0207',
 'cat3': 'A02070200',
 'contentid': '952988',
 'contenttypeid': '15',
 'createdtime': '20100219201036',
 'firstimage': 'http://tong.visitkorea.or.kr/cms/resource/46/2953046_image2_1.jpg',
 'firstimage2': 'http://tong.visitkorea.or.kr/cms/resource/46/2953046_image3_1.jpg',
 'cpyrhtDivCd': 'Type3',
 'mapx': '127.1275545162',
 'mapy': '36.4702917892',
 'mlevel': '6',
 'modifiedtime': '20240808174411',
 'sigungucode': '1',
 'tel': '공주시 041-840-8090<br>부여군 041-830-2208',
 'title': '백제문화제'}
"""

def get_festival_info(search_keyword):

    URL = f"http://apis.data.go.kr/B551011/KorService1/searchKeyword1?numOfRows=12&pageNo=1&MobileOS=ETC&MobileApp=AppTest&ServiceKey={API_KEY}&listYN=Y&arrange=A&areaCode=&sigunguCode=&cat1=A02&cat2=A0207&cat3=&keyword={search_keyword}&_type=json"
    response = requests.get(URL)
    result = response.json()['response']['body']['items']['item'][0]
    map_lat_lon = float(result['mapy']), float(result['mapx'])
    addr_list = [result['addr1']]
    addr_list.append(result['addr2'].split(',')[-1])

    for i, addr in enumerate(addr_list):
        if addr.endswith('일원'):
            addr_list[i] = ' '.join(addr.split()[:-1])
        if '(' in addr:
            addr_list[i] = addr[:addr.find('(')]
    # print(addr_list)
    lat_lon_dict = {}
    for addr in addr_list:
        place_name, lat_lon = get_lon_lat(addr)
        lat_lon_dict[(place_name, addr)] = list(map(float, lat_lon))

    image = result['firstimage']
    phones = result['tel'].split('<br>')[1:-1]

    return search_keyword, map_lat_lon, lat_lon_dict, image, phones