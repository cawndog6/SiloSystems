
import os
import json
import time
import consolemenu
from consolemenu import *
from consolemenu.items import *
import config
import requests
import _thread
import datetime

def main():
    Screen.clear()
    os.system("node signin.js")
    f = open(".idToken.txt", "r")
    f2 = open(".userdata.txt", "r")
    config.tokenId = f.read()
    f.close
    if config.tokenId is None:
        print("User failed to sign in.")
        quit()
    userData = f2.read()
    if userData is not None:
        userData = json.loads(userData)
        config.email = userData['email']
    f2.close
    try: 
        _thread.start_new_thread(tokenUpdater, ())
    except:
        print("Error: Unable to start token updater thread")
    #create main menu
    menu = ConsoleMenu("Lab Companion", "Main Menu")
    # Create some items
    # MenuItem is the base class for all items, it doesn't do anything when selected
    #menu_item = MenuItem("Menu Item")
    # A CommandItem runs a console command
    #command_item = CommandItem("Run a console4
    #  command",  "touch hello.txt")
    # A SelectionMenu constructs a menu from a list of strings
    #selection_menu = SelectionMenu(["item1", "item2", "item3"])
    print("Fetching account data (this may take a while)...")
    config.serial = getserial()
    config.serial = int(config.serial, 16)
    #config.serial = 1557011288
    #print(availableSites)
    refreshConfig()
    if config.availableSites is not None:
        if config.myDeviceInfo is None:
            menu.prologue_text = "This device does not belong to a site. Enter device settings to add it to a site."
        else:
            menu.prologue_text = "Connected to site [" + config.mySiteInfo['site_name'] + "]" + " as [" + config.myDeviceInfo['device_name'] + "]"
    else:
        menu.prologue_text = "No sites are available for this user. Create a site on the web application to connect this device to."
        #print(s['site_name'])
    Screen.clear()
    #Create the menu
    #main menu
    if config.availableSites is not None:
        dataCollectItem = FunctionItem("Begin Data Collection", function=startDataCollectionThread)
        #settings submenu
        settingsSubmenu = ConsoleMenu("Lab Companion", "Device Settings", exit_option_text="Return To Main Menu")
    
        if config.mySiteInfo is not None:
            settingsSubmenu.append_item(FunctionItem("Change connected site (" + config.mySiteInfo['site_name'] + ")",args=[settingsSubmenu], function=addDeviceToSite))
            settingsSubmenu.append_item(FunctionItem("Remove device from site", function=removeDeviceFromSite))
            configureParamItem = FunctionItem("Configure this device's parameters", configureParameters)
            settingsSubmenu.append_item(configureParamItem)
            settingsSubmenu.append_item(FunctionItem("Configure this device's triggers", configureTriggers))
        else:
            settingsSubmenu.append_item(FunctionItem("Add device to site", args=[settingsSubmenu], function=addDeviceToSite))
        
        submenu_item = SubmenuItem("Device Settings", settingsSubmenu, menu)

        # Once we're done creating them, we just add the items to the menu
        menu.append_item(dataCollectItem)
        menu.append_item(submenu_item)
        
    # Finally, we call show to show the menu and allow the user to interact
    logOutItem = FunctionItem(text="Log Out (" + config.email + ")", args=[menu], function=signOut)
    menu.append_item(logOutItem)
    menu.show()
def tokenUpdater():
    while True:
        time.sleep(3480)
        os.system("node signin.js")
        f = open(".idToken.txt", "r")
        config.tokenId = f.read()
        config.header = {"Authorization": "Bearer {}".format(config.tokenId)}
        f.close

def refreshConfig():
    config.header = {"Authorization": "Bearer {}".format(config.tokenId)}
    r = requests.get('https://us-west2-silo-systems-292622.cloudfunctions.net/getAvailableSites', headers=config.header)
    if not r.ok:
        if r.status_code == 500:
            availableSites = r.text
    else: 
       config.availableSites = r.json()
    if config.availableSites['result'] is not None:
        for s in config.availableSites['result']:
            r = requests.get('https://us-west2-silo-systems-292622.cloudfunctions.net/getDeviceSiteInformation?site_id={}'.format(str(s['site_id'])), headers=config.header)
            if r.ok:
                siteDeviceInfo = r.json()
                for d in siteDeviceInfo['devices']:
                    if config.serial == d['device_id']:
                        config.mySiteInfo = s
                        config.myDeviceInfo = d
                        config.availableTriggers = siteDeviceInfo['availableTriggers']
                        config.availableParameters = siteDeviceInfo['availableParameters']
