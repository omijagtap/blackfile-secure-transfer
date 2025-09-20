/**
 * BlackFile - Modern JavaScript Framework
 * Enhanced user interactions and security features
 */

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize components
    initializeNavigation();
    initializeAnimations();
    initializeUtilities();
    initializeSecurity();
    
    console.log('🔒 BlackFile initialized - Ultra secure file transfer');
}

// ==================== NAVIGATION ====================
function initializeNavigation() {
    const navbar = document.querySelector('.navbar');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.getElementById('navMenu');
    
    // Enhanced glass effect on scroll - keep navbar always visible
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        // Always keep navbar visible with enhanced glass effect on scroll
        if (currentScrollY > 50) {
            navbar.style.background = 'rgba(10, 10, 15, 0.98)';
            navbar.style.borderBottomColor = 'rgba(255, 255, 255, 0.15)';
            navbar.style.backdropFilter = 'blur(25px)';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.4)';
        } else {
            navbar.style.background = 'rgba(10, 10, 15, 0.95)';
            navbar.style.borderBottomColor = 'rgba(255, 255, 255, 0.1)';
            navbar.style.backdropFilter = 'blur(30px)';
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.3)';
        }
    });
    
    // Mobile menu
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenuBtn.classList.toggle('active');
            navMenu.classList.toggle('active');
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });
        
        // Close mobile menu on link click
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenuBtn.classList.remove('active');
                navMenu.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
        
        // Close mobile menu on outside click
        document.addEventListener('click', (e) => {
            if (!navbar.contains(e.target) && navMenu.classList.contains('active')) {
                mobileMenuBtn.classList.remove('active');
                navMenu.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
}

// ==================== ANIMATIONS ====================
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Stagger animations for children
                const children = entry.target.querySelectorAll('.feature-card, .glass, .alert');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.classList.add('animate-in');
                    }, index * 100);
                });
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.hero-section, .glass-card, .features-grid, .feature-card').forEach(el => {
        observer.observe(el);
    });
    
    // Parallax effect for background
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const bg = document.querySelector('body::before');
        if (bg) {
            document.body.style.setProperty('--scroll', `${scrolled * 0.5}px`);
        }
    });
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            animation: fadeInUp 0.6s ease forwards;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeOut {
            from {
                opacity: 1;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                transform: translateY(-10px);
            }
        }
    `;
    document.head.appendChild(style);
}

// ==================== UTILITIES ====================
function initializeUtilities() {
    // Enhanced clipboard functionality
    window.copyToClipboard = async function(text, button) {
        try {
            await navigator.clipboard.writeText(text);
            
            // Visual feedback
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.style.background = 'var(--success)';
            button.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.background = '';
                button.style.transform = '';
            }, 2000);
            
            // Show notification
            showNotification('Copied to clipboard successfully!', 'success');
            
            // Add haptic feedback on mobile
            if ('vibrate' in navigator) {
                navigator.vibrate(50);
            }
            
        } catch (err) {
            console.error('Failed to copy:', err);
            
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                showNotification('Copied to clipboard!', 'success');
            } catch (err) {
                showNotification('Copy failed. Please select and copy manually.', 'error');
            }
            
            document.body.removeChild(textArea);
        }
    };
    
    // Enhanced notification system
    window.showNotification = function(message, type = 'info', duration = 4000) {
        // Remove existing notifications
        document.querySelectorAll('.notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification alert alert-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            max-width: 500px;
            animation: slideInRight 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        `;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        notification.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <div>${message}</div>
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                color: inherit;
                opacity: 0.7;
                cursor: pointer;
                padding: 0;
                margin-left: auto;
                font-size: 1.2rem;
            ">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
        
        // Click to dismiss
        notification.addEventListener('click', (e) => {
            if (e.target === notification) {
                notification.remove();
            }
        });
    };
    
    // Enhanced form validation
    window.validateForm = function(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            const value = input.value.trim();
            let fieldValid = true;
            
            // Basic required check
            if (!value) {
                fieldValid = false;
            }
            
            // Email validation
            if (input.type === 'email' && value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                fieldValid = emailRegex.test(value);
            }
            
            // File validation
            if (input.type === 'file' && input.hasAttribute('required')) {
                fieldValid = input.files && input.files.length > 0;
            }
            
            // Visual feedback
            if (!fieldValid) {
                input.style.borderColor = 'var(--error)';
                input.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.2)';
                isValid = false;
                
                // Add shake animation
                input.style.animation = 'shake 0.3s ease-in-out';
                setTimeout(() => {
                    input.style.animation = '';
                }, 300);
            } else {
                input.style.borderColor = '';
                input.style.boxShadow = '';
            }
        });
        
        return isValid;
    };
    
    // Loading state for buttons
    window.setButtonLoading = function(button, loading = true) {
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<div class="loading"></div> Processing...';
            button.disabled = true;
            button.style.cursor = 'not-allowed';
            button.style.opacity = '0.8';
        } else {
            button.innerHTML = button.dataset.originalText || 'Submit';
            button.disabled = false;
            button.style.cursor = '';
            button.style.opacity = '';
        }
    };
    
    // Add shake animation CSS
    const shakeStyle = document.createElement('style');
    shakeStyle.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(shakeStyle);
}

