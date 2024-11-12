import pandas as pd 
import json 
from itertools import combinations, product
from sklearn.preprocessing import MinMaxScaler
import sys
import os

# 현재 모듈 파일의 디렉터리 경로를 가져옴
module_dir = os.path.dirname(os.path.abspath(__file__))

# CSV 파일의 경로를 모듈 파일 경로를 기준으로 설정
DATA_PATH = os.path.join(module_dir, '..', 'data', '추천장소통합리스트.csv')


def print_json(data:json):
    """json 형태의 데이터를 출력하는 함수입니다.

    Args:
        data (json): json 형태의 데이터
    """
    pretty_json = json.dumps(data, indent=4)
    print(pretty_json)


def get_topk_per_category(df:pd.DataFrame, region:str="부여", k:int=5):
    """카테고리 별 점수 

    Args:
        df (pd.DataFrame): 장소 통합 데이터프레임 (관광지, 맛집, 카페)
        region (str, optional): 필터링 할 지역명칭(시군구 기준, 지방행정단위 제외). Defaults to "부여".
        k (int, optional): 카테고리 별 추출할 장소 개수 (최종점수 기준). Defaults to 5.

    Returns:
        _type_: pd.DataFrame
    """

    result_idx = []
    df_copy = df[df["지역"] == region].copy(deep=True)
    for i in range(k):
        topk_idx = df_copy.groupby("분류")["최종점수"].idxmax()
        df_copy = df_copy.drop(topk_idx)
        result_idx.extend(topk_idx)
    result_df = df.loc[result_idx]
    return result_df


def get_festival_region_df(df:pd.DataFrame, region:str):
    """추천 장소 데이터에서 축제 지역(region)에 해당하는 데이터만 필터링 하는 함수입니다.

    Args:
        df (pd.DataFrame): 추천 장소 데이터
        region (str): 축제 지역

    Returns:
        _type_: pd.DataFrame
    """
    return df[df["지역"] == region]


def get_place_comb_list(region:str, n=3, k=5):
    """cafe_list와 res_list에서 각각 하나의 원소를 선택하고, 나머지는 land_list에서 선택하는 조합을 만듭니다.

    Args:
        df (pd.DataFrame): 추천 장소 데이터프레임
        region (str): 선정한 축제 지역 키워드
        n (int, optional): 선택할 조합의 개수. Defaults to 3.
        k (int, optional): 카테고리 별 선택할 상위 k개. Defaults to 5.

    Returns:
        _type_: 만들어진 모든 조합으로 구성된 리스트

    사용 예시:
        comb_list = get_place_comb_list(region="부여", n=3, k=5)

    참고 사항:
        SK Open API 요청 건수 한계로 인해 k 파라미터 생성.
    """
    df = pd.read_csv(DATA_PATH)
    
    # 지역 필터링
    festival_region_df = get_festival_region_df(df=df, region=region)

    # 분류(카테고리)별 '최종점수' 컬럼 기준 topk 개 
    festival_region_df = get_topk_per_category(festival_region_df, region, 5)

    # 카테고리 리스트
    cafe_list = festival_region_df[festival_region_df['분류'] == '카페']['목적지명'].values
    res_list = festival_region_df[festival_region_df['분류'] == '식당']['목적지명'].values
    land_list = festival_region_df[festival_region_df['분류'] == '관광지']['목적지명'].values
    
    combinations_list = []
    
    # cafe_list와 res_list에서 각각 1개를 선택하는 조합을 생성합니다.
    for cafe in cafe_list:
        for res in res_list:
            # 나머지 n-2 개의 원소는 land_list에서 선택합니다.
            for land_comb in combinations(land_list, n - 2):
                # 선택된 원소들을 조합하여 리스트에 추가합니다.
                combinations_list.append([cafe, res] + list(land_comb))
    
    return combinations_list


def get_places_score(place_list:list, region:str)->list:
    """추천 장소들에 대한 자체 산정 점수 리스트를 반환하는 함수입니다.

    Args:
        place_keyword (str): 출발지, 도착지 그리고 축제 장소를 제외한 장소 리스트 
        region (str): 지역명 for 데이터 필터링
    Returns:
        list: 장소들의 '최종점수' 리스트 
    """
    place_df = pd.read_csv(DATA_PATH)
    place_df = place_df[place_df["지역"] == region]
    # print(place_df)
    
    place_scores = []
    # print(place_list)
    for place_keyword in place_list:
        place_data = place_df[place_df["목적지명"] == place_keyword]
        place_score = float(place_data["최종점수"].values[0])
        place_scores.append(place_score)
    
    return place_scores


def get_route_score(place_list:list, region:str)->float:
    """경로 내 추천 장소에 대한 점수 합을 반환하는 함수입니다.

    Args:
        place_list (list): 추천 장소 리스트 
        region (str): 지역명(시군구 단위)

    Returns:
        float: 경로 내 추천 장소에 대한 점수 합
    """
    place_score_list = get_places_score(place_list=place_list, region=region)
    route_score = sum(place_score_list)

    return route_score


def get_scaled_score(route_list:json):
    """각 점수에 대해 minmax scaling 진행 후 전체 점수를 합한 totalScore 컬럼을 추가하는 함수 

    Args:
        route_list (json): 경로 리스트 

    Returns:
        list: totalScore 컬럼이 추가 된 경로들의 리스트 
    """
    # properties의 데이터를 모아서 scaling 적용하기
    properties_data = []
    for route in route_list:
        properties_data.append(route["properties"])

    properties_df = pd.DataFrame(properties_data)

    # print(properties_df)
    # Min-Max Scaler 생성
    scaler = MinMaxScaler()

    # Min-Max Scaling 적용
    scaled_properties = scaler.fit_transform(properties_df)
    # print(scaled_properties)

    # DataFrame으로 변환
    scaled_properties_df = pd.DataFrame(scaled_properties, columns=properties_df.columns)

    scaled_properties_df['totalScore'] = scaled_properties_df.sum(axis=1)
    # print(scaled_properties_df)

    for i, route in enumerate(route_list):
        route["properties"]["totalScore"] = round(float(scaled_properties_df.loc[i, "totalScore"]), 2)

    return route_list


def get_topk_optimized_route(route_list, k:int=3):
    """전체 경로 리스트에서 totalScore 기준 상위 k 개의 경로를 반환합니다.

    Args:
        route_list (_type_): 경로 리스트 
        k (int, optional): 상위 k 개. Defaults to 3.

    Returns:
        list: 상위 k개 경로 리스트
    """
    route_list.sort(key=lambda x: x["properties"]["totalScore"], reverse=True)
    return route_list[:k]