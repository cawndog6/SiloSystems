//This file contains API keys, static configurations, etc.

const loginMessageLevel = {MESSAGE: 0, ERROR: 1, ERRORNOTRYAGAIN: 2};
const level = {DEBUG: 0, WARNING: 1, ERROR: 2};

const firebaseConfig = {
    apiKey: "AIzaSyDjyljriWPsr2qCz_CDi1X0apNzpsVdxMc",
    authDomain: "silo-systems-292622.firebaseapp.com",
    databaseURL: "https://silo-systems-292622.firebaseio.com",
    projectId: "silo-systems-292622",
    storageBucket: "silo-systems-292622.appspot.com",
    messagingSenderId: "664599356034",
    appId: "1:664599356034:web:962f6119ebaaece13f8a9b"
}; //This is from the Firebase Console in project settings

let apiRoot = "https://us-west2-silo-systems-292622.cloudfunctions.net";