var firebase = require("firebase/app");
var fs = require('fs');
var userDataFile = './.userdata.txt';
var idTokenFile = './.idToken.txt';
require("firebase/auth");
var prompt = require('prompt');
var email = "email";
var password = "password";
var firebaseConfig = {
    apiKey: "AIzaSyAfOt45U844Kk5NpL87m73hY9NQJvMLzGY",
    authDomain: "silo-systems-292622.firebaseapp.com",
    databaseURL: "https://silo-systems-292622.firebaseio.com",
    projectId: "silo-systems-292622",
    storageBucket: "silo-systems-292622.appspot.com",
    messagingSenderId: "664599356034",
    appId: "1:664599356034:web:2fcb0086fa058e0f3f8a9b"
  };
  // Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth()
//Attempt to read user data for last signed in user (for persistent login, so user does not have to sign in each time the application is run)
var args = process.argv.slice(2);
if (args[0] == 'signout') {
  fs.readFile(userDataFile, 'utf8', function(err, data) {
    if(err) {
      //Wrote the code this way in all readfiles to help with debugging. We don't really need to do anything if a file failed to be read, as the contents will be erased anyways
      fs.writeFile(userDataFile, "", function(err) {
        if(err) {
          console.error("ERROR: Failed to write to file. ", err)
        }})
      fs.writeFile(idTokenFile, "", function(err) {
        if(err) {
          console.error("ERROR: Failed to write to file. ", err)
        }})
    }
    else {
      if (data != "") {
        const userJSON = JSON.parse(data)
        const user = new firebase.User(userJSON, userJSON.stsTokenManager, userJSON);
        auth.updateCurrentUser(user).then(function() {
          //if there is data, attempt to validate it and get an idToken to use for API calls. If data is bad or DNE, call signUserIn to get valid data
          if(auth.currentUser) { 
            firebase.auth().signOut().then(() => {
              // Sign-out successful.
              fs.writeFile(userDataFile, "", function(err) {
                if(err) {
                  console.error("ERROR: Failed to write to file. ", err)
                }})
              fs.writeFile(idTokenFile, "", function(err) {
                if(err) {
                  console.error("ERROR: Failed to write to file. ", err)
                }})
            }).catch((error) => {
              // An error happened signing out. Still erase contents of user and token files
              fs.writeFile(userDataFile, "", function(err) {
                if(err) {
                  console.error("ERROR: Failed to write to file. ", err)
                }})
              fs.writeFile(idTokenFile, "", function(err) {
                if(err) {
                  console.error("ERROR: Failed to write to file. ", err)
                }})
            });
          }
          //The user in userDataFile may have had bad info, was out of data, or corrupt
          else {
            fs.writeFile(userDataFile, "", function(err) {
              if(err) {
                console.error("ERROR: Failed to write to file. ", err)
              }})
            fs.writeFile(idTokenFile, "", function(err) {
              if(err) {
                console.error("ERROR: Failed to write to file. ", err)
              }})
          }
        })
      } else {
        fs.writeFile(userDataFile, "", function(err) {
          if(err) {
            console.error("ERROR: Failed to write to file. ", err)
          }})
        fs.writeFile(idTokenFile, "", function(err) {
          if(err) {
            console.error("ERROR: Failed to write to file. ", err)
          }})
      }
    }
  });
} else {
  fs.readFile(userDataFile, 'utf8', function(err, data) {
    if(err) {
        signUserIn();
    }
    else {
      if (data != "") {
        const userJSON = JSON.parse(data)
        const user = new firebase.User(userJSON, userJSON.stsTokenManager, userJSON);
        auth.updateCurrentUser(user).then(function() {
          //if there is data, attempt to validate it and get an idToken to use for API calls. If data is bad or DNE, call signUserIn to get valid data
          if(auth.currentUser) {
            auth.currentUser.getIdToken(true).then((function(idToken) {
            fs.writeFile(idTokenFile, idToken, function(err) {
            if(err) {
              console.error("ERROR: Failed to write to file. ", err)
            }})
            })).catch(function(error) {
            //data stored in userDataFile was likely out of date or corrupt and user must sign in again
            signUserIn();
            })
          }
          //data stored in userDataFile was likely out of data or corrupt and user must sign in again
          else {
            signUserIn();
        }
      })} else {
        //File [userDataFile] was empty and user must sign in again
        signUserIn()
      }
    }
  });
  
}

//call this to sign a user in
function signUserIn() {
  prompt.start()
  prompt.get([{
    name: 'Email',
    required: true
  }, {
    name: 'Password',
    hidden: true,
    conform: function (value) {
      return true;
    }
  }], function(err, result) {
  auth.signInWithEmailAndPassword(result.Email, result.Password)
  .then((userCredential) => {
    var user = userCredential.user;
    const userJSON = JSON.stringify(auth.currentUser.toJSON())
    fs.writeFile(userDataFile, userJSON, function(err) {
      if (err) {
        console.error("ERROR: Failed to write to file. ", err)
      }
    })
    auth.currentUser.getIdToken(true).then((function(idToken) {
      fs.writeFile(idTokenFile, idToken, function(err) {
        if(err) {
          console.error("ERROR: Failed to write to file. ", err)
        }
      })
    })).catch(function(error) {
      //data stored in userDataFile was likely out of date or corrupt and user must sign in again
      fs.writeFile(idTokenFile, "", function(err) {
        if(err) {
          console.error("ERROR: Failed to write to file. ", err)
        }
      })
      fs.writeFile(userDataFile, "", function(err) {
        if(err) {
          console.error("ERROR: Failed to write to file. ", err)
        }
      })
      signUserIn();
    })
  })
  .catch((error) => {
    var errorCode = error.code;
    var errorMessage = error.message;
    console.log(errorMessage)
    signUserIn();
  })});
}