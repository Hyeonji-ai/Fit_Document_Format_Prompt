var chatBox = document.getElementById('chat-box');
var inputBox = document.getElementById('user-input');

var emailInfo = {
    from: '',
    to: '',
    content: '',
    department: ''
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

    inputBox.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    var botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';

    if (currentStep === 0) {
        emailInfo.content = userInput;
        botMessage.textContent = '당신의 부서를 입력해주세요';
        currentStep++;
    } else if (currentStep === 1) {
        emailInfo.department = userInput;
        botMessage.textContent = '당신의 이름을 입력해주세요';
        currentStep++;
    } else if (currentStep === 2) {
        emailInfo.to = userInput;
        botMessage.textContent = '받는 분 부서와 이름을 입력해주세요.';
        currentStep++;
    } else if (currentStep === 3) {
        emailInfo.from = userInput;
        botMessage.textContent = '이메일을 생성 중입니다. 잠시만 기다려주세요...';
        chatBox.appendChild(botMessage);

        generateEmail(emailInfo).then(result => {
            if (result.error) {
                botMessage.textContent = '이메일 생성 중 오류가 발생했습니다.';
            } else {
                botMessage.innerHTML = `<h3>제목: ${result.subject}</h3><pre>${result.body}</pre>`;
            }
            chatBox.appendChild(botMessage);
            currentStep = 0; 
        }).catch(error => {
            botMessage.textContent = '이메일 생성 중 오류가 발생했습니다.';
            chatBox.appendChild(botMessage);
            console.error(error);
            currentStep = 0; 
        });
    }

    chatBox.appendChild(botMessage);
}

document.addEventListener('DOMContentLoaded', function() {
    var botMessage1 = document.createElement('div');
    botMessage1.className = 'message bot-message';
    botMessage1.textContent = '안녕하세요! 저는 이메일 문구 작성을 도와주는 FICL 말하는대로 챗봇입니다. 이메일 작성을 도와드릴게요!';
    chatBox.appendChild(botMessage1);

    var botMessage2 = document.createElement('div');
    botMessage2.className = 'message bot-message';
    botMessage2.textContent = '어떤 내용을 보내실건가요?';
    chatBox.appendChild(botMessage2);
});

inputBox.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

async function generateEmail(emailInfo) {
    const response = await fetch('/generate-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(emailInfo)
    });

    if (!response.ok) {
        throw new Error('Network response was not ok');
    }

    const result = await response.json();
    return result;
}
