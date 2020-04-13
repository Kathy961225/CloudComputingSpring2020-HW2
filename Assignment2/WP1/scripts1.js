function dynamicallyLoadScript(url) {
  var script = document.createElement("script"); // create a script DOM node
  script.src = url; // set its src to the provided URL
  document.head.appendChild(script); // add it to the end of the head section of the page (could change 'head' to 'body' to add it to the end of the body section instead)
}
var apigClient;

$(window).load(function () {
  dynamicallyLoadScript("apiGateway-js-sdk/apigClient.js");
  dynamicallyLoadScript("apiGateway-js-sdk/aws-sdk-min.js");
  apigClient = apigClientFactory.newClient();
});

var valid;
var lastName;
var firstName;
var phone;

var imgUrl = "https://2020-cc-smart-door.s3.amazonaws.com/unknown.jpg"; // image url
$(".btn").click(function () {
  console.log(2);
  firstName = document.getElementById("inputFirstName").value;
  lastName = document.getElementById("inputLastName").value;
  phone = document.getElementById("inputPhone").value;

  if ($.trim(firstName) == "") {
    alert("no first name");
    self.location = "./webpage1.html";
    return false;
  } else if ($.trim(lastName) == "") {
    alert("no last name");
    self.location = "./webpage1.html";
    return false;
  } else if ($.trim(phone) == "") {
    alert("no phone number");
    self.location = "./webpage1.html";
    return false;
  }
  var name = firstName.toLowerCase() + "_" + lastName.toLowerCase(); // 名字传输格式  firstname_lastname
  var body = {
    messages: [
      {
        type: "UserMessage",
        unconstructed: {
          user_id: "wl2655", // user 的 id
          name: name,
          phone: phone,
          img: imgUrl,
          timestamp: 1, // 这个expiration怎么处理
        },
      },
    ],
  };
  console.log(body);
  apigClient
    .uploadInterfacePost({}, body, {})
    .then(function (result) {
      // Add success callback code here
      console.log(result);
      valid = result["data"]["body"]["messages"][0]["unconstructed"]["valid"];
      txt = result["data"]["body"]["messages"][0]["unconstructed"]["text"];
      console.log("valid");
      console.log(valid);
      if (valid == true) {
        console.log(txt);
        self.location = "./webpage1_success.html";
      } else if (valid == false) {
        console.log(txt);
        self.location = "./webpage1_deny.html";
      }
    })
    .catch(function (result) {
      // Add error callback code here.
      console.log("failded");
    });
});
