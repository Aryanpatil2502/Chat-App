const socket = io();

function showStatus(elementId, text, isError) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = text;
    el.className = "lobby-status " + (isError ? "status-error" : "status-ok");
}


function createRoom() {
    const nameInput = document.getElementById("room-name-input");
    const name = nameInput.value.trim() || "Untitled Room";

    socket.emit("create_room", name, function (response) {
        if (response && response.success) {
            window.location.href = "/room/" + response.room_code;
        } else {
            showStatus(
                "room-code-display",
                (response && response.error) || "Could not create room",
                true
            );
        }
    });
}



function joinRoom() {
    const code = document
        .getElementById("room-code-input")
        .value.trim()
        .toUpperCase();

    if (code === "") {
        showStatus("error-message", "Enter a room code", true);
        return;
    }

    socket.emit("join_room", code, function (response) {
        if (response && response.success) {
            window.location.href = "/room/" + response.room_code;
        } else if (response && response.pending) {
            showStatus("error-message", response.message, false);
        } else {
            showStatus(
                "error-message",
                (response && response.error) || "Could not join room",
                true
            );
        }
    });
}



socket.on("join_accepted", function (data) {
    window.location.href = "/room/" + data.room_code;
});

socket.on("join_rejected", function (data) {
    showStatus(
        "error-message",
        "Your request to join " + data.room_code + " was rejected.",
        true
    );
});



socket.on("join_request", function (data) {
    const panel = document.getElementById("requests-panel");
    const list = document.getElementById("requests-list");
    if (!panel || !list) return;

    if (list.querySelector('[data-request-id="' + data.request_id + '"]')) {
        return;
    }

    panel.style.display = "block";

    const li = document.createElement("li");
    li.dataset.requestId = data.request_id;

    const label = document.createElement("span");
    label.textContent = data.username + " wants to join " + data.room_code;
    li.appendChild(label);

    const accept = document.createElement("button");
    accept.className = "accept-button";
    accept.textContent = "Accept";
    accept.onclick = function () {
        respondToRequest(data.request_id, "accept", li);
    };
    li.appendChild(accept);

    const reject = document.createElement("button");
    reject.className = "reject-button";
    reject.textContent = "Reject";
    reject.onclick = function () {
        respondToRequest(data.request_id, "reject", li);
    };
    li.appendChild(reject);

    list.appendChild(li);
});


function respondToRequest(requestId, action, li) {
    socket.emit(
        "handle_join_request",
        { request_id: requestId, action: action },
        function (response) {
            if (response && response.success) {
                li.remove();
                const list = document.getElementById("requests-list");
                if (list && list.children.length === 0) {
                    document.getElementById("requests-panel").style.display = "none";
                }
            } else {
                alert((response && response.error) || "Could not handle request");
            }
        }
    );
}


document
    .getElementById("room-code-input")
    .addEventListener("keydown", function (event) {
        if (event.key === "Enter") joinRoom();
    });

document
    .getElementById("room-name-input")
    .addEventListener("keydown", function (event) {
        if (event.key === "Enter") createRoom();
    });
