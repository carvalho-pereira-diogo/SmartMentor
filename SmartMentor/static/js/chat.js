document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('send-button').addEventListener('click', function() {
        var input = document.getElementById('message-input');
        if (input.value.trim() !== '') {
            sendMessage(input.value);
            input.value = ''; // Clear the input after sending
        }
    });
});

function sendMessage(message) {
    var messageContainer = document.getElementById('messages');
    var newMessage = document.createElement('div');
    newMessage.textContent = 'You: ' + message;
    messageContainer.appendChild(newMessage);

    fetch('/api/send_message/', {
            method: 'POST',
            body: JSON.stringify({ message: message }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data); // Log the response data
            var replyMessage = document.createElement('div');
            replyMessage.textContent = 'Tutor: ' + (data.reply || 'Error: No response from server');
            messageContainer.appendChild(replyMessage);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}



function getCSRFToken() {
    // Function to get the CSRF token from a cookie
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return null;
}