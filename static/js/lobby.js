const socket = io();

socket.on('room_created', function(data) {
    window.location.href = "/room/" + data.code;
});


function createRoom() {
    socket.emit('create_room', {});
}


function joinRoom() {
    const code = document.getElementById("room-code-input").value.trim().toUpperCase();

    if (code === "") {
        return;
    }

    window.location.href = "/room/" + code;
}