import folium
import pandas as pd
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# import streamlit as st
# import base64

# 데이터프레임 생성
data = {
    '목적지명': ['12월의왈츠', '24시전주명가콩나물국밥/공주점', '505펜션앤키즈캠핑장', '60계치킨/충남공주신관점', 'BBQ/공주신월점', 'BBQ/공주신월점', 'BHC/공주대점'],
    '목적지X좌표': [127.246099, 127.1334532, 127.0201282, 127.1365903, 127.1478949, 127.1478949, 127.1371736],
    '목적지Y좌표': [36.358756, 36.46930583, 36.50125213, 36.47292271, 36.47375601, 36.47375601, 36.47331156],
    '목적지읍면동명': ['반포면', '신관동', '사곡면', '신관동', '신관동', '월송동', '신관동'],
    '소분류': ['펜션', '한식', '캠프장', '치킨', '치킨', '치킨', '치킨'],
    '방문건수': [18, 42, 105, 3, 6, 3, 9],
    '방문건수구간': [4, 4, 5, 1, 2, 1, 3]
}

df=pd.read_csv("data/g_togo_count.csv")
df.head()

# 지도 생성 (중심을 대략적인 평균 좌표로 설정)
map_center = [df['목적지Y좌표'].mean(), df['목적지X좌표'].mean()]
m = folium.Map(location=map_center, zoom_start=12)

# 색상을 위한 방문건수 구간에 따른 색상 설정 함수
def get_color(방문건수구간):
    if 방문건수구간 == 1:
        return 'lightgray'
    elif 방문건수구간 == 2:
        return 'lightblue'
    elif 방문건수구간 == 3:
        return 'orange'
    elif 방문건수구간 == 4:
        return 'red'
    else:
        return 'darkred'

# 방문건수구간이 5인 경우 라벨 붙이기
for _, row in df.iterrows():
    color = get_color(row['방문건수구간'])
    folium.CircleMarker(
        location=[row['목적지Y좌표'], row['목적지X좌표']],
        radius=7 + row['방문건수'] * 0.005,  # 방문건수에 따라 크기 조절
        color=color,
        fill=True,
        fill_opacity=0.7
    ).add_to(m)
    
    # 방문건수구간이 5인 경우 라벨 추가
    if row['방문건수구간'] == 5:
        label = f"{row['목적지읍면동명']}, {row['소분류']}, 방문건수: {row['방문건수']}"
        folium.Marker(
            location=[row['목적지Y좌표'], row['목적지X좌표']],
            popup=label,
            icon=folium.Icon(color='darkred')
        ).add_to(m)

st_data = st_folium(m, width=700, height=500)

# 지도 저장
# m.save('map.html')