//################## INITIALIZATION #######################

const level = {DEBUG: 0, WARNING: 1, ERROR: 2};
let logLevel = level.DEBUG;

let loggedIn = false;

let apiRoot = "https://us-west2-silo-systems-292622.cloudfunctions.net";

window.addEventListener("load", StartLoad);

//################## UTILITY FUNCTIONS ####################

function Log(thisLevel, msg) {
    if(thisLevel >= logLevel) {
        switch(thisLevel) {
            case level.DEBUG:
                console.log(msg);
                break;
            case level.WARNING:
                console.warn(msg);
                break;
            case level.ERROR:
                console.error(msg);
                break;
        }
    }
}

async function Get(url, isJson) {
    if(isJson === undefined) {
        isJson = true;
    }

    let response = await fetch(url);
    
    if(response.ok) {
        Log(level.DEBUG, `Request to ${url} succeeded with code ${response.status}`);
        if(isJson) {
            return await response.json();
        } else {
            return await response.text();
        }
    } else {
        Log(level.ERROR, `Request to ${url} failed with code ${response.status}`);
        return undefined;
    }
}

function FormatDate(date, format) {
    //valid formats are sortable (yyyy-MM-dd) or readable (MM/dd/yyyy)
    if(format === undefined) {
        format = "sortable"
    }

    let month = "0" + (date.getMonth() + 1);
    month = month.substring(month.length - 2);

    let day = "0" + date.getDate();
    day = day.substring(day.length - 2);

    if(format == "sortable") {
        return `${date.getFullYear()}-${month}-${day}`;
    } else {
        return `${month}/${day}/${date.getFullYear()}`;
    }
}

function DrawLineChart(dataTable, x_title, y_title, width, height, vAxis_fmt) {
    let dataChart = document.getElementById('data-chart');
    
    if(vAxis_fmt === undefined) {
        vAxis_fmt = "none";
    }

    let title = `${y_title} by ${x_title}, ${FormatDate(dataTable[0][0], "readable")} through ${FormatDate(dataTable[dataTable.length-1][0], "readable")}`;
    let data = new google.visualization.DataTable();
    data.addColumn('date', x_title);
    data.addColumn('number', y_title);
    data.addRows(dataTable);

    let options =  {'title':title,
                    'width':width,
                    'height':height,
                    'legend':{'position':'none'},
                    'hAxis':{'format':'M/d/yy', 
                        'minorGridlines':{'count':0}
                        },
                    'vAxis':{'format':vAxis_fmt},
                    'pointSize': 6
                    };

    let chart = new google.visualization.LineChart(dataChart);
    chart.draw(data, options);
}

//################# DATA FUNCTIONS ########################

function StartLoad() {
    ValidateUser();

    Promise.all([google.charts.load('current', {'packages':['corechart']}),Get("shim_sensors")])
        .then(DrawSensorTable);
}

function DrawSensorTable(response) {
    let sensorTable = document.getElementById("sensor-table").tBodies[0];

    response = response[1];

    response.sensors.forEach(function(sensor) {
        let row = sensorTable.insertRow();

        let deviceIdCell = row.insertCell();
        deviceIdCell.appendChild(document.createTextNode(sensor.deviceId));

        let deviceNameCell = row.insertCell();
        deviceNameCell.appendChild(document.createTextNode(sensor.deviceName));

        let sensorIdCell = row.insertCell();
        sensorIdCell.appendChild(document.createTextNode(sensor.sensorId));

        let sensorNameCell = row.insertCell();
        sensorNameCell.appendChild(document.createTextNode(sensor.sensorName));

        let viewCell = row.insertCell();
        let viewLink = document.createElement("a");
        viewLink.href = "#";
        viewLink.id = `v-${sensor.deviceId}`; //-${sensor.sensorId}`;
        viewLink.onclick = ViewSensor;
        viewLink.appendChild(document.createTextNode("View Data"));
        viewCell.appendChild(viewLink);

        let downloadCell = row.insertCell();
        let downloadLink = document.createElement("a");
        downloadLink.href = "#";
        downloadLink.id = `d-${sensor.deviceId}`; //-${sensor.sensorId}`;
        downloadLink.onclick = DownloadSensor;
        downloadLink.appendChild(document.createTextNode("Download Data"));
        downloadCell.appendChild(downloadLink);
    });

    sensorTable.parentElement.classList.remove("hidden");
}

function ViewSensor(event) {
    if(!loggedIn) {
        alert("Sorry, you must be logged in to perform that action. Please log in and try again.");
        return;
    }

    let fullId = event.target.id;
    let id = fullId.substring(2);

    Get(`${apiRoot}/returnSQLresponse?sensor=Temperatures&deviceID=${id}`).then(function(response) {
        DrawLineChart(response.data.map(row => [new Date(row.date), row.value]), "Date", response.sensorName, "100%", "400px", (response.sensorName.indexOf("%") > -1 ? "percent" : "decimal"))
    });
}

function DownloadSensor(event) {
    if(!loggedIn) {
        alert("Sorry, you must be logged in to perform that action. Please log in and try again.");
        return;
    }

    let fullId = event.target.id;
    let id = fullId.substring(2);

    let today = FormatDate(new Date());

    Get(`${apiRoot}/returnSQLresponse?sensor=Temperatures&deviceID=${id}`).then(function(response) {
        let download = `Date,${response.sensorName}\n`;
        download += response.data.map(row => `${FormatDate(new Date(row.date))},${row.value}`).join('\n');

        let dummyLink = document.createElement("a");
        dummyLink.href = `data:text/csv;charset=utf-8,${encodeURI(download)}`;
        dummyLink.target = "_blank";
        dummyLink.download = `Download_${id}_${today}.csv`;
        dummyLink.click();
        dummyLink.remove();
    });
}

//################# LOGIN FUNCTIONS #######################

function ShowLogin() {
    let template = document.getElementsByTagName("template")[0];
    let login = template.content.getElementById("login").cloneNode(true);
    document.body.appendChild(login);
}

function UnshowLogin() {
    document.body.classList.remove("noScroll");
    let login = document.getElementById("login");
    login.remove();
}

function ValidateLogin() {
    let form = document.getElementById("login-form");

    let username = form.elements.username.value;
    let password = form.elements.password.value;
    let remember = form.elements.remember.checked;

    if(username == password) {
        Log(level.DEBUG, `Successful ${(remember) ? "persistent":"session"} login for user ${username}`);
        let today = new Date();
        let todayPlus30 = new Date();
        todayPlus30.setDate(today.getDate()+30);

        if(remember) {
            document.cookie = `username=${username}; expires=${todayPlus30}`;
        } else {
            document.cookie = `username=${username}`;
        }

        ValidateUser();
        UnshowLogin();
    } else {
        Log(level.WARNING, `Invalid login attempt for user ${username}`);
        document.getElementById("login-failure").classList.remove("hidden");
    }
}

function Logout() {
    document.cookie = "username=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    window.location.reload();
}

function ValidateUser() {
    let userDisplay = document.getElementById("current-user");
    let loginLink = document.getElementById("show-login-link");
    let logoutLink = document.getElementById("logout-link");

    if(document.cookie.indexOf("username=") == -1) {
        userDisplay.innerText = "You are not logged in. ";
        loginLink.classList.remove("hidden");
        logoutLink.classList.add("hidden");

        loggedIn = false;
    } else {
        let username = document.cookie.split("username=")[1].split(";")[0];
        userDisplay.innerHTML = `Currently logged in as <strong>${username}</strong>`;
        loginLink.classList.add("hidden");
        logoutLink.classList.remove("hidden");

        loggedIn = true;
    }
}