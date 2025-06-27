// Session Management JavaScript with Security Enhancements
class SessionManager {
    constructor() {
        this.warningTime = 5 * 60 * 1000; // 5 minutes before expiry
        this.sessionDuration = 24 * 60 * 60 * 1000; // 24 hours
        this.warningShown = false;
        this.lastActivity = Date.now();
        this.securityChecks = 0;
        
        this.setupActivityTracking();
        this.startSessionCheck();
        this.startSecurityMonitoring();
    }
    
    setupActivityTracking() {
        // Track user activity with security considerations
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, (e) => {
                this.lastActivity = Date.now();
                this.warningShown = false;
                this.hideWarning();
                
                // Basic security check - detect rapid automated activity
                this.securityChecks++;
                if (this.securityChecks > 100) {
                    // Reset counter after reasonable time
                    setTimeout(() => { this.securityChecks = 0; }, 10000);
                }
            });
        });
        
        // Detect page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.lastActivity = Date.now();
            }
        });
    }
    
    startSecurityMonitoring() {
        // Monitor for potential security issues
        setInterval(() => {
            this.performSecurityChecks();
        }, 30000); // Every 30 seconds
    }
    
    performSecurityChecks() {
        // Check for suspicious activity patterns
        if (this.securityChecks > 50) {
            console.warn('High activity detected - potential automated behavior');
            // In production, this could trigger additional validation
        }
        
        // Check if multiple tabs/windows are open (basic check)
        if (localStorage.getItem('session_tab_count')) {
            let tabCount = parseInt(localStorage.getItem('session_tab_count')) || 1;
            localStorage.setItem('session_tab_count', tabCount + 1);
            
            // Reset after reasonable time
            setTimeout(() => {
                localStorage.removeItem('session_tab_count');
            }, 60000);
        } else {
            localStorage.setItem('session_tab_count', '1');
        }
    }
    
    // ...existing methods...
    
    startSessionCheck() {
        // Check session status every minute
        setInterval(() => {
            this.checkSession();
        }, 60000);
    }
    
    checkSession() {
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivity;
        const timeUntilExpiry = this.sessionDuration - timeSinceLastActivity;
        
        // Show warning if close to expiry
        if (timeUntilExpiry <= this.warningTime && !this.warningShown) {
            this.showSessionWarning(Math.floor(timeUntilExpiry / 60000));
            this.warningShown = true;
        }
        
        // Auto-logout if session expired
        if (timeUntilExpiry <= 0) {
            this.logout();
        }
    }
    
    showSessionWarning(minutesLeft) {
        const warningHtml = `
            <div id="session-warning" class="alert alert-warning alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                <strong><i class="fas fa-exclamation-triangle"></i> Session Expiring!</strong><br>
                Your session will expire in ${minutesLeft} minutes due to inactivity.
                <br><small>Move your mouse or click anywhere to extend your session.</small>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Remove existing warning
        this.hideWarning();
        
        // Add new warning
        document.body.insertAdjacentHTML('beforeend', warningHtml);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideWarning();
        }, 10000);
    }
    
    hideWarning() {
        const warning = document.getElementById('session-warning');
        if (warning) {
            warning.remove();
        }
    }
    
    extendSession() {
        // Make AJAX call to extend session
        fetch('/extend-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.lastActivity = Date.now();
                this.warningShown = false;
                this.hideWarning();
            }
        })
        .catch(error => {
            console.error('Error extending session:', error);
        });
    }
    
    logout() {
        // Show logout message
        const logoutHtml = `
            <div class="modal fade show" id="logout-modal" style="display: block; background: rgba(0,0,0,0.5);">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-warning">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle"></i> Session Expired
                            </h5>
                        </div>
                        <div class="modal-body text-center">
                            <p>Your session has expired due to inactivity.</p>
                            <p>You will be redirected to the login page in <span id="countdown">5</span> seconds.</p>
                        </div>
                        <div class="modal-footer">
                            <a href="/login" class="btn btn-primary">Login Now</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', logoutHtml);
        
        // Countdown and redirect
        let countdown = 5;
        const countdownEl = document.getElementById('countdown');
        const countdownInterval = setInterval(() => {
            countdown--;
            if (countdownEl) countdownEl.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                window.location.href = '/login';
            }
        }, 1000);
    }
}

// Initialize session manager when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname !== '/login') {
        new SessionManager();
    }
});

// Add session extend button functionality
document.addEventListener('DOMContentLoaded', function() {
    const extendButtons = document.querySelectorAll('.extend-session-btn');
    extendButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.sessionManager?.extendSession();
        });
    });
});
