//This file contains functions for user account creation, login, and other account functions

//################# INITIALIZATION ########################

let currentToken = undefined;
let currentSite = undefined;
const loginMessageLevel = {MESSAGE: 0, ERROR: 1, ERRORNOTRYAGAIN: 2}

//initialize Firebase authentication
const firebaseConfig = {
    apiKey: "AIzaSyDjyljriWPsr2qCz_CDi1X0apNzpsVdxMc",
    authDomain: "silo-systems-292622.firebaseapp.com",
    databaseURL: "https://silo-systems-292622.firebaseio.com",
    projectId: "silo-systems-292622",
    storageBucket: "silo-systems-292622.appspot.com",
    messagingSenderId: "664599356034",
    appId: "1:664599356034:web:962f6119ebaaece13f8a9b"
}; //This is from the Firebase Console in project settings

firebase.initializeApp(firebaseConfig);
//create auth reference
const auth = firebase.auth();

//################# COMMON FUNCTIONS ######################

function SetUserCookies(user, token, site, remember) {
    let today = new Date();
    let todayPlus30 = new Date();
    todayPlus30.setDate(today.getDate()+30);
    let expireString = "";
    if(remember) {
        expireString = `; expires=${todayPlus30}`;
    }

    if(token !== undefined) {
        document.cookie = `token=${token}${expireString}`;
        currentToken = token;
    }

    if(user !== undefined) {
        document.cookie = `user=${user}${expireString}`;
    }
    
    if(site !== undefined) {
        document.cookie = `site=${site}${expireString}`;
    }
}

function UpdateUserDisplay() {
    let userDisplay = document.getElementById("current-user");
    let loginLink = document.getElementById("show-login-link");
    let logoutLink = document.getElementById("logout-link");

    if(document.cookie.indexOf("user=") == -1) {
        userDisplay.innerText = "You are not logged in. ";
        loginLink.classList.remove("hidden");
        logoutLink.classList.add("hidden");
    } else {
        currentToken = document.cookie.split("token=")[1].split(";")[0];
        let user = document.cookie.split("user=")[1].split(";")[0];
        userDisplay.innerHTML = `Currently logged in as <strong>${user}</strong>`;
        loginLink.classList.add("hidden");
        logoutLink.classList.remove("hidden");
    }
}

function ShowLoginMessage(err, level) {
    let loginMessageBox = document.getElementById("login-message-box");

    document.getElementById("login-box").classList.add("showLoginMessage");

    let messageNode = document.createTextNode(err);
    let brNode = document.createElement("br");
    let errorNode = document.createTextNode("Please try again.");

    switch(level) {
        case loginMessageLevel.MESSAGE:
            loginMessageBox.appendChild(messageNode);
            break;
        case loginMessageLevel.ERROR:
            loginMessageBox.appendChild(messageNode);
            loginMessageBox.appendChild(brNode);
            loginMessageBox.appendChild(errorNode);
            loginMessageBox.style.color = "red";
            break;
        case loginMessageLevel.ERRORNOTRYAGAIN:
            loginMessageBox.appendChild(messageNode);
            loginMessageBox.style.color = "red";
            break;
    }

    loginMessageBox.classList.remove("hidden");
}

function UnshowLoginMessage() {
    document.getElementById("login-box").classList.remove("showLoginMessage");

    let loginMessageBox = document.getElementById("login-message-box");

    Array.from(loginMessageBox.childNodes).forEach((node)=>node.remove());

    loginMessageBox.classList.add("hidden");
}

//################# LOGIN FUNCTIONS #######################

function ShowLogin() {
    let template = document.getElementsByTagName("template")[0];
    let login = template.content.getElementById("login").cloneNode(true);
    document.body.appendChild(login);

    document.getElementById("login-form").elements.user.focus();
}

function UnshowLogin() {
    document.body.classList.remove("noScroll");
    let login = document.getElementById("login");
    login.remove();
}

function Login() {
    let form = document.getElementById("login-form");

    let user = form.elements.user.value;
    let password = form.elements.password.value;
    let remember = form.elements.remember.checked;

    UnshowLoginMessage();

    auth.signInWithEmailAndPassword(user, password).catch(()=> {
        Log(level.WARNING, `Invalid login attempt for user ${user}`);
        ShowLoginMessage("Either your username or password was incorrect.", loginMessageLevel.ERROR);
    }).then((token)=> {
        if(token === undefined) {
            return;
        }
        console.log(token)
        Log(level.DEBUG, `Successful ${(remember) ? "persistent":"session"} login for user ${user}`);

        SetUserCookies(user, token.user.refreshToken, undefined, remember);

        UpdateUserDisplay();
        UnshowLogin();
    });
}

function Logout() {
    auth.signOut().then(()=> {
        document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie = "user=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        window.location.reload();
    });
}

//################# SIGNUP FUNCTIONS ######################

