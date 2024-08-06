##문서생성

import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from google.oauth2 import service_account
import re
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

PROJECT_ID = ""#GCP 프로젝트 ID 작성하면됨
LOCATION = "us-central1"
MODEL_ID = "gemini-1.5-flash-001"

SERVICE_ACCOUNT_FILE = ''#API Key json 파일 경로   
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

class DocumentProcessor:
    def __init__(self, doc_data_path,ref_doc_path,MODEL_ID):
        self.doc_data_path = doc_data_path
        self.ref_doc_data_path = ref_doc_path
        self.model = GenerativeModel(MODEL_ID)

    def modify_doc(self, doc_category):
        pdf_file_uri = self.doc_data_path
        prompt_template = """{document_category} 보고서 포맷 맞출건데 {pdf_path}를 기반으로 {document_category} 작성시 폰트나 문서 작업에 필요한 작성 요령 알려줘"""
        prompt_reference = """{reference_pdf_path}의 표의 위치 내용 구성 글꼴, 정렬, 그림 위치, 크기 등을 다 포함하여 word 코드 작성해줘"""
        prompt = prompt_template.format(document_category=doc_category, pdf_path=self.doc_data_path)
        pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
        contents = [pdf_file, prompt]
        response = self.model.generate_content(contents)
        return response.text, prompt_reference
    
    def extract_reference_doc_style(self):
        pdf_file_uri = self.ref_doc_data_path
        prompt_reference = """{reference_pdf_path}의 표의 위치 내용 구성 글꼴, 정렬, 그림 위치, 크기 등을 다 포함하여 word 코드 작성해줘"""
        prompt = prompt_reference.format(pdf_path=self.doc_data_path)
        pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
        contents = [pdf_file, prompt]
        response = self.model.generate_content(contents)
        return response.text


class MakingDoc:
    def __init__(self, project, location, model_name, ):
        self.project = project
        self.location = location
        self.model_name = model_name
        self.model = None
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

        self.common_guideline = """공문서의 양식은 국어기본법에 따른 어문규범을 준수해야 하고, 숫자는 아라비아 숫자를 사용해야 해. 연도는 서기연도를 쓰되 '서기'는 표시하지 않으며, 날짜는 숫자로 표현하되 년월일을 .으로 표시해. 시간은 24시각제로 표기하되 시분은 :로 구분하여 써야 해. 금액은 아라비아 숫자로 쓰되 숫자 다음에 괄호로 한글로 써야 해. 모든 글꼴은 맑은 고딕으로 써야 해."""

        self.text_template = {
            "기안문": """기안문은 특정 안건에 대해 기관의 의사를 결정하기 위하여 작성되며, 결재를 통해 성립되는 문서야. 기안의 근거를 밝히고 시작하고 사업이나 활동의 목적과 방향, 실행 방법 등이 명확하게 드러나야 하며 관련자 모두가 그 내용을 쉽고 정확하게 숙지할 수 있도록 필요한 정보를 일목요연하고 상세하게 기입하여야 해.""",
            "보도자료": """보도자료는 국민에게 널리 알려야 할 특정한 정책이나 사업 내용을 언론 매체에서 쉽게 보도할 수 있도록 정리한 문서와 시청각 매체야. 쉽고 친근한 어휘를 사용하여 적절한 길이의 문장으로 써야 하고 내용은 객관성과 신뢰성, 공정성 등을 고려하여 작성해야 하고 인용한 자료는 정확한 출처를 밝혀야 하며 적절한 양의 정보를 제공해야 하고 시각적 편의를 고려하여 구성해야 해.""",
            "결재문서": """내부문서는 행정기관이 내부적으로 업무 계획 수립, 현안 업무 보고, 관련 사항 검토, 처리 방침 결정 등을 하기 위하여 작성하는 문서야. 단락을 구조적이고 계층적으로 구성해야 하고 제목에 본문의 핵심적인 내용을 드러내는 용어(위촉, 계획, 개최, 조사, 회의 결과 등)을 사용하여 문서의 성격을 쉽게 파악할 수 있도록 하며 추상적이고 일반적인 표현보다 구체적이고 개별적인 표현을 써야 해.""",
            "공고문": """공고문은 특정한 사안이나 정책을 대중에게 널리 알리는 문서야. 공고하고자 하는 사안을 명료하게 설명해야 하고, 시행 주체와 시행 내용이 분명하게 드러나야 하며 간결하면서 정확한 표현을 사용해야 해."""
        }

        
        self.prompt_template = {
            "기안문": """{common_guideline}\n\n{template_text}\n\n작성자: {author}\n받는 사람: {recipient}\n주요 내용: {main_content}\n 이 문서를 위 지침에 맞춰 작성하는데 아래 코드의 내용에 맞춰서 생성해줘 그리고
            {referece_document_style} 이 부분은 꼭 반영해서 코드 작성해줘, 그리고 코드설명은 하지마""",

            
            "결재문서": """{common_guideline}\n\n{template_text}\n\n작성자: {author}\n받는 사람: {recipient}\n주요 내용: {main_content}\n 이 문서를 위 지침에 맞춰 작성하는데 아래의 코드에 기반하여 내용을 생성해줘 그리고
            {referece_document_style} 에 기반하여 문서 내용을 생성된 내용으로 변경하고 제목도 변경하여 파이썬 Document 라이브러리 이용하여 Word 코드 작성해줘,그리고 코드설명은 하지마""",

            "공고문": """{common_guideline}\n\n{template_text}\n\n작성자: {author}\n받는 사람: {recipient}\n주요 내용: {main_content}\n 이 문서를 위 지침에 맞춰 작성하는데 아래의 코드에 기반하여 내용을 생성해줘 그리고
             {referece_document_style} 에 기반하여 문서 내용을 생성된 내용으로 변경하고 제목도 변경하여 파이썬 Document 라이브러리 이용하여 Word 코드 작성해줘,그리고 코드설명은 하지마"""
            }

        self.make_file_prompt_template = """{generate_contents}를 문서로 만들건데
\n\n{common_guideline}를 배경지식으로 폰트나 여백 등에 맞춰서
\n\n{file_type} 파일로 만들수 있는 코드 알려줘"""

    def initialize_model(self):
        vertexai.init(project=self.project, location=self.location)
        self.model = GenerativeModel(self.model_name)

    def parse_user_input(self, user_input):
        parts = user_input.split('#')
        if len(parts) != 4:
            raise ValueError("입력 형식이 올바르지 않습니다. 작성자, 받는 사람, 주요 내용을 포함하여 입력해 주세요.")

        doc_type, author, recipient, main_content= [part.strip() for part in parts]
        return doc_type, author, recipient, main_content

    def generate_document(self, user_input, user_guideline=None):
        if self.model is None:
            self.initialize_model()

        doc_type, author, recipient, main_content = self.parse_user_input(user_input)

        if user_guideline:
            guideline = user_guideline
        elif doc_type in self.text_template:
            guideline = self.text_template[doc_type]
        else:
            raise ValueError("지원되지 않는 문서 유형입니다.")

        full_text = self.prompt_template[doc_type].format(
            common_guideline=self.common_guideline,
            template_text=guideline,
            author=author,
            recipient=recipient,
            main_content=main_content,
            referece_document_style = self.extract_reference_doc_style(),
        )

        file_prompt = self.make_file_prompt_template.format(
            generate_contents=full_text,
            common_guideline=self.common_guideline,
            file_type="word"
        )

        responses = self.model.generate_content(
            [full_text],
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            stream=True,
        )
        final_data = ''
        for response in responses:
            final_data += response.text
        return final_data

