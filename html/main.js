//This file contains functions for HTTP requests, data processing and display, and other miscellaneous needs

//################# INITIALIZATION ########################

//the ID of the current refresh interval - used for clearing the interval when it's no longer needed
let currentInterval = 0;

//the current refresh function, called every {refreshFrequency} milliseconds
let refreshHandler;

//the Google Charts object which can be reused every refresh
let chart;

//the data table from the last refresh, used for validating whether any data has changed
let lastDataTable;

//################# COMMON FUNCTIONS #####################

function Log(thisLevel, msg) {
    //log msg to the browser console
    //if thisLevel is the same or higher than the logLevel, log it using the appropriate log type. Otherwise, take no action.
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
    //display the loading animation on top of the page
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

    setTimeout(UnshowLoading, 20000); //in case the load fails or something else strange happens, remove loader after 20sec
}

function UnshowLoading() {
    //remove the loading animation from the page
    let loadingOverlay = document.getElementById("loading-overlay");
    let loadingCanvas = document.getElementById("loading-wheel");

    loadingCanvas.classList.remove("animate");
    loadingOverlay.classList.add("hidden");
}

async function Get(url, isJson) {
    //make an HTTP GET request to url
    //if isJson is set, interpret the results as JSON and return a JS object
    //otherwise, return the results as a text string

    if(isJson === undefined) {
        isJson = true;
    }

    let init;
    if(auth.currentUser === null || url.substring(0,apiRoot.length) != apiRoot) {    //don't send auth header to outside requests
        init = {};
    } else {
        init = {'headers': new Headers({'Authorization': `Bearer ${await auth.currentUser.getIdToken(true)}`})};
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
    //make an HTTP POST request to url with the passed request body
    //if isJson is set, interpret the results as JSON and return a JS object
    //otherwise, return the results as a text string

    if(isJson === undefined) {
        isJson = true;
    }

    let init;
    if(auth.currentUser === null || url.substring(0,apiRoot.length-1) != apiRoot) {    //don't send auth header to outside requests
        init = {"method": "POST", "body": body}
    } else {
        init = {"headers": new Headers({"Authorization": `Bearer ${await auth.currentUser.getIdToken(true)}`}), "method": "POST", "body": body} 
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
    //convert date to a string in a specific format
    //valid formats are sortable (yyyy-MM-dd) or readable (MM/dd/yyyy)
    //this was originally used to provide formatting for chart labels, but Google's autoformatting is more robust
    //now primarily used for chart title and other miscellaneous uses
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
    //draw a line chart inside the "data-chart" element that should already exist on the page
    //dataTable is expected to be a 2D array where each entry in the parent array represents a row and each entry in the child arrays represents a cell:
    //  [[Date(2000,1,1), 123], [Date(2000,1,2), 234]]
    //the first character of x_title and y_title will be capitalized (if they aren't already); the rest will be left untouched
    //width and height should be a number representing the number of pixels in each dimension
    //vAxis_fmt should be a valid format string as expected by the Google Charts API - typically "decimal", "percent", or "none"

    // let dataChartOptions = document.getElementById("data-chart-options");    //disabled until we have options to read

    if(JSON.stringify(dataTable) === JSON.stringify(lastDataTable)) {
        //if this dataTable matches the dataTable from the last refresh, don't bother redrawing the chart
        return;
    }

    lastDataTable = dataTable.slice();  //save a deep copy of the dataTable so that we can compare it on the next refresh

    let dataChart = document.getElementById("data-chart");
    
    if(vAxis_fmt === undefined) {
        vAxis_fmt = "none";
    }

    x_title = x_title[0].toUpperCase()+x_title.substring(1);
    y_title = y_title[0].toUpperCase()+y_title.substring(1)

    let title = `${y_title} by ${x_title}, ${FormatDate(dataTable[0][0], "readable")} through ${FormatDate(dataTable[dataTable.length-1][0], "readable")}`;
    
    let inputData = {
        cols: [{id: x_title, label: x_title, type: 'date'},
               {id: y_title, label: y_title, type: 'number'}],
        rows: dataTable.map((row)=>{return {c: [{v: row[0]}, {v: row[1]}]};})
    };
    
    let data = new google.visualization.DataTable(inputData);

    let options =  {'title':title,
                    'width':width,
                    'height':height,
                    'legend':{'position':'none'},
                    'hAxis':{/*'format':'M/d/yy h:mm:ss a', */
                        'minorGridlines':{'count':0}
                        },
                    'vAxis':{'format':vAxis_fmt},
                    'pointSize': 6
                    };

    if(chart === undefined) {   //to reduce memory usage, we only need a single chart object. It can be redrawn as many times as we need
        chart = new google.visualization.LineChart(dataChart);
    }
    chart.draw(data, options);

    // dataChartOptions.classList.remove("hidden"); //disabled until we have options to read
}

function SetSiteCookie(site) {
    //store the current site in the cookie jar for future reference

    let todayPlus30 = new Date();
    todayPlus30.setDate(todayPlus30.getDate()+30);  //this is not a security-related cookie, so we can toss it a month out in the future regardless of whether the user is logged in persistently or not

    if(site !== undefined) {
        document.cookie = `site=${site}; expires=${todayPlus30}`;
    }
}

//################# DATA FUNCTIONS ########################

async function LoadSiteList() {
    //request and display the list of sites the user is eligible to access

    let siteList = document.getElementById("site-selector");

    return await GetAvailableSites().then((response)=> {
        if(response == -1) {
            return;
        }

        Array.from(siteList.children).forEach((listItem)=> {
            listItem.remove();
        });

        Array.from(response.result).forEach((site)=> {
            if(site.site_id == 11) {    //site 11 was broken during development and could not be fixed. A new installation wouldn't need these lines
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
            //if site isn't already set, assume first site in the list
            currentSite = siteList.children[0].id;
            SetSiteCookie(currentSite);
        }
        
        //update selection element to match selected site from cookie/default
        siteList.selectedIndex = Array.from(siteList.children).map((child)=>child.id).indexOf(currentSite);

        siteList.onchange = ChangeSite;

        siteList.disabled = false;
    });
}

function ChangeSite(event) {
    //handle the user changing site from the dropdown

    ShowLoading();
    let newSite = event.target.options[event.target.selectedIndex].id;
    currentSite = newSite;
    SetSiteCookie(newSite);
    LoadSensorTable().then(UnshowLoading);
}

async function LoadSensorTable() {
    //request and display the sensors in the current site

    let sensorTable = document.getElementById("sensor-table").tBodies[0];

    return await GetSiteDeviceInformation(currentSite.split("_")[1]).then((response)=> {
        Array.from(sensorTable.children).forEach((tableChild)=> {
            tableChild.remove();
        });

        let currentTriggers = document.getElementById("current-triggers");
        currentTriggers.innerHTML = "";

        let triggerDeviceParams = document.getElementById("trigger-device-params");
        triggerDeviceParams.innerHTML = "";

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

                device.triggers.forEach((trigger)=>{
                    if(parameter.parameter_id == trigger.parameter_id) {
                        currentTriggers.appendChild(document.createTextNode(`When ${device.device_name} ${parameter.parameter_name} ${trigger.relation_to_reading} ${trigger.reading_value},\nsend an email. (`));
                        
                        let deleteLink = document.createElement("a");
                        deleteLink.href = "#";
                        deleteLink.id = `delete_${currentSite.split("_")[1]}_${trigger.trigger_id}`;
                        deleteLink.onclick = DeleteTrigger;
                        deleteLink.appendChild(document.createTextNode("delete and reload page"));

                        currentTriggers.appendChild(deleteLink);
                        currentTriggers.appendChild(document.createTextNode(")"));

                        currentTriggers.appendChild(document.createElement("br"));
                        currentTriggers.appendChild(document.createElement("br"));
                    }
                });

                let paramDevice = document.createElement("option");
                paramDevice.appendChild(document.createTextNode(`${device.device_name} ${parameter.parameter_name}`));
                paramDevice.id = `add_${device.device_id}_${parameter.parameter_id}`;
                triggerDeviceParams.appendChild(paramDevice);
            });  
        });

        document.getElementById("data-chart-sidebar").classList.remove("hidden");
        document.getElementById("welcome-message").classList.add("hidden");
        sensorTable.parentElement.classList.remove("hidden");
    });
}

