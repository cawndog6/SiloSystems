//This file contains functions for HTTP requests, data processing and display, and other miscellaneous needs

//################# INITIALIZATION ########################

let logLevel = level.DEBUG;
let currentInterval = 0;

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

function ShowLoading() {
    let loadingOverlay = document.getElementById("loading-overlay");
    let loadingCanvas = document.getElementById("loading-wheel");

    let ctx = loadingCanvas.getContext("2d");

    ctx.fillStyle = '#aaa';

    ctx.beginPath();
    ctx.arc(50, 50, 35, 0, Math.PI * 1.8);
    
    ctx.arc(50, 50, 25, Math.PI * 1.8, 0, true);
    ctx.lineTo(85, 50);
    ctx.fill();

    loadingOverlay.classList.remove("hidden");
    loadingCanvas.classList.add("animate");

    setTimeout(UnshowLoading, 20000); //in case the load fails, remove loader after 20sec
}

function UnshowLoading() {
    let loadingOverlay = document.getElementById("loading-overlay");
    let loadingCanvas = document.getElementById("loading-wheel");

    loadingCanvas.classList.remove("animate");
    loadingOverlay.classList.add("hidden");
}

async function Get(url, isJson) {
    if(isJson === undefined) {
        isJson = true;
    }

    let init;
    if(currentToken === undefined || url.substring(0,apiRoot.length) != apiRoot) {    //don't send auth header to outside requests
        init = {};
    } else {
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
    if(currentToken === undefined || url.substring(0,apiRoot.length-1) != apiRoot) {    //don't send auth header to outside requests
        init = {"headers": new Headers({"Authorization": `Bearer ${currentToken}`}), "method": "POST", "body": body} 
    } else {
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
                    'hAxis':{'format':'M/d/yy h:m:s a', 
                        'minorGridlines':{'count':0}
                        },
                    'vAxis':{'format':vAxis_fmt},
                    'pointSize': 6
                    };

    let chart = new google.visualization.LineChart(dataChart);
    chart.draw(data, options);
}

//################# DATA FUNCTIONS ########################

async function LoadSiteList() {
    let siteList = document.getElementById("site-selector");

    return await GetAvailableSites().then((response)=> {
        if(response == -1) {
            return;
        }

        Array.from(siteList.children).forEach((listItem)=> {
            listItem.remove();
        });

        Array.from(response.result).forEach((site)=> {
            if(site.site_id == 11) {    //TODO temporary fix for broken site
                return;
            }
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

function ChangeSite(event) {
    ShowLoading();
    let newSite = event.target.options[event.target.selectedIndex].id;
    currentSite = newSite;
    SetUserCookies(undefined, undefined, newSite, true);
    LoadSensorTable().then(UnshowLoading);
}

async function LoadSensorTable() {
    let sensorTable = document.getElementById("sensor-table").tBodies[0];

    return await GetSiteDeviceInformation(currentSite.split("_")[1]).then((response)=> {
        Array.from(sensorTable.children).forEach((tableChild)=> {
            tableChild.remove();
        });

        response.devices.forEach((device)=> {
            device.parameters.forEach((parameter)=> {
                let row = sensorTable.insertRow();
    
                let deviceIdCell = row.insertCell();
                deviceIdCell.appendChild(document.createTextNode(device.device_id));
        
                let deviceNameCell = row.insertCell();
                deviceNameCell.appendChild(document.createTextNode(device.device_name));
        
                let parameterIdCell = row.insertCell();
                parameterIdCell.appendChild(document.createTextNode(parameter.parameter_id));
        
                let parameterNameCell = row.insertCell();
                parameterNameCell.appendChild(document.createTextNode(parameter.parameter_name));
        
                let viewCell = row.insertCell();
                let viewLink = document.createElement("a");
                viewLink.href = "#";
                viewLink.id = `v-${device.device_id}-${parameter.parameter_id}`;
                viewLink.onclick = ViewSensor;
                viewLink.appendChild(document.createTextNode("View Data"));
                viewCell.appendChild(viewLink);
        
                let downloadCell = row.insertCell();
                let downloadLink = document.createElement("a");
                downloadLink.href = "#";
                downloadLink.id = `d-${device.device_id}-${parameter.parameter_id}`;
                downloadLink.onclick = DownloadSensor;
                downloadLink.appendChild(document.createTextNode("Download Data"));
                downloadCell.appendChild(downloadLink);
            });  
        });
        document.getElementById("welcome-message").classList.add("hidden");
        sensorTable.parentElement.classList.remove("hidden");
    });
}

async function GetSensorData(site_id, parameter_id, device_id, from_date) {
    site_id = encodeURIComponent(site_id);
    parameter_id = encodeURIComponent(parameter_id);
    if(device_id !== undefined) {
        device_id = encodeURIComponent(device_id);
    }
    if(from_date !== undefined) {
        from_date = encodeURIComponent(from_date);
    }

    let queryString;
    let errString;

    if(device_id == undefined && from_date == undefined) {
        queryString = `site_id=${site_id}&parameter_id=${parameter_id}`;
        errString = `Failed to get data for ${parameter_id} in site ${site_id}`;
    }
    else if(device_id == undefined) {
        queryString = `site_id=${site_id}&parameter_id=${parameter_id}&from_date=${from_date}`;
        errString = `Failed to get data for ${parameter_id} in site ${site_id} from date ${from_date}`;
    }
    else if(from_date == undefined) {
        queryString = `site_id=${site_id}&device_id=${device_id}&parameter_id=${parameter_id}`;
        errString = `Failed to get data for ${parameter_id} on device ${device_id} in site ${site_id}`;
    }
    else {
        queryString = `site_id=${site_id}&device_id=${device_id}&parameter_id=${parameter_id}&from_date=${from_date}`;
        errString = `Failed to get data for ${parameter_id} on device ${device_id} in site ${site_id} from date ${from_date}`;
    }

    return await Get(`${apiRoot}/getSensorData?${queryString}`).catch((err)=> {
        Log(logLevel.ERROR, `${errString}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function ViewSensor(event) {
    ShowLoading();

    clearInterval(currentInterval);

    let idParts = event.target.id.split("-");

    return await GetSensorData(currentSite.split("_")[1], idParts[2]).then((response)=> {
        DrawLineChart(response.data.map(row => [new Date(row.date_time), row.reading]), "Date", response.parameter_name, "100%", "400px", (response.parameter_name.indexOf("%") > -1 ? "percent" : "decimal"));
        currentInterval = setInterval(()=>{
            GetSensorData(currentSite.split("_")[1], idParts[2]).then((response)=> {
                DrawLineChart(response.data.map(row => [new Date(row.date_time), row.reading]), "Date", response.parameter_name, "100%", "400px", (response.parameter_name.indexOf("%") > -1 ? "percent" : "decimal"));
            });
        }, 5000);
        UnshowLoading();
    });
}

async function DownloadSensor(event) {
    ShowLoading();

    let today = FormatDate(new Date());

    let idParts = event.target.id.split("-");

    return await GetSensorData(currentSite.split("_")[1], idParts[2]).then((response)=> {
        let download = `Date,${response.parameter_name}\n`;
        download += response.data.map(row => `${FormatDate(new Date(row.date_time))},${row.reading}`).join('\n');

        let invisibleLink = document.createElement("a");
        invisibleLink.href = `data:text/csv;charset=utf-8,${encodeURI(download)}`;
        invisibleLink.target = "_blank";
        invisibleLink.download = `Download_${id}_${today}.csv`;
        invisibleLink.click();
        invisibleLink.remove();

        UnshowLoading();
    });
}