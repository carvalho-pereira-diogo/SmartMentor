document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('send-button').addEventListener('click', function() {
        var input = document.getElementById('message-input');
        if (input.value.trim() !== '') {
            sendMessage(input.value); // No longer passing tutor_id
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
            var replyMessage = document.createElement('div');
            // Accessing 'reply' property of the response object
            replyMessage.textContent = 'Tutor: ' + (data.reply || 'Error: No response from server');
            messageContainer.appendChild(replyMessage);
        })
        .catch(error => {
            console.error('Error:', error);
            var errorMessage = document.createElement('div');
            errorMessage.textContent = 'Tutor: Error communicating with server.';
            messageContainer.appendChild(errorMessage);
        });
}


function getCSRFToken() {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}