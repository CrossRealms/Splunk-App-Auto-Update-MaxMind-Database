require([
    'jquery',
    'splunkjs/mvc',
    'splunkjs/mvc/simplexml/ready!'
], function ($, mvc) {

    function getMaxMindDBConfiguration(){
        $("#mmdb_configuration_mmdb_license_key").val('******');
        // password (license key) will not sent to UI
    }
    getMaxMindDBConfiguration();


    function updateMaxMindDBLicenseKey(){
        let maxmind_database_license_key = $("#mmdb_configuration_mmdb_license_key").val();
        let msg_location = "#mmdb_configuration_mmdb_license_key_msg";
        if(maxmind_database_license_key === "******"){
            $(msg_location).addClass('error_msg');
            $(msg_location).removeClass('success_msg');
            $(msg_location).text(`Please re-enter a valid license Key.`);
            return;
        }
        let service = mvc.createService();
        let data = {
            "maxmind_database_license_key": maxmind_database_license_key
        };
        data = JSON.stringify(data);
        service.post("/MaxMindDBConfiguration/configuration", {"data": data}, function(error, response){
            if(response && response.data.entry[0].content['success'] && response.data.entry[0].content['success'] != ''){
                $(msg_location).removeClass('error_msg');
                $(msg_location).addClass('success_msg');
                $(msg_location).text("Max Mind database license key saved successfully.");
            }
            else if(response && response.data.entry[0].content['error'] && response.data.entry[0].content['error'] != ''){
                $(msg_location).addClass('error_msg');
                $(msg_location).removeClass('success_msg');
                $(msg_location).text(`Unable to save the Max Mind database license key. ${response.data.entry[0].content['error']}`);
            }
            else if(error && error['error']){
                console.log(`Error while getting updating Max Mind database license key: ${error['error']}`);
            }
            else{
                console.log("Unknown error while updating Max Mind database license key.");
            }
        });
    }

    $(`#mmdb_configuration_mmdb_license_key_button`).on("click", function(){
        updateMaxMindDBLicenseKey();
    });
});
