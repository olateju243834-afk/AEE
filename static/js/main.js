/**
 * Agricultural and Environmental Engineering Department Website
 * JavaScript functionality for enhanced user experience
 */

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function() {
    initializeScrollSpy();
    initializeAnimations();
    initializeFormValidation();
    initializeNavbarBehavior();
    initializeSmoothScrolling();
    initializeFlashMessageHandling();
    handleContactFormSubmission();
});

/**
 * Initialize Bootstrap ScrollSpy for navigation
 */
function initializeScrollSpy() {
    // Bootstrap ScrollSpy is initialized via data attributes in HTML
    // Additional custom behavior can be added here
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
            
            // Close mobile menu if open
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    });
}

/**
 * Initialize scroll animations
 */
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, observerOptions);

    // Observe all animatable elements
    const animateElements = document.querySelectorAll('.card, .notice-item, .gallery-item');
    animateElements.forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            if (!validateContactForm()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            contactForm.classList.add('was-validated');
        });
    }
}

/**
 * Validate contact form
 */
function validateContactForm() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value.trim();
    
    let isValid = true;
    
    // Name validation
    if (name.length < 2) {
        showFieldError('name', 'Name must be at least 2 characters long');
        isValid = false;
    } else {
        clearFieldError('name');
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    } else {
        clearFieldError('email');
    }
    
    // Subject validation
    if (subject === '') {
        showFieldError('subject', 'Please select a subject');
        isValid = false;
    } else {
        clearFieldError('subject');
    }
    
    // Message validation
    if (message.length < 10) {
        showFieldError('message', 'Message must be at least 10 characters long');
        isValid = false;
    } else {
        clearFieldError('message');
    }
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const existingError = field.parentNode.querySelector('.field-error');
    
    if (existingError) {
        existingError.textContent = message;
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-danger small mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
    
    field.classList.add('is-invalid');
}

/**
 * Clear field error
 */
function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorDiv = field.parentNode.querySelector('.field-error');
    
    if (errorDiv) {
        errorDiv.remove();
    }
    
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
}

/**
 * Initialize navbar behavior
 */
function initializeNavbarBehavior() {
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove shadow based on scroll position
        if (currentScrollTop > 50) {
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.2)';
        } else {
            navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
        
        // Update active navigation link based on scroll position
        updateActiveNavLink();
        
        lastScrollTop = currentScrollTop;
    });
}

/**
 * Update active navigation link based on current section
 */
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    let current = '';
    const scrollTop = window.pageYOffset;
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        const sectionHeight = section.offsetHeight;
        
        if (scrollTop >= sectionTop && scrollTop < sectionTop + sectionHeight) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                const offsetTop = targetElement.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
Newly added function for payment submission
*/
document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('submitPayment');
    if (!submitBtn) return; // stop if button doesn't exist

    submitBtn.addEventListener('click', async (e) => {
        e.preventDefault();

        // collect the form data
        const formData = new FormData();

        // collect student details
        formData.append('fullName', document.getElementById('fullName').value.trim());
        formData.append('matricNumber', document.getElementById('matricNumber').value.trim());
        formData.append('level', document.getElementById('level').value.trim());
        formData.append('email', document.getElementById('email').value.trim());
        formData.append('phoneNumber', document.getElementById('phoneNumber').value.trim());
        formData.append('transactionRef', document.getElementById('transactionRef').value.trim());
        formData.append('paymentDate', document.getElementById('paymentDate').value);

        // handle file upload
        const receiptFile = document.getElementById('paymentReceipt').files[0];
        if (receiptFile) formData.append('receipt', receiptFile);

        // collect selected payment items
        const selectedItems = [];
        document.querySelectorAll('.payment-checkbox:checked').forEach(cb => {
            selectedItems.push({
                name: cb.dataset.name,
                amount: parseFloat(cb.value)
            });
        });
        formData.append('paymentItems', JSON.stringify(selectedItems));

        // calculate total (₦8,000 base + selected)
        const totalAmount = selectedItems.reduce((sum, item) => sum + item.amount, 8000);
        formData.append('totalAmount', totalAmount);

        // debug log
        console.log('Submitting payment data:', Object.fromEntries(formData));

        try {
            const res = await fetch('/submit-payment', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                alert(`✅ ${data.message}`);
                window.location.href = '/'; // optional redirect after success
            } else {
                alert(`❌ Error: ${data.error}`);
            }
        } catch (err) {
            console.error('Payment submission failed:', err);
            alert('⚠️ Failed to connect to the server.');
        }
    });
});







/**
 * Initialize flash message handling
 */
function initializeFlashMessageHandling() {
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    
    flashMessages.forEach(message => {
        // Auto-hide success messages after 5 seconds
        if (message.classList.contains('alert-success')) {
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.parentNode.removeChild(message);
                    }
                }, 300);
            }, 5000);
        }
    });
}

/**
 * Handle contact form submission with loading state
 */
function handleContactFormSubmission() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function() {
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // Show loading state
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
            submitButton.disabled = true;
            
            // Note: The actual form submission is handled by Flask
            // This is just for UI feedback
        });
    }
}

/**
 * Initialize gallery lightbox functionality
 */
function initializeGallery() {
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            // This would open a lightbox or modal for gallery images
            // For now, we'll just add a click effect
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

/**
 * Initialize search functionality (if needed)
 */
function initializeSearch() {
    const searchInput = document.querySelector('#searchInput');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            if (query.length > 2) {
                // Implement search logic here
                highlightSearchResults(query);
            } else {
                clearSearchHighlights();
            }
        });
    }
}

/**
 * Highlight search results
 */
function highlightSearchResults(query) {
    // This function would highlight search terms in the content
    const textNodes = getTextNodes(document.body);
    
    textNodes.forEach(node => {
        if (node.textContent.toLowerCase().includes(query)) {
            // Highlight matching text
            const parent = node.parentNode;
            const wrapper = document.createElement('span');
            wrapper.className = 'search-highlight';
            
            const text = node.textContent;
            const regex = new RegExp(`(${query})`, 'gi');
            wrapper.innerHTML = text.replace(regex, '<mark>$1</mark>');
            
            parent.replaceChild(wrapper, node);
        }
    });
}

/**
 * Clear search highlights
 */
function clearSearchHighlights() {
    const highlights = document.querySelectorAll('.search-highlight');
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
    });
}

/**
 * Get all text nodes in an element
 */
