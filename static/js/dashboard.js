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


window.onload = function () {
    var data = {};
    var body = JSON.stringify(data);
    var options = {
        method: 'POST',
        body: body,
        headers: { 'content-type': 'application/json', 'X-CSRFToken': csrftoken },
        redirect: "follow"
    }
    fetch("/api/dashboard_resources/", options).then(response => {
        response.json().then(response => {
            if (response.status == 200) {
                const ctx = document.getElementById('myChart').getContext('2d');
                const myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: response.labels,
                        datasets: [{
                            label: 'SGPA',
                            data: response.sgpa_data,
                            backgroundColor: [
                                'rgba(143, 79, 0, 0.8)'
                            ]
                        },
                        {
                            label: 'CGPA',
                            data: response.cgpa_data,
                            backgroundColor: [
                                '#00758F'
                            ]
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: false
                            }
                        }
                    }
                });
                document.getElementById("dashboard_cgpa").innerText = response.cgpa;
                document.getElementById("dashboard_credits").innerText = response.credits;
            }
        })
    });
}