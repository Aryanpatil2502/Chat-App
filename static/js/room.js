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

socket.on('chat_history', function(data) {
    data.messages.forEach(function(m) {
        appendMessage(m.username, m.message);
    });
});

socket.on('room_deleted', function(data) {
    alert("This room was deleted.");
    window.location.href = "/";
});

socket.on('delete_error', function(data) {
    alert(data.error);
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


function deleteRoom() {
    if (!confirm("Delete this room for everyone? This cannot be undone.")) {
        return;
    }
    socket.emit('delete_room_event', { code: roomCode });
}


document.getElementById("message-input").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});