function getTextNodes(element) {
    const textNodes = [];
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim().length > 0) {
            textNodes.push(node);
        }
    }
    
    return textNodes;
}

/**
 * Initialize tooltip functionality
 */
function initializeTooltips() {
    // Initialize Bootstrap tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize print functionality
 */
function initializePrintFunctionality() {
    const printButtons = document.querySelectorAll('.print-btn');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });
}

/**
 * Handle back to top functionality
 */
function initializeBackToTop() {
    // Create back to top button
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTopButton.className = 'btn btn-primary btn-back-to-top position-fixed';
    backToTopButton.style.cssText = `
        bottom: 30px;
        right: 30px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(backToTopButton);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.opacity = '1';
            backToTopButton.style.visibility = 'visible';
        } else {
            backToTopButton.style.opacity = '0';
            backToTopButton.style.visibility = 'hidden';
        }
    });
    
    // Smooth scroll to top
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize back to top on load
document.addEventListener('DOMContentLoaded', function() {
    initializeBackToTop();
});

/**
 * Utility function to debounce rapid function calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        // Escape key closes any open modals or dropdowns
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
        
        // Enter key on card elements triggers click
        if (e.key === 'Enter' && e.target.classList.contains('card')) {
            e.target.click();
        }
    });
    
    // Add focus indicators for keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
}

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAccessibility();
    initializeGallery();
    initializeTooltips();
    initializePrintFunctionality();
});

// Performance monitoring
window.addEventListener('load', function() {
    console.log('Agricultural Engineering Website loaded successfully');
    
    // Log performance metrics
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`Page load time: ${loadTime}ms`);
    }
});









/**
 * Agricultural and Environmental Engineering Department Website
 * JavaScript functionality for enhanced user experience
 */

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function() {
    initializeScrollSpy();
    initializeAnimations();
    initializeFormValidation();
    initializeNavbarBehavior();
    initializeSmoothScrolling();
    initializeFlashMessageHandling();
    handleContactFormSubmission();
});

/**
 * Initialize Bootstrap ScrollSpy for navigation
 */
function initializeScrollSpy() {
    // Bootstrap ScrollSpy is initialized via data attributes in HTML
    // Additional custom behavior can be added here
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
            
            // Close mobile menu if open
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    });
}

/**
 * Initialize scroll animations
 */
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, observerOptions);

    // Observe all animatable elements
    const animateElements = document.querySelectorAll('.card, .notice-item, .gallery-item');
    animateElements.forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            if (!validateContactForm()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            contactForm.classList.add('was-validated');
        });
    }
}

/**
 * Validate contact form
 */
function validateContactForm() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value.trim();
    
    let isValid = true;
    
    // Name validation
    if (name.length < 2) {
        showFieldError('name', 'Name must be at least 2 characters long');
        isValid = false;
    } else {
        clearFieldError('name');
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    } else {
        clearFieldError('email');
    }
    
    // Subject validation
    if (subject === '') {
        showFieldError('subject', 'Please select a subject');
        isValid = false;
    } else {
        clearFieldError('subject');
    }
    
    // Message validation
    if (message.length < 10) {
        showFieldError('message', 'Message must be at least 10 characters long');
        isValid = false;
    } else {
        clearFieldError('message');
    }
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const existingError = field.parentNode.querySelector('.field-error');
    
    if (existingError) {
        existingError.textContent = message;
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-danger small mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
    
    field.classList.add('is-invalid');
}

/**
 * Clear field error
 */
function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorDiv = field.parentNode.querySelector('.field-error');
    
    if (errorDiv) {
        errorDiv.remove();
    }
    
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
}

/**
 * Initialize navbar behavior
 */
function initializeNavbarBehavior() {
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove shadow based on scroll position
        if (currentScrollTop > 50) {
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.2)';
        } else {
            navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
        
        // Update active navigation link based on scroll position
        updateActiveNavLink();
        
        lastScrollTop = currentScrollTop;
    });
}

/**
 * Update active navigation link based on current section
 */
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    let current = '';
    const scrollTop = window.pageYOffset;
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        const sectionHeight = section.offsetHeight;
        
        if (scrollTop >= sectionTop && scrollTop < sectionTop + sectionHeight) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                const offsetTop = targetElement.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Initialize flash message handling
 */
function initializeFlashMessageHandling() {
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    
    flashMessages.forEach(message => {
        // Auto-hide success messages after 5 seconds
        if (message.classList.contains('alert-success')) {
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.parentNode.removeChild(message);
                    }
                }, 300);
            }, 5000);
        }
    });
}

/**
 * Handle contact form submission with loading state
 */
function handleContactFormSubmission() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function() {
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // Show loading state
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
            submitButton.disabled = true;
            
            // Note: The actual form submission is handled by Flask
            // This is just for UI feedback
        });
    }
}

/**
 * Initialize gallery lightbox functionality
 */
function initializeGallery() {
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            // This would open a lightbox or modal for gallery images
            // For now, we'll just add a click effect
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

/**
 * Initialize search functionality (if needed)
 */
function initializeSearch() {
    const searchInput = document.querySelector('#searchInput');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            if (query.length > 2) {
                // Implement search logic here
                highlightSearchResults(query);
            } else {
                clearSearchHighlights();
            }
        });
    }
}

/**
 * Highlight search results
 */
function highlightSearchResults(query) {
    // This function would highlight search terms in the content
    const textNodes = getTextNodes(document.body);
    
    textNodes.forEach(node => {
        if (node.textContent.toLowerCase().includes(query)) {
            // Highlight matching text
            const parent = node.parentNode;
            const wrapper = document.createElement('span');
            wrapper.className = 'search-highlight';
            
            const text = node.textContent;
            const regex = new RegExp(`(${query})`, 'gi');
            wrapper.innerHTML = text.replace(regex, '<mark>$1</mark>');
            
            parent.replaceChild(wrapper, node);
        }
    });
}

/**
 * Clear search highlights
 */
function clearSearchHighlights() {
    const highlights = document.querySelectorAll('.search-highlight');
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
    });
}

/**
 * Get all text nodes in an element
 */
function getTextNodes(element) {
    const textNodes = [];
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim().length > 0) {
            textNodes.push(node);
        }
    }
    
    return textNodes;
}

/**
 * Initialize tooltip functionality
 */
function initializeTooltips() {
    // Initialize Bootstrap tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize print functionality
 */
function initializePrintFunctionality() {
    const printButtons = document.querySelectorAll('.print-btn');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });
}

/**
 * Handle back to top functionality
 */
function initializeBackToTop() {
    // Create back to top button
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTopButton.className = 'btn btn-primary btn-back-to-top position-fixed';
    backToTopButton.style.cssText = `
        bottom: 30px;
        right: 30px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(backToTopButton);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.opacity = '1';
            backToTopButton.style.visibility = 'visible';
        } else {
            backToTopButton.style.opacity = '0';
            backToTopButton.style.visibility = 'hidden';
        }
    });
    
    // Smooth scroll to top
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize back to top on load
document.addEventListener('DOMContentLoaded', function() {
    initializeBackToTop();
});

