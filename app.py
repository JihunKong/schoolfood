import streamlit as st
import requests
import json
import openai

# NEIS API 키 설정
NEIS_API_KEY = "bad69babd5034282a754c2b8b364ea53"

# OpenAI API 키 설정 (실제 키로 교체해야 함)
openai.api_key = "your_openai_api_key_here"

def get_school_info(school_name):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "SCHUL_NM": school_name,
        "pIndex": 1,
        "pSize": 100
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get('schoolInfo', [{}])[1].get('row', [])

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
    response = requests.get(url, params=params)
    data = response.json()
    return data.get('mealServiceDietInfo', [{}])[1].get('row', [])

def get_gpt_summary(meal_info):
    prompt = f"다음은 오늘의 급식 메뉴입니다: {meal_info}. 이 메뉴에 대해 간단히 요약해주세요."
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

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
                    st.write(f"{meal['MMEAL_SC_NM']}: {meal['DDISH_NM']}")
                    
                    summary = get_gpt_summary(meal['DDISH_NM'])
                    st.write("GPT 요약:", summary)
            else:
                st.write("해당 날짜의 급식 정보가 없습니다.")
    else:
        st.write("학교 정보를 찾을 수 없습니다.")
