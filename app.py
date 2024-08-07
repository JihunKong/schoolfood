import streamlit as st
import requests
from openai import OpenAI

# NEIS API 키 설정
NEIS_API_KEY = st.secrets["api_keys"]["neis"]

# OpenAI 클라이언트 설정
client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

def get_school_info(school_name):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "SCHUL_NM": school_name,
        "pIndex": 1,
        "pSize": 100
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        data = response.json()
        return data.get('schoolInfo', [{}])[1].get('row', [])
    except requests.exceptions.RequestException as e:
        st.error(f"학교 정보를 가져오는 중 오류 발생: {str(e)}")
        return []

def get_meal_info(edu_office_code, school_code, date):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": edu_office_code,
        "SD_SCHUL_CODE": school_code,
        "MLSV_YMD": date,
        "pIndex": 1,
        "pSize": 100
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        data = response.json()
        meal_service_diet_info = data.get('mealServiceDietInfo', [])
        if len(meal_service_diet_info) > 1:
            return meal_service_diet_info[1].get('row', [])
        else:
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"급식 정보를 가져오는 중 오류 발생: {str(e)}")
        return []

def get_gpt_summary(meal_info):
    prompt = f"다음은 오늘의 급식 메뉴입니다: {meal_info}. 이 메뉴에 대해 간단히 요약해주세요."
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # gpt-4o-mini 모델이 존재하지 않아 gpt-3.5-turbo로 변경
            messages=[
                {"role": "system", "content": "당신은 학교 급식 메뉴를 분석하고 요약하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API 오류: {str(e)}")
        return "요약 생성 중 오류가 발생했습니다."

def clean_meal_info(meal_info):
    """HTML 태그를 제거하고 급식 정보를 깔끔하게 정리합니다."""
    return meal_info.replace('<br/>', '\n')  # 'repalce'를 'replace'로 수정

st.title("학교 급식 검색 앱")

school_name = st.text_input("학교 이름을 입력하세요")
if school_name:
    schools = get_school_info(school_name)
    if schools:
        selected_school = st.selectbox("학교를 선택하세요", 
                                       [school['SCHUL_NM'] for school in schools])
        selected_school_info = next(school for school in schools if school['SCHUL_NM'] == selected_school)
        
        date = st.date_input("날짜를 선택하세요")
        if date:
            meal_info = get_meal_info(selected_school_info['ATPT_OFCDC_SC_CODE'],
                                      selected_school_info['SD_SCHUL_CODE'],
                                      date.strftime("%Y%m%d"))
            if meal_info:
                st.subheader("오늘의 급식")
                for meal in meal_info:
                    st.write(f"**{meal['MMEAL_SC_NM']}**")
                    clean_menu = clean_meal_info(meal['DDISH_NM'])
                    st.text(clean_menu)
                    
                    summary = get_gpt_summary(clean_menu)
                    st.write("**GPT 요약:**")
                    st.write(summary)
                    st.write("---")  # 각 식사 정보 사이에 구분선 추가
            else:
                st.write("해당 날짜의 급식 정보가 없습니다.")
    else:
        st.write("학교 정보를 찾을 수 없습니다.")
