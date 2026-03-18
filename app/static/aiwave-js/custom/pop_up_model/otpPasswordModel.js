function clearOtpModalFields() {
  // Clear all input values
  document.getElementById('resetEmail').value = '';
  document.getElementById('otpInput').value = '';
  document.getElementById('newPassword').value = '';
  document.getElementById('confirmPassword').value = '';
  // Clear all error messages
  document.getElementById('emailError').textContent = '';
  document.getElementById('otpError').textContent = '';
  document.getElementById('passwordError').textContent = '';
  // Clear alerts
  document.getElementById('otpModalAlerts').innerHTML = '';
}

function setButtonLoading(buttonId, isLoading) {
  const button = document.getElementById(buttonId);
  const btnText = button.querySelector('.btn-text');
  const btnLoading = button.querySelector('.btn-loading');
  
  if (isLoading) {
    button.disabled = true;
    btnText.classList.add('d-none');
    btnLoading.classList.remove('d-none');
  } else {
    button.disabled = false;
    btnText.classList.remove('d-none');
    btnLoading.classList.add('d-none');
  }
}

function showOtpModalStep(step) {
  document.getElementById('emailStep').classList.add('d-none');
  document.getElementById('otpStep').classList.add('d-none');
  document.getElementById('passwordStep').classList.add('d-none');
  document.getElementById(step).classList.remove('d-none');
  // Clear all error messages when switching steps
  document.getElementById('emailError').textContent = '';
  document.getElementById('otpError').textContent = '';
  document.getElementById('passwordError').textContent = '';
}
function openOtpPasswordModal() {
  var modal = document.getElementById('otpPasswordModal');
  modal.classList.add('show');
  modal.style.display = 'block';
  document.body.classList.add('modal-open');
  clearOtpModalFields();
  showOtpModalStep('emailStep');
}
function closeOtpPasswordModal() {
  var modal = document.getElementById('otpPasswordModal');
  modal.classList.remove('show');
  modal.style.display = 'none';
  document.body.classList.remove('modal-open');
  clearOtpModalFields();
}

// AJAX logic for each step

document.addEventListener('DOMContentLoaded', function() {
  const csrftoken = getCookie('csrftoken');

  // Email step
  document.getElementById('emailForm').onsubmit = function(e) {
    e.preventDefault();
    
    // Set loading state
    setButtonLoading('sendOtpBtn', true);
    
    var email = document.getElementById('resetEmail').value;
    var formData = new FormData();
    formData.append('email', email);
    fetch('/aiwave/forgot-password/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      // Clear loading state
      setButtonLoading('sendOtpBtn', false);
      
      // Clear previous errors
      document.getElementById('emailError').textContent = '';
      document.getElementById('otpError').textContent = '';
      document.getElementById('passwordError').textContent = '';
      
      if (data.error) {
        document.getElementById('emailError').textContent = data.error;
      } else if (data.status === 'otp_sent') {
        // Clear any previous alerts
        document.getElementById('otpModalAlerts').innerHTML = '';
        showOtpModalStep('otpStep');
      }
    })
    .catch(error => {
      // Clear loading state
      setButtonLoading('sendOtpBtn', false);
      document.getElementById('emailError').textContent = 'An error occurred. Please try again.';
    });
  };

  // OTP step
  document.getElementById('otpForm').onsubmit = function(e) {
    e.preventDefault();
    
    // Set loading state
    setButtonLoading('verifyOtpBtn', true);
    
    var otp = document.getElementById('otpInput').value;
    var formData = new FormData();
    formData.append('otp', otp);
    fetch('/aiwave/forgot-password/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      // Clear loading state
      setButtonLoading('verifyOtpBtn', false);
      
      // Clear previous errors
      document.getElementById('emailError').textContent = '';
      document.getElementById('otpError').textContent = '';
      document.getElementById('passwordError').textContent = '';
      
      if (data.error) {
        document.getElementById('otpError').textContent = data.error;
      } else if (data.status === 'otp_verified') {
        // Clear any previous alerts
        document.getElementById('otpModalAlerts').innerHTML = '';
        showOtpModalStep('passwordStep');
      }
    })
    .catch(error => {
      // Clear loading state
      setButtonLoading('verifyOtpBtn', false);
      document.getElementById('otpError').textContent = 'An error occurred. Please try again.';
    });
  };

  // Password step
  document.getElementById('passwordForm').onsubmit = function(e) {
    e.preventDefault();
    
    // Set loading state
    setButtonLoading('changePasswordBtn', true);
    
    var newPassword = document.getElementById('newPassword').value;
    var confirmPassword = document.getElementById('confirmPassword').value;
    var formData = new FormData();
    formData.append('new_password', newPassword);
    formData.append('confirm_password', confirmPassword);
    fetch('/aiwave/forgot-password/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      // Clear loading state
      setButtonLoading('changePasswordBtn', false);
      
      // Clear previous errors
      document.getElementById('emailError').textContent = '';
      document.getElementById('otpError').textContent = '';
      document.getElementById('passwordError').textContent = '';
      
      if (data.error) {
        document.getElementById('passwordError').textContent = data.error;
      } else if (data.status === 'password_reset') {
        // Show success message in modal first
        if (data.alerts_html) {
          document.getElementById('otpModalAlerts').innerHTML = data.alerts_html;
        }
        // Close modal after a short delay to show the success message
        setTimeout(function() {
          closeOtpPasswordModal();
        }, 2000);
      }
    })
    .catch(error => {
      // Clear loading state
      setButtonLoading('changePasswordBtn', false);
      document.getElementById('passwordError').textContent = 'An error occurred. Please try again.';
    });
  };

  // Resend OTP
  document.getElementById('resendOtpBtn').onclick = function() {
    // Set loading state
    setButtonLoading('resendOtpBtn', true);
    
    var formData = new FormData();
    formData.append('email', document.getElementById('resetEmail').value);
    formData.append('resend', 'true');
    fetch('/aiwave/forgot-password/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      // Clear loading state
      setButtonLoading('resendOtpBtn', false);
      document.getElementById('otpModalAlerts').innerHTML = data.alerts_html || '';
    })
    .catch(error => {
      // Clear loading state
      setButtonLoading('resendOtpBtn', false);
      document.getElementById('otpModalAlerts').innerHTML = '<div class="alert alert-danger">Failed to resend OTP. Please try again.</div>';
    });
  };
});

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