from flask import Flask, render_template, request, jsonify, send_file
import re
from docx import Document
import io
import os
from datetime import datetime
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


from Algorithm import bogoseo_generator, email_generator, graph_generate
app = Flask(__name__)

PROJECT_ID = ''#GCP 프로젝트 ID 작성하면됨  
LOCATION = 'us-central1'      
BOGOSEO_LOCATION = "asia-northeast3"
MODEL_ID = "gemini-1.5-flash-001"
data_path = "gs://ficl_public_document/public_doc.pdf"#구글 클라우드 연동

email_module = email_generator.EmailGenerator(PROJECT_ID, LOCATION)
bogoseo = bogoseo_generator.MakingDoc(PROJECT_ID, BOGOSEO_LOCATION, MODEL_ID)
extract_guidline = bogoseo_generator.DocumentProcessor(data_path, MODEL_ID)
generate_graph_module = graph_generate.Graph(PROJECT_ID, LOCATION)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/generate.html')
def index1():
    return render_template('generate.html')

@app.route('/generate-bogoseo', methods=['POST'])
def generate_bogoseo():
    data = request.json
    doctype = data.get('doctype')
    userName = data.get('userName')
    res = data.get('res')
    content = data.get('content')

    if not all([doctype, userName, res, content]):
        return jsonify({"error": "Invalid input data"}), 400

    input_data = f"{doctype}#{userName}#{res}#{content}"
    user_guideline = extract_guidline.modify_doc(doctype)

    try:
        bogoseo_content = bogoseo.generate_document(input_data, user_guideline)
        print(f"Input doctype: {doctype}")
        print(f"Input userName: {userName}")
        print(f"User res: {res}")
        print(f"User content: {content}")
        print(f"User input_data: {input_data}")

        # 파이썬 코드 추출
        code_block = re.search(r'```python(.*?)```', bogoseo_content, re.DOTALL)
        if code_block:
            test= bogoseo_content.strip('\n').strip('```').strip('python').replace('\t','')
            local_namespace = {}
            exec(test, globals(), local_namespace)
            
            # in-memory buffer 생성
            file_buffer = io.BytesIO()
            document = local_namespace['report_generator']
            document.doc.save(file_buffer)
            file_buffer.seek(0)

            # 버퍼를 전역변수에 저장
            app.file_buffer = file_buffer
        
        # 동적 파일을 로컬에 저장
        app.filename = f"{doctype}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"

        # 다운로드 링크 출력
        return jsonify({"bogoseo_content": "문서 생성이 완료되었습니다", "download_link": "/download-report"})
    except Exception as e:
        error_message = str(e)
        print(f"Input doctype: {doctype}")
        print(f"Input userName: {userName}")
        print(f"User res: {res}")
        print(f"User content: {content}")
        print(f"User input_data: {input_data}")
        print(f"User guideline: {user_guideline}")
        print(f"Error: {error_message}")  # 로그에 에러 메시지 출력
        return jsonify({"error": error_message}), 500

@app.route('/download-report')
def download_report():
    # file_buffer 설정 확인
    if hasattr(app, 'file_buffer') and app.file_buffer:
        app.file_buffer.seek(0)
        return send_file(app.file_buffer, as_attachment=True, download_name=app.filename)
    else:
        return "No report available", 404

@app.route('/intergrate.html')
def index3():
    return render_template('intergrate.html')

@app.route('/generate-graph', methods=['POST'])
def generate_graph():
    data = request.json
    graph_type = data['graph_type']
    report = data['content']

    try:
        png_title = generate_graph_module.make_graph(graph_type, report)
        print(f"Input graph_type: {graph_type}")
        print(f"Input report: {report}")
        return jsonify({"graph_path": png_title})
    except Exception as e:
        error_message = str(e)
        print(f"Input doctype: {graph_type}")
        print(f"Error: {error_message}")  
        return jsonify({"error": error_message}), 500

@app.route('/download-graph/<filename>')
def download_graph(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return "File not found", 404


@app.route('/email.html')
def index4():
    return render_template('email.html')

@app.route('/generate-email', methods=['POST'])
def generate_email():
    data = request.json
    user_input = data['content']
    user_name = data['from']
    department = data['department']
    recipient_name = data['to']

    print(f"Input doctype: {user_input}")
    print(f"Input user_name: {user_name}")
    print(f"Input department: {department}")
    print(f"Input recipient_name: {recipient_name}")

    try:
        subject, body = email_module.generate_email(user_input, recipient_name, department, user_name)
        print(f"Input doctype: {user_input}")
        print(f"Input doctype: {user_name}")
        print(f"Input doctype: {department}")
        print(f"Input doctype: {recipient_name}")
        
        return jsonify({"subject": subject, "body": body})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
