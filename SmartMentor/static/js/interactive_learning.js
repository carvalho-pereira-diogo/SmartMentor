function fetchContent(action, subject) {
    let data = { 'action': action, 'subject': subject, 'prompt': document.getElementById('promptInput').value };
    fetch('/actual/endpoint/', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('courseMaterial').innerHTML = data.content;
            document.getElementById('aiResponse').textContent = data.ai_response;
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

document.getElementById('aiInteractionForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(this);
    fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // Update the UI based on the response
        })
        .catch(error => {
            console.error('Error:', error);
        });
});

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(form);
        console.log('Form data:', Array.from(formData.entries()));
        form.submit(); // comment this out if you want to prevent actual submission for testing
    });
});