// ==================== SECURITY ====================
function initializeSecurity() {
    // Disable right-click context menu on sensitive elements
    document.querySelectorAll('.copy-input, .form-input[readonly]').forEach(element => {
        element.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            showNotification('Use the copy button for secure clipboard access', 'info', 2000);
        });
    });
    
    // Disable print screen for sensitive pages
    if (window.location.pathname.includes('/sent/') || window.location.pathname.includes('/verify/')) {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'PrintScreen') {
                e.preventDefault();
                showNotification('Screenshots are disabled for security', 'warning', 2000);
            }
            
            // Disable F12, Ctrl+Shift+I, etc.
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'J') ||
                (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                showNotification('Developer tools are disabled for security', 'warning', 2000);
            }
        });
    }
    
    // Auto-clear sensitive fields on page unload
    window.addEventListener('beforeunload', () => {
        document.querySelectorAll('input[type="password"], input[readonly], textarea[readonly]').forEach(input => {
            input.value = '';
        });
    });
    
    // Detect if DevTools is open
    let devtools = {
        open: false,
        orientation: null
    };
    
    setInterval(() => {
        if (window.outerHeight - window.innerHeight > 200 || window.outerWidth - window.innerWidth > 200) {
            if (!devtools.open) {
                devtools.open = true;
                console.clear();
                console.log('%c🔒 BlackFile Security Notice', 'color: #ff6b6b; font-size: 20px; font-weight: bold;');
                console.log('%cThis is a browser feature intended for developers. Misuse of this tool may compromise your security.', 'color: #ffa726; font-size: 14px;');
            }
        } else {
            devtools.open = false;
        }
    }, 500);
}

// ==================== FILE HANDLING ====================
function initializeFileUpload() {
    const uploadAreas = document.querySelectorAll('.upload-area, .modern-upload-area');
    
    uploadAreas.forEach(uploadArea => {
        const fileInput = uploadArea.querySelector('input[type="file"]') || 
                         document.querySelector('input[type="file"]');
        
        if (!fileInput) return;
        
        // Drag and drop handlers
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            });
        });
        
        uploadArea.addEventListener('drop', handleDrop);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                handleFileSelection(files[0], fileInput, uploadArea);
            }
        }
        
        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelection(e.target.files[0], fileInput, uploadArea);
            }
        });
    });
}

function handleFileSelection(file, fileInput, uploadArea) {
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification(`File size (${formatFileSize(file.size)}) exceeds 10MB limit`, 'error');
        return;
    }
    
    // Update UI
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    
    if (fileInfo && fileName && fileSize) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.classList.remove('d-none');
        uploadArea.style.display = 'none';
    }
    
    // Create DataTransfer to properly set files
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    
    // Visual feedback
    uploadArea.classList.add('upload-success');
    setTimeout(() => {
        uploadArea.classList.remove('upload-success');
    }, 1000);
    
    showNotification(`File "${file.name}" selected successfully`, 'success', 2000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ==================== KEYBOARD SHORTCUTS ====================
document.addEventListener('keydown', (e) => {
    // Global shortcuts
    if (e.altKey && e.key === 'h') {
        e.preventDefault();
        window.location.href = '/';
    }
    
    // Escape to close modals/menus
    if (e.key === 'Escape') {
        // Close mobile menu
        const mobileMenu = document.getElementById('navMenu');
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            mobileMenuBtn.classList.remove('active');
            mobileMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        // Close notifications
        document.querySelectorAll('.notification').forEach(n => n.remove());
    }
});

// ==================== PERFORMANCE ====================
// Preload critical resources
function preloadResources() {
    const resources = [
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
    ];
    
    resources.forEach(url => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = url.endsWith('.css') ? 'style' : 'script';
        link.href = url;
        document.head.appendChild(link);
    });
}

// Initialize file upload on page load
document.addEventListener('DOMContentLoaded', initializeFileUpload);

// Initialize performance optimizations
document.addEventListener('DOMContentLoaded', preloadResources);

// ==================== EXPORT ====================
window.BlackFile = {
    showNotification,
    copyToClipboard,
    validateForm,
    setButtonLoading,
    formatFileSize
};

console.log('✨ BlackFile Modern UI loaded successfully');