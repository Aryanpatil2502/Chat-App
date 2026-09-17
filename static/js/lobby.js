const socket = io();

socket.on('room_created', function(data) {
    window.location.href = "/room/" + data.code;
});


function createRoom() {
    const nameInput = document.getElementById("room-name-input");
    const name = nameInput.value.trim() || "Untitled Room";
    socket.emit('create_room', { name: name });
}

function joinRoom() {
    const code = document.getElementById("room-code-input").value.trim().toUpperCase();

    if (code === "") {
        return;
    }

    window.location.href = "/room/" + code;
}