#Starts the collection/upload of data to the site's database
def startDataCollectionThread():
    Screen.clear()
    config.stopDataCollection = False
    _thread.start_new_thread(dataCollection, ()) 
    dataCollectionMenu = ConsoleMenu(title="Lab Companion", subtitle="Data Collection", prologue_text="Collecting and sending data to site [{}]".format(config.mySiteInfo['site_name']), exit_option_text="Back To Main Menu (Stops Data Collection)")
    dataCollectionMenu.show()
    #Above call^ blocks. Unblocks when menu exits. Stop data collection after menu exits
    stopDataCollectionThread()
    return
# Stops the collection/upload of data to the site's database
def stopDataCollectionThread():
    config.stopDataCollection = True
    return
#collects/uploads data to site database for each added parameter. Also handles triggers 
def dataCollection():
    if config.tokenId is None:
        print("You must be logged in.")
        time.sleep(3)
        return
    for p in config.myDeviceInfo['parameters']:
        p['errorPrinted'] = False
    for t in config.myDeviceInfo['triggers']:
        t['lastTriggerEvent'] = None #used to make sure an email trigger only happens once per hour to prevent flood of emails.
        t['errorPrinted'] = False
    paramData = []
    while True:
        if config.stopDataCollection == True:
            config.stopDataCollection = False
            _thread.exit()
        for p in config.myDeviceInfo['parameters']:
            parameterEntry = {}
            parameterName = p['parameter_name']
            parameterEntry['parameter_name'] = p['parameter_name']
            parameterEntry['parameter_id'] = p['parameter_id']
            parameterEntry['readings'] = []
            parameterEntry['date_time'] = str(datetime.datetime.now())
            #os.system("python3 " + "scripts/" + parameterName + ".py" + "&> ./data/null")
            os.system("python3 " + "scripts/" + parameterName + ".py")
            try:
                f = open("data/" + parameterName + ".txt", "r")
                contents = json.loads(f.read())
                for c in contents:
                    parameterEntry['readings'].append(c)
                    paramData.append(parameterEntry)
                requestHeader = config.header
                requestHeader['content-type'] = 'application/json'
                r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/upstreamHandler?site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" + str(config.myDeviceInfo['device_id']), json=paramData, headers=requestHeader)
                if not r.ok:
                    print(r.text)
                for t in config.myDeviceInfo['triggers']:
                    if t['parameter_id'] == parameterEntry['parameter_id']:
                        triggered = False
                        if t['relation_to_reading'] == ">":
                            if parameterEntry['readings'][0] > t['reading_value']:
                                triggered = True
                        elif t['relation_to_reading'] == ">=":
                            if parameterEntry['readings'][0] >= t['reading_value']:
                                triggered = True
                        elif t['relation_to_reading'] == "<":
                            if parameterEntry['readings'][0] < t['reading_value']:
                                triggered = True
                        elif t['relation_to_reading'] == "<=":
                            if parameterEntry['readings'][0] <= t['reading_value']:
                                triggered = True
                        elif t['relation_to_reading'] == "==":
                            if parameterEntry['readings'][0] == t['reading_value']:
                                triggered = True
                        if triggered:
                            currentTime = time.time()
                            if t['lastTriggerEvent'] is None or currentTime >= t['lastTriggerEvent'] +  3600:
                                _thread.start_new_thread(handleTrigger, (t, parameterEntry['readings'][0])) #process the trigger. Do it in a thread so it doesnt hold up the current thread.
            except:
                if p['errorPrinted'] == False:
                    print("""Error: Cannot read parameter data for {}. Ensure that there exists a python script in scripts/ that writes to a file in data/ 
                        containing the data reading for the parameter. Both the script and file should have the exact same name as the parameter.""" .format(p['parameter_name']))
                    p['errorPrinted'] = True
        paramData = [] #reset json string
        time.sleep(1)

