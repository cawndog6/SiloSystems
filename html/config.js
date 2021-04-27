//This file contains API keys, static configurations, etc.

//what types of messages can be displayed in the login flow?
//MESSAGE should be displayed as ordinary text
//ERROR should be displayed with a color or other formatting to indicate that an action failed, and should end with something to the effect of "please try again"
//ERRORNOTRYAGAIN should be displayed like an ERROR, but should not include the "please try again" text (useful for fatal errors that shouldn't be tried again
const loginMessageLevel = {MESSAGE: 0, ERROR: 1, ERRORNOTRYAGAIN: 2};  

//console logging levels - DEBUG calls console.log, WARNING calls console.warn, ERROR calls console.error
const level = {DEBUG: 0, WARNING: 1, ERROR: 2};

//API config details from the Firebase console in project settings
const firebaseConfig = {
    apiKey: "AIzaSyDjyljriWPsr2qCz_CDi1X0apNzpsVdxMc",
    authDomain: "silo-systems-292622.firebaseapp.com",
    databaseURL: "https://silo-systems-292622.firebaseio.com",
    projectId: "silo-systems-292622",
    storageBucket: "silo-systems-292622.appspot.com",
    messagingSenderId: "664599356034",
    appId: "1:664599356034:web:962f6119ebaaece13f8a9b"
};

//root of cloud functions
const apiRoot = "https://us-west2-silo-systems-292622.cloudfunctions.net";

//default refresh frequency in milliseconds
let refreshFrequency = 10000;

//minimum logging level - any messages at or above this level will be handled; any below this level will be dropped
let logLevel = level.DEBUG;