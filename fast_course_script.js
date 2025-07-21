// Fast Course Fetching JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Fast AI Course Fetching with Real-time Updates
    let addCoursesTimeout = null;
    let lastAddCoursesRequest = 0;
    const DEBOUNCE_DELAY = 2000; // 2 seconds minimum between requests
    
    window.handleAddCoursesSubmit = function(form) {
      const now = Date.now();
      const button = form.querySelector('#addCoursesBtn');
      
      // Check if button is already processing
      if (button.disabled) {
        console.log('Course Fetching: Already processing, ignoring request');
        showToast('Course fetching already in progress', 'warning');
        return false;
      }
      
      // Debounce check
      if (now - lastAddCoursesRequest < DEBOUNCE_DELAY) {
        const remaining = Math.ceil((DEBOUNCE_DELAY - (now - lastAddCoursesRequest)) / 1000);
        showToast(`Please wait ${remaining} more second(s) before fetching again`, 'warning');
        return false;
      }
      
      // Start the AJAX request instead of form submission
      startFastCourseFetching(button);
      lastAddCoursesRequest = now;
      
      return false; // Prevent form submission
    };
    
    function startFastCourseFetching(button) {
      // Disable button and show loading state
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching from APIs...';
      
      // Show initial toast
      showToast('Starting fast course fetch from live APIs (no fallbacks)', 'info');
      
      // AJAX request to start course fetching
      fetch('/admin/populate-ai-courses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showToast('Course fetching started! Real-time updates below...', 'success');
          
          // Start polling for status updates
          pollFetchStatus(data.fetch_id, button);
        } else {
          throw new Error(data.error || 'Failed to start course fetching');
        }
      })
      .catch(error => {
        console.error('Error starting course fetch:', error);
        showToast(`Error: ${error.message}`, 'error');
        resetButton(button);
      });
    }
    
    function pollFetchStatus(fetchId, button) {
      const statusInterval = setInterval(() => {
        fetch(`/admin/course-fetch-status/${fetchId}`)
          .then(response => response.json())
          .then(status => {
            console.log('Fetch status:', status);
            
            if (status.status === 'fetching') {
              showToast(status.message, 'info');
              button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${status.message}`;
            } 
            else if (status.status === 'complete') {
              clearInterval(statusInterval);
              const result = status.result;
              
              if (result.courses_added > 0) {
                showToast(
                  `Success! Added ${result.courses_added} courses in ${result.total_time}s from ${result.apis_used} APIs`, 
                  'success'
                );
                
                // Refresh the course list
                setTimeout(() => {
                  window.location.reload();
                }, 2000);
              } else {
                showToast('No new courses found (may be duplicates or API issues)', 'warning');
              }
              
              resetButton(button);
            }
            else if (status.status === 'error') {
              clearInterval(statusInterval);
              showToast(`Error: ${status.message}`, 'error');
              resetButton(button);
            }
          })
          .catch(error => {
            clearInterval(statusInterval);
            console.error('Error polling status:', error);
            showToast('Lost connection to status updates', 'error');
            resetButton(button);
          });
      }, 2000); // Poll every 2 seconds
      
      // Safety timeout after 30 seconds
      setTimeout(() => {
        clearInterval(statusInterval);
        showToast('Fetch timeout - please check manually', 'warning');
        resetButton(button);
      }, 30000);
    }
    
    function resetButton(button) {
      button.disabled = false;
      button.innerHTML = '<i class="fas fa-download"></i> Fetch Live AI Courses';
    }
    
    function showToast(message, type) {
      // Create toast container if it doesn't exist
      let toastContainer = document.getElementById('toast-container');
      if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 9999;
          max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
      }
      
      // Create toast element
      const toast = document.createElement('div');
      const bgColor = {
        success: '#d4edda',
        error: '#f8d7da',
        warning: '#fff3cd',
        info: '#d1ecf1'
      }[type] || '#d1ecf1';
      
      const textColor = {
        success: '#155724',
        error: '#721c24',
        warning: '#856404',
        info: '#0c5460'
      }[type] || '#0c5460';
      
      toast.style.cssText = `
        background-color: ${bgColor};
        color: ${textColor};
        border: 1px solid;
        border-radius: 5px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        opacity: 0;
        transition: opacity 0.3s ease;
        font-size: 14px;
        line-height: 1.4;
      `;
      
      toast.textContent = message;
      toastContainer.appendChild(toast);
      
      // Animate in
      setTimeout(() => {
        toast.style.opacity = '1';
      }, 100);
      
      // Auto remove after 5 seconds
      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }, 5000);
    }

    // Update button text to reflect new functionality
    const fetchButton = document.getElementById('addCoursesBtn');
    if (fetchButton) {
        fetchButton.innerHTML = '<i class="fas fa-download"></i> Fetch Live AI Courses';
        fetchButton.title = 'Fetch 10 AI/Copilot courses from live APIs (Microsoft Learn, GitHub) - No fallbacks, real APIs only';
    }
});
