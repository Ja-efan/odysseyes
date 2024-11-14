import os 
import sys 
import pandas as pd
from itertools import combinations

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
        # 컬럼명 변경
        self.place_data.rename(
            columns={
                '목적지명': 'name', 
                '분류': 'category', 
                '지역': 'region',
                '위도': 'latitude', 
                '경도':'longitude'
            }, inplace=True)
    
    def get_filtered_places(self, region: str, category: str, top_k: int = 5) -> pd.DataFrame:
        """특정 지역과 카테고리에 맞는 상위 장소 필터링"""
        filtered_data = self.place_data[(self.place_data['region'] == region) & (self.place_data['category'] == category)]
        return filtered_data.nlargest(top_k, '최종점수')
    
    def generate_place_combinations(self, region: str, n: int = 3, k: int = 5) -> list:
        """카페와 식당에서 각각 1개, 나머지는 관광지에서 선택하여 조합 생성"""

        # 장소 별 전체 정보를 넘기도록 코드 수정
        cafe_list = self.get_filtered_places(region, '카페', k).to_dict("records")
        res_list = self.get_filtered_places(region, '식당', k).to_dict("records")
        land_list = self.get_filtered_places(region, '관광지', k).to_dict("records")

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