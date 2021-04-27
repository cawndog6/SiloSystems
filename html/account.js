//This file contains functions for user account creation, login, and other account functions

//################# INITIALIZATION ########################

let currentSite = undefined;

//initialize Firebase authentication
firebase.initializeApp(firebaseConfig);

//create auth reference
const auth = firebase.auth();

//################# COMMON FUNCTIONS ######################

function UpdateUserDisplay() {
    //update the text in the top right of the screen to display the current username if the user is logged in, or a link to log in otherwise
    let userDisplay = document.getElementById("current-user");
    let loginLink = document.getElementById("show-login-link");
    let loggedInLinks = document.getElementById("logged-in-links");

    if(auth.currentUser === null) {
        userDisplay.innerText = "You are not logged in. ";
        loginLink.classList.remove("hidden");
        loggedInLinks.classList.add("hidden");
    } else {
        userDisplay.innerHTML = `Currently logged in as <strong>${auth.currentUser.email}</strong>`;
        loginLink.classList.add("hidden");
        loggedInLinks.classList.remove("hidden");
    }
}

function ShowLoginMessage(err, level) {
    //add a message with text from err to the bottom of the login box
    //the value of level controls how this message is displayed
    //the options for level are detailed in config.js
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
    //remove a previously displayed login message from the DOM
    document.getElementById("login-box").classList.remove("showLoginMessage");

    let loginMessageBox = document.getElementById("login-message-box");

    Array.from(loginMessageBox.childNodes).forEach((node)=>node.remove());

    loginMessageBox.classList.add("hidden");
}

//################# LOGIN FUNCTIONS #######################

function ShowLogin() {
    //display the login box (which contains login fields by default, but can also contain signup fields)
    let template = document.getElementsByTagName("template")[0];
    let login = template.content.getElementById("login").cloneNode(true);
    document.body.appendChild(login);

    document.getElementById("login-form").elements.user.focus();
}

function UnshowLogin() {
    //remove the login box from the DOM
    document.body.classList.remove("noScroll");
    let login = document.getElementById("login");
    login.remove();
}

function Login() {
    //attempt logging in the user with the provided credentials
    //if login is successful, then UpdateUserDisplay, LoadSiteList, LoadSensorTable, and UnshowLogin
    //otherwise, display an error to the user
    let form = document.getElementById("login-form");

    let user = form.elements.user.value;
    let password = form.elements.password.value;
    let remember = form.elements.remember.checked;

    UnshowLoginMessage();

    auth.signInWithEmailAndPassword(user, password).catch((err)=> {
        Log(level.WARNING, `Invalid login attempt for user ${user}`);
        switch(err.code) {
            case "auth/invalid-email":
                ShowLoginMessage("Your username seems to be invalid.", loginMessageLevel.ERROR);
                break;
            case "auth/user-disabled":
                ShowLoginMessage("Your account has been disabled. Please contact your administrator.", loginMessageLevel.ERRORNOTRYAGAIN);
                break;
            case "auth/user-not-found":
                ShowLoginMessage("Your username was not found in the system.", loginMessageLevel.ERROR);
                break;
            case "auth/wrong-password":
                ShowLoginMessage("Either your username or password was incorrect.", loginMessageLevel.ERROR);
                break;
            default:
                ShowLoginMessage(err.message, loginMessageLevel.ERROR);
                break;
        }
    }).then((token)=> {
        if(token === undefined) {
            return;
        }

        Log(level.DEBUG, `Successful ${(remember) ? "persistent":"session"} login for user ${user}`);

        ShowLoading();

        if(remember) {
            auth.setPersistence("local");
        }
        else {
            auth.setPersistence("session");
        }

        UpdateUserDisplay();
        LoadSiteList().then(LoadSensorTable);
        UnshowLogin();

        UnshowLoading();
    });
}

function Logout() {
    //log the current user out locally and on the server, then reload the page
    auth.signOut().then(()=> {
        window.location.reload();
    });
}

//################# SIGNUP FUNCTIONS ######################

