function submitForm(action) {
    const form = document.getElementById('aiForm');
    const responseSection = document.getElementById('responseSection');
    const aiResponse = document.getElementById('aiResponse');
    const promptInput = document.getElementById('prompt');

    document.getElementById('formAction').value = action;

    const formData = new FormData(form);

    fetch(window.location.href, {
            method: 'POST',
            body: formData,
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newResponse = doc.querySelector('#aiResponse').innerText;
            aiResponse.innerText = newResponse;
            promptInput.value = ''; // Clear input after submission
        })
        .catch(error => console.error('Error handling form submission:', error));
}