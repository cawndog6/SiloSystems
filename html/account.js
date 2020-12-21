//################# INITIALIZATION ########################

let currentToken = undefined;

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

function SetUserCookies(user, token, remember) {
    let today = new Date();
    let todayPlus30 = new Date();
    todayPlus30.setDate(today.getDate()+30);

    if(remember) {
        document.cookie = `token=${token}; expires=${todayPlus30}`;
        document.cookie = `user=${user}; expires=${todayPlus30}`;
    } else {
        document.cookie = `token=${user}`;
        document.cookie = `user=${user}`;
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
        token = document.cookie.split("token=")[1].split(";")[0];
        let user = document.cookie.split("user=")[1].split(";")[0];
        userDisplay.innerHTML = `Currently logged in as <strong>${user}</strong>`;
        loginLink.classList.add("hidden");
        logoutLink.classList.remove("hidden");
    }
}

function ShowLoginError(err) {
    document.getElementById("login-box").classList.add("showLoginError");
    document.getElementById("login-error-box-text").innerText = err;
    document.getElementById("login-error-box").classList.remove("hidden");
}

function UnshowLoginError() {
    document.getElementById("login-box").classList.remove("showLoginError");
    document.getElementById("login-error-box").classList.add("hidden");
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

    auth.signInWithEmailAndPassword(user, password).catch(()=> {
        Log(level.WARNING, `Invalid login attempt for user ${user}`);
        ShowLoginError("Either your username or password was incorrect.");
    }).then((token)=> {
        if(token === undefined) {
            return;
        }
        console.log(token)
        Log(level.DEBUG, `Successful ${(remember) ? "persistent":"session"} login for user ${user}`);

        SetUserCookies(user, token, remember);

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

    UnshowLoginError();

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

    UnshowLoginError();

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

    if(password != passwordConfirmation) {
        ShowLoginError("The passwords you entered didn't match.");
        return;
    }

    auth.createUserWithEmailAndPassword(user, password).catch((err)=> {
        Log(level.WARNING, `Signup failed with a ${err.code} error`);

        if(err.message.substring(len(err.message)-1) == ".") {
            ShowLoginError(`Error: ${err.message}`);
        }
        else {
            ShowLoginError(`Error: ${err.message}.`);
        }
        return undefined;
    }).then((token)=> {
        if(token === undefined) {
            return;
        }

        Log(level.DEBUG, `Successful registration for user ${user}`);
        
        SetUserCookies(user, token, false);

        UpdateUserDisplay();
        UnshowLogin();
    });
}