/**
 * Utility function to debounce rapid function calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        // Escape key closes any open modals or dropdowns
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
        
        // Enter key on card elements triggers click
        if (e.key === 'Enter' && e.target.classList.contains('card')) {
            e.target.click();
        }
    });
    
    // Add focus indicators for keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
}

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAccessibility();
    initializeGallery();
    initializeTooltips();
    initializePrintFunctionality();
    initializePaymentPortal();
});

// Performance monitoring
window.addEventListener('load', function() {
    console.log('Agricultural Engineering Website loaded successfully');
    
    // Log performance metrics
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`Page load time: ${loadTime}ms`);
    }
});

/**
 * ================================
 * PAYMENT PORTAL FUNCTIONALITY
 * ================================
 */

/**
 * Initialize payment portal features
 */
function initializePaymentPortal() {
    // Check if we're on the payment page
    if (!document.getElementById('payment-main')) return;
    
    initializePaymentCalculator();
    initializeLevelBasedOptions();
    initializeReceiptUpload();
    initializeFormValidation();
    initializePaymentSubmission();
    console.log('Payment portal initialized successfully');
}

/**
 * Initialize payment calculator functionality
 */
function initializePaymentCalculator() {
    const checkboxes = document.querySelectorAll('.payment-checkbox');
    const totalAmountElement = document.getElementById('totalAmount');
    const selectedItemsElement = document.getElementById('selectedItems');
    
    if (!checkboxes.length || !totalAmountElement) return;
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updatePaymentSummary();
            updateSelectedItems();
        });
    });
    
    // Initial calculation
    updatePaymentSummary();
    updateSelectedItems();
}

/**
 * Update payment summary total
 */
function updatePaymentSummary() {
    const checkboxes = document.querySelectorAll('.payment-checkbox:checked');
    const totalAmountElement = document.getElementById('totalAmount');
    
    let total = 0;
    checkboxes.forEach(checkbox => {
        total += parseInt(checkbox.value) || 0;
        
        // Add visual feedback to selected items
        const paymentItem = checkbox.closest('.payment-item');
        if (paymentItem) {
            if (checkbox.checked) {
                paymentItem.classList.add('selected');
            } else {
                paymentItem.classList.remove('selected');
            }
        }
    });
    
    if (totalAmountElement) {
        totalAmountElement.textContent = `₦${total.toLocaleString()}`;
        
        // Add animation effect
        totalAmountElement.style.transform = 'scale(1.1)';
        setTimeout(() => {
            totalAmountElement.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Update selected items list
 */
function updateSelectedItems() {
    const checkboxes = document.querySelectorAll('.payment-checkbox:checked');
    const selectedItemsElement = document.getElementById('selectedItems');
    
    if (!selectedItemsElement) return;
    
    if (checkboxes.length === 0) {
        selectedItemsElement.innerHTML = '<small class="text-muted">Selected items will appear here</small>';
        return;
    }
    
    let itemsHTML = '';
    checkboxes.forEach(checkbox => {
        const name = checkbox.getAttribute('data-name') || 'Unknown Item';
        const amount = parseInt(checkbox.value) || 0;
        
        itemsHTML += `
            <div class="selected-item">
                <span class="item-name">${name}</span>
                <span class="item-amount">₦${amount.toLocaleString()}</span>
            </div>
        `;
    });
    
    selectedItemsElement.innerHTML = itemsHTML;
}

/**
 * Initialize level-based payment options
 */
function initializeLevelBasedOptions() {
    const levelSelect = document.getElementById('level');
    const industrialTrainingCheckbox = document.getElementById('industrialTraining');
    const projectSupervisionCheckbox = document.getElementById('projectSupervision');
    
    if (!levelSelect) return;
    
    levelSelect.addEventListener('change', function() {
        const selectedLevel = parseInt(this.value);
        
        // Update level-specific styling
        updateLevelStyling(selectedLevel);
        
        // Enable/disable level-specific options
        if (industrialTrainingCheckbox) {
            if (selectedLevel >= 400) {
                industrialTrainingCheckbox.disabled = false;
                industrialTrainingCheckbox.closest('.payment-item').style.opacity = '1';
            } else {
                industrialTrainingCheckbox.disabled = true;
                industrialTrainingCheckbox.checked = false;
                industrialTrainingCheckbox.closest('.payment-item').style.opacity = '0.6';
            }
        }
        
        if (projectSupervisionCheckbox) {
            if (selectedLevel === 500) {
                projectSupervisionCheckbox.disabled = false;
                projectSupervisionCheckbox.closest('.payment-item').style.opacity = '1';
            } else {
                projectSupervisionCheckbox.disabled = true;
                projectSupervisionCheckbox.checked = false;
                projectSupervisionCheckbox.closest('.payment-item').style.opacity = '0.6';
            }
        }
        
        // Update amounts based on level (if needed)
        updateLevelBasedAmounts(selectedLevel);
        
        // Recalculate totals
        updatePaymentSummary();
        updateSelectedItems();
    });
}

/**
 * Update styling based on selected level
 */
function updateLevelStyling(level) {
    const paymentItems = document.querySelectorAll('.payment-item');
    
    // Remove existing level classes
    paymentItems.forEach(item => {
        item.classList.remove('level-100', 'level-200', 'level-300', 'level-400', 'level-500');
    });
    
    // Add new level class
    if (level) {
        paymentItems.forEach(item => {
            item.classList.add(`level-${level}`);
        });
    }
}

/**
 * Update amounts based on level (example: different pricing for different levels)
 */
function updateLevelBasedAmounts(level) {
    // Example: Adjust examination fee based on level
    const examFeeCheckbox = document.getElementById('examFee');
    const examFeeAmountElement = document.getElementById('examFeeAmount');
    
    if (examFeeCheckbox && examFeeAmountElement) {
        let examFee = 3000; // Base fee
        
        // Adjust fee based on level
        switch(level) {
            case 500:
                examFee = 5000; // Higher fee for final year
                break;
            case 400:
                examFee = 4000; // Higher fee for 4th year
                break;
            default:
                examFee = 3000;
        }
        
        examFeeCheckbox.value = examFee;
        examFeeAmountElement.textContent = `₦${examFee.toLocaleString()}`;
    }
}

/**
 * Initialize receipt upload functionality
 */
function initializeReceiptUpload() {
    const receiptInput = document.getElementById('paymentReceipt');
    const receiptPreview = document.getElementById('receiptPreview');
    const receiptImage = document.getElementById('receiptImage');
    
    if (!receiptInput) return;
    
    receiptInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
            if (!allowedTypes.includes(file.type)) {
                showPaymentError('Please upload a valid file (JPG, PNG, or PDF)');
                this.value = '';
                return;
            }
            
            // Validate file size (5MB max)
            const maxSize = 5 * 1024 * 1024; // 5MB
            if (file.size > maxSize) {
                showPaymentError('File size must be less than 5MB');
                this.value = '';
                return;
            }
            
            // Show preview for images
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    receiptImage.src = e.target.result;
                    receiptPreview.style.display = 'block';
                    
                    // Add success feedback
                    receiptInput.classList.add('is-valid');
                    receiptInput.classList.remove('is-invalid');
                };
                reader.readAsDataURL(file);
            } else if (file.type === 'application/pdf') {
                receiptPreview.style.display = 'none';
                receiptInput.classList.add('is-valid');
                receiptInput.classList.remove('is-invalid');
                showPaymentSuccess('PDF receipt uploaded successfully');
            }
        } else {
            receiptPreview.style.display = 'none';
            receiptInput.classList.remove('is-valid', 'is-invalid');
        }
    });
    
    // Drag and drop functionality
    const uploadArea = receiptInput.closest('.card-body');
    if (uploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            uploadArea.classList.add('drag-over');
        }
        
        function unhighlight(e) {
            uploadArea.classList.remove('drag-over');
        }
        
        uploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                receiptInput.files = files;
                receiptInput.dispatchEvent(new Event('change'));
            }
        }
    }
}

