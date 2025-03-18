require([
    'jquery',
    'splunkjs/mvc',
    'splunkjs/mvc/simplexml/ready!'
], function ($, mvc) {

    function getMaxMindDBConfiguration(){
        let service = mvc.createService();
        service.get("/MaxMindDBConfiguration", {}, function(error, response){
            if(response && response.data.entry[0].content && response.data.entry[0].content['maxmind_database_account_id'] != ''){
                response = response.data.entry[0].content;
                $("#mmdb_configuration_mmdb_account_id").val(response['maxmind_database_account_id']);
                $("#mmdb_configuration_mmdb_license_key").val(response['maxmind_database_license_key']);
                $("input[name='mmdb_geo_database'][value='" + response['maxmind_database_file'] + "']").prop("checked", true);
                $("#mmdb_config_proxy_url").val(response['mmdb_config_proxy_url']);
                // $("#mmdb_config_is_ssl_verify").prop('checked', response['mmdb_config_is_ssl_verify']);
            }
            else if(response && response.data.entry[0].content['error'] && response.data.entry[0].content['error'] != ''){
                let msg_location = "#mmdb_configuration_mmdb_license_key_msg";
                $(msg_location).addClass('error_msg');
                $(msg_location).removeClass('success_msg');
                $(msg_location).text(`Unable to get Max Mind database configuration, may be there is no configuration. Please set the configuration and save.`);
            }
            else if(error && error['error']){
                console.log(`Error while getting updating Max Mind database configuration: ${error['error']}`);
            }
            else{
                console.log("Unknown error while updating Max Mind database configuration.");
            }
        });
    }
    getMaxMindDBConfiguration();


    function updateMaxMindDBLicenseKey(){
        let msg_location = "#mmdb_configuration_mmdb_license_key_msg";
        $(msg_location).text(` `);

        let maxmind_database_account_id = $('#mmdb_configuration_mmdb_account_id').val();
        let maxmind_database_license_key = $("#mmdb_configuration_mmdb_license_key").val();

        let maxmind_geo_database_file = $("input[name='mmdb_geo_database']:checked").val();

        let mmdb_config_proxy_url = $("#mmdb_config_proxy_url").val();
        if (mmdb_config_proxy_url.trim() == ""){
            mmdb_config_proxy_url = "None";
        }

        // let mmdb_config_is_ssl_verify = $("#mmdb_config_is_ssl_verify").is(":checked");

        if(maxmind_database_license_key === "******"){
            $(msg_location).addClass('error_msg');
            $(msg_location).removeClass('success_msg');
            $(msg_location).text(`Please re-enter a valid License Key.`);
            return;
        }
        let service = mvc.createService();
        let data = {
            "maxmind_database_account_id": maxmind_database_account_id,
            "maxmind_database_license_key": maxmind_database_license_key,
            "maxmind_database_file": maxmind_geo_database_file,
            "mmdb_config_proxy_url": mmdb_config_proxy_url
            // "mmdb_config_is_ssl_verify": mmdb_config_is_ssl_verify
        };
        data = JSON.stringify(data);
        service.post("/MaxMindDBConfiguration/configuration", {"data": data}, function(error, response){
            if(response && response.data.entry[0].content['success'] && response.data.entry[0].content['success'] != ''){
                $(msg_location).removeClass('error_msg');
                $(msg_location).addClass('success_msg');
                $(msg_location).text("Max Mind database configuration saved successfully.");
            }
            else if(response && response.data.entry[0].content['error'] && response.data.entry[0].content['error'] != ''){
                $(msg_location).addClass('error_msg');
                $(msg_location).removeClass('success_msg');
                $(msg_location).text(`Unable to save the Max Mind database configuration. ${response.data.entry[0].content['error']}`);
            }
            else if(error && error['error']){
                console.log(`Error while getting updating Max Mind database configuration: ${error['error']}`);
            }
            else{
                console.log("Unknown error while updating Max Mind database configuration.");
            }
        });
    }

    $(`#mmdb_configuration_mmdb_license_key_button`).on("click", function(){
        updateMaxMindDBLicenseKey();
    });
});