def handleTrigger(trigger, latestReading):
    trigger['trigger_type'] = trigger['trigger_type'].lower()
    if trigger['trigger_type'] == "function":
        trigger['lastTriggerEvent'] = None #a function trigger should always fire, so keep this value "None". 
        result = os.system("python3 " + "triggers/" + trigger['action'] + ".py" + "&> ./data/null")
        if result != 0 and trigger['errorPrinted'] is False:
            print("Error calling function for trigger " + trigger['trigger_name'] + ".")
            print("Ensure a Python script exists with the name " + trigger['action'] + " in the directory src/triggers/.")
            trigger['errorPrinted'] == True
    elif trigger['trigger_type'] == "email":
        trigger['lastTriggerEvent'] = time.time() #an email trigger should only fire once per hour, so give this a value
        requestHeader = config.header
        requestHeader['content-type'] = 'application/json'
        r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/handleEmailTrigger?device_name=" + str(config.myDeviceInfo['device_name']) + "&current_reading=" + str(latestReading), json=trigger, headers=requestHeader)
#displays menu with list of available sites to add the Pi to
def addDeviceToSite(settingsSubmenu):
    Screen.clear()
    if config.tokenId is None:
        print("You must be logged in.")
        time.sleep(3)
        return
    #add device submenu
    site_names = []
    siteId = 0
    #addDeviceSubmenu = ConsoleMenu("Lab Companion", "Add Device To Site", exit_option_text="Return To Device Settings")
    for s in config.availableSites['result']:
        if config.mySiteInfo is None:
            site_names.append(str(s['site_name']))
        else:
            if s['site_name'] != config.mySiteInfo['site_name']:
                site_names.append(str(s['site_name']))


    addDeviceSubmenu = SelectionMenu(strings=site_names, title="Choose a site to connect this device to.")
    addDeviceSubmenu.show()
    selectedSite = addDeviceSubmenu.selected_item
    if addDeviceSubmenu.is_selected_item_exit() != True:
        if config.mySiteInfo is not None:
            decisionMenu = SelectionMenu(strings=["Yes", "No"], title="WARNING:", prologue_text="This action will remove this device from its current site [" + config.mySiteInfo['site_name'] + "]. All data from this device will be erased on the site's database. Do you want to continue?", show_exit_option=False)
            decisionMenu.show()
            decision = decisionMenu.selected_item
            if decision.text == "No":
                return
            else:
                for s in config.availableSites['result']:
                    if s['site_name'] == selectedSite.text:
                        siteId = s['site_id']
                newName = input("Enter a name for this device: ")
                r = removeDeviceFromSite()
                if r.ok:
                    r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/addDeviceToSite?" + "site_id=" + str(siteId) + "&device_name=" + newName + "&device_id=" + str(config.serial), headers=config.header)
                    print("Adding device to site...")
                    if r.ok:
                        refreshConfig()
                    else:
                        print("Error: Add device to site failed.")
                        print(r.text)
                        time.sleep(4)
                    itemsList = []
                    for i in settingsSubmenu.items:
                        itemsList.append(i)
                    for i in itemsList:
                        settingsSubmenu.remove_item(i)
                    settingsSubmenu.add_exit()
                    settingsSubmenu.append_item(FunctionItem("Change connected site (" + config.mySiteInfo['site_name'] + ")",args=[settingsSubmenu], function=addDeviceToSite))
                    settingsSubmenu.append_item(FunctionItem("Remove device from site", function=removeDeviceFromSite))
                    settingsSubmenu.append_item(FunctionItem("Configure this device's parameters", configureParameters))
                    settingsSubmenu.append_item(FunctionItem("Configure this device's triggers", configureTriggers))
                    settingsSubmenu.parent.prologue_text = "Connected to site [" + config.mySiteInfo['site_name'] + "]" + " as [" + config.myDeviceInfo['device_name'] + "]"
                    
                else:
                    print(r.text)
        else:
            for s in config.availableSites['result']:
                if s['site_name'] == selectedSite.text:
                    siteId = s['site_id']
            newName = input("Enter a name for this device: ")
            r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/addDeviceToSite?" + "site_id=" + str(siteId) + "&device_name=" + newName + "&device_id=" + str(config.serial), headers=config.header)
            print("\nAdding device to site...")
            if not r.ok:
                print("Error: Add device to site failed.")
                print(r.text)
                time.sleep(5)
            else:
                refreshConfig()
                itemsList = []
                for i in settingsSubmenu.items:
                    itemsList.append(i)
                for i in itemsList:
                    settingsSubmenu.remove_item(i)
                settingsSubmenu.add_exit()
                settingsSubmenu.append_item(FunctionItem("Change connected site (" + config.mySiteInfo['site_name'] + ")",args=[settingsSubmenu], function=addDeviceToSite))
                settingsSubmenu.append_item(FunctionItem("Remove device from site", function=removeDeviceFromSite))
                settingsSubmenu.append_item(FunctionItem("Configure this device's parameters", configureParameters))
                settingsSubmenu.append_item(FunctionItem("Configure this device's triggers", configureTriggers))
                settingsSubmenu.parent.prologue_text = "Connected to site [" + config.mySiteInfo['site_name'] + "]" + " as [" + config.myDeviceInfo['device_name'] + "]"
    #menu.prologue_text = "hi"
    #menu.draw()
