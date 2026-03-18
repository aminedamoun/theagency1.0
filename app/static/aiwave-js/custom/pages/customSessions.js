    document.addEventListener('DOMContentLoaded', function() {
        // Function to load sessions
        function loadSessions() {
            fetch('/aiwave/api/sessions/')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        const sessionsList = document.getElementById('sessions-list');
                        sessionsList.innerHTML = '';
                        
                        data.sessions.forEach(session => {
                            const sessionCard = createSessionCard(session);
                            sessionsList.appendChild(sessionCard);
                        });
                    }
                })
                .catch(() => {});
        }
    
        // Function to create session card
        function createSessionCard(session) {
            const card = document.createElement('div');
            card.className = 'list-card';
            const browserIcon = getBrowserIcon(session.browser_info || '');
            card.innerHTML = `
                <div class="inner">
                    <div class="left-content">
                        <div class="img-section">
                            <img src="${window.BROWSER_ICON_PATH}${browserIcon}" alt="Browser Icon">
                        </div>
                        <div class="content-section">
                            <h6 class="title">${session.device_info}</h6>
                            <p class="desc">${session.ip_address}</p>
                            <p class="date">Last active: ${session.last_activity}</p>
                            ${session.is_current ? '<span class="badge bg-success">Current Session</span>' : ''}
                        </div>
                    </div>
                    <div class="right-content">
                        ${!session.is_current ? `
                            <button class="btn-default btn-border terminate-btn" data-session-id="${session.id}">
                                <i class="fa-solid fa-trash-can"></i> Remove
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
    
            // Add event listener for terminate button
            const terminateBtn = card.querySelector('.terminate-btn');
            if (terminateBtn) {
                terminateBtn.onclick = () => confirmTerminateSession(session.id, terminateBtn);
            }
    
            return card;
        }
    
        // Function to get browser icon
        function getBrowserIcon(browserInfo) {
            if (!browserInfo || typeof browserInfo !== 'string') {
                return 'default-browser.png';
            }
            const browser = browserInfo.toLowerCase();
            let icon = 'default-browser.png';
            if (browser.includes('chrome')) icon = 'chrome.png';
            else if (browser.includes('firefox')) icon = 'firefox.png';
            else if (browser.includes('safari')) icon = 'safari.png';
            else if (browser.includes('edge')) icon = 'edge.png';
            else if (browser.includes('brave')) icon = 'brave.png';
            return icon;
        }
    
        // Function to confirm and terminate a session
        function confirmTerminateSession(sessionId, button) {
            const originalText = button.innerHTML;
            const originalClass = button.className;
            
            // Change button to confirmation state
            button.innerHTML = '<i class="fa-solid fa-exclamation-triangle"></i> Confirm Remove';
            button.className = 'btn-default btn-danger terminate-btn';
            button.disabled = false;
            
            // Remove the original click handler and add confirmation handler
            button.onclick = () => {
                terminateSession(sessionId, button, originalText, originalClass);
            };
            
            // Reset button after 5 seconds if not confirmed
            setTimeout(() => {
                if (button.innerHTML.includes('Confirm')) {
                    button.innerHTML = originalText;
                    button.className = originalClass;
                    button.disabled = false;
                    // Restore original click handler
                    button.onclick = () => confirmTerminateSession(sessionId, button);
                }
            }, 5000);
        }
        
        // Function to terminate a session
        function terminateSession(sessionId, button, originalText, originalClass) {
            // Show loading state
            button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Removing...';
            button.disabled = true;
    
            fetch('/aiwave/api/sessions/terminate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `session_id=${sessionId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    loadSessions(); // Reload sessions
                } else {
                    // Reset button on error
                    button.innerHTML = originalText;
                    button.className = originalClass;
                    button.disabled = false;
                    alert(data.message || 'Error terminating session');
                }
            })
            .catch(error => {
                // Error occurred while terminating session
                // Reset button on error
                button.innerHTML = originalText;
                button.className = originalClass;
                button.disabled = false;
            });
        }
    
        // Function to terminate all sessions
        function terminateAllSessions() {
            const button = document.getElementById('terminate-all-btn');
            const originalText = button.innerHTML;
            const originalClass = button.className;
            
            // Check if button is already in confirmation state
            if (button.innerHTML.includes('Confirm')) {
                // User confirmed, proceed with termination
                performTerminateAll(button, originalText, originalClass);
                return;
            }
            
            // Change button to confirmation state
            button.innerHTML = '<i class="fa-solid fa-exclamation-triangle"></i> Confirm Sign Out All';
            button.className = 'btn-default btn-danger';
            button.disabled = false;
            
            // Change the onclick handler to the confirmation function
            button.onclick = () => terminateAllSessions();
            
            // Reset button after 5 seconds if not confirmed
            setTimeout(() => {
                if (button.innerHTML.includes('Confirm')) {
                    button.innerHTML = originalText;
                    button.className = originalClass;
                    button.disabled = false;
                    // Restore original click handler
                    button.onclick = terminateAllSessions;
                }
            }, 5000);
        }
        
        // Function to perform the actual termination of all sessions
        function performTerminateAll(button, originalText, originalClass) {
            // Show loading state
            button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing Out...';
            button.disabled = true;
    
            fetch('/aiwave/api/sessions/terminate-all/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    loadSessions(); // Reload sessions
                } else {
                    // Reset button on error
                    button.innerHTML = originalText;
                    button.className = originalClass;
                    button.disabled = false;
                    alert(data.message || 'Error terminating sessions');
                }
            })
            .catch(error => {
                // Error occurred while terminating sessions
                // Reset button on error
                button.innerHTML = originalText;
                button.className = originalClass;
                button.disabled = false;
            });
        }
    
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
    
        // Add event listener for terminate all button
        document.getElementById('terminate-all-btn').onclick = terminateAllSessions;
    
        // Load sessions initially
        loadSessions();
    
        // Refresh sessions every 30 seconds
        setInterval(loadSessions, 30000);
    });