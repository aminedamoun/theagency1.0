document.addEventListener('DOMContentLoaded', function() {
    const exportBtn = document.getElementById('export-btn');
    
    exportBtn.addEventListener('click', function() {
        const selectedSessions = Array.from(document.querySelectorAll('.session-checkbox:checked'))
            .map(checkbox => checkbox.value);
            
        if (selectedSessions.length === 0) {
            alert('Please select at least one conversation to export.');
            return;
        }
        
        // Create form data
        const formData = new FormData();
        selectedSessions.forEach(id => formData.append('session_ids[]', id));
        
        // Send export request
        fetch('/aiwave/api/export-chats/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Create and download the export file
                const exportData = JSON.stringify(data.data, null, 2);
                const blob = new Blob([exportData], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'chat_export_' + new Date().toISOString().split('T')[0] + '.json';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                alert(data.message || 'Error exporting chats');
            }
        })
        .catch(error => {
            alert('Error exporting chats');
        });
    });
    
    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});