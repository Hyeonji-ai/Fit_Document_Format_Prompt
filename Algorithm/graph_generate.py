# 사용자가 그래프 종류 직접 입력해서 데이터 시각화 하는 코드

from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
from vertexai.preview.generative_models import GenerativeModel, Image
import ast
from google.oauth2 import service_account
import vertexai
from flask import Flask, send_file
from datetime import datetime

import re
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import ast
import os

PROJECT_ID = ""#GCP 프로젝트 ID 작성하면됨
LOCATION = "us-central1"
MODEL_ID = "gemini-1.5-flash-001"

SERVICE_ACCOUNT_FILE = ''#API Key json 파일 경로  
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

class Graph:
    def __init__(self,project, location):
        self.project = project
        self.location = location
        self.generation_config = {
            "max_output_tokens": 8192,
            "temperature": 1,
            "top_p": 0.95,
        }
        self.safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    def make_graph(self,ex_graph, report): # 그래프 생성
        ex_graph = ex_graph
        report = report
        model = GenerativeModel('gemini-1.5-flash-001')

        # 데이터 영어로 변환
        title_guideline = "다른 설명 필요없이 영어로 번역해"
        to_English = model.generate_content([title_guideline,report])

        # 그래프 제목
        summurize_English = "데이터 내용 분석해서 그래프로 시각화할려고 해. 그래프에 적을 적절한 제목 만들어줘. 명확하고 간결한 제목으로. 부가 설명 필요 없이 제목만 나열"
        title = model.generate_content([summurize_English,to_English.text])
        title1 = title.text
        title2_guideline = "데이터 분석을 통한 최종 제목 선택, 데이터의 키워드를 포함한 제목. 간결하면서 명확한 제목.다른 설명 필요없이 최종 제목만 프린트"
        title2 = model.generate_content([title2_guideline,to_English.text,title1])
        TITLE = title2.text  # ***** 그래프 제목 *****
        print(TITLE)

        # 그래프 생성
        making_graph_guideline = """{to_English} 내용 분석해서 {ex_graph} 모양 그래프로 생성할거야. 시각화한 그래프의 제목은 {title}로 넣어서 그래프 이미지 생성해줘.
                                    그래프 폰트 설정 따로 하지마
                                    그래프 제목은 한글로 하고 라벨 이름도 {report}에서 한국어로 나와있으면 한국어로 적어.""".format(to_English=to_English.text, ex_graph= ex_graph, title=TITLE,report=report)
        model = GenerativeModel('gemini-1.5-pro-001')
        graph_image = model.generate_content([making_graph_guideline])
        #print(graph_image.text)

        # matplotlib으로 그래프 시각화
        show_guideline = "Please just extract the Python code from the given text."
        graph_show = model.generate_content([show_guideline,graph_image.text])
        have_to_remove = graph_show.text
        # print(graph_show.text)
        code = self.remove(have_to_remove) # 코드 부분만 추출
        TITLE = TITLE[:-2]
        TITLE = re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z\s]", "", TITLE) # 제목 특수문자 제거
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        png_title = "{}_{}.png".format(TITLE, timestamp)
        png_title = png_title.replace('\n','')
        print('png_title : ', png_title)
        last_code = r"""코드 맨 처음에 "import matplotlib\nmatplotlib.use('Agg')" 추가해.
                       코드에 '\nfont_path = ".\\font\\NanumGothic.ttf"  \n
                               fontprop = fm.FontProperties(fname=font_path)\nplt.rcParams['axes.unicode_minus'] = False'\n
                               \nplt.xticks(fontproperties=fontprop)\nplt.yticks(fontproperties=fontprop) 추가해.
                       그래프에 모든 폰트를 fontprop의 폰트로 설정해.
                       코드 마지막에 'plt.savefig('graph.png',format='png')\n추가해.
                       코드에 'plt.show()'가 포함되어 있다면 해당 코드 제거해.
                       코드에 'plt.xlabel()'가 포함되어 있는데 안에 내용이 문장이면 해당 코드 제거해."""
        last_code_make = model.generate_content([last_code,code])
        changing_code = last_code_make.text
        code2 = self.remove(changing_code) #plt.show 제거, plt.savefig 저장
        print(code2)

        # 그래프 초기화 코드 추가. 안 그러면 이전 생성한 그래프에 추가돼서 다시 생성하고 있어
        plt.clf()
        plt.close()

        exec(code2)
        os.rename('graph.png',png_title)
        return png_title

    def remove(self,have_to_remove):
      have_to_remove = have_to_remove
      line = have_to_remove.split('\n')
      code = []
      for i in line:
        try:
          ast.parse(i)
          code.append(i)
        except SyntaxError:
          pass
      return '\n'.join(code)