/**
 * Initialize form validation for payment portal
 */
function initializeFormValidation() {
    const form = document.getElementById('studentInfoForm');
    const inputs = form ? form.querySelectorAll('input, select') : [];
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validatePaymentField(this);
        });
        
        input.addEventListener('input', function() {
            // Clear validation state on input
            this.classList.remove('is-valid', 'is-invalid');
        });
    });
}

/**
 * Validate individual payment form field
 */
function validatePaymentField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    switch(field.id) {
        case 'fullName':
            isValid = value.length >= 2;
            errorMessage = 'Full name must be at least 2 characters';
            break;
            
        case 'matricNumber':
            isValid = /^\d{6}$/.test(value);
            errorMessage = 'Matric number must be 6 digits';
            break;
            
        case 'email':
            isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            errorMessage = 'Please enter a valid email address';
            break;
            
        case 'phoneNumber':
            isValid = /^(\+234|0)[789]\d{9}$/.test(value.replace(/\s/g, ''));
            errorMessage = 'Please enter a valid Nigerian phone number';
            break;
            
        case 'level':
            isValid = value !== '';
            errorMessage = 'Please select your academic level';
            break;
    }
    
    if (isValid) {
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
        clearFieldError(field.id);
    } else {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        showFieldError(field.id, errorMessage);
    }
    
    return isValid;
}

/**
 * Initialize payment submission
 */
function initializePaymentSubmission() {
    const submitButton = document.getElementById('submitPayment');
    
    if (!submitButton) return;
    
    submitButton.addEventListener('click', function() {
        if (validatePaymentForm()) {
            submitPaymentForm();
        }
    });
}

/**
 * Validate entire payment form
 */
function validatePaymentForm() {
    const form = document.getElementById('studentInfoForm');
    const requiredFields = form ? form.querySelectorAll('input[required], select[required]') : [];
    const receiptInput = document.getElementById('paymentReceipt');
    const selectedItems = document.querySelectorAll('.payment-checkbox:checked');
    
    let isValid = true;
    
    // Validate student information
    requiredFields.forEach(field => {
        if (!validatePaymentField(field)) {
            isValid = false;
        }
    });
    
    // Validate receipt upload
    if (!receiptInput.files.length) {
        showPaymentError('Please upload your payment receipt');
        receiptInput.classList.add('is-invalid');
        isValid = false;
    }
    
    // Validate selected items
    if (selectedItems.length === 0) {
        showPaymentError('Please select at least one payment item');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Submit payment form
 */
function submitPaymentForm() {
    const submitButton = document.getElementById('submitPayment');
    const originalText = submitButton.innerHTML;
    
    // Show loading state
    submitButton.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
    submitButton.disabled = true;
    
    // Collect form data
    const formData = new FormData();
    
    // Student information
    formData.append('fullName', document.getElementById('fullName').value);
    formData.append('matricNumber', document.getElementById('matricNumber').value);
    formData.append('level', document.getElementById('level').value);
    formData.append('email', document.getElementById('email').value);
    formData.append('phoneNumber', document.getElementById('phoneNumber').value);
    
    // Selected payment items
    const selectedItems = document.querySelectorAll('.payment-checkbox:checked');
    const items = Array.from(selectedItems).map(checkbox => ({
        name: checkbox.getAttribute('data-name'),
        amount: parseInt(checkbox.value)
    }));
    formData.append('paymentItems', JSON.stringify(items));
    
    // Total amount
    const totalAmount = document.getElementById('totalAmount').textContent.replace('₦', '').replace(',', '');
    formData.append('totalAmount', totalAmount);
    
    // Receipt file
    const receiptFile = document.getElementById('paymentReceipt').files[0];
    if (receiptFile) {
        formData.append('receipt', receiptFile);
    }
    
    // Additional information
    formData.append('transactionRef', document.getElementById('transactionRef').value);
    formData.append('paymentDate', document.getElementById('paymentDate').value);
    
    // Simulate form submission (replace with actual endpoint)
    setTimeout(() => {
        // Success simulation
        showPaymentSuccess('Payment information submitted successfully! You will receive a confirmation email shortly.');
        
        // Reset button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
        
        // Optionally scroll to success message
        document.querySelector('.payment-success, .alert-success')?.scrollIntoView({ behavior: 'smooth' });
        
    }, 2000);
}

/**
 * Show payment success message
 */
function showPaymentSuccess(message) {
    removeExistingAlerts();
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('#payment-main .container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
    }
}

/**
 * Show payment error message
 */
function showPaymentError(message) {
    removeExistingAlerts();
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('#payment-main .container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
    }
}

/**
 * Remove existing alert messages
 */
function removeExistingAlerts() {
    const existingAlerts = document.querySelectorAll('#payment-main .alert');
    existingAlerts.forEach(alert => alert.remove());
}

/**
 * Format Nigerian phone number
 */
function formatPhoneNumber(phoneInput) {
    phoneInput.addEventListener('input', function() {
        let value = this.value.replace(/\D/g, '');
        
        if (value.startsWith('234')) {
            value = '+' + value;
        } else if (value.startsWith('0')) {
            value = '+234' + value.substring(1);
        } else if (value.length === 10) {
            value = '+234' + value;
        }
        
        this.value = value;
    });
}

// Auto-format phone number if field exists
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phoneNumber');
    if (phoneInput) {
        formatPhoneNumber(phoneInput);
    }
});