async function GetSensorData(site_id, parameter_id, device_id, from_date) {
    //request and return the data gathered by the requested sensor

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
    //request and display data for the requested sensor

    ShowLoading();

    clearInterval(currentInterval);

    let idParts = event.target.id.split("-");

    return await GetSensorData(currentSite.split("_")[1], idParts[2]).then((response)=> {
        document.getElementById("update-chart-options").classList.remove("hidden");
        DrawLineChart(response.data.map(row => [new Date(row.date_time), row.reading]), "Date", response.parameter_name, "100%", "400px", (response.parameter_name.indexOf("%") > -1 ? "percent" : "decimal"));
        refreshHandler = async ()=>{
            return await GetSensorData(currentSite.split("_")[1], idParts[2]).then((response)=> {
                DrawLineChart(response.data.map(row => [new Date(row.date_time), row.reading]), "Date", response.parameter_name, "100%", "400px", (response.parameter_name.indexOf("%") > -1 ? "percent" : "decimal"));
            });
        };
        currentInterval = setInterval(refreshHandler, refreshFrequency);
        UnshowLoading();
    });
}

async function DownloadSensor(event) {
    //request data for the requested sensor, then serialize it as a CSV for user download

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

function UpdateChartOptions(event) {
    //update refresh frequency based on user input by canceling and resetting interval
    let form = event.target;

    refreshFrequency = form.elements.refreshFrequency.value;

    clearInterval(currentInterval);
    currentInterval = setInterval(refreshHandler, refreshFrequency);
}