def configureTriggers():
    if config.tokenId is None:
        print("You must be logged in.")
        time.sleep(3)
        return
    if config.mySiteInfo is None:
        print("Connect this device to a site before configuring triggers")
        time.sleep(3)
        return
    trigMenu = ConsoleMenu(title="Lab Companion", subtitle="Device Trigger Settings", exit_option_text="Return to Device Settings")
    if not config.myDeviceInfo['triggers']:
        trigMenu.prologue_text = "No triggers are currently attached."
    else:
        trigMenu.prologue_text = "Attached trigger(s): "
        first = True
        for t in config.myDeviceInfo['triggers']:
            if first:
                trigMenu.prologue_text = trigMenu.prologue_text + t['trigger_name']
                first = False
            else:
                trigMenu.prologue_text = trigMenu.prologue_text + ", " + t['trigger_name']
    trigMenu.append_item(FunctionItem("Add a trigger to this device", args=[trigMenu], function=addNewTrigger))
    trigMenu.append_item(FunctionItem("Remove a trigger from this device", args=[trigMenu], function=removeTrigger))
    trigMenu.append_item(FunctionItem("Delete a trigger from this site (removes from all devices)", args=[trigMenu], function=deleteTrigger))
    trigMenu.show()
# Adds a new trigger to the site/device or adds an existing trigger on the site to this device
def addNewTrigger(trigMenu):
    availableTrigs = []
    for t in config.availableTriggers:
        if not any(attached['trigger_id'] == t['trigger_id'] for attached in config.myDeviceInfo['triggers']):
            availableTrigs.append(t['trigger_name'])
    availableTrigs.append("Create New Trigger")
    addTrigMenu = SelectionMenu(strings=availableTrigs, title="Lab Companion", subtitle="Add trigger to this device", exit_option_text="Return to Trigger Settings")
    if not config.availableTriggers:
        addTrigMenu.prologue_text = "No available triggers. Select Create New Trigger to create one and add it to this device."
    else:
        addTrigMenu.prologue_text = "Select a trigger to add to this device or select Create New Trigger to create one and add it to this device. "
    addTrigMenu.show()
    selectedTrig = addTrigMenu.selected_item
    if addTrigMenu.is_selected_item_exit() != True:
        if selectedTrig.text == "Create New Trigger":
            trigger_name = input("Enter a name for the new trigger: ")
            trigger_type = input("Enter trigger type. (can be function or email): ")
            trigger_type = trigger_type.lower()
            if trigger_type == "function":
                action = input("Enter function name that should be executed when trigger occurs: ")
            else:
                action = input("Enter the email address to send an email to when trigger occurs: ")
            print("Parameter(s) available: ")
            for p in config.myDeviceInfo['parameters']: 
                print(p['parameter_name'])
            parameter_name = input("Enter Parameter that should be monitored: ")
            parameter_id = 0
            for p in config.myDeviceInfo['parameters']:
                if p['parameter_name'] == parameter_name:
                    parameter_id = p['parameter_id']
            reading_value = input("At what value should this trigger be executed?: ")
            print("Should this trigger occur when the current reading is >=, <=, >, <, or == to the specified trigger value?")
            relation_to_reading = input("Enter >=, <=, >, <, or == ")
            choice = input("Is the above information correct? Enter yes to add this trigger or no to return to the Trigger Configuration Menu.: ")
            choice = choice.lower()
            if choice == "yes":
                requests.post("""https://us-west2-silo-systems-292622.cloudfunctions.net/createTrigger?site_id={}&trigger_name={}&trigger_type={}&action={}&parameter_id={}&reading_value={}&relation_to_reading={}&add_to_device=true&device_id={}""".format(config.mySiteInfo['site_id'], trigger_name, trigger_type, action, parameter_id, reading_value, relation_to_reading, config.myDeviceInfo['device_id']), headers=config.header)
                print("Adding trigger...")
                refreshConfig()
                trigMenu.prologue_text = "Attached trigger(s):"
                first = True
                for t in config.myDeviceInfo['triggers']:
                    if first:
                        trigMenu.prologue_text = trigMenu.prologue_text + t['trigger_name']
                        first = False
                    else:
                        trigMenu.prologue_text = trigMenu.prologue_text + ", " + t['trigger_name']
        else:
            for t in config.availableTriggers:
                if t['trigger_name'] == selectedTrig.text:
                    r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/addTriggerToDevice?" + "site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" + str(config.myDeviceInfo['device_id']) + "&trigger_id=" + str(t['trigger_id']), headers=config.header)
                    print("Adding trigger...")
                    refreshConfig()
                    if not config.myDeviceInfo['triggers']:
                        trigMenu.prologue_text = "No triggers are currently attached."
                    else:                    
                        trigMenu.prologue_text = "Attached trigger(s):"
                        first = True
                        for t in config.myDeviceInfo['triggers']:
                            if first:
                                trigMenu.prologue_text = trigMenu.prologue_text + t['trigger_name']
                                first = False
                            else:
                                trigMenu.prologue_text = trigMenu.prologue_text + ", " + t['trigger_name']