function ShowSignup() {
    //replace the contents of the login box (which should already be visible) with the fields necessary to sign up a new user
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
    //replace the contents of the login box [which should already be both visible and full of signup fields due to ShowSignup()] with its original login fields
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

async function CreateNewUser(user) {
    //attempt to add a new user to the database. They must have already been created with Firebase using Signup()
    let email = encodeURIComponent(user);

    let queryString = `email=${email}`;

    return await Get(`${apiRoot}/createNewUser?${queryString}`, false).catch((err)=> {
        Log(logLevel.ERROR, `Failed to add user ${email} to user database: ${err}`);
        return -1;
    }).then((response)=> {
        return response;
    });
}

function Signup() {
    //add a new user to Firebase
    //CreateNewUser should be called after signing up a new user to add them to the local database
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

        switch(err.code) {
            case "auth/email-already-in-use":
                ShowLoginMessage("An account associated with that username already exists. Please choose a different username or try logging in instead.", loginMessageLevel.ERRORNOTRYAGAIN);
                break;
            case "auth/invalid-email":
                ShowLoginMessage("Your username seems to be invalid.", loginMessageLevel.ERROR);
                break;
            case "auth/weak-password":
                ShowLoginMessage("Your password needs to be stronger. Add more complex characters and avoid simple phrases.", loginMessageLevel.ERROR);
                break;
            default:
                ShowLoginMessage(err.message, loginMessageLevel.ERROR);
                break;
        }

        return undefined;
    }).then((token)=> {
        if(token === undefined) {
            return;
        }

        Log(level.DEBUG, `Successful registration for user ${user}`);

        auth.setPersistence("session"); //user is automatically logged in after account creation

        CreateNewUser(user);    //add user to site database

        UpdateUserDisplay();
        UnshowLogin();
    });
}

//################# PASSWORD RESET FUNCTIONS ##############

function RequestPasswordReset() {
    //send a password reset code to the requested user's email address
    let loginForm = document.getElementById("login-form");
    let resetForm = document.getElementById("reset-form");
    let user = loginForm.elements.user.value;

    UnshowLoginMessage();

    if(user.length < 1) {
        ShowLoginMessage("Please enter your email address and try again.", loginMessageLevel.ERRORNOTRYAGAIN);
        return;
    }

    auth.sendPasswordResetEmail(user, null).catch((err)=> {
        Log(level.WARNING, `Reset request failed with a ${err.code} error`);

        switch(err.code) {
            case "auth/invalid-email":
                ShowLoginMessage("Your username seems to be invalid.", loginMessageLevel.ERROR);
                break;
            case "auth/user-not-found":
                ShowLoginMessage("Your username was not found in the system.", loginMessageLevel.ERROR);
                break;
            default:
                ShowLoginMessage(err.message, loginMessageLevel.ERROR);
                break;
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
    //attempt to validate a password reset code requested using RequestPasswordReset()
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

        switch(err.code) {
            case "auth/expired-action-code":
                ShowLoginMessage("Your password reset code has expired. Please start the password reset process again.", loginMessageLevel.ERRORNOTRYAGAIN);
                break;
            case "auth/invalid-action-code":
                ShowLoginMessage("Your password reset code is incorrect.", loginMessageLevel.ERROR);
                break;
            case "auth/user-disabled":
                ShowLoginMessage("Your account has been disabled. Please contact your administrator.", loginMessageLevel.ERRORNOTRYAGAIN);
                break;
            case "auth/user-not-found":
                ShowLoginMessage("Your username was not found in the system. Please start the password reset process again.", loginMessageLevel.ERRORNOTRYAGAIN);
                break;
            case "auth/weak-password":
                ShowLoginMessage("Your password needs to be stronger. Add more complex characters and avoid simple phrases.", loginMessageLevel.ERROR);
                break;
            default:
                ShowLoginMessage(err.message, loginMessageLevel.ERROR);
                break;
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
    //replace the contents of the login box with the login form, hiding the password reset form
    let loginForm = document.getElementById("login-form");
    let resetForm = document.getElementById("reset-form");

    loginForm.classList.remove("hidden");
    resetForm.classList.add("hidden");
}