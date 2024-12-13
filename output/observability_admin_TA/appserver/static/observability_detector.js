requirejs([
    '../app/observability_admin_TA/lib/jquery-3.6.0-umd-min',
    '../app/observability_admin_TA/lib/underscore-1.6.0-umd-min',
    'splunkjs/mvc',
    'splunkjs/mvc/simplexml/ready!'
], 

function detector_functions ($, _, mvc) {

    function setToken(name, value) {
        

        var defaultTokenModel = mvc.Components.get('default');
        if (defaultTokenModel) {
            defaultTokenModel.set(name, value);
        }
        var submittedTokenModel = mvc.Components.get('submitted');
        if (submittedTokenModel) {
            submittedTokenModel.set(name, value);
        }
    }

    $('.dashboard-body').on('click', '[data-set-token],[data-unset-token],[data-token-json]', function(e) {
        e.preventDefault();
        var target = $(e.currentTarget);

        var setTokenName = target.data('set-token');
        if (setTokenName) {
            setToken(setTokenName, target.data('value'));
        }

        var unsetTokenName = target.data('unset-token');
        if (unsetTokenName) {
            setToken(unsetTokenName, undefined);
        }

        var tokenJson = target.data('token-json');
        if (tokenJson) {
            try {
                if (_.isObject(tokenJson)) {
                    _(tokenJson).each(function(value, key) {
                        if (value === null) {
                            // Unset the token
                            setToken(key, undefined);
                        } else {
                            setToken(key, value);
                        }
                    });
                }
            } catch (e) {
               
            }
        }

    });


    var defaultTokenModel = mvc.Components.get("default");
    defaultTokenModel.on("change:json", format_JSON_token);

    function format_JSON_token() {
            var tokens = mvc.Components.get("default");
            var tokenValue = tokens.get("json");
            if (tokenValue != "$result.json$" && tokenValue != "init"){
                var tokenValue = JSON.stringify(JSON.parse(tokenValue), null, 2);
                var tokenValue = tokenValue.replace(/true/g,"True");
                var tokenValue = tokenValue.replace(/false/g,"False");
                var tokenValue = tokenValue.replace(/null/g,"None");
                tokens.set("json_pretty", tokenValue);
            }
    };


    // wait for ID to load as this collabarates with the realm to create links/scripts
    defaultTokenModel.on("change:id",get_realm);

    function get_realm() {
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

        storagePasswords.fetch(function(err, storagePasswordsCollection) {
        if (err) {

            return;
        }
        
        // Find the password with id "realm"
        var passwordEntry = storagePasswordsCollection.item("observability_admin_TA:realm:");

        if (passwordEntry) {
            // Access the password value
            var passwordValue = passwordEntry._properties.clear_password;

            var tokens = mvc.Components.get("default");
            var tokenValue = tokens.get("id");
            if (tokenValue!="$result.id$"){
            set_realm_dashboard(passwordValue,tokenValue);
            }

        } else {
          return;
        }
    });
        
    };

    function set_realm_dashboard(realm,id){
        var myLink = document.getElementById("link_to_object");
        myLink.href = "https://app."+realm+".signalfx.com/#/detector/v2/"+id+"/edit";

       var realmEdit = document.getElementById("realm_edit");
        realmEdit.innerText ="REALM = \""+realm+"\"";

        var realmDelete = document.getElementById("realm_delete");
        realmDelete.innerText ="REALM = \""+realm+"\"";

    };
    
});



