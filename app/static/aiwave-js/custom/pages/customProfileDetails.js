(function() {
    // Show image preview when a new file is selected
    var imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        try {
            imageUpload.addEventListener('change', function(event) {
                var input = event.target;
                if (input.files && input.files[0]) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        var preview = document.getElementById('profileImagePreview');
                        if (preview) preview.src = e.target.result;
                    };
                    reader.readAsDataURL(input.files[0]);
                }
            });
        } catch (e) { /* silent */ }
    }

    // Password change form handling
    var changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        try {
            changePasswordForm.addEventListener('submit', function(e) {
                e.preventDefault();
                var formData = new FormData(this);
                var submitButton = this.querySelector('button[type="submit"]');
                var newPassword = formData.get('new_password');
                var confirmPassword = formData.get('confirm_password');
                if (newPassword !== confirmPassword) {
                    alert('New password and confirm password do not match!');
                    return;
                }
                submitButton.disabled = true;
                submitButton.innerHTML = 'Updating...';
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(function(response) {
                    if (!response.ok) return response.json().then(function(data){return data;});
                    return response.json();
                })
                .then(function(data) {
                    var msg = (data && data.alert && data.alert.message) || (data && data.message) || 'Password updated!';
                    if (data && data.success) {
                        alert(msg);
                        changePasswordForm.reset();
                    }
                })
                .catch(function() {/* silent */})
                .finally(function() {
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Update Password';
                });
            });
        } catch (e) { /* silent */ }
    }

    // Delete account form handling
    var deleteAccountForm = document.getElementById('deleteAccountForm');
    if (deleteAccountForm) {
        try {
            deleteAccountForm.addEventListener('submit', function(e) {
                e.preventDefault();
                if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) return;
                var formData = new FormData(this);
                var submitButton = this.querySelector('button[type="submit"]');
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(function(response) {
                    if (!response.ok) return response.json().then(function(data){return data;});
                    return response.json();
                })
                .then(function(data) {
                    var msg = (data && data.message) || 'Account deleted!';
                    if (data && data.success) {
                        alert(msg);
                        window.location.href = "{% url 'aiwave-signin' %}";
                    } else if (data && data.requirePassword) {
                        var deletePasswordField = document.getElementById('delete_password');
                        if (deletePasswordField) deletePasswordField.focus();
                    }
                })
                .catch(function() {/* silent */})
                .finally(function() {
                    submitButton.disabled = false;
                    submitButton.innerHTML = '<i class="fa-solid fa-trash-can"></i> Delete Account';
                });
            });
        } catch (e) { /* silent */ }
    }
})();

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
const csrftoken = getCookie('csrftoken');