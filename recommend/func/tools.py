import json 

def print_json(data:json):
    """json 형태의 데이터를 출력하는 함수입니다.

    Args:
        data (json): json 형태의 데이터
    """
    pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
    print(pretty_json)