# Removes a trigger from this device, but does not delete it from the site
def removeTrigger(trigMenu):
    availableTrigs = []
    for t in config.myDeviceInfo['triggers']:
        availableTrigs.append(t['trigger_name'])
    removeTrigMenu = SelectionMenu(strings=availableTrigs, title="Lab Companion", subtitle="Remove A Trigger From This Device", exit_option_text="Return to Trigger Settings")
    if not config.myDeviceInfo['triggers']:
        removeTrigMenu.prologue_text = "No triggers currently exist on this device. "
    else:
        removeTrigMenu.prologue_text = "Select a trigger to remove from this device. "
    removeTrigMenu.show()
    selectedTrig = removeTrigMenu.selected_item
    trigger_id = 0
    if removeTrigMenu.is_selected_item_exit() != True:
        for t in config.myDeviceInfo['triggers']:
            if t['trigger_name'] == selectedTrig.text:
                trigger_id = t['trigger_id']
        r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/removeTriggerFromDevice?site_id={}&device_id={}&trigger_id={}".format(str(config.mySiteInfo['site_id']), str(config.myDeviceInfo['device_id']), str(trigger_id)), headers = config.header)
        print("Removing Trigger...")
        refreshConfig()
        if not config.myDeviceInfo['triggers']:
            trigMenu.prologue_text = "No triggers are currently attached."
        else:
            trigMenu.prologue_text = "Attached trigger(s):"
            first = True
            for t in config.myDeviceInfo['triggers']:
                if first:
                    trigMenu.prologue_text = trigMenu.prologue_text + t['trigger_name']
                    first = False
                else:
                    trigMenu.prologue_text = trigMenu.prologue_text + ", " + t['trigger_name']
