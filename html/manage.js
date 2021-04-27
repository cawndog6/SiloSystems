//This file contains functions for managing sites and devices

//################# MENU FUNCTIONS ########################

async function ShowManage() {
    //display the management menu

    ShowLoading();
    let template = document.getElementsByTagName("template")[0];
    let manage = template.content.getElementById("manage").cloneNode(true);

    document.body.appendChild(manage);

    let siteList = document.getElementById("site-selector");
    let siteAddList = document.getElementById("site-selector-add");
    let siteDeleteList = document.getElementById("site-selector-delete");
    let userAddList = document.getElementById("site-selector-user-add");
    let userRemoveList = document.getElementById("site-selector-user-remove");
    let deviceAddList = document.getElementById("device-selector-add");
    let deviceRemoveList = document.getElementById("device-selector-remove");
    let siteListIds = [];
    let siteListNames = [];

    Array.from(siteList.children).forEach((child)=> {   //populate the site various lists
        let addSite = siteAddList.appendChild(child.cloneNode(true));
        addSite.id = `add${child.id}`;
        let deleteSite = siteDeleteList.appendChild(child.cloneNode(true));
        deleteSite.id = `delete${child.id}`;

        let userAddSite = userAddList.appendChild(child.cloneNode(true));
        userAddSite.id = `useradd${child.id}`;
        let userRemoveSite = userRemoveList.appendChild(child.cloneNode(true));
        userRemoveSite.id = `userremove${child.id}`;

        siteListIds.push(child.id);
        siteListNames.push(child.innerText);
    });

    [siteAddList, siteDeleteList, userAddList, userRemoveList].forEach((list)=> {
        list.children[0].remove();  //remove the placeholder entries
        list.disabled = false;
    });

    let promises = [];  //we want to load the device lists for all sites in parallel. This array stores the promises for each

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

    Promise.all(promises).then(UnshowLoading);  //here we wait for the array of promises to resolve
}

function UnshowManage() {
    //remove the management menu from the DOM
    document.body.classList.remove("noScroll");
    let manage = document.getElementById("manage");
    manage.remove();
}

//################# DEVICE MANAGEMENT #####################

async function AddDeviceToSite(event) {
    //make the necessary API call to add the requested device to the requested site
    let form = event.target;
    let selector = document.getElementById("site-selector-add");

    let site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);
    let device_name = encodeURIComponent(form.elements.newDeviceName.value);

    let queryString = `site_id=${site_id}&device_name=${device_name}`;

    return await Get(`${apiRoot}/addDeviceToSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add device ${device_name} to site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function AddParameterToDevice(event) {
    //make the necessary API call to add the requested parameter type to the requested devlce
    let form = event.target;
    let selector = document.getElementById("device-selector-add");
    let site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);
    let device_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[2]);
    let parameter_name = encodeURIComponent(form.elements.newParameterName.value);
    let data_val = encodeURIComponent(form.elements.newDataVal.value);
    let data_type = encodeURIComponent(form.elements.newDataType.value);

    let queryString = `site_id=${site_id}&device_id=${device_id}&parameter_name=${parameter_name}&data_val=${data_val}&data_type=${data_type}`;

    return await Get(`${apiRoot}/addParameterToDevice?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add parameter ${parameter_name} to device ${device_id} in site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function RemoveDeviceFromSite(event) {
    //make the necessary API call to remove the requested device from its site
    //note that this doesn't delete it from the database entirely, only disassociates it from this site
    let form = event.target;
    let selector = document.getElementById("device-selector-remove");

    let confirmation = form.elements.confirmRemove.value;
    if(confirmation != "YES") {
        alert("Please enter YES to confirm you want to delete this device.");
        return;
    }

    let site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);

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
    //make the necessary API call to add the requested user to the requested site
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
    //make the necessary API call to remove the user from the requested site
    //note that this does not delete the user entirely, only disassociates it from the requested site
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

async function DeleteUserAccount(event) {
    //make the necessary API call to delete the CURRENT user account
    //note that this does not delete the underlying Firebase account, only the user details in the database
    let form = event.target;

    let confirmation = form.elements.confirmDelete.value;
    if(confirmation != "YES") {
        alert("Please enter YES to confirm you want to delete your account.");
        return;
    }

    return await Get(`${apiRoot}/deleteUserAccount`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to delete user ${new_user_email}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

//################# SITE MANAGEMENT #######################

async function CreateNewSite(event) {
    //make the necessary API call to create a new empty site
    let site_name = encodeURIComponent(event.target.elements.newSiteName.value);

    let queryString = `site_name=${site_name}`;

    return await Get(`${apiRoot}/createNewSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to create site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function DeleteSite(event) {
    //make the necessary API call to delete the requested site
    let form = event.target;

    let confirmation = form.elements.confirmDelete.value;
    if(confirmation != "YES") {
        alert("Please enter YES to confirm you want to delete this site.");
        return;
    }

    let selector = document.getElementById("site-selector-delete");

    let site_id = encodeURIComponent(selector.options[selector.selectedIndex].id.split("_")[1]);

    let queryString = `site_id=${site_id}`;

    return await Get(`${apiRoot}/deleteSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to delete site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

//################# TRIGGER FUNCTIONS #####################

async function CreateTrigger(event) {
    //make the necessary API call to add a new trigger to the database for the requested device
    let form = event.target;

    let trigger_device_params = document.getElementById("trigger-device-params").value;
    let site_id = encodeURIComponent(trigger_device_params.options[trigger_device_params.selectedIndex].id.split("_")[1]);
    let parameter_id = encodeURIComponent(trigger_device_params.options[trigger_device_params.selectedIndex].id.split("_")[2]);

    let trigger_direction = document.getElementById("trigger-direction").value;
    let relationship_to_reading = encodeURIComponent(trigger_direction.options[trigger_direction.selectedIndex].innerText);

    let trigger_value = form.elements["trigger-value"].value;

    let name = `${trigger_device_params.options[trigger_device_params.selectedIndex].innerText.substring(0,4)}${relationship_to_reading}${trigger_value}`;
    let type = "email";

    let queryString = `site_id=${site_id}&trigger_name=${name}&trigger_type=${type}&action=${name}&parameter_id=${parameter_id}&reading_value=${trigger_value}&relationship_to_reading=${relationship_to_reading}`;

    return await Get(`${apiRoot}/createTrigger?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to create trigger with request ${queryString}: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function DeleteTrigger(event) {
    //make the necessary API call to delete the requested trigger from the database
    let link_id = event.target.id;

    let queryString = `site_id=${encodeURIComponent(link_id.split("_")[1])}&trigger_id=${encodeURIComponent(link_id.split("_")[2])}`;

    return await Get(`${apiRoot}/deleteTrigger?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to delete trigger ${link_id.split("_")[2]}: ${err}`);
        return -1;
    }).then((response)=> {
        window.location.reload();
        return response;
    });
}

//################# READ-ONLY FUNCTIONS ###################

async function GetAvailableSites() {
    //retrieve the list of sites that the current user is authorized to access
    return await Get(`${apiRoot}/getAvailableSites`).catch((err)=> {
        Log(logLevel.ERROR, `Failed to get list of sites for current user: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

async function GetSiteDeviceInformation(site_id) {
    //retrieve the list of devices in the requested site along with some information about each
    site_id = encodeURIComponent(site_id);

    let queryString = `site_id=${site_id}`;

    return await Get(`${apiRoot}/getSiteDeviceInformation?${queryString}`).catch((err)=> {
        Log(logLevel.ERROR, `Failed to get devices for site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
       return response;
    });
}