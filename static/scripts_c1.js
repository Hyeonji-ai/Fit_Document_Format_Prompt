var chatBox = document.getElementById('chat-box');
var inputBox = document.getElementById('user-input');

var bogoseoInfo = {
    doctype: '',
    res: '',
    userName: '',
    content: ''
};
var currentStep = 0;

function sendMessage() {
    var userInput = inputBox.value.trim();

    if (userInput === '') {
        return;
    }

    var userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);
    console.log(currentStep);
    inputBox.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    var botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';

    if (currentStep === 0) {
        bogoseoInfo.doctype = userInput;
        botMessage.textContent = '작성자 소속과 이름을 알려주세요';
        console.log(currentStep);
        currentStep++;
    } else if (currentStep === 1) {
        bogoseoInfo.userName = userInput;
        botMessage.textContent = '서류 받는 사람의 소속과 이름을 알려주세요';
        console.log(currentStep);
        currentStep++;
    } else if (currentStep === 2) {
        bogoseoInfo.res = userInput;
        botMessage.textContent = '서류에 들어갈 내용을 알려주세요.';
        console.log(currentStep);
        currentStep++;
    } else if (currentStep === 3) {
        bogoseoInfo.content = userInput;
        chatBox.appendChild(botMessage);
        console.log(currentStep);
        currentStep++;

        var loadingMessage = document.createElement('div');
        loadingMessage.className = 'message bot-message';
        loadingMessage.style.color = 'blue';
        loadingMessage.textContent = '생성 중...';
        chatBox.appendChild(loadingMessage);
        chatBox.scrollTop = chatBox.scrollHeight;

        generate_bogoseo(bogoseoInfo).then(result => {
            chatBox.removeChild(loadingMessage);
            var resultMessage = document.createElement('div');
            resultMessage.className = 'message bot-message';
            if (result.error) {
                resultMessage.textContent = '문서 생성 중 오류가 발생했습니다.';
            } else {
                resultMessage.innerHTML = `<pre>${result.bogoseo_content}</pre><a href="${result.download_link}" download>보고서 다운로드</a>`;
            }
            chatBox.appendChild(resultMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
            currentStep = 0;
        }).catch(error => {
            chatBox.removeChild(loadingMessage);
            var errorMessage = document.createElement('div');
            errorMessage.className = 'message bot-message';
            errorMessage.textContent = '문서 생성 중 오류가 발생했습니다.';
            chatBox.appendChild(errorMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
            console.error(error);
            currentStep = 0;
        });
    }

    chatBox.appendChild(botMessage);
}

document.addEventListener('DOMContentLoaded', function() {
    var botMessage1 = document.createElement('div');
    botMessage1.className = 'message bot-message';
    botMessage1.textContent = '안녕하세요, 문서 생성을 도와드리는 챗봇입니다. 저와 대화를 통해 손쉽게 작성해봐요~ 먼저 위에 포맷을 맞춰야하는 파일을 업로드 해주세요';
    chatBox.appendChild(botMessage1);

    var botMessage2 = document.createElement('div');
    botMessage2.className = 'message bot-message';
    botMessage2.textContent = '어떤 보고서를 작성할 생각이신가요?(보도자료, 기안문, 공고문, 결재문서)';
    chatBox.appendChild(botMessage2);
});

inputBox.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

async function generate_bogoseo(bogoseoInfo) {
    const response = await fetch('/generate-bogoseo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bogoseoInfo)
    });

    if (!response.ok) {
        throw new Error('Network response was not ok');
    }

    const result = await response.json();
    return result;
}

document.getElementById('fileInput').addEventListener('change', function() {
    var fileName = this.files[0].name;
    var nextSibling = this.nextElementSibling;
    nextSibling.innerText = fileName;
});