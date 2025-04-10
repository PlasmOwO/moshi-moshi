window.onload = function() {

    // Get references to elements on the page.
    //var form = document.getElementById('message-form');
    //var messageField = document.getElementById('message');
    var messagesOutput = document.getElementById('api-output');
    var socketStatus = document.getElementById('status');
    //var closeBtn = document.getElementById('close');
  
  
    // Create a new WebSocket.
    var socket = new WebSocket('http://13.37.121.132:7890/ws/testArea');
  
  
    // Handle any errors that occur.
    socket.onerror = function(error) {
      console.log('WebSocket Error: ' + error);
    };
  
  
    // Show a connected message when the WebSocket is opened.
    socket.onopen = function(event) {
      socketStatus.innerHTML = 'Connected to: ' + event.currentTarget.url;
      socketStatus.className = 'open';
    };

    socket.onmessage = function(event) {
        var message = event.data;
        messagesList.innerHTML +=  message;
      };
};