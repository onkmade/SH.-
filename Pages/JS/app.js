// Main Content Switching - Define globally before DOMContentLoaded
function showContent(sectionId) {
    console.log('Switching to section:', sectionId); // Debug log
    
    // Get all content sections
    const allSections = document.querySelectorAll('.content-section');
    console.log('Found sections:', allSections.length); // Debug log
    
    // Remove active class from all sections
    allSections.forEach(section => {
        section.classList.remove('active-content');
    });
    
    // Add active class to the selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active-content');
        console.log('Activated section:', sectionId); // Debug log
    } else {
        console.error('Section not found:', sectionId); // Debug log
    }
    
    // Update active nav link styling
    const allNavLinks = document.querySelectorAll('.nav-links');
    allNavLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.getElementById(`link-${sectionId}`);
    if (activeLink) {
        activeLink.classList.add('active');
        console.log('Activated link:', `link-${sectionId}`); // Debug log
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Loaded'); // Debug log
    
    // 1. Get references to the form containers (if they exist)
    const signUpSection = document.getElementById('new-account');
    const signInSection = document.getElementById('login-account');

    // 2. Get references to the toggle links (if they exist)
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

    if (signInBtn) {
        signInBtn.addEventListener('click', (e) => {
            toggleForms(e, signInSection, signUpSection);
        });
    }

    if (signUpBtn) {
        signUpBtn.addEventListener('click', (e) => {
            toggleForms(e, signUpSection, signInSection);
        });
    }
    
    if (signUpSection && signInSection) {
        signUpSection.style.display = 'block';
        signUpSection.style.opacity = '1';
        signInSection.style.display = 'none';
        signInSection.style.opacity = '0';
    }

    showContent('feed');
    
    const navLinks = document.querySelectorAll('.nav-links');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const linkId = this.id;
            if (linkId.startsWith('link-')) {
                e.preventDefault();
                const sectionId = linkId.replace('link-', '');
                showContent(sectionId);
            }
        });
    });
});