# Deletes a trigger from this site, which will remove it from all devices on the site
def deleteTrigger(trigMenu):
    availableTrigs = []
    for t in config.availableTriggers:
        availableTrigs.append(t['trigger_name'])
    removeTrigMenu = SelectionMenu(strings=availableTrigs, title="Lab Companion", subtitle="Delete A Trigger From This Site", exit_option_text="Return to Trigger Settings")
    if not config.availableTriggers:
        removeTrigMenu.prologue_text = "No triggers currently exist on this site. "
    else:
        removeTrigMenu.prologue_text = "Select a trigger to remove from this site. "
    removeTrigMenu.show()
    selectedTrig = removeTrigMenu.selected_item
    trigger_id = 0
    if removeTrigMenu.is_selected_item_exit() != True:
        for t in config.availableTriggers:
            if t['trigger_name'] == selectedTrig.text:
                trigger_id = t['trigger_id']
        decisionMenu = SelectionMenu(strings=["Yes", "No"], title="WARNING:", prologue_text="This action will delete this trigger from site [" + config.mySiteInfo['site_name'] + "]. It will be removed from all devices it is attached to. Do you want to continue?", show_exit_option=False)
        decisionMenu.show()
        decision = decisionMenu.selected_item
        if decision.text == "No":
            return
        else:
            r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/deleteTrigger?site_id={}&trigger_id={}".format(str(config.mySiteInfo['site_id']), str(trigger_id)), headers = config.header)
            print("Deleting trigger...")
            refreshConfig()
            if not config.myDeviceInfo['triggers']:
                trigMenu.prologue_text = "No triggers currently exist on this site."
            else:
                trigMenu.prologue_text = "Attached trigger(s):"
                first = True
                for t in config.availableTriggers:
                    if first:
                        trigMenu.prologue_text = trigMenu.prologue_text + t['trigger_name']
                        first = False
                    else:
                        trigMenu.prologue_text = trigMenu.prologue_text + ", " + t['trigger_name']
# Removes this device from the site
def removeDeviceFromSite():
    Screen.clear()
    if config.tokenId is None:
        print("You must be logged in.")
        time.sleep(3)
        return
    r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/removeDeviceFromSite?" + "site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" + str(config.serial), headers=config.header)
    print("\nAdding device...")
    if not r.ok:
        print(r.text)
        time.sleep(2)
    return r
def configureParameters():
    if config.tokenId is None:
        print("You must be logged in.")
        time.sleep(3)
        return
    if config.mySiteInfo is None:
        print("Connect this device to a site before configuring parameters")
        time.sleep(3)
        return
    addParamMenu = ConsoleMenu(title="Lab Companion", subtitle="Device Parameter Settings", exit_option_text="Return to Device Settings")
    if not config.myDeviceInfo['parameters']:
        addParamMenu.prologue_text = "No parameters are currently attached."
    else:
        addParamMenu.prologue_text = "Attached parameter(s):  "
        first = True
        for p in config.myDeviceInfo['parameters']:
            if first:
                addParamMenu.prologue_text = addParamMenu.prologue_text + p['parameter_name']
                first = False
            else:
                addParamMenu.prologue_text = addParamMenu.prologue_text + ", " + p['parameter_name']
    addParamMenu.append_item(FunctionItem("Add a parameter to this device", args=[addParamMenu], function=addNewParam))
    addParamMenu.append_item(FunctionItem("Remove a parameter from this device", args=[addParamMenu], function=removeParam))
    addParamMenu.show()
# Create and/or add a new parameter to this device.
def addNewParam(menu): 
    availableParams = []
    for t in config.availableParameters:
        if not any(attached['parameter_id'] == t['parameter_id'] for attached in config.myDeviceInfo['parameters']):
            availableParams.append(t['parameter_name'])
    availableParams.append("Create New Parameter")
    addParamMenu = SelectionMenu(strings=availableParams, title="Lab Companion", subtitle="Add parameter to this device", exit_option_text="Return to Parameter Settings")
    if not config.availableParameters:
        addParamMenu.prologue_text = "No available parameters. Select Create New Parameter to create one and add it to this device."
    else:
        addParamMenu.prologue_text = "Select a parameter to add to this device or select Create New Parameter to create one and add it to this device. "
    addParamMenu.show()
    selectedParam = addParamMenu.selected_item
    if addParamMenu.is_selected_item_exit() != True:
        if selectedParam.text == "Create New Parameter":
            #input: site_id, device_id, uid, parameter_name, data_val, data_type
            paramName = input("Enter a name for the new parameter: ")
            dataType = input("Enter this parameters data type (The mySQL data type eg. INTEGER, VARCHAR(20), etc) ")
            choice = input("Is the above information correct? Enter \"yes\" to add this parameter to the site or \"no\" to return to the Parameter Configuration Menu. ")
            if choice.lower() == "yes":
                dataType = dataType.upper()
                r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/addParameterToDevice?parameter_name=" + paramName + "&data_type=" + dataType + "&site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" +  str(config.myDeviceInfo['device_id']) + "&parameter_exists=false", headers=config.header)
            else:
                return
        else:
            paramName = selectedParam.text
            r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/addParameterToDevice?parameter_name=" + paramName + "&site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" +  str(config.myDeviceInfo['device_id']) + "&parameter_exists=true", headers=config.header)
        print("Adding parameter...")
        refreshConfig()
        if not r.ok:
            print(r.text)
            time.sleep(4)
        if not config.myDeviceInfo['parameters']:
            menu.prologue_text = "No parameters are currently attached."
        else:
            menu.prologue_text = "Attached parameter(s):  "
            first = True
            for p in config.myDeviceInfo['parameters']:
                if first:
                    menu.prologue_text = menu.prologue_text + p['parameter_name']
                    first = False
                else:
                    menu.prologue_text = menu.prologue_text + ", " + p['parameter_name']