function ShowSignup() {
    let loginForm = document.getElementById("login-form");
    let signupForm = document.getElementById("signup-form");

    let user = loginForm.elements.user.value;
    signupForm.elements.user.value = user;

    let password = loginForm.elements.password.value;
    signupForm.elements.password.value = password;

    loginForm.classList.add("hidden");
    signupForm.classList.remove("hidden");

    UnshowLoginMessage();

    if(user == "") {
        signupForm.elements.user.focus();
    }
    else if(password == "") {
        signupForm.elements.password.focus();
    } else {
        signupForm.elements.passwordConfirmation.focus();   
    }
}

function UnshowSignup() {
    let loginForm = document.getElementById("login-form");
    let signupForm = document.getElementById("signup-form");

    let user = signupForm.elements.user.value;
    loginForm.elements.user.value = user;

    let password = signupForm.elements.password.value;
    loginForm.elements.password.value = password;

    signupForm.elements.passwordConfirmation.value = "";

    loginForm.classList.remove("hidden");
    signupForm.classList.add("hidden");

    UnshowLoginMessage();

    if(user == "" || (user != "" && password != "")) {
        loginForm.elements.user.focus();
    }
    else {
        loginForm.elements.password.focus();
    }
}

function Signup() {
    let form = document.getElementById("signup-form");

    let user = form.elements.user.value;
    let password = form.elements.password.value;
    let passwordConfirmation = form.elements.passwordConfirmation.value;

    UnshowLoginMessage();

    if(password != passwordConfirmation) {
        ShowLoginMessage("The passwords you entered didn't match.", loginMessageLevel.ERROR);
        return;
    }

    auth.createUserWithEmailAndPassword(user, password).catch((err)=> {
        Log(level.WARNING, `Signup failed with a ${err.code} error`);

        err = JSON.parse(err.message);

        if(err.error.message.substring(err.error.message.length-1) == ".") {
            ShowLoginMessage(`Error: ${err.error.message}`, loginMessageLevel.ERROR);
        }
        else {
            ShowLoginMessage(`Error: ${err.error.message}.`, loginMessageLevel.ERROR);
        }
        return undefined;
    }).then((token)=> {
        if(token === undefined) {
            return;
        }

        Log(level.DEBUG, `Successful registration for user ${user}`);
        
        SetUserCookies(user, token, undefined, false);

        UpdateUserDisplay();
        UnshowLogin();
    });
}

//################# PASSWORD RESET FUNCTIONS ##############

function RequestPasswordReset() {
    let loginForm = document.getElementById("login-form");
    let resetForm = document.getElementById("reset-form");
    let user = loginForm.elements.user.value;

    UnshowLoginMessage();

    if(user.length < 1) {
        ShowLoginMessage("Please enter your email address and try again.", loginMessageLevel.ERRORNOTRYAGAIN);
        return;
    }

    auth.sendPasswordResetEmail(user).catch((err)=> {
        Log(level.WARNING, `Reset request failed with a ${err.code} error`);

        if(err.message.substring(err.message.length-1) == ".") {
            ShowLoginMessage(`Error: ${err.message}`, loginMessageLevel.ERROR);
        }
        else {
            ShowLoginMessage(`Error: ${err.message}.`, loginMessageLevel.ERROR);
        }

        return -1;
    }).then((status)=> {
        if(status == -1) {
            return;
        }

        Log(level.DEBUG, `Successful reset request for user ${user}`);
        
        resetForm.classList.remove("hidden");
        loginForm.classList.add("hidden");
    })
}

function ConfirmPasswordReset() {
    let loginForm = document.getElementById("login-form");
    let resetForm = document.getElementById("reset-form");

    let code = resetForm.elements.code.value;
    let password = resetForm.elements.password.value;
    let passwordConfirmation = resetForm.elements.passwordConfirmation.value;

    UnshowLoginMessage();

    if(password != passwordConfirmation) {
        ShowLoginMessage("The passwords you entered didn't match.", loginMessageLevel.ERROR);
        return;
    }

    auth.confirmPasswordReset(code, password).catch((err)=> {
        Log(level.WARNING, `Reset confirmation failed with a ${err.code} error`);

        if(err.message.substring(err.message.length-1) == ".") {
            ShowLoginMessage(`Error: ${err.error.message}`, loginMessageLevel.ERROR);
        }
        else {
            ShowLoginMessage(`Error: ${err.error.message}.`, loginMessageLevel.ERROR);
        }

        return -1;
    }).then(()=> {
        if(status == -1) {
            return;
        }

        Log(level.DEBUG, `Password successfully reset`);
        
        resetForm.classList.remove("hidden");
        loginForm.classList.add("hidden");

        resetForm.elements.user.value = user;

        ShowLoginMessage("Password successfully reset.<br>Please log in using your new password.", loginMessageLevel.MESSAGE);

        setTimeout(()=>window.location.reload(), 3000);
    })
}

function UnshowReset() {
    let loginForm = document.getElementById("login-form");
    let resetForm = document.getElementById("reset-form");

    loginForm.classList.remove("hidden");
    resetForm.classList.add("hidden");
}