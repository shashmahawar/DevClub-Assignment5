function checkFill() {
    var username = localStorage.getItem("username");
    var field = document.getElementById("username");
    var remember = document.querySelector("#remember");
    if (username) {
        field.value = username;
        remember.checked = true;
    }
}

function checkSave() {
    var remember = document.querySelector("#remember");
    if (remember.checked) {
        var username = document.getElementById("username");
        localStorage.setItem("username", username.value);
    } else {
        localStorage.removeItem("username");
    }
}

window.onload = checkFill;