#Remove a parameter from this device
def removeParam(menu):
    Screen.clear()
    if not config.myDeviceInfo['parameters']:
        print("No parameters are currently attached to this device.")
        time.sleep(4)
        return
    else:
        deviceParams = []
        for p in config.myDeviceInfo['parameters']:
            deviceParams.append(p['parameter_name'])
    removeParamMenu = SelectionMenu(strings=deviceParams, title="Choose a parameter to remove from this device")
    removeParamMenu.show()
    selectedParam = removeParamMenu.selected_item
    if removeParamMenu.is_selected_item_exit() != True:
        for p in config.myDeviceInfo['parameters']:
            if p['parameter_name'] == selectedParam.text:
                paramId = p['parameter_id']
        r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/removeParameterFromDevice?parameter_id=" + str(paramId) + "&site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" +  str(config.myDeviceInfo['device_id']), headers = config.header)
        print("Removing parameter...")
        if not r.ok:
            print("Error: " + r.text)
            time.sleep(4)
        refreshConfig()
    if not config.myDeviceInfo['parameters']:
        menu.prologue_text = "No parameters are currently attached."
    else:
        menu.prologue_text = "Attached parameter(s):  "
        first = True
        for p in config.myDeviceInfo['parameters']:
            if first:
                menu.prologue_text = menu.prologue_text + p['parameter_name']
                first = False
            else:
                menu.prologue_text = menu.prologue_text + ", " + p['parameter_name']
#Sign a user out of their Firebase Account
def signOut(menu):
    Screen.clear()
    os.system("node signin.js signout")
    menu.remove_item(menu.selected_item)
    menu.append_item(FunctionItem("Log In", args=[menu], function=signIn))
    config.email = None
    config.tokenId = None
    config.myDeviceInfo = None
    config.mySiteInfo = None
    config.availableSites = None
    #menu.show()
    menu.prologue_text = "Sign into your Lab Companion account"
    menu.draw()
# Sign a user into their Firebase Account
def signIn(menu):
    Screen.clear()
    os.system("node signin.js")
    time.sleep(1)
    f = open(".idToken.txt", "r")
    f2 = open(".userdata.txt", "r")
    config.tokenId = f.read()
    f.close
    if config.tokenId is None:
        print("User failed to sign in.")
        quit()
    userData = f2.read()
    if userData is not None:
        userData = json.loads(userData)
        config.email = userData['email']
    f2.close
    refreshConfig()
    menu.remove_item(menu.selected_item)
    menu.append_item(FunctionItem("Log Out (" + config.email + ")", args=[menu], function=signOut))
    if config.availableSites is not None:
        if config.myDeviceInfo is None:
            menu.prologue_text = "This device does not belong to a site. Enter device settings to add it to a site."
        else:
            menu.prologue_text = "Connected to site [" + config.mySiteInfo['site_name'] + "]" + " as [" + config.myDeviceInfo['device_name'] + "]"
    else:
        menu.prologue_text = "No sites are available for this user. Create a site on the web application to connect this device to."
    menu.draw()
def getserial():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "0"

  return cpuserial

if __name__ == "__main__":
    main()
