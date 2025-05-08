// Main JavaScript file for SHOP AURA

document.addEventListener('DOMContentLoaded', function() {
    // Handle navigation dropdown menus
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                menu.classList.toggle('show');
            });
        }
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target)) {
                const menu = dropdown.querySelector('.dropdown-menu');
                if (menu && menu.classList.contains('show')) {
                    menu.classList.remove('show');
                }
            }
        });
    });
    
    // Quantity increment/decrement buttons
    const quantityForms = document.querySelectorAll('.quantity-form');
    
    quantityForms.forEach(form => {
        const input = form.querySelector('input[type="number"]');
        const incrementBtn = form.querySelector('.increment');
        const decrementBtn = form.querySelector('.decrement');
        
        if (input && incrementBtn && decrementBtn) {
            incrementBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value, 10);
                const maxValue = parseInt(input.getAttribute('max'), 10);
                
                if (currentValue < maxValue) {
                    input.value = currentValue + 1;
                }
            });
            
            decrementBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value, 10);
                
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                }
            });
        }
    });
    
    // Edit profile form toggle
    const editProfileBtn = document.querySelector('.edit-profile-btn');
    const editProfileForm = document.getElementById('edit-profile-form');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    
    if (editProfileBtn && editProfileForm && cancelEditBtn) {
        editProfileBtn.addEventListener('click', function(event) {
            event.preventDefault();
            editProfileForm.style.display = 'block';
        });
        
        cancelEditBtn.addEventListener('click', function() {
            editProfileForm.style.display = 'none';
        });
    }
    
    // Flash messages auto-hide
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s ease';
            
            setTimeout(() => {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // Product card hover animations
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            if (!this.classList.contains('out-of-stock')) {
                this.style.transform = 'translateY(-10px)';
                this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
            }
        });
        
        card.addEventListener('mouseleave', function() {
            if (!this.classList.contains('out-of-stock')) {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
            }
        });
    });
    
    // Responsive navigation menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
    }
    
    // Password confirmation validation
    const signupForm = document.querySelector('form[action*="signup"]');
    
    if (signupForm) {
        const password = signupForm.querySelector('input[name="password1"]');
        const confirmPassword = signupForm.querySelector('input[name="password2"]');
        
        if (password && confirmPassword) {
            confirmPassword.addEventListener('input', function() {
                if (password.value !== confirmPassword.value) {
                    confirmPassword.setCustomValidity('Passwords do not match');
                } else {
                    confirmPassword.setCustomValidity('');
                }
            });
        }
    }
    
    // Initialize animations for elements with animation classes
    const animatedElements = document.querySelectorAll('.fade-in, .slide-in-up, .slide-in-left, .fade-in-scale');
    
    animatedElements.forEach(element => {
        // Check if element is in viewport
        const isInViewport = function(el) {
            const rect = el.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        };
        
        if (isInViewport(element)) {
            element.style.opacity = '1';
        } else {
            element.style.opacity = '0';
            
            window.addEventListener('scroll', function() {
                if (isInViewport(element)) {
                    element.style.opacity = '1';
                }
            });
        }
    });
});
