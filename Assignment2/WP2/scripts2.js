function dynamicallyLoadScript(url) {
    var script = document.createElement("script");  // create a script DOM node
    script.src = url;  // set its src to the provided URL
    document.head.appendChild(script);  // add it to the end of the head section of the page (could change 'head' to 'body' to add it to the end of the body section instead)
}
var apigClient;


$(window).load(function() {
  dynamicallyLoadScript("apiGateway-js-sdk/apigClient.js");
  dynamicallyLoadScript("apiGateway-js-sdk/aws-sdk-min.js");
  apigClient = apigClientFactory.newClient();
});

var valid
var name

function successful(name1, face){
    var name = name1;
    sessionStorage.setItem("sent", name);
    var face = "https://gate-known-faces-bucket.s3.amazonaws.com/" + face  // face照片的url
    sessionStorage.setItem("face_url", face);
    self.location = "./webpage2_success.html";
}





$('.btn').click(function() {
  console.log(2)
  passcode = $('.form-control').val();
  console.log(passcode)
  // if ($.trim(passcode) == '') {
  // 	self.location='./webpage2.html'
  //   return false;
  // }
  var body = {
                "messages": [
                    {
                        "type": "UserMessage",
                        "unconstructed": {
                            "user_id": "wl2655",
                            "passcode": passcode,
                            "timestamp": 1
                        }
                    }
                ]
            };
  // console.log(body);
  apigClient.virtualDoorPost({}, body, {})
      .then(function(result){
        // Add success callback code here
        console.log(result);
        console.log(result['data']['body']['messages']);
        console.log(result['data']['body']['messages']);
        console.log("before");
        valid = result["data"]["body"]["messages"][0]["unconstructed"]["valid"];
        console.log(valid);
        console.log("valid")
        if (valid == true){
          name = result['data']['body']['messages'][0]['unconstructed']['visitor_info']['name'].replace("_"," ");
          face = result['data']['body']['messages'][0]['unconstructed']['visitor_info']['photos'][0]['objectKey'];
        }
        //console.log(face);
        console.log("valid");
        console.log(valid);

        if (valid == true){
          successful(name, face);//self.location='./webpage2_success.html'

        }
        if (valid == false){
            self.location = "./webpage2_deny.html";
        }
      }).catch( function(result){
        // Add error callback code here.
        console.log("failded");
      });


});
