//This file contains functions for HTTP requests, data processing and display, and other miscellaneous needs

//################# INITIALIZATION ########################

const level = {DEBUG: 0, WARNING: 1, ERROR: 2};
let logLevel = level.DEBUG;

let apiRoot = "https://us-west2-silo-systems-292622.cloudfunctions.net";

//################# COMMON FUNCTIONS #####################

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

    let init;
    if(true || currentToken === undefined || url.substring(0,apiRoot.length) != apiRoot) {    //don't send auth header to outside requests
        init = {};
    } else {
        //disabled 2/14 pending Access-Control-Allow-Headers update on the server
        init = {'headers': new Headers({'Authorization': `Bearer ${currentToken}`})};
    }

    let response = await fetch(url, init);
    
    if(response.ok) {
        Log(level.DEBUG, `Get request to ${url} succeeded with code ${response.status}`);
        if(isJson) {
            return await response.json();
        } else {
            return await response.text();
        }
    } else {
        Log(level.ERROR, `Get request to ${url} failed with code ${response.status}`);
        return undefined;
    }
}

async function Post(url, body, isJson) {
    if(isJson === undefined) {
        isJson = true;
    }

    let init;
    if(true || currentToken === undefined || url.substring(0,apiRoot.length-1) != apiRoot) {    //don't send auth header to outside requests
        init = {"headers": new Headers({"Authorization": `Bearer ${currentToken}`}), "method": "POST", "body": body} 
    } else {
        //disabled 2/14 pending Access-Control-Allow-Headers update on the server
        init = {"method": "POST", "body": body}
    }
    let response = await fetch(url, init);
    
    if(response.ok) {
        Log(level.DEBUG, `Post request to ${url} succeeded with code ${response.status}`);
        if(isJson) {
            return await response.json();
        } else {
            return await response.text();
        }
    } else {
        Log(level.ERROR, `Post request to ${url} failed with code ${response.status}`);
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

function LoadSiteList() {
    let siteList = document.getElementById("site-selector");

    GetAvailableSites().then((response)=> {
        if(response == -1) {
            return;
        }

        Array.from(siteList.children).forEach((listItem)=> {
            listItem.remove();
        });

        Array.from(response.result).forEach((site)=> {
            let listItem = document.createElement("option");
            listItem.innerText = site.site_name;
            listItem.id = `site_${site.site_id}`;

            siteList.appendChild(listItem);
        });

        if(document.cookie.indexOf("site=") > -1) {
            currentSite = document.cookie.split("site=")[1].split(";")[0];
        }
        else {
            currentSite = siteList.children[0].id;
            SetUserCookies(undefined, undefined, currentSite, true);
        }
        
        siteList.selectedIndex = Array.from(siteList.children).map((child)=>child.id).indexOf(currentSite);

        siteList.onchange = ChangeSite;

        siteList.disabled = false;
    });
}

function ChangeSite(evt) {
    let newSite = evt.target.options[evt.target.selectedIndex].id;
    currentSite = newSite;
    SetUserCookies(undefined, undefined, newSite, true);
}

function DrawSensorTable(response) {
    let sensorTable = document.getElementById("sensor-table").tBodies[0];

    response = response[1];

    response.sensors.forEach((sensor)=> {
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
    if(currentToken === undefined) {
        alert("Sorry, you must be logged in to perform that action. Please log in and try again.");
        return;
    }

    let fullId = event.target.id;
    let id = fullId.substring(2);

    Get(`${apiRoot}/returnSQLresponse?sensor=Temperatures&deviceID=${id}`).then((response)=> {
        DrawLineChart(response.data.map(row => [new Date(row.date), row.value]), "Date", response.sensorName, "100%", "400px", (response.sensorName.indexOf("%") > -1 ? "percent" : "decimal"))
    });
}

function DownloadSensor(event) {
    if(currentToken === undefined) {
        alert("Sorry, you must be logged in to perform that action. Please log in and try again.");
        return;
    }

    let fullId = event.target.id;
    let id = fullId.substring(2);

    let today = FormatDate(new Date());

    Get(`${apiRoot}/returnSQLresponse?sensor=Temperatures&deviceID=${id}`).then((response)=> {
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