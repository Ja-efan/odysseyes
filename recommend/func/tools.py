import os 
import json 
from typing import Union

def print_json(data:json):
    """json 형태의 데이터를 출력하는 함수입니다.

    Args:
        data (json): json 형태의 데이터
    """
    pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
    print(pretty_json)


def save_json(data: Union[dict, list], file_name: str):
    """JSON 데이터를 파일에 저장하는 함수입니다.

    Args:
        data (dict): 저장할 JSON 데이터
        file_name (str): 저장할 파일 이름 (예: "data.json")
    """
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Data saved to {file_name}")


def find_target_directory(target_dir_name):
    current_path = os.getcwd()
    while True:
        # 상위 디렉토리에서 대상 디렉토리 이름을 찾음
        parent_path, current_dir = os.path.split(current_path)
        
        if current_dir == target_dir_name:
            return current_path
        
        if parent_path == current_path:  # 최상위 디렉토리에 도달하면 종료
            break
        
        # 상위 디렉토리로 이동
        current_path = parent_path
    
    return None  # 대상 디렉토리를 찾지 못한 경우


def get_project_root_path(proejct_directory_name: str='odysseyes'):
    return  find_target_directory(target_dir_name=proejct_directory_name)
