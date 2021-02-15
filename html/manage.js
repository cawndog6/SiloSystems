//This file contains functions for managing sites and devices

//################# INITIALIZATION ########################

//currentToken is defined in account.js and is used for the functions in this file

//################# DEVICE MANAGEMENT #####################

function AddDeviceToSite(site_id, device_name) {
    site_id = encodeURIComponent(site_id);
    device_name = encodeURIComponent(device_name);

    let queryString = `uid=${currentToken}&site_id=${site_id}&device_name=${device_name}`;

    Get(`${apiRoot}/addDeviceToSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add device ${device_name} to site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}

function AddParameterToDevice(site_id, device_id, parameter_name, data_val, data_type) {
    site_id = encodeURIComponent(site_id);
    device_id = encodeURIComponent(device_id);
    parameter_name = encodeURIComponent(parameter_name);
    data_val = encodeURIComponent(data_val);
    data_type = encodeURIComponent(data_type);

    let queryString = `uid=${currentToken}&site_id=${site_id}&device_id=${device_id}&parameter_name=${parameter_name}&data_val=${data_val}&data_type=${data_type}`;

    Get(`${apiRoot}/addParameterToDevice?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add parameter ${parameter_name} to device ${device_id} in site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}

function RemoveDeviceFromSite(site_id, device_id) {
    site_id = encodeURIComponent(site_id);
    device_id = encodeURIComponent(device_id);

    let queryString = `uid=${currentToken}&site_id=${site_id}&device_ide=${device_id}`;

    Get(`${apiRoot}/removeDeviceFromSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to remove device ${device_name} from site ${site_id}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}

//################# USER MANAGEMENT #######################

function AddUserToSite(new_user_email, site_name) {
    new_user_email = encodeURIComponent(new_user_email);
    site_name = encodeURIComponent(site_name);

    let queryString = `requestor_uid=${currentToken}&site_name=${site_name}&new_user_email=${new_user_email}`;

    Get(`${apiRoot}/addUserToSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add user ${new_user_email} to site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}

function RemoveUserFromSite(delete_user_email, site_name) {
    delete_user_email = encodeURIComponent(delete_user_email);
    site_name = encodeURIComponent(site_name);

    let queryString = `requestor_uid=${currentToken}&site_name=${site_name}&delete_user_email=${delete_user_email}`;

    Get(`${apiRoot}/removeUserFromSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to remove user ${new_user_email} from site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}

//################# SITE MANAGEMENT #######################

function CreateNewSite(site_name) {
    site_name = encodeURIComponent(site_name);

    let queryString = `uid=${currentToken}&site_name=${site_name}`;

    Get(`${apiRoot}/createNewSite?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to create site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}

//################# READ-ONLY FUNCTIONS ###################

async function GetAvailableSites() {
    let queryString = `uid=${currentToken}`;

    let siteObj = await Get(`${apiRoot}/getAvailableSites?${queryString}`).catch((err)=> {
        Log(logLevel.ERROR, `Failed to get list of sites for current user: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });

    return await siteObj;
}

function GetSiteDeviceInformation(site_id) {
    site_id = encodeURIComponent(site_id);

    let queryString = `uid=${currentToken}&site_id=${site_id}`;

    Get(`${apiRoot}/getSiteDeviceInformation?${queryString}`).catch((err)=> {
        Log(logLevel.ERROR, `Failed to get devices for site ${site_name}: ${err}`);
        return -1;
    }).then((response)=> {
        if(response === -1) {
            return;
        }
        //process response
    });
}