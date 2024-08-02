var chatBox = document.getElementById('chat-box');
var inputBox = document.getElementById('user-input');

var graph_Info = {
    graph_type: '',
    content: '',
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
    graph_Info.graph_type = userInput;
    chatBox.appendChild(userMessage);
    console.log(currentStep);
    inputBox.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    var botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';

    if (currentStep === 0) {
        
        botMessage.textContent = '그래프로 시각화 할 데이터의 내용을 입력하세요';
        graph_Info.content = userInput;
        console.log(currentStep);
        currentStep++;
    } else if (currentStep === 1){

        graph_Info.content = userInput;

        var generatingMessage = document.createElement('div');
        generatingMessage.className = 'message bot-message';
        generatingMessage.style.color = 'blue';
        generatingMessage.textContent = '생성 중...';
        chatBox.appendChild(generatingMessage);
        chatBox.scrollTop = chatBox.scrollHeight;

        generate_bogoseo(graph_Info).then(result => {
            chatBox.removeChild(generatingMessage);
            if (result.error) {
                botMessage.textContent = '그래프 생성 중 오류가 발생했습니다.';
            } else {
                botMessage.innerHTML = `<a href="/download-graph/${result.graph_path}" download>그래프 다운로드</a>`;
            }
            chatBox.appendChild(botMessage);
            currentStep = 0; 
        }).catch(error => {
            chatBox.removeChild(generatingMessage);
            botMessage.textContent = '그래프 생성 중 오류가 발생했습니다.';
            chatBox.appendChild(botMessage);
            console.error(error);
            currentStep = 0; 
        });
    }
        


    chatBox.appendChild(botMessage);
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.addEventListener('DOMContentLoaded', function() {
    var botMessage1 = document.createElement('div');
    botMessage1.className = 'message bot-message';
    botMessage1.textContent = '안녕하세요, 이미지 및 그래프를 생성해주는 챗봇입니다. 저와 대화를 통해 손쉽게 이미지 혹은 그래프를 그려봐요~';
    chatBox.appendChild(botMessage1);

    var botMessage2 = document.createElement('div');
    botMessage2.className = 'message bot-message';
    botMessage2.textContent = '시각화 하고 싶은 그래프 종류를 입력하세요(원형, 막대, 꺽은선 그래프)';
    chatBox.appendChild(botMessage2);
});

inputBox.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

async function generate_bogoseo(graph_Info) {
    const response = await fetch('/generate-graph', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(graph_Info)
    });

    if (!response.ok) {
        throw new Error('Network response was not ok');
    }

    const result = await response.json();
    return result;  
}
