//This file contains functions for managing sites and devices

//################# INITIALIZATION ########################



//################# MENU FUNCTIONS ########################

async function ShowManage() {
    ShowLoading();
    let template = document.getElementsByTagName("template")[0];
    let manage = template.content.getElementById("manage").cloneNode(true);

    document.body.appendChild(manage);

    let siteList = document.getElementById("site-selector");
    let siteAddList = document.getElementById("site-selector-add");
    let deviceAddList = document.getElementById("device-selector-add");
    let deviceRemoveList = document.getElementById("device-selector-remove");
    let siteListIds = [];
    let siteListNames = [];

    Array.from(siteList.children).forEach((child)=> {
        let addSite = siteAddList.appendChild(child.cloneNode(true));
        addSite.id = `add${child.id}`;
        siteListIds.push(child.id);
        siteListNames.push(child.innerText);
    });

    siteAddList.children[0].remove();
    siteAddList.disabled = false;

    let promises = [];

    for(var i = 0; i < siteListIds.length; i++) {
        promises.push(await GetSiteDeviceInformation(siteListIds[i].split("_")[1]).then((response)=> {
            response.devices.forEach((device)=> {
                let listAddItem = document.createElement("option");
                listAddItem.innerText = `${siteListNames[i]} - ${device.device_name}`;
                listAddItem.id = `remove${siteListIds[i]}_${device.device_id}`;

                let listRemoveItem = document.createElement("option");
                listRemoveItem.innerText = `${siteListNames[i]} - ${device.device_name}`;
                listRemoveItem.id = `add${siteListIds[i]}_${device.device_id}`;

                deviceAddList.appendChild(listAddItem);
                deviceRemoveList.appendChild(listRemoveItem);
            });
        }));
    }

    deviceAddList.children[0].remove();
    deviceAddList.disabled = false;

    deviceRemoveList.children[0].remove();
    deviceRemoveList.disabled = false;

    Promise.all(promises).then(UnshowLoading);
}

function UnshowManage() {
    document.body.classList.remove("noScroll");
    let manage = document.getElementById("manage");
    manage.remove();
}

//################# DEVICE MANAGEMENT #####################


async function AddDeviceToSite(event) {
    let form = event.target;
    let selector = document.getElementById("site-selector-add");

    site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);
    device_name = encodeURIComponent(form.elements.newDeviceName.value);

    let queryString = `site_id=${site_id}&device_name=${device_name}`;

    return await Get(`${apiRoot}/addDeviceToSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add device ${device_name} to site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function AddParameterToDevice(event) {
    let form = event.target;
    let selector = document.getElementById("device-selector-add");
    site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);
    device_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[2]);
    parameter_name = encodeURIComponent(form.elements.newParameterName.value);
    data_val = encodeURIComponent(form.elements.newDataVal.value);
    data_type = encodeURIComponent(form.elements.newDataType.value);

    let queryString = `site_id=${site_id}&device_id=${device_id}&parameter_name=${parameter_name}&data_val=${data_val}&data_type=${data_type}`;

    return await Get(`${apiRoot}/addParameterToDevice?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add parameter ${parameter_name} to device ${device_id} in site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function RemoveDeviceFromSite(event) {
    let form = event.target;
    let selector = document.getElementById("device-selector-remove");

    let confirmation = form.elements.confirmRemove.value;
    if(confirmation != "YES") {
        alert("Please enter YES to confirm you want to delete this device.");
        return;
    }

    site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);

    let queryString = `site_id=${site_id}&device_id=${device_id}`;

    return await Get(`${apiRoot}/removeDeviceFromSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to remove device ${device_name} from site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

//################# USER MANAGEMENT #######################

async function AddUserToSite(event) {
    let form = event.target;
    let selector = document.getElementById("site-selector-user-add");
    let site_name = encodeURIComponent(selector.options[selector.selectedIndex].innerText);
    let new_user_email = encodeURIComponent(form.elements.newUserEmail.value);

    let queryString = `site_name=${site_name}&new_user_email=${new_user_email}`;

    return await Get(`${apiRoot}/addUserToSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add user ${new_user_email} to site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function RemoveUserFromSite(event) {
    let form = event.target;
    let selector = document.getElementById("site-selector-user-remove");
    let site_name = encodeURIComponent(selector.options[selector.selectedIndex].innerText);
    let delete_user_email = encodeURIComponent(form.elements.deleteUserEmail.value);

    let queryString = `site_name=${site_name}&delete_user_email=${delete_user_email}`;

    return await Get(`${apiRoot}/removeUserFromSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to remove user ${new_user_email} from site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

//################# SITE MANAGEMENT #######################

async function CreateNewSite(event) {
    let site_name = encodeURIComponent(event.target.elements.newSiteName.value);

    let queryString = `site_name=${site_name}`;

    return await Get(`${apiRoot}/createNewSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to create site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

//################# READ-ONLY FUNCTIONS ###################

async function GetAvailableSites() {
    return await Get(`${apiRoot}/getAvailableSites`).catch((err)=> {
        Log(logLevel.ERROR, `Failed to get list of sites for current user: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function GetSiteDeviceInformation(site_id) {
    site_id = encodeURIComponent(site_id);

    let queryString = `site_id=${site_id}`;

    return await Get(`${apiRoot}/getDeviceSiteInformation?${queryString}`).catch((err)=> {
        Log(logLevel.ERROR, `Failed to get devices for site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
       return response;
    });
}