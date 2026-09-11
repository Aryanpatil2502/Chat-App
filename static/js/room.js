const socket = io();

socket.emit('join_room_event', { code: roomCode });

socket.on('join_error', function(data) {
    alert(data.error);
    window.location.href = "/";
});

socket.on('user_joined', function(data) {
    appendSystemMessage(data.username + " joined the room");
});

socket.on('new_message', function(data) {
    appendMessage(data.username, data.message);
});


function appendMessage(username, message) {
    const chatBox = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.classList.add("message");
    div.innerHTML = "<strong>" + username + ":</strong> " + message;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}


function appendSystemMessage(text) {
    const chatBox = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.classList.add("system-message");
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}


function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();

    if (message === "") {
        return;
    }

    socket.emit('send_message', {
        room: roomCode,
        message: message
    });

    input.value = "";
}


document.getElementById("message-input").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});