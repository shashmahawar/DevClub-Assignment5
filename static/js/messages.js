function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

var csrftoken = readCookie('csrftoken');

function scrollDown() {
    localStorage.setItem("my_user_id", document.getElementById("my_user_id").innerText)
    var doc = document.getElementById("messages");
    doc.scrollTop = doc.scrollHeight;
}
window.onload = scrollDown();

function send_message() {
    var username = window.location.href.split('/')[4];
    var message = document.getElementById("message_input").value;
    if (!message.replace(/\s/g, '').length) {
        return false;
    }
    var data = {'username': username, 'message': message};
    var body = JSON.stringify(data);
    var options = {
        method: 'POST',
        body: body,
        headers: { 'content-type': 'application/json', 'X-CSRFToken': csrftoken },
        redirect: "follow"
    }
    fetch("/api/send_message/", options).then(response => {
        response.json().then(response => {
            if (response.status == 200) {
                document.getElementById("message_input").value = "";
                if (response.message.length > 15) {
                    document.getElementById("curr_user_bar").innerText = `${response.message.slice(0,14)}...`;
                } else {
                    document.getElementById("curr_user_bar").innerText = `${response.message}`;
                }
                var date = new Date(response.date_time);
                document.getElementById("messages").innerHTML += `<div class="sent_message">
                <div class="sent_message_inner">
                <p class="message">${response.message}</p>
                <p class="time_stamp">${date.getDate()}/${date.getMonth()+1}, ${date.getHours()}:${date.getMinutes()}</p>
                </div>
                </div>`
                var doc = document.getElementById("messages");
                doc.scrollTop = doc.scrollHeight;
            }
        })
    });
}

function get_messages() {
    var username = window.location.href.split('/')[4];
    var data = {'username': username};
    var body = JSON.stringify(data);
    var options = {
        method: 'POST',
        body: body,
        headers: { 'content-type': 'application/json', 'X-CSRFToken': csrftoken },
        redirect: "follow"
    }
    fetch("/api/get_messages/", options).then(response => {
        response.json().then(response => {
            if (response.status == 200) {
                var msgbox = document.getElementById("messages");
                msgbox.innerHTML = "";
                for (var items in response.chat) {
                    var chat_item = response.chat[items];
                    if (chat_item.message_from_id == localStorage.getItem("my_user_id")) {
                        var date = new Date(chat_item.date_time);
                        msgbox.innerHTML += (`<div class="sent_message">
                            <div class="sent_message_inner">
                                <p class="message">${chat_item.message}</p>
                                <p class="time_stamp">${date.getDate()}/${date.getMonth()+1}, ${date.getHours()}:${date.getMinutes()}</p>
                            </div>
                        </div>`)
                    } else {
                        var date = new Date(chat_item.date_time);
                        msgbox.innerHTML += (`<div class="received_message">    
                            <div class="received_message_inner">
                                <p class="message">${chat_item.message}</p>
                                <p class="time_stamp">${date.getDate()}/${date.getMonth()+1}, ${date.getHours()}:${date.getMinutes()}</p>
                            </div>
                        </div>`)
                    }
                }
                if (chat_item.message.length > 15) {
                    document.getElementById("curr_user_bar").innerText = `${chat_item.message.slice(0,14)}...`;
                } else {
                    document.getElementById("curr_user_bar").innerText = `${chat_item.message}`;
                }
            }
        })
    });
    setTimeout(get_messages, 1000)
}

window.onload = get_messages()