/**
 * Agricultural and Environmental Engineering Department Website
 * JavaScript functionality for enhanced user experience
 */

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function() {
    initializeScrollSpy();
    initializeAnimations();
    initializeFormValidation();
    initializeNavbarBehavior();
    initializeSmoothScrolling();
    initializeFlashMessageHandling();
    handleContactFormSubmission();
});

/**
 * Initialize Bootstrap ScrollSpy for navigation
 */
function initializeScrollSpy() {
    // Bootstrap ScrollSpy is initialized via data attributes in HTML
    // Additional custom behavior can be added here
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
            
            // Close mobile menu if open
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    });
}

/**
 * Initialize scroll animations
 */
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, observerOptions);

    // Observe all animatable elements
    const animateElements = document.querySelectorAll('.card, .notice-item, .gallery-item');
    animateElements.forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            if (!validateContactForm()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            contactForm.classList.add('was-validated');
        });
    }
}

/**
 * Validate contact form
 */
function validateContactForm() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value.trim();
    
    let isValid = true;
    
    // Name validation
    if (name.length < 2) {
        showFieldError('name', 'Name must be at least 2 characters long');
        isValid = false;
    } else {
        clearFieldError('name');
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    } else {
        clearFieldError('email');
    }
    
    // Subject validation
    if (subject === '') {
        showFieldError('subject', 'Please select a subject');
        isValid = false;
    } else {
        clearFieldError('subject');
    }
    
    // Message validation
    if (message.length < 10) {
        showFieldError('message', 'Message must be at least 10 characters long');
        isValid = false;
    } else {
        clearFieldError('message');
    }
    
    return isValid;
}

/**
 * Show field error
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const existingError = field.parentNode.querySelector('.field-error');
    
    if (existingError) {
        existingError.textContent = message;
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-danger small mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
    
    field.classList.add('is-invalid');
}

/**
 * Clear field error
 */
function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorDiv = field.parentNode.querySelector('.field-error');
    
    if (errorDiv) {
        errorDiv.remove();
    }
    
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
}

/**
 * Initialize navbar behavior
 */
function initializeNavbarBehavior() {
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove shadow based on scroll position
        if (currentScrollTop > 50) {
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.2)';
        } else {
            navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
        
        // Update active navigation link based on scroll position
        updateActiveNavLink();
        
        lastScrollTop = currentScrollTop;
    });
}

/**
 * Update active navigation link based on current section
 */
function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    let current = '';
    const scrollTop = window.pageYOffset;
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        const sectionHeight = section.offsetHeight;
        
        if (scrollTop >= sectionTop && scrollTop < sectionTop + sectionHeight) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                const offsetTop = targetElement.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Initialize flash message handling
 */
function initializeFlashMessageHandling() {
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    
    flashMessages.forEach(message => {
        // Auto-hide success messages after 5 seconds
        if (message.classList.contains('alert-success')) {
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.parentNode.removeChild(message);
                    }
                }, 300);
            }, 5000);
        }
    });
}

/**
 * Handle contact form submission with loading state
 */
function handleContactFormSubmission() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function() {
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // Show loading state
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
            submitButton.disabled = true;
            
            // Note: The actual form submission is handled by Flask
            // This is just for UI feedback
        });
    }
}

/**
 * Initialize gallery lightbox functionality
 */
function initializeGallery() {
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
        item.addEventListener('click', function() {
            // This would open a lightbox or modal for gallery images
            // For now, we'll just add a click effect
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

/**
 * Initialize search functionality (if needed)
 */
function initializeSearch() {
    const searchInput = document.querySelector('#searchInput');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            if (query.length > 2) {
                // Implement search logic here
                highlightSearchResults(query);
            } else {
                clearSearchHighlights();
            }
        });
    }
}

/**
 * Highlight search results
 */
function highlightSearchResults(query) {
    // This function would highlight search terms in the content
    const textNodes = getTextNodes(document.body);
    
    textNodes.forEach(node => {
        if (node.textContent.toLowerCase().includes(query)) {
            // Highlight matching text
            const parent = node.parentNode;
            const wrapper = document.createElement('span');
            wrapper.className = 'search-highlight';
            
            const text = node.textContent;
            const regex = new RegExp(`(${query})`, 'gi');
            wrapper.innerHTML = text.replace(regex, '<mark>$1</mark>');
            
            parent.replaceChild(wrapper, node);
        }
    });
}

/**
 * Clear search highlights
 */
function clearSearchHighlights() {
    const highlights = document.querySelectorAll('.search-highlight');
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
    });
}

/**
 * Get all text nodes in an element
 */
function getTextNodes(element) {
    const textNodes = [];
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim().length > 0) {
            textNodes.push(node);
        }
    }
    
    return textNodes;
}

/**
 * Initialize tooltip functionality
 */
function initializeTooltips() {
    // Initialize Bootstrap tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize print functionality
 */
function initializePrintFunctionality() {
    const printButtons = document.querySelectorAll('.print-btn');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });
}

/**
 * Handle back to top functionality
 */
