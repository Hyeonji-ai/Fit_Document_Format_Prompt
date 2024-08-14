Fit_Document_Format_Prompt
==========================
### 보고서 자동 변환 프롬프트 시스템입니다.

Installation
---------------
First install :
  !pip3 install python-docx
  !pip3 install --upgrade --user --quiet google-cloud-aiplatform
  !pip install matplolib
  !pip install flask
  !pip install vertexai
end

How to Use
---------------
#### 1. FICL_Code.ipynb 파일이 각 시스템 모듈별로 실행 할 수 있는 파일입니다.
#### 2. server.py 챗봇형 웹서비스를 로컬에서 실행하는 파일입니다. server.py 파일을 실행하시고 해당 로컬 주소로 가시면 챗봇 서비스를 이용하실 수 있습니다. 
#### 3.Google API를 사용하기 때문에 각 개별 프로젝트 ID API Key가 필요합니다. Google Cloud Platform에서 API Key를 json 파일로 다운 받고 Algorithm 파일에 포함된 bogosea_generater.py, email_generator.py, graph_generate.py에 SERVICE_ACCOUNT_FILE에 각 개별로 다운받은 API Key를 입력하시면 됩니다.
#### 4.생성된 파일은 로컬에 저장됩니다.
