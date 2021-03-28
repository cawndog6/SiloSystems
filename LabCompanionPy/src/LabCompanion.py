
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
    #config.serial = 6699
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
        time.sleep(3000)
        os.system("node signin.js")
        f = open(".idToken.txt", "r")
        config.tokenId = f.read()
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
#collects/uploads data to site database for each added parameter
def dataCollection():
    if config.tokenId is None:
        print("You must be logged in.")
        time.sleep(3)
        return
    #print(email)
    for p in config.myDeviceInfo['parameters']:
        p['errorPrinted'] = False
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
            os.system("python " + "scripts/" + parameterName + ".py" + "&> ./data/null")
            try:
                f = open("data/" + parameterName + ".txt", "r")
                contents = json.loads(f.read())
                for c in contents:
                    parameterEntry['readings'].append(c)
            except:
                if p['errorPrinted'] == False:
                    print("""Error: Cannot read parameter data for {}. Ensure that there exists a python script in scripts/ that writes to a file in data/ 
                        containing the data reading for the parameter. Both the script and file should have the exact same name as the parameter.""" .format(p['parameter_name']))
                    p['errorPrinted'] = True
            paramData.append(parameterEntry)
        #paramData = json.dumps(paramData)
        #print(paramData)
        requestHeader = config.header
        requestHeader['content-type'] = 'application/json'
        r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/upstreamHandler?site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" + str(config.myDeviceInfo['device_id']), json=paramData, headers=requestHeader)
        if not r.ok:
            print(r.text)
        paramData = [] #reset json string
        time.sleep(1)


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
    #selectedSite = addDeviceSubmenu.get_selection(site_names)
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
                settingsSubmenu.parent.prologue_text = "Connected to site [" + config.mySiteInfo['site_name'] + "]" + " as [" + config.myDeviceInfo['device_name'] + "]"
    #menu.prologue_text = "hi"
    #menu.draw()
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
        print("Connect this device to site before configuring parameters")
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
    addParamMenu.append_item(FunctionItem("Add a new parameter to this device", args=[addParamMenu], function=addNewParam))
    addParamMenu.append_item(FunctionItem("Remove a parameter from this device", args=[addParamMenu], function=removeParam))
    addParamMenu.show()

def addNewParam(menu): 
    #input: site_id, device_id, uid, parameter_name, data_val, data_type
    paramName = input("Enter a name for the new parameter: ")
    dataType = input("Enter this parameters data type (The mySQL data type eg. INTEGER, VARCHAR(20), etc)")
    r = requests.post("https://us-west2-silo-systems-292622.cloudfunctions.net/addParameterToDevice?parameter_name=" + paramName + "&data_val=reading" + "&data_type=" + dataType + "&site_id=" + str(config.mySiteInfo['site_id']) + "&device_id=" +  str(config.myDeviceInfo['device_id']), headers=config.header)

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
