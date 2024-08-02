// script.js
function sendMessage() {
    var inputBox = document.getElementById('user-input');
    var chatBox = document.getElementById('chat-box');
    var userInput = inputBox.value.trim();

    if (userInput === '') {
        return;
    }

    // 사용자 응답
    var userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    // 챗봇 응답
    var botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';
    botMessage.textContent = userInput === '안녕' ? '안녕하세요! 무엇을 도와드릴까요?' : '죄송합니다, 이해하지 못했습니다.';
    chatBox.appendChild(botMessage);

    // 입력 부분 초기화
    inputBox.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 처음 챗봇 화면 로드시 초기 메시지
document.addEventListener('DOMContentLoaded', function() {
    var chatBox = document.getElementById('chat-box');

    var botMessage = document.createElement('div');
    botMessage.className = 'message bot-message';
    botMessage.textContent = '안녕하세요! 저는 문서 작성을 도와주는 FICL 말하는대로 챗봇입니다.무엇을 도와드릴까요?';
    chatBox.appendChild(botMessage);
});
