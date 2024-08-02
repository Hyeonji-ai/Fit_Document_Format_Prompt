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
    def __init__(self, doc_data_path,MODEL_ID):
        self.doc_data_path = doc_data_path
        self.model = GenerativeModel(MODEL_ID)

    def modify_doc(self, doc_category):
        pdf_file_uri = self.doc_data_path
        prompt_template = """{document_category} 보고서 포맷 맞출건데 {pdf_path}를 기반으로 {document_category} 작성시 폰트나 문서 작업에 필요한 작성 요령 알려줘"""
        prompt = prompt_template.format(document_category=doc_category, pdf_path=self.doc_data_path)
        pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
        contents = [pdf_file, prompt]
        response = self.model.generate_content(contents)
        return response.text


class MakingDoc:
    def __init__(self, project, location, model_name):
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
            from docx import Document
            from docx.shared import Inches, Pt, Cm
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn


            class DocFormatting:
                def __init__(self, save_path):
                    self.save_path = save_path
                    self.doc = Document()

                def location_selection(self, position):
                    position = position
                    if position == 'left':
                        location = WD_PARAGRAPH_ALIGNMENT.LEFT
                    elif position == 'center':
                        location = WD_PARAGRAPH_ALIGNMENT.CENTER
                    elif position == 'right':
                        location = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    return location
                
                def add_title(self, title):
                    title = title
                    title_paragraph = self.doc.add_paragraph(title)
                    title_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    run = title_paragraph.runs[0]
                    run.font.size = Pt(12)
                    run.bold=True


                def add_slogan(self, slogan, position):
                    position = position
                    slogan_paragraph = self.doc.add_paragraph(slogan)
                    slogan_paragraph.alignment = self.location_selection(position)
                    run = slogan_paragraph.runs[0]
                    run.font.size = Pt(10)

                def add_logos_and_titles(self,sub_title):
                    table = self.doc.add_table(rows=1, cols=2)
                    row = table.rows[0].cells
                    row[0].width = Cm(9.0)

                    # 부제목
                    title_cell = row[0].add_paragraph()
                    run = title_cell.add_run(sub_title)
                    run.font.size = Pt(11) 
                    title_cell.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

                    # 오른쪽 표
                    right_table = table.cell(0,1).add_table(rows=2,cols=3)
                    right_table.rows[0].height = Cm(1.0)
                    right_table.rows[1].height = Cm(1.5)
                    right_table.cell(0,0).text = '팀장'
                    right_table.cell(0,1).text = '본부장'
                    right_table.cell(0,2).text = '사장'
                    for row in right_table.rows:
                        for cell in row.cells:
                            tc = cell._element
                            tc_pr = tc.xpath('./w:tcPr')[0]
                            tc_borders = OxmlElement('w:tcBorders')
                            for border_name in ['top', 'left', 'bottom', 'right']:
                                border = OxmlElement(f'w:border_name')
                            
                                border.set(qn('w:val'), 'single')
                                border.set(qn('w:sz'), '4')  # 두께 설정
                                border.set(qn('w:space'), '0')
                                border.set(qn('w:color'), '000000')  # 색상 설정(검정색)
                                tc_borders.append(border)
                            tc_pr.append(tc_borders)
                    for row in right_table.rows:
                        for cell in row.cells:
                            cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # 수평 가운데 정렬


                def bottom(self, title, sub_title):
                    table = self.doc.add_table(rows=2, cols=1)
                    row = table.rows[0].cells

                    # 위
                    title_cell = row[0].add_paragraph()
                    run = title_cell.add_run(title)
                    run.bold = True
                    run.font.size = Pt(12) 
                    title_cell.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                    # 아래
                    subtitle_paragraph = self.doc.add_paragraph(sub_title)
                    subtitle_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    subtitle_run = subtitle_paragraph.runs[0]
                    subtitle_run.bold = False
                    subtitle_run.font.size = Pt(10) 
                    subtitle_paragraph.space_after = Pt(0)

                def add_logos(self, path, position):
                    path = path # 이미지 경로
                    position = position # 로고 위치
                    paragraph = self.doc.add_paragraph()
                    run = paragraph.add_run()
                    run.add_picture(path)
                    paragraph.alignment = self.location_selection(position)

                def add_separator(self):
                    # 긴 줄 추가
                    separator_paragraph = self.doc.add_paragraph()
                    separator_paragraph.space_before = Pt(0)  # 구분선과 부제목 사이에 간격 제거
                    separator_paragraph.space_after = Pt(0)  # 구분선과 본문 사이에 간격 제거
                    run = separator_paragraph.add_run()
                    run.font.size = Pt(1)
                    separator_paragraph.add_run('─' * 55).font.size = Pt(12)
                    run.add_break()

                def add_paragraphs(self, paragraphs):
                    for paragraph in paragraphs:
                        p = self.doc.add_paragraph(paragraph)
                        p.space_before = Pt(0)  # 본문과 구분선 사이에 간격 제거

                def save_document(self):
                    self.doc.save(self.save_path)

                def make_table(self, x, y, content):
                    x = x
                    y = y
                    content = content
                    table = self.doc.add_table(rows=x, cols=y) # 표 생성
                    for row in table.rows:
                        for cell in row.cells:
                            tc = cell._element
                            tc_pr = tc.xpath('./w:tcPr')[0]
                            tc_borders = OxmlElement('w:tcBorders')
                            for border_name in ['top', 'left', 'bottom', 'right']:
                                border = OxmlElement(f'w:border_name')
               
                                border.set(qn('w:val'), 'single')
                                border.set(qn('w:sz'), '4')  # 두께 설정
                                border.set(qn('w:space'), '0')
                                border.set(qn('w:color'), '000000')  # 색상 설정(검정색)
                                tc_borders.append(border)
                            tc_pr.append(tc_borders)
                    data = content.split('|') # 표에 들어갈 내용 '|' 단위로 분할
                    data_list = [data[i:i+y] for i in range(0,len(data),y)]
                    for i in range(x):
                        for j in range(y):
                            table.cell(i,j).text = data_list[i][j]
                    for row in table.rows:
                        for cell in row.cells:
                            cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # 수평 가운데 정렬


            save_path = './기안문.docx'  # 저장할 파일 경로

            # 문서 내용
            slogan = ""
            title = '(주)00'
            sub_title = '수신:서울특별시장 \n참조:사회공헌 포상업무 담당자\n제목:20**년 사회공헌 포상대상자 추천'

            paragraphs1 = [
                '       1. 귀 기관의 무궁한 발전을 기원합니다.',
                '       2. 관련근거 : 서울특별시 공고 제2024-xxx호(2024.07.06)',
                '       3. 위 관련근거에 의거 2024년 우수개발자를 아래와 같이 추천합니다.',
                '           가. 추천대상자 인적사항'
            ]
            paragraphs2 = ['\n첨 부 : 공적조서 1부. 끝']

            # 클래스 인스턴스 생성 및 사용
            report_generator = DocFormatting(save_path)
            report_generator.add_title(title)
            report_generator.add_logos_and_titles(sub_title)
            report_generator.add_separator()  # 제목 아래에 줄 추가
            report_generator.add_paragraphs(paragraphs1)
            report_generator.make_table(2,4,'성명|생년월일|소속|공적개요|김현지|19xx.xx.xx|홍보팀|** 사회봉사 활동을 기획하고 적극적으로 참여')
            report_generator.add_paragraphs(paragraphs2)
            report_generator.bottom('(주)00 대표이사 홍길동',"담당자 : 고성대, 서울특별시 종로구 세종대로 xxx, sh@ddd.co.kr\n문서번호 : 서울2024-xxx\n시행일자 : 2024.07.01")
            report_generator.save_document()
            에 기반하여 문서 내용을 생성된 내용으로 변경하고 제목도 변경하여 파이썬 Document 라이브러리 이용하여 Word 코드 작성해줘,그리고 코드설명은 하지마""",



            "보도자료": """{common_guideline}\n\n{template_text}\n\n작성자: {author}\n받는 사람: {recipient}\n주요 내용: {main_content}\n 이 문서를 위 지침에 맞춰 작성하는데 아래의 코드에 기반하여 내용을 생성해줘 그리고 무조건 제목은 네모 박스내에 작성되게 해줘
            from docx import Document
            from docx.shared import Inches, Pt, Cm
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn

            class DocFormatting:
                def __init__(self, logo1_path, logo2_path, save_path):
                    self.logo1_path = logo1_path
                    self.logo2_path = logo2_path
                    self.save_path = save_path
                    self.doc = Document()

                def add_header(self):
                    table = self.doc.add_table(rows=1, cols=3)
                    row = table.rows[0].cells

                    # Left logo
                    left_logo = row[0].add_paragraph()
                    left_logo.add_run().add_picture(self.logo1_path, width=Inches(1.0))
                    row[0].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

                    # Middle cell
                    middle_cell = row[1].add_paragraph()
                    middle_cell.add_run("보도자료").bold = True
                    middle_cell.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                    # Right logo
                    right_logo = row[2].add_paragraph()
                    right_logo.add_run().add_picture(self.logo2_path, width=Inches(1.0))
                    right_logo.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

                    self.doc.add_paragraph()
                    date_time_table = self.doc.add_table(rows=1, cols=4)
                    date_time_row = date_time_table.rows[0].cells

                    date_time_row[0].paragraphs[0].add_run(f"보도시점   2024.07.01  오후 7시").font.size = Pt(10)
                    date_time_row[1].paragraphs[0].add_run(f"배포    2024.07.01  오후 7시").font.size = Pt(10)
                    for cell in date_time_row:
                        cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                def add_title(self, title, subtitle):
                    # Create a table with one cell for the title box
                    table = self.doc.add_table(rows=1, cols=1)
                    cell = table.cell(0, 0)

                    # Add title to the cell
                    title_paragraph = cell.add_paragraph(title)
                    title_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    run = title_paragraph.runs[0]
                    run.bold = True
                    run.font.size = Pt(14)

                    # Add subtitle to the cell
                    subtitle_paragraph = cell.add_paragraph(subtitle)
                    subtitle_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    subtitle_run = subtitle_paragraph.runs[0]
                    subtitle_run.italic = True
                    subtitle_run.font.size = Pt(12)

                    # Set cell borders
                    tc = cell._element
                    tcPr = tc.get_or_add_tcPr()
                    tcBorders = OxmlElement('w:tcBorders')
                    for border_name in ['top', 'left', 'bottom', 'right']:
                        border = OxmlElement(f'w:border_name')
                        border.set(qn('w:val'), 'single')
                        border.set(qn('w:sz'), '12')
                        border.set(qn('w:space'), '0')
                        border.set(qn('w:color'), '000000')
                        tcBorders.append(border)
                    tcPr.append(tcBorders)

                def add_paragraphs(self, paragraphs):
                    for paragraph in paragraphs:
                        p = self.doc.add_paragraph(paragraph)
                        p.space_before = Pt(0)

                def save_document(self):
                    self.doc.save(self.save_path)

            logo1_path = './logo1.png' 
            logo2_path = './logo2.png'  
            save_path = './보도자료.docx'  

            # Document content
            release_date = "2023. 4. 19. (수)"
            release_time = "17:00"
            distribution_date = "2023. 4. 19. (수)"
            distribution_time = "16:30"
            title = '전세사기 관련 경·공매 유예 방안 구체화'
            subtitle = '- 전세사기 피해 지원 범부처 TF 가동'
            paragraphs = [
                '정부는 전세사기 피해자에 대한 효과적이고 일체적인 지원을 위해 기존 지원 기능을 확대·개편하여 기재부, 국토부, 금융위 등이 폭넓게 참여하는 전세사기 피해지원 범부처 TF를 가동, 오늘 16시 첫 회의를 개최하였다.'
            ]

            # Create and use the class instance
            report_generator = DocFormatting(logo1_path, logo2_path, save_path)
            report_generator.add_header()
            report_generator.add_title(title, subtitle)
            report_generator.add_paragraphs(paragraphs)
            report_generator.save_document()


            에 기반하여 문서 내용을 생성된 내용으로 변경하고 제목도 변경하여 파이썬 Document 라이브러리 이용한 Word 코드 작성해줘,word 코드 작성 시에 def add_title(self, title, subtitle):
        # Create a table with one cell for the title box
        table = self.doc.add_table(rows=1, cols=1)
        cell = table.cell(0, 0)

        # Add title to the cell
        title_paragraph = cell.add_paragraph(title)
        title_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = title_paragraph.runs[0]
        run.bold = True
        run.font.size = Pt(14)

        # Add subtitle to the cell
        subtitle_paragraph = cell.add_paragraph(subtitle)
        subtitle_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        subtitle_run = subtitle_paragraph.runs[0]
        subtitle_run.italic = True
        subtitle_run.font.size = Pt(12)

        # Set cell borders
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        for border_name in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:border_name')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '12')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')
            tcBorders.append(border)
        tcPr.append(tcBorders) 이 부분은 꼭 반영해서 코드 작성해줘, 그리고 코드설명은 하지마""",

            
            "결재문서": """{common_guideline}\n\n{template_text}\n\n작성자: {author}\n받는 사람: {recipient}\n주요 내용: {main_content}\n 이 문서를 위 지침에 맞춰 작성하는데 아래의 코드에 기반하여 내용을 생성해줘 그리고
            from docx import Document
            from docx.shared import Inches, Pt, Cm
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn

            class DocFormatting:
                def __init__(self, logo1_path, logo2_path, save_path):
                    self.logo1_path = logo1_path
                    self.logo2_path = logo2_path
                    self.save_path = save_path
                    self.doc = Document()

                def add_slogan(self, slogan):
                    slogan_paragraph = self.doc.add_paragraph(slogan)
                    slogan_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    run = slogan_paragraph.runs[0]
                    run.font.size = Pt(10)  # 글씨 크기 조정

                def add_logos_and_titles(self, title, sub_title):
                    table = self.doc.add_table(rows=1, cols=3)
                    row = table.rows[0].cells

                    # 왼쪽 로고
                    left_logo = row[0].add_paragraph()
                    left_logo.add_run().add_picture(self.logo1_path, width=Inches(1.0))
                    row[0].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

                    # 제목
                    title_cell = row[1].add_paragraph()
                    run = title_cell.add_run(title)
                    run.bold = True
                    run.font.size = Pt(12)  # 제목 글씨 크기 설정
                    title_cell.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                    # 오른쪽 로고
                    right_logo = row[2].add_paragraph()
                    right_logo.add_run().add_picture(self.logo2_path, width=Inches(1.0))
                    right_logo.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

                    # 부제목
                    subtitle_paragraph = self.doc.add_paragraph(sub_title)
                    subtitle_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    subtitle_run = subtitle_paragraph.runs[0]
                    subtitle_run.bold = True
                    subtitle_run.font.size = Pt(10)  # 부제목 글씨 크기 설정
                    subtitle_paragraph.space_after = Pt(0)  # 부제목과 구분선 사이에 간격 제거

                def add_separator(self):
                    # 긴 줄 추가
                    separator_paragraph = self.doc.add_paragraph()
                    separator_paragraph.space_before = Pt(0)  # 구분선과 부제목 사이에 간격 제거
                    separator_paragraph.space_after = Pt(0)  # 구분선과 본문 사이에 간격 제거
                    run = separator_paragraph.add_run()
                    run.font.size = Pt(1)
                    separator_paragraph.add_run('─' * 36).font.size = Pt(12)
                    run.add_break()

                def add_paragraphs(self, paragraphs):
                    for paragraph in paragraphs:
                        p = self.doc.add_paragraph(paragraph)
                        p.space_before = Pt(0)  # 본문과 구분선 사이에 간격 제거

                def save_document(self):
                    self.doc.save(self.save_path)

            logo1_path = './logo1.png'  # 로고 1 이미지 경로
            logo2_path = './logo2.png'  # 로고 2 이미지 경로
            save_path = './안전사고_조사_결과보고서.docx'  # 저장할 파일 경로

            # 문서 내용
            slogan = "아이 키우기 좋은 도시, '탄생용원 서울 프로젝트'"
            sub_title = '수신   내부결재\n제목   안전사고 조사 결과보고서[2024-06-27]'
            paragraphs = [
                '1. 관련근거',
                '가. 서울특별시 안전사고 조사 및 재발방지에 관한 조례',
                '나. 市 현장대응단-6393(2024.4.11.)호「2024년 안전사고조사 및 재발방지 시행 계획 알림」',
                '2. 안전사고 발생원인을 철저히 조사하여 명확한 원인을 규명하고, 이에 따른 재발 방지를 위한 안전사고 조사 결과보고서를 다음과 같이 보고합니다.',
                '가. 발생일시: ',
                '나. 발생장소: ',
                '다. 사고유형: ',
                '라. 사고개요:',
                '***********************',
                '마. 인명피해: ',
                '바. 재산피해: ',
                '붙임 안전사고조사서 1부. 끝.'
            ]

            # 클래스 인스턴스 생성 및 사용
            report_generator = DocFormatting(logo1_path, logo2_path, save_path)
            report_generator.add_slogan(slogan)
            report_generator.add_logos_and_titles(title, sub_title)
            report_generator.add_separator()  # 제목 아래에 줄 추가
            report_generator.add_paragraphs(paragraphs)
            report_generator.save_document()

            에 기반하여 문서 내용을 생성된 내용으로 변경하고 제목도 변경하여 파이썬 Document 라이브러리 이용하여 Word 코드 작성해줘,그리고 코드설명은 하지마""",

            "공고문": """{common_guideline}\n\n{template_text}\n\n작성자: {author}\n받는 사람: {recipient}\n주요 내용: {main_content}\n 이 문서를 위 지침에 맞춰 작성하는데 아래의 코드에 기반하여 내용을 생성해줘 그리고
            from docx import Document
            from docx.shared import Inches, Pt, Cm
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn


            class DocFormatting:
                def __init__(self, save_path):
                    self.save_path = save_path
                    self.doc = Document()

                def add_slogan(self, slogan, position):
                    position = position
                    slogan_paragraph = self.doc.add_paragraph(slogan)
                    if position == 'left':
                        slogan_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    elif position == 'center':
                        slogan_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    elif position == 'right':
                        slogan_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    run = slogan_paragraph.runs[0]
                    run.font.size = Pt(10)  

                def add_logos_and_titles(self, title, sub_title):
                    table = self.doc.add_table(rows=2, cols=1)
                    row = table.rows[0].cells

                    # 제목
                    title_cell = row[0].add_paragraph()
                    run = title_cell.add_run(title)
                    run.bold = True
                    run.font.size = Pt(12) 
                    title_cell.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                    # 부제목
                    subtitle_paragraph = self.doc.add_paragraph(sub_title)
                    subtitle_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    subtitle_run = subtitle_paragraph.runs[0]
                    subtitle_run.bold = True
                    subtitle_run.font.size = Pt(10) 
                    subtitle_paragraph.space_after = Pt(0)

                def add_logos(self, path, position):
                    path = path # 이미지 경로
                    position = position # 로고 위치
                    paragraph = self.doc.add_paragraph()
                    run = paragraph.add_run()
                    run.add_picture(path)
                    if position == 'left':
                        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    elif position == 'center':
                        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    elif position == 'right':
                        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

                def add_separator(self):
                    # 긴 줄 추가
                    separator_paragraph = self.doc.add_paragraph()
                    separator_paragraph.space_before = Pt(0)  # 구분선과 부제목 사이에 간격 제거
                    separator_paragraph.space_after = Pt(0)  # 구분선과 본문 사이에 간격 제거
                    run = separator_paragraph.add_run()
                    run.font.size = Pt(1)
                    separator_paragraph.add_run('─' * 55).font.size = Pt(12)
                    run.add_break()

                def add_paragraphs(self, paragraphs):
                    for paragraph in paragraphs:
                        p = self.doc.add_paragraph(paragraph)
                        p.space_before = Pt(0)  # 본문과 구분선 사이에 간격 제거

                def save_document(self):
                    self.doc.save(self.save_path)

                def make_table(self, x, y, content):
                    x = x
                    y = y
                    content = content

                    table = self.doc.add_table(rows=x, cols=y) # 표 생성
                    for row in table.rows:
                        for cell in row.cells:
                            tc = cell._element
                            tc_pr = tc.xpath('./w:tcPr')[0]
                            tc_borders = OxmlElement('w:tcBorders')
                            for border_name in ['top', 'left', 'bottom', 'right']:
                                border = OxmlElement(f'w:border_name')
                                border.set(qn('w:val'), 'single')
                                border.set(qn('w:sz'), '4')  # 두께 설정
                                border.set(qn('w:space'), '0')
                                border.set(qn('w:color'), '000000')  # 색상 설정(검정색)
                                tc_borders.append(border)
                            tc_pr.append(tc_borders)
                    data = content.split('|') # 표에 들어갈 내용 '|' 단위로 분할
                    data_list = [data[i:i+y] for i in range(0,len(data),y)]
                    for i in range(x):
                        for j in range(y):
                            table.cell(i,j).text = data_list[i][j]
                    for row in table.rows:
                        for cell in row.cells:
                            cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # 수평 가운데 정렬


            logo1_path = './logo1.png'  # 로고 1 이미지 경로
            logo2_path = './logo2.png'
            save_path = './공고문.docx'  # 저장할 파일 경로

            # 문서 내용
            slogan = "(재)인천인재평생교육진흥원 공고 제2022-031호"
            title = '''2022년도 애터미 거주비 지원 장학생 선발 공고'''
            sub_title = '''2022년도 재단법인 인천인재평생교육진흥원 애터미 거주비 지원 장학생 선발을 아래와 같이 공고하오니 많은 참여 바랍니다.\n\n2022년 3월 23일''' 

            paragraphs1 = [
                '''1. 장학생 선발인원 및 지급예정액.'''
            ]
            paragraphs2 = ['''2. 장학생 신청방법''',
                        '''    - 신청기간 : 2024.xx.xx(수) ~ 2024.xx.xx(금) 18:00까지''',
                        '''    - 신청방법 : 인천인재평생교육진흥원 장학금 신청페이지(www.prompt.com/scholarship)에 \n        구비서류 온라인을 통해 제출''',
                        '''    - 장학금 지급 과정''']
            paragraphs3 = ['''자세한 내용은 위 홈페이지를 통해 확인.\n''']

            # 클래스 인스턴스 생성 및 사용
            report_generator = DocFormatting(save_path)
            report_generator.add_slogan(slogan, 'left')
            report_generator.add_logos_and_titles(title, sub_title)
            report_generator.add_paragraphs(paragraphs1)
            report_generator.make_table(3,4,'''선발대상|선발인원|지급금액(1인당)|지급예정액|대 학 생|10명|100만원|100,000원|계|10명|-|100,000원''')
            report_generator.add_paragraphs(paragraphs2)
            report_generator.make_table(2,6,'''-|접수|서류심사|선발심사|결과발표|장학급 지급|기간|xx.xx(수)~xx.xx\n(금) 18:00|xx.xx(월)\n~xx.xx(금)|xx.xx(월)\n~xx.xx(수)|xx.xx(목)|xx.xx(수)''')
            report_generator.add_paragraphs(paragraphs3)
            report_generator.add_logos(logo2_path,'center')
            report_generator.save_document()
            에 기반하여 문서 내용을 생성된 내용으로 변경하고 제목도 변경하여 파이썬 Document 라이브러리 이용하여 Word 코드 작성해줘,그리고 코드설명은 하지마"""
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