function initializeBackToTop() {
    // Create back to top button
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTopButton.className = 'btn btn-primary btn-back-to-top position-fixed';
    backToTopButton.style.cssText = `
        bottom: 30px;
        right: 30px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(backToTopButton);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.opacity = '1';
            backToTopButton.style.visibility = 'visible';
        } else {
            backToTopButton.style.opacity = '0';
            backToTopButton.style.visibility = 'hidden';
        }
    });
    
    // Smooth scroll to top
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Initialize back to top on load
document.addEventListener('DOMContentLoaded', function() {
    initializeBackToTop();
});

/**
 * Utility function to debounce rapid function calls
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        // Escape key closes any open modals or dropdowns
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
        }
        
        // Enter key on card elements triggers click
        if (e.key === 'Enter' && e.target.classList.contains('card')) {
            e.target.click();
        }
    });
    
    // Add focus indicators for keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
}

// Initialize all functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAccessibility();
    initializeGallery();
    initializeTooltips();
    initializePrintFunctionality();
    initializePaymentPortal();
});

// Performance monitoring
window.addEventListener('load', function() {
    console.log('Agricultural Engineering Website loaded successfully');
    
    // Log performance metrics
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`Page load time: ${loadTime}ms`);
    }
});

/**
 * ================================
 * PAYMENT PORTAL FUNCTIONALITY
 * ================================
 */

/**
 * Initialize payment portal features
 */
function initializePaymentPortal() {
    // Check if we're on the payment page
    if (!document.getElementById('payment-main')) return;
    
    initializePaymentCalculator();
    initializeLevelBasedOptions();
    initializeReceiptUpload();
    initializeFormValidation();
    initializePaymentSubmission();
    console.log('Payment portal initialized successfully');
}

/**
 * Initialize payment calculator functionality
 */
function initializePaymentCalculator() {
    const checkboxes = document.querySelectorAll('.payment-checkbox');
    const totalAmountElement = document.getElementById('totalAmount');
    const selectedItemsElement = document.getElementById('selectedItems');
    
    if (!checkboxes.length || !totalAmountElement) return;
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updatePaymentSummary();
            updateSelectedItems();
        });
    });
    
    // Initial calculation
    updatePaymentSummary();
    updateSelectedItems();
}

/**
 * Update payment summary total
 */
function updatePaymentSummary() {
    const checkboxes = document.querySelectorAll('.payment-checkbox:checked');
    const totalAmountElement = document.getElementById('totalAmount');
    
    let total = 0;
    checkboxes.forEach(checkbox => {
        total += parseInt(checkbox.value) || 0;
        
        // Add visual feedback to selected items
        const paymentItem = checkbox.closest('.payment-item');
        if (paymentItem) {
            if (checkbox.checked) {
                paymentItem.classList.add('selected');
            } else {
                paymentItem.classList.remove('selected');
            }
        }
    });
    
    if (totalAmountElement) {
        totalAmountElement.textContent = `₦${total.toLocaleString()}`;
        
        // Add animation effect
        totalAmountElement.style.transform = 'scale(1.1)';
        setTimeout(() => {
            totalAmountElement.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Update selected items list
 */
function updateSelectedItems() {
    const checkboxes = document.querySelectorAll('.payment-checkbox:checked');
    const selectedItemsElement = document.getElementById('selectedItems');
    
    if (!selectedItemsElement) return;
    
    if (checkboxes.length === 0) {
        selectedItemsElement.innerHTML = '<small class="text-muted">Selected items will appear here</small>';
        return;
    }
    
    let itemsHTML = '';
    checkboxes.forEach(checkbox => {
        const name = checkbox.getAttribute('data-name') || 'Unknown Item';
        const amount = parseInt(checkbox.value) || 0;
        
        itemsHTML += `
            <div class="selected-item">
                <span class="item-name">${name}</span>
                <span class="item-amount">₦${amount.toLocaleString()}</span>
            </div>
        `;
    });
    
    selectedItemsElement.innerHTML = itemsHTML;
}

/**
 * Initialize level-based payment options
 */
function initializeLevelBasedOptions() {
    const levelSelect = document.getElementById('level');
    const industrialTrainingCheckbox = document.getElementById('industrialTraining');
    const projectSupervisionCheckbox = document.getElementById('projectSupervision');
    
    if (!levelSelect) return;
    
    levelSelect.addEventListener('change', function() {
        const selectedLevel = parseInt(this.value);
        
        // Update level-specific styling
        updateLevelStyling(selectedLevel);
        
        // Enable/disable level-specific options
        if (industrialTrainingCheckbox) {
            if (selectedLevel >= 400) {
                industrialTrainingCheckbox.disabled = false;
                industrialTrainingCheckbox.closest('.payment-item').style.opacity = '1';
            } else {
                industrialTrainingCheckbox.disabled = true;
                industrialTrainingCheckbox.checked = false;
                industrialTrainingCheckbox.closest('.payment-item').style.opacity = '0.6';
            }
        }
        
        if (projectSupervisionCheckbox) {
            if (selectedLevel === 500) {
                projectSupervisionCheckbox.disabled = false;
                projectSupervisionCheckbox.closest('.payment-item').style.opacity = '1';
            } else {
                projectSupervisionCheckbox.disabled = true;
                projectSupervisionCheckbox.checked = false;
                projectSupervisionCheckbox.closest('.payment-item').style.opacity = '0.6';
            }
        }
        
        // Update amounts based on level (if needed)
        updateLevelBasedAmounts(selectedLevel);
        
        // Recalculate totals
        updatePaymentSummary();
        updateSelectedItems();
    });
}

/**
 * Update styling based on selected level
 */
function updateLevelStyling(level) {
    const paymentItems = document.querySelectorAll('.payment-item');
    
    // Remove existing level classes
    paymentItems.forEach(item => {
        item.classList.remove('level-100', 'level-200', 'level-300', 'level-400', 'level-500');
    });
    
    // Add new level class
    if (level) {
        paymentItems.forEach(item => {
            item.classList.add(`level-${level}`);
        });
    }
}

/**
 * Update amounts based on level (example: different pricing for different levels)
 */
function updateLevelBasedAmounts(level) {
    // Example: Adjust examination fee based on level
    const examFeeCheckbox = document.getElementById('examFee');
    const examFeeAmountElement = document.getElementById('examFeeAmount');
    
    if (examFeeCheckbox && examFeeAmountElement) {
        let examFee = 3000; // Base fee
        
        // Adjust fee based on level
        switch(level) {
            case 500:
                examFee = 5000; // Higher fee for final year
                break;
            case 400:
                examFee = 4000; // Higher fee for 4th year
                break;
            default:
                examFee = 3000;
        }
        
        examFeeCheckbox.value = examFee;
        examFeeAmountElement.textContent = `₦${examFee.toLocaleString()}`;
    }
}

/**
 * Initialize receipt upload functionality
 */
function initializeReceiptUpload() {
    const receiptInput = document.getElementById('paymentReceipt');
    const receiptPreview = document.getElementById('receiptPreview');
    const receiptImage = document.getElementById('receiptImage');
    
    if (!receiptInput) return;
    
    receiptInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
            if (!allowedTypes.includes(file.type)) {
                showPaymentError('Please upload a valid file (JPG, PNG, or PDF)');
                this.value = '';
                return;
            }
            
            // Validate file size (5MB max)
            const maxSize = 5 * 1024 * 1024; // 5MB
            if (file.size > maxSize) {
                showPaymentError('File size must be less than 5MB');
                this.value = '';
                return;
            }
            
            // Show preview for images
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    receiptImage.src = e.target.result;
                    receiptPreview.style.display = 'block';
                    
                    // Add success feedback
                    receiptInput.classList.add('is-valid');
                    receiptInput.classList.remove('is-invalid');
                };
                reader.readAsDataURL(file);
            } else if (file.type === 'application/pdf') {
                receiptPreview.style.display = 'none';
                receiptInput.classList.add('is-valid');
                receiptInput.classList.remove('is-invalid');
                showPaymentSuccess('PDF receipt uploaded successfully');
            }
        } else {
            receiptPreview.style.display = 'none';
            receiptInput.classList.remove('is-valid', 'is-invalid');
        }
    });
    
    // Drag and drop functionality
    const uploadArea = receiptInput.closest('.card-body');
    if (uploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            uploadArea.classList.add('drag-over');
        }
        
        function unhighlight(e) {
            uploadArea.classList.remove('drag-over');
        }
        
        uploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                receiptInput.files = files;
                receiptInput.dispatchEvent(new Event('change'));
            }
        }
    }
}

/**
 * Initialize form validation for payment portal
 */
function initializeFormValidation() {
    const form = document.getElementById('studentInfoForm');
    const inputs = form ? form.querySelectorAll('input, select') : [];
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validatePaymentField(this);
        });
        
        input.addEventListener('input', function() {
            // Clear validation state on input
            this.classList.remove('is-valid', 'is-invalid');
        });
    });
}

/**
 * Validate individual payment form field
 */
function validatePaymentField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    switch(field.id) {
        case 'fullName':
            isValid = value.length >= 2;
            errorMessage = 'Full name must be at least 2 characters';
            break;
            
        case 'matricNumber':
            isValid = /^\d{6}$/.test(value);
            errorMessage = 'Matric number must be 6 digits';
            break;
            
        case 'email':
            isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            errorMessage = 'Please enter a valid email address';
            break;
            
        case 'phoneNumber':
            isValid = /^(\+234|0)[789]\d{9}$/.test(value.replace(/\s/g, ''));
            errorMessage = 'Please enter a valid Nigerian phone number';
            break;
            
        case 'level':
            isValid = value !== '';
            errorMessage = 'Please select your academic level';
            break;
    }
    
    if (isValid) {
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
        clearFieldError(field.id);
    } else {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        showFieldError(field.id, errorMessage);
    }
    
    return isValid;
}

/**
 * Initialize payment submission
 */
function initializePaymentSubmission() {
    const submitButton = document.getElementById('submitPayment');
    
    if (!submitButton) return;
    
    submitButton.addEventListener('click', function() {
        if (validatePaymentForm()) {
            submitPaymentForm();
        }
    });
}

/**
 * Validate entire payment form
 */
function validatePaymentForm() {
    const form = document.getElementById('studentInfoForm');
    const requiredFields = form ? form.querySelectorAll('input[required], select[required]') : [];
    const receiptInput = document.getElementById('paymentReceipt');
    const selectedItems = document.querySelectorAll('.payment-checkbox:checked');
    
    let isValid = true;
    
    // Validate student information
    requiredFields.forEach(field => {
        if (!validatePaymentField(field)) {
            isValid = false;
        }
    });
    
    // Validate receipt upload
    if (!receiptInput.files.length) {
        showPaymentError('Please upload your payment receipt');
        receiptInput.classList.add('is-invalid');
        isValid = false;
    }
    
    // Validate selected items
    if (selectedItems.length === 0) {
        showPaymentError('Please select at least one payment item');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Submit payment form
 */
function submitPaymentForm() {
    const submitButton = document.getElementById('submitPayment');
    const originalText = submitButton.innerHTML;
    
    // Show loading state
    submitButton.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
    submitButton.disabled = true;
    
    // Collect form data
    const formData = new FormData();
    
    // Student information
    formData.append('fullName', document.getElementById('fullName').value);
    formData.append('matricNumber', document.getElementById('matricNumber').value);
    formData.append('level', document.getElementById('level').value);
    formData.append('email', document.getElementById('email').value);
    formData.append('phoneNumber', document.getElementById('phoneNumber').value);
    
    // Selected payment items
    const selectedItems = document.querySelectorAll('.payment-checkbox:checked');
    const items = Array.from(selectedItems).map(checkbox => ({
        name: checkbox.getAttribute('data-name'),
        amount: parseInt(checkbox.value)
    }));
    formData.append('paymentItems', JSON.stringify(items));
    
    // Total amount
    const totalAmount = document.getElementById('totalAmount').textContent.replace('₦', '').replace(',', '');
    formData.append('totalAmount', totalAmount);
    
    // Receipt file
    const receiptFile = document.getElementById('paymentReceipt').files[0];
    if (receiptFile) {
        formData.append('receipt', receiptFile);
    }
    
    // Additional information
    formData.append('transactionRef', document.getElementById('transactionRef').value);
    formData.append('paymentDate', document.getElementById('paymentDate').value);
    
    // Submit form to server
    fetch('/submit-payment', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPaymentSuccess(`${data.message} Your submission ID is: ${data.payment_id}`);
            // Clear form
            document.getElementById('studentInfoForm').reset();
            document.getElementById('paymentReceipt').value = '';
            document.getElementById('transactionRef').value = '';
            document.getElementById('paymentDate').value = '';
            document.getElementById('receiptPreview').style.display = 'none';
            // Reset checkboxes
            document.querySelectorAll('.payment-checkbox').forEach(cb => {
                if (!cb.disabled || cb.id === 'departmentalDues' || cb.id === 'examFee') {
                    cb.checked = cb.disabled;
                }
            });
            updatePaymentSummary();
            updateSelectedItems();
        } else {
            showPaymentError(data.error || 'Error submitting payment. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showPaymentError('Network error. Please check your connection and try again.');
    })
    .finally(() => {
        // Reset button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
        
        // Scroll to message
        document.querySelector('.alert')?.scrollIntoView({ behavior: 'smooth' });
    });
}

/**
 * Show payment success message
 */
function showPaymentSuccess(message) {
    removeExistingAlerts();
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('#payment-main .container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
    }
}

/**
 * Show payment error message
 */
function showPaymentError(message) {
    removeExistingAlerts();
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('#payment-main .container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
    }
}

/**
 * Remove existing alert messages
 */
function removeExistingAlerts() {
    const existingAlerts = document.querySelectorAll('#payment-main .alert');
    existingAlerts.forEach(alert => alert.remove());
}

/**
 * Format Nigerian phone number
 */
function formatPhoneNumber(phoneInput) {
    phoneInput.addEventListener('input', function() {
        let value = this.value.replace(/\D/g, '');
        
        if (value.startsWith('234')) {
            value = '+' + value;
        } else if (value.startsWith('0')) {
            value = '+234' + value.substring(1);
        } else if (value.length === 10) {
            value = '+234' + value;
        }
        
        this.value = value;
    });
}

// Auto-format phone number if field exists
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phoneNumber');
    if (phoneInput) {
        formatPhoneNumber(phoneInput);
    }
});



//New

// University of Ibadan Agricultural and Environmental Engineering Portal
// Main JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize common functionality
    initializeAlerts();
    initializeFormsValidation();
    initializeMobileMenu();
});

// Alert management
function initializeAlerts() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

// Form validation
function initializeFormsValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Specific validations
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
    });
    
    const phoneFields = form.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(field => {
        if (field.value && !isValidPhone(field.value)) {
            showFieldError(field, 'Please enter a valid phone number');
            isValid = false;
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-danger';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
    field.style.borderColor = '#dc3545';
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.style.borderColor = '';
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[0-9\-\s\(\)]{10,}$/;
    return phoneRegex.test(phone);
}

// Mobile menu functionality
function initializeMobileMenu() {
    // Handle responsive navigation
    const navTabs = document.querySelector('.nav-tabs');
    if (navTabs) {
        // Add scroll indicators for mobile
        if (navTabs.scrollWidth > navTabs.clientWidth) {
            navTabs.classList.add('scrollable');
        }
    }
}

//Analytics




// Utility functions for admin dashboard
function toggleStudentStatus(studentId, isActive) {
    fetch('/admin/toggle-student-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: studentId, is_active: !isActive })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadStudents(); // refresh the student table
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error toggling student status:', error);
    });
}


function deleteResult(resultId) {
    if (confirm('Are you sure you want to delete this result? This action cannot be undone.')) {
        fetch('/admin/delete-result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ result_id: resultId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) location.reload();
            else alert('Error: ' + data.message);
        })
        .catch(err => {
            console.error('Error:', err);
            alert('An error occurred. Please try again.');
        });
    }
}

// Grade calculation utility
function calculateGradePoints(score, level) {
    if (level === 100) {
        if (score >= 70) return 5.0;
        else if (score >= 60) return 4.0;
        else if (score >= 50) return 3.0;
        else if (score >= 45) return 2.0;
        else if (score >= 40) return 1.0;
        else return 0.0;
    } else {
        if (score >= 70) return 4.0;
        else if (score >= 60) return 3.0;
        else if (score >= 50) return 2.0;
        else if (score >= 45) return 1.0;
        else return 0.0;
    }
}

function getLetterGrade(score) {
    if (score >= 70) return 'A';
    else if (score >= 60) return 'B';
    else if (score >= 50) return 'C';
    else if (score >= 45) return 'D';
    else if (score >= 40) return 'E';
    else return 'F';
}

// Result preview for manual entry
function previewResult() {
    const score = parseInt(document.getElementById('score').value);
    const level = parseInt(document.getElementById('student_select').selectedOptions[0]?.dataset.level || 200);

    if (!isNaN(score) && score >= 0 && score <= 100) {
        const grade = getLetterGrade(score);
        const points = calculateGradePoints(score, level);
        const preview = document.getElementById('result-preview');

        if (preview) {
            preview.innerHTML = `
                <div class="alert alert-info">
                    <strong>Preview:</strong> Score: ${score} | Grade: ${grade} | Points: ${points.toFixed(2)}
                    (${level === 100 ? '5.0' : '4.0'} scale)
                </div>
            `;
        }
    }
}

// Loading states
function showLoading(element) {
    element.innerHTML = '<div class="text-center"><div class="loading"></div> Loading...</div>';
}

// Format numbers
function formatCGPA(cgpa) {
    return parseFloat(cgpa).toFixed(2);
}


function printElement(elementId, studentName, matricNumber, level, cgpa) {
    const element = document.getElementById(elementId);
    const table = element.querySelector('table'); // pick only the table
    const printWindow = window.open('', '', 'height=600,width=800');

    printWindow.document.write('<html><head><title>Print</title><style>');
    printWindow.document.write(`
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #0B5D1E; color: white; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #0B5D1E; margin: 0; }
        .header h2 { margin: 5px 0; color: #333; }
        .header p { margin: 5px 0; color: #666; }
        img.logo { height: 80px; margin-bottom: 10px; }
        .student-info { margin-top: 15px; text-align: left; }
        .student-info strong { color: #0B5D1E; }
    `);
    printWindow.document.write('</style></head><body>');

    // New custom header
    printWindow.document.write('<div class="header">');
    printWindow.document.write('<img src="/static/images/logo.png" alt="Logo" class="logo">');
    printWindow.document.write('<h1>University of Ibadan</h1>');
    printWindow.document.write('<h2>Department of Agricultural & Environmental Engineering</h2>');
    printWindow.document.write('<p><strong>Academic Results</strong></p>');
    printWindow.document.write('</div>');

    // Student info
    printWindow.document.write('<div class="student-info">');
    printWindow.document.write(`<p><strong>Name:</strong> ${studentName}</p>`);
    printWindow.document.write(`<p><strong>Matric Number:</strong> ${matricNumber}</p>`);
    printWindow.document.write(`<p><strong>Level:</strong> ${level}</p>`);
    printWindow.document.write(`<p><strong>CGPA:</strong> ${parseFloat(cgpa).toFixed(2)}</p>`);
    printWindow.document.write('</div>');

    // Results table only
    if (table) {
        printWindow.document.write(table.outerHTML);
    }

    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

