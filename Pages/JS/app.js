document.addEventListener('DOMContentLoaded', () => {
    // 1. Get references to the form containers
    const signUpSection = document.getElementById('new-account');
    const signInSection = document.getElementById('login-account');

    // 2. Get references to the toggle links
    const signInBtn = document.getElementById('sign-in-btn');
    const signUpBtn = document.getElementById('sign-up-btn');

    /**
     * Toggles the visibility of the forms.
     * @param {Event} event - The click event.
     * @param {HTMLElement} showForm - The form section to show.
     * @param {HTMLElement} hideForm - The form section to hide.
     */
    const toggleForms = (event, showForm, hideForm) => {
        event.preventDefault(); // Stop the <a> tag from navigating
        
        // Hide the currently visible form smoothly
        hideForm.style.opacity = '0';
        setTimeout(() => {
            hideForm.style.display = 'none';
            
            // Show the target form
            showForm.style.display = 'block'; // Or 'grid', depending on your CSS layout
            // Use a short timeout to re-enable the opacity transition
            setTimeout(() => {
                showForm.style.opacity = '1';
            }, 10); // Small delay to ensure display:block is applied first
            
        }, 300); // Wait for the opacity transition (0.3s) to finish before setting display:none
    };

    // 3. Attach event listeners
    // When 'Sign-in' link is clicked (inside Sign-Up form)
    if (signInBtn) {
        signInBtn.addEventListener('click', (e) => {
            toggleForms(e, signInSection, signUpSection);
        });
    }

    // When 'Sign-up' link is clicked (inside Sign-In form)
    if (signUpBtn) {
        signUpBtn.addEventListener('click', (e) => {
            toggleForms(e, signUpSection, signInSection);
        });
    }
    
    // Initial setup: ensure Sign-Up is visible and Sign-In is hidden
    if (signUpSection && signInSection) {
        signUpSection.style.display = 'block';
        signUpSection.style.opacity = '1';
        signInSection.style.display = 'none';
        signInSection.style.opacity = '0';
    }
});