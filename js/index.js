// angular
//     .module("recorderDemo", ["angularAudioRecorder"])
//     .controller("DemoController", function($scope, $timeout) {
//     console.log("Loaded");
// });


function createCORSRequest(method, url){
      var xhttp=new XMLHttpRequest();
      if ("withCredentials" in xhttp){
        xhttp.open(method, url, true);
      } 
      else if (typeof XDomainRequest != "undefined"){
        xhttp= new XDomainRequest();
        xhttp.open(method, url);
      }
      else{
        xhttp=null;
      }
      return xhttp;
    }



// function get_topic() {
//     //var url = 'http://localhost:8080/getques'
//     var url = 'https://sagniklp.pythonanywhere.com/getques'
//     var request=createCORSRequest('get',url);
//     var q;
//     if (request){
//       //request.responseType = 'json';
//       request.onload= function () {
//         obj= JSON.parse(request.responseText)  // gives a json object
//         q=obj.ques
//         document.getElementById("topic").innerHTML = q;
//       };
//       request.send()
//     }

// };


// function upload_consent() {
//     var input = document.getElementById('consentFile');
//     if (input.files.length == 0){
//         alert("No files are selected")
//     }
//     else{
//         var url='https://sagniklp.pythonanywhere.com/upload_consent'
//         //var url = 'http://localhost:8080/upload_consent'
//         var formData = new FormData();
//         var request = createCORSRequest('post',url);
//         var content = input.files[0];
//         //console.log(content);
//         formData.append("file", content);
//         formData.append("url",id);
//         // //request.open("POST", url, true);
//         if (request){
//             request.open('post',url, true);
//             request.send(formData);
//             request.onload= function () {
//                 //console.log(request.responseText)
//                 obj= JSON.parse(request.responseText)  // gives a json object
//                 var resp=obj.msg
//                 // var text=obj.text
//                 document.getElementById("file_upload_text").innerHTML = resp;
//                 // document.getElementById("debrief").innerHTML = text;
//                 // document.getElementById("info").innerHTML ='<a class="page-scroll" style="font-size:15px;" href="contact">Know more about data usage!</a>'
//             };
//         }
//     }
// };


// get_topic();

angular.module('recorderDemo', ['angularAudioRecorder'])
.config(['recorderServiceProvider', function(recorderServiceProvider){
}])
.controller('DemoController', function($scope, $timeout) {
  $scope.logResult = function() {
    $timeout(function() {
      console.log($scope.recordedInput);
    });
  };
});


//jQuery to collapse the navbar on scroll
$(window).scroll(function() {
    if ($(".navbar").offset().top > 50) {
        $(".navbar-fixed-top").addClass("top-nav-collapse");
    } else {
        $(".navbar-fixed-top").removeClass("top-nav-collapse");
    }
});


$(function() {
    $('a.page-scroll').bind('click', function(event) {
        var $anchor = $(this);
        event.preventDefault(); 
 $anchor.parent().addClass("active").siblings().removeClass("active");
        $('html, body').stop().animate({
            scrollTop: $("#" + $anchor.attr('href')).offset().top
        }, 1500, 'easeInOutExpo');
        event.preventDefault();
    });
});



// var no_chek= document.getElementById('no');
// var yes_chek= document.getElementById('yes');

// yes_chek.checked=false;
// no_chek.checked=false;

var input = document.getElementById( 'uploadTrack' );
console.log(input)
var label  = input.nextElementSibling,
  labelVal = label.innerHTML;
var labelTag=document.getElementById( 'file-label' );

console.log(labelVal)
console.log(label.innerHTML)

input.addEventListener( 'change', function( e )
{
  var fileName = '';

  fileName = e.target.value.split( '\\' ).pop();
  console.log(fileName)
  if( fileName )
    labelTag.innerHTML = fileName;
  else
    label.innerHTML = labelVal;
});



  
