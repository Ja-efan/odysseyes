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


def load_json(file_path):
    """
    Load JSON data from a file and return it as a Python dictionary.
    
    Parameters:
        file_path (str): Path to the JSON file.
        
    Returns:
        dict: JSON data as a Python dictionary.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. Please check the file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



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


def format_time(total_seconds: int) -> str:
    """초 단위의 소요 시간을 'h시간 m분' 형식으로 변환하는 함수.

    Args:
        total_seconds (int): 소요 시간(초 단위)

    Returns:
        str: 'h시간 m분' 형식의 문자열
    """
    total_minutes = total_seconds // 60  # 초를 분으로 변환
    hours = total_minutes // 60  # 시간 계산
    minutes = total_minutes % 60  # 남은 분 계산
    if hours > 0:
        # print(f"")
        # print(total_minutes)
        return f"{hours}시간 {minutes}분" if minutes > 0 else f"{hours}시간"
    else:
        return f"{minutes}분"
