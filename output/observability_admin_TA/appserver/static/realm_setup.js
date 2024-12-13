// used from https://github.com/splunk/splunk-app-examples/blob/master/setup_pages/weather_app_example/appserver/static/javascript/views/storage_passwords.js

const appName = "observability_admin_TA";
const appNamespace = {
    owner: "nobody",
    app: appName,
    sharing: "app",
};
const http = new splunkjs.SplunkWebHttp();
const service = new splunkjs.Service(
    http,
    appNamespace,
);
var storagePasswords = service.storagePasswords();
// storagePasswords.create({
//     name: "user1", 
//     realm: "realm1", 
//     password: "password1"}, 
//     function(err, storagePassword) {
//         if (err) 
//             {console.warn(err);}
//         else {
//         // Secret was created successfully
//         console.log(storagePassword.properties());
//         }
//     });


async function write_secret(
  splunk_js_sdk_service,
  realm,
  name,
  secret,
) {
  // /servicesNS/<NAMESPACE_USERNAME>/<SPLUNK_APP_NAME>/storage/passwords/<REALM>%3A<NAME>%3A
  var storage_passwords_accessor = splunk_js_sdk_service.storagePasswords();
  storage_passwords_accessor = await promisify(storage_passwords_accessor.fetch)()

  var password_exists = does_storage_password_exist(
    storage_passwords_accessor,
    realm,
    name,
  );

  if (password_exists) {
    delete_storage_password(
        storage_passwords_accessor,
        realm,
        name,
    );

  }

  // wait for password to be deleted
  while (password_exists) {
    storage_passwords_accessor = await promisify(storage_passwords_accessor.fetch)();

    password_exists = does_storage_password_exist(
      storage_passwords_accessor,
      realm,
      name,
    );
  }

  await create_storage_password_stanza(
      storage_passwords_accessor,
      realm,
      name,
      secret,
  );
}

function does_storage_password_exist(
  storage_passwords_accessor,
  realm,
  name,
) {
  var storage_passwords = storage_passwords_accessor.list();
  const password_id = realm + ":" + name + ":";

  for (var index = 0; index < storage_passwords.length; index++) {
    if (storage_passwords[index].name === password_id) {
      return true
    }
  }
  return false
};


function delete_storage_password(
  storage_passwords_accessor,
  realm,
  name,
) {
  // can't be promisified, for some reason
  return storage_passwords_accessor.del(realm + ":" + name + ":");
};

function create_storage_password_stanza(
  storage_passwords_accessor,
  realm,
  name,
  secret,
) {
  return promisify(storage_passwords_accessor.create)(
      {
          name: name,
          password: secret,
          realm: realm,
      }
  );
};

function promisify(fn) {


  // return a new promisified function
  return (...args) => {
    return new Promise((resolve, reject) => {
      // create a callback that resolves and rejects
      function callback(err, result) {
        if (err) {
          reject(err);
        } else {
          resolve(result);
        }
      }

      args.push(callback)

      // pass the callback into the function
      fn.call(this, ...args);
    })
  }
}

function noitificationAlert(text, success){
  document.getElementById("notificationText").innerHTML = text;
  var notificationBox = document.getElementById("notificationBox");

  if (success){
    notificationBox.style.backgroundColor = "green";
  }
  else{
    notificationBox.style.backgroundColor = "red";
  }

  fadeIn();

  setTimeout(function() {
    fadeOut();
  }, 3000)
};

function fadeIn() {
  var notificationBox = document.getElementById("notificationBox");
  notificationBox.style.opacity = 1;
};

function fadeOut() {
  var notificationBox = document.getElementById("notificationBox");
  notificationBox.style.opacity = 0;
};

// async function setAPIToken() {
//   var tokenValue = document.getElementById("token").value;
//   if (tokenValue == ""){
//     noitificationAlert("Please enter a value", false);
//     fadeIn();
//   }
//   else {
//   write_secret(service, appName, "token", tokenValue);
//   noitificationAlert("Token Created/Updated", true);
//   }
// };

async function setRealm() {
  var realmValue = document.getElementById("realm").value;
  if (realmValue == ""){
    noitificationAlert("Please enter a value", false);
  }
  else {
  write_secret(service, appName, "realm", realmValue);
  noitificationAlert("Realm Created/Updated", true);
  }
};

function doSomething() {
  document.getElementById("realm_button").addEventListener("click", setRealm);
};

if (document.readyState === "loading") {
  // Loading hasn't finished yet
  document.addEventListener("DOMContentLoaded", doSomething);
} else {
  // `DOMContentLoaded` has already fired
  doSomething();
};

        // await StoragePasswords.write_secret(
        //     splunk_js_sdk_service,
        //     SECRET_REALM,
        //     SECRET_NAME,
        //     token
        // )