import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from google.oauth2 import service_account

PROJECT_ID = ""#GCP 프로젝트 ID 작성하면됨
LOCATION = "us-central1"
MODEL_ID = "gemini-1.5-flash-001"

SERVICE_ACCOUNT_FILE = ''#API Key json 파일 경로  
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

class EmailGenerator:
    def __init__(self, project, location):
        self.project = project
        self.location = location
        self.model = self.initialize_vertex_ai()
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

        self.templates = {
            "문의": {
                "subject": "Re: 문의 사항",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 부분에 대해 문의드립니다. 확인 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "오류수정": {
                "subject": """Re: 오류 수정 요청""",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 부분에 오류가 있어 수정 요청드립니다. 확인 후 수정 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "승인요청": {
                "subject": "Re: 승인 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 부분에 대해 승인 요청드립니다. 확인 후 승인 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "자료요청": {
                "subject": "Re: 자료 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 관련 자료를 요청드립니다. 확인 후 자료 제공 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "협조요청": {
                "subject": "Re: 협조 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 부분에 대해 협조를 요청드립니다. 확인 후 협조 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "회의일정조정": {
                "subject": "Re: 회의 일정 조정",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 관련하여 회의 일정을 조정하고자 합니다. 가능한 시간대 확인 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "제출확인요청": {
                "subject": "Re: 제출 확인 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 보고서를 제출합니다. 검토 후 피드백 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "제출요청": {
                "subject": "Re: 제출 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 서류를 제출해 주시기 바랍니다. {deadline}까지 제출해 주세요.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "피드백요청": {
                "subject": "Re: 피드백 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 부분에 대한 피드백을 요청드립니다. 검토 후 의견 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "공문발송": {
                "subject": "Re: 공문 발송",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 공문을 발송드립니다. 확인 후 회신 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            },
            "교육참가요청": {
                "subject": "Re: 교육/훈련 참가 요청",
                "body": """{recipient_name}님, 안녕하세요. {department} {user_name}입니다.
                {details} 교육/훈련에 참가를 요청드립니다. 확인 후 참가 부탁드립니다.
                감사합니다. 수고하십시오.
                [부서]: {department}
                {user_name} 드림"""
            }
        }

    def initialize_vertex_ai(self):
        vertexai.init(project=self.project, location=self.location, credentials=credentials)
        return GenerativeModel(MODEL_ID)

    def infer_email_type(self, user_input):
        if any(keyword in user_input for keyword in ["문의", "질문", "문의드립니다"]):
            return "문의"
        elif any(keyword in user_input for keyword in ["오류", "수정", "잘못", "문제"]):
            return "오류수정"
        elif any(keyword in user_input for keyword in ["승인", "허가", "승인 부탁"]):
            return "승인요청"
        elif any(keyword in user_input for keyword in ["자료", "정보", "데이터", "요청드립니다"]):
            return "자료요청"
        elif any(keyword in user_input for keyword in ["협조", "협력", "도움", "요청드립니다"]):
            return "협조요청"
        elif any(keyword in user_input for keyword in ["회의", "일정", "조정", "미팅"]):
            return "회의일정조정"
        elif any(keyword in user_input for keyword in ["제출확인"]):
            return "제출확인요청"
        elif any(keyword in user_input for keyword in ["까지","보내"]):
            return "제출요청"
        elif any(keyword in user_input for keyword in ["피드백", "의견", "검토"]):
            return "피드백요청"
        elif any(keyword in user_input for keyword in ["공문", "발송", "문서"]):
            return "공문발송"
        elif any(keyword in user_input for keyword in ["교육", "훈련", "참가", "신청"]):
            return "교육참가요청"
        else:
            return "문의"

    def generate_email(self, user_input, user_name, department, recipient_name):
        email_type = self.infer_email_type(user_input)

        if "까지" in user_input:
            deadline = user_input.split("까지")[0].strip()
        else:
            deadline = "기한 없음"

        details = user_input

        if email_type in self.templates:
            subject_template = self.templates[email_type]["subject"]
            body_template = self.templates[email_type]["body"]
        else:
            raise ValueError("지원되지 않는 이메일 유형입니다.")

        subject = subject_template
        body_prompt = body_template.format(details=details, recipient_name=recipient_name, department=department, user_name=user_name, deadline=deadline)

        responses = self.model.generate_content(
            [body_prompt],
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
            stream=True,
        )

        body = ""
        for response in responses:
            body += response.text

        body_lines = body.split("\n")
        body_lines = [line for line in body_lines if not line.startswith("## 제목: ")]
        body = "\n".join(body_lines)

        if f"{user_name} 드림" not in body:
            body += f"\n\n{user_name} 드림"

        return subject, body.strip()

