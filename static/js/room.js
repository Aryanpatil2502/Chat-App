const socket = io();


socket.emit("join_room", roomCode, function (response) {
    if (!response || (!response.success && !response.pending)) {
        alert((response && response.error) || "Could not join this room");
        window.location.href = "/";
    }
});




socket.on("receive_message", function (data) {
    appendMessage(data.username, data.message);
});

socket.on("room_members", function (data) {
    renderMembers(data.members);
});

socket.on("room_deleted", function () {
    alert("This room was deleted.");
    window.location.href = "/";
});

socket.on("kicked", function (data) {
    if (data.room_code === roomCode) {
        alert("You were removed from this room.");
        window.location.href = "/";
    }
});

socket.on("join_request", function (data) {
    if (data.room_code !== roomCode) return;
    addRequestRow(data.request_id, data.username);
});



function appendMessage(username, message) {
    const chatBox = document.getElementById("chat-box");

    const div = document.createElement("div");
    div.classList.add("message");

    const name = document.createElement("strong");
    name.textContent = username + ": ";
    div.appendChild(name);
    div.appendChild(document.createTextNode(message));

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


function renderMembers(members) {
    const list = document.getElementById("members-list");
    if (!list) return;

    list.innerHTML = "";

    members.forEach(function (member) {
        const li = document.createElement("li");
        li.dataset.userId = member.id;

        const name = document.createElement("span");
        name.textContent = member.username;
        li.appendChild(name);

        if (isCreator && member.id !== creatorId) {
            const btn = document.createElement("button");
            btn.className = "kick-button";
            btn.textContent = "Kick";
            btn.onclick = function () {
                kickMember(member.id);
            };
            li.appendChild(btn);
        }

        list.appendChild(li);
    });
}


function addRequestRow(requestId, username) {
    const list = document.getElementById("requests-list");
    if (!list) return;

    if (list.querySelector('[data-request-id="' + requestId + '"]')) return;

    const empty = document.getElementById("requests-empty");
    if (empty) empty.style.display = "none";

    const li = document.createElement("li");
    li.dataset.requestId = requestId;

    const name = document.createElement("span");
    name.textContent = username;
    li.appendChild(name);

    const accept = document.createElement("button");
    accept.className = "accept-button";
    accept.textContent = "Accept";
    accept.onclick = function () {
        handleRequest(requestId, "accept");
    };
    li.appendChild(accept);

    const reject = document.createElement("button");
    reject.className = "reject-button";
    reject.textContent = "Reject";
    reject.onclick = function () {
        handleRequest(requestId, "reject");
    };
    li.appendChild(reject);

    list.appendChild(li);
}



function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();

    if (message === "") return;

    socket.emit(
        "send_message",
        { room_code: roomCode, message: message },
        function (response) {
            if (!response || !response.success) {
                appendSystemMessage(
                    (response && response.error) || "Message failed to send"
                );
            }
        }
    );

    input.value = "";
}


function leaveRoom() {
    socket.emit("leave_room", roomCode, function (response) {
        if (response && response.success) {
            window.location.href = "/";
        } else {
            alert((response && response.error) || "Could not leave room");
        }
    });
}


function deleteRoom() {
    if (!confirm("Delete this room for everyone? This cannot be undone.")) {
        return;
    }

    socket.emit("delete_room", roomCode, function (response) {
        if (!response || !response.success) {
            alert((response && response.error) || "Could not delete room");
        }
    });
}


function kickMember(userId) {
    if (!confirm("Remove this member from the room?")) return;

    socket.emit(
        "kick_member",
        { room_code: roomCode, user_id: userId },
        function (response) {
            if (!response || !response.success) {
                alert((response && response.error) || "Could not kick member");
            }
        }
    );
}


function handleRequest(requestId, action) {
    socket.emit(
        "handle_join_request",
        { request_id: requestId, action: action },
        function (response) {
            if (response && response.success) {
                const row = document.querySelector(
                    '#requests-list [data-request-id="' + requestId + '"]'
                );
                if (row) row.remove();

                const list = document.getElementById("requests-list");
                const empty = document.getElementById("requests-empty");
                if (list && empty && list.children.length === 0) {
                    empty.style.display = "block";
                }
            } else {
                alert((response && response.error) || "Could not handle request");
            }
        }
    );
}



document
    .getElementById("message-input")
    .addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

const chatBoxEl = document.getElementById("chat-box");
chatBoxEl.scrollTop = chatBoxEl.scrollHeight;