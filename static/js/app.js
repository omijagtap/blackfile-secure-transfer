document.addEventListener("DOMContentLoaded", () => {
  const fileUploadArea = document.getElementById("fileUploadArea");
  const fileInput = document.getElementById("file");
  const fileNameDisplay = document.getElementById("fileName");
  const uploadForm = document.getElementById("uploadForm");
  const verifyForm = document.getElementById("verifyForm");
  const overlay = document.getElementById("overlay");
  const stepsContainer = document.getElementById("stepsContainer");
  const submitBtn = document.getElementById("submitBtn");
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const navMenu = document.querySelector('.nav-menu');
  const themeToggle = document.getElementById('themeToggle');
  const motionToggle = document.getElementById('motionToggle');
  const soundToggle = document.getElementById('soundToggle');
  
  // Theme Toggle Functionality
  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
  };

  const initMotion = () => {
    const savedMotion = localStorage.getItem('motion') || 'reduced';
    document.documentElement.setAttribute('data-motion', savedMotion);
    updateMotionButton(savedMotion);
  };
  
  const updateThemeButton = (theme) => {
    const icon = themeToggle?.querySelector('i');
    const text = themeToggle?.querySelector('.theme-text');
    
    if (icon && text) {
      if (theme === 'light') {
        icon.className = 'fas fa-fire';
        text.textContent = 'Warm';
      } else {
        icon.className = 'fas fa-moon';
        text.textContent = 'Dark';
      }
    }
  };
  
  // Initialize theme and motion on load
  initTheme();
  initMotion();
  
  // Theme toggle event listener
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeButton(newTheme);
    });
  }

  const updateMotionButton = (motion) => {
    const icon = motionToggle?.querySelector('i');
    const text = motionToggle?.querySelector('.motion-text');
    if (icon && text) {
      if (motion === 'reduced') {
        icon.className = 'fas fa-wind';
        text.textContent = 'Calm';
      } else {
        icon.className = 'fas fa-wave-square';
        text.textContent = 'Dynamic';
      }
    }
  };

  if (motionToggle) {
    motionToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-motion');
      const next = current === 'reduced' ? 'full' : 'reduced';
      document.documentElement.setAttribute('data-motion', next);
      localStorage.setItem('motion', next);
      updateMotionButton(next);
    });
  }

  // Simple sound feedback (off by default)
  const ping = new Audio('data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABYAAAB9AAAASGFuZC1jcmFmdGVkIHNpbGVuY2U=');
  const updateSoundButton = (on) => {
    const icon = soundToggle?.querySelector('i');
    const text = soundToggle?.querySelector('.sound-text');
    if (icon && text) {
      if (on) { icon.className = 'fas fa-volume-up'; text.textContent = 'Sound On'; }
      else { icon.className = 'fas fa-volume-mute'; text.textContent = 'Sound Off'; }
    }
  };
  const initSound = () => {
    const val = localStorage.getItem('sound') === 'on';
    updateSoundButton(val);
    return val;
  };
  let soundOn = initSound();
  if (soundToggle) {
    soundToggle.addEventListener('click', () => {
      soundOn = !soundOn;
      localStorage.setItem('sound', soundOn ? 'on' : 'off');
      updateSoundButton(soundOn);
    });
  }

  // Mobile menu toggle
  if (mobileMenuBtn && navMenu) {
    mobileMenuBtn.addEventListener('click', function() {
      mobileMenuBtn.classList.toggle('active');
      navMenu.classList.toggle('active');
    });
    
    // Close menu when clicking a nav link (but not theme toggle)
    document.querySelectorAll('.nav-link:not(.theme-toggle)').forEach(link => {
      link.addEventListener('click', () => {
        mobileMenuBtn.classList.remove('active');
        navMenu.classList.remove('active');
      });
    });
  }

  // Modern file upload area drag & drop with animations
  if (fileUploadArea) {
    let dragCounter = 0;
    
    fileUploadArea.addEventListener("dragenter", (e) => {
      e.preventDefault();
      dragCounter++;
      fileUploadArea.classList.add("dragover");
    });
    
    fileUploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
    });
    
    fileUploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault();
      dragCounter--;
      if (dragCounter === 0) {
        fileUploadArea.classList.remove("dragover");
      }
    });
    
    fileUploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      dragCounter = 0;
      fileUploadArea.classList.remove("dragover");
      
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        showFileSuccess(e.dataTransfer.files[0]);
      }
    });
    
    fileUploadArea.addEventListener("click", () => {
      if (!fileUploadArea.classList.contains('upload-success')) {
        fileInput.click();
      }
    });

    // Keyboard accessibility
    fileUploadArea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (!fileUploadArea.classList.contains('upload-success')) {
          fileInput.click();
        }
      }
    });
    
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        showFileSuccess(fileInput.files[0]);
      }
    });

    function showFileSuccess(file) {
      // Add success animation to upload area
      fileUploadArea.classList.add('upload-success');
      
      // Show success elements
      const fileInfo = document.getElementById('fileInfo');
      const checkmark = fileInfo.querySelector('.success-checkmark');
      const fileName = document.getElementById('fileName');
      
      fileInfo.style.display = 'block';
      checkmark.style.display = 'flex';
      
      // Format file size
      const fileSize = (file.size / 1024 / 1024).toFixed(2);
      fileName.textContent = `${file.name} (${fileSize} MB)`;
      
      // Hide original upload content
      const uploadIcon = fileUploadArea.querySelector('i');
      const uploadTexts = fileUploadArea.querySelectorAll('p');
      
      uploadIcon.style.display = 'none';
      uploadTexts.forEach(text => text.style.display = 'none');
      
      // Optional sound
      if (soundOn) {
        try { ping.currentTime = 0; ping.play().catch(()=>{}); } catch(e) {}
      }

      // Add click to change functionality
      setTimeout(() => {
        const changeText = document.createElement('p');
        changeText.innerHTML = '<small style="color: var(--text-secondary-color); cursor: pointer;">Click to change file</small>';
        changeText.addEventListener('click', () => {
          resetUploadArea();
          fileInput.click();
        });
        fileInfo.appendChild(changeText);
      }, 800);
    }
    
    function resetUploadArea() {
      fileUploadArea.classList.remove('upload-success');
      document.getElementById('fileInfo').style.display = 'none';
      
      // Show original content
      const uploadIcon = fileUploadArea.querySelector('i');
      const uploadTexts = fileUploadArea.querySelectorAll('p');
      
      uploadIcon.style.display = 'block';
      uploadTexts.forEach(text => text.style.display = 'block');
      
      // Clear file input
      fileInput.value = '';
    }
  }

  // Handle form submission with overlay
  if (uploadForm) {
    const uploadSequence = [
      { icon: "<i class='fas fa-key'></i>", text: "Generating encryption key" },
      { icon: "<i class='fas fa-lock'></i>", text: "Encrypting file securely" },
      { icon: "<i class='fas fa-fingerprint'></i>", text: "Creating file hash" },
      { icon: "<i class='fas fa-random'></i>", text: "Generating One-Time Password" },
      { icon: "<i class='fas fa-envelope'></i>", text: "Sending secure email to recipient" },
      { icon: "<i class='fas fa-check-circle'></i>", text: "Transfer complete" }
    ];
    
    uploadForm.addEventListener("submit", (e) => {
      e.preventDefault();
      
      if (submitBtn.disabled) {
        return;
      }

      // show network badge
      const badge = document.getElementById('netBadge');
      if (badge) badge.style.display = 'inline-flex';

      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <div class="spinner"></div>
        Processing...
      `;

      runSteps(uploadSequence, () => uploadForm.submit());
    });
  }

  if (verifyForm) {
    const downloadSequence = [
      { icon: "<i class='fas fa-shield-alt'></i>", text: "Verifying credentials" },
      { icon: "<i class='fas fa-unlock'></i>", text: "Decrypting file" },
      { icon: "<i class='fas fa-file-download'></i>", text: "Preparing secure download" },
      { icon: "<i class='fas fa-check-circle'></i>", text: "Download initiated" }
    ];

    const verifyBtn = verifyForm.querySelector("button[type='submit']");
    
    // Add button hover effect
    if (verifyBtn) {
      verifyBtn.addEventListener("mouseover", () => {
        verifyBtn.classList.add("btn-hover");
      });
      
      verifyBtn.addEventListener("mouseout", () => {
        verifyBtn.classList.remove("btn-hover");
      });
    }

    verifyForm.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!verifyBtn || verifyBtn.disabled) {
        return;
      }
      
      verifyBtn.disabled = true;
      verifyBtn.classList.add("btn-processing");
      verifyBtn.innerHTML = `
        <div class="spinner"></div>
        Processing...
      `;
      
      runSteps(downloadSequence, () => verifyForm.submit());
    });
  }

  function runSteps(sequence, callback) {
    overlay.classList.add("visible");
    setTimeout(() => {
      overlay.classList.add("active");
    }, 10);
    stepsContainer.innerHTML = "";

    // Add temporary skeleton lines for premium feel
    const skel = document.createElement('div');
    skel.className = 'skeleton';
    skel.innerHTML = '<div class="skeleton-line" style="width:70%"></div>'+
                     '<div class="skeleton-line" style="width:55%"></div>'+
                     '<div class="skeleton-line" style="width:65%"></div>';
    stepsContainer.appendChild(skel);

    // Add progress bar
    const progressBar = document.createElement("div");
    progressBar.className = "loader-progress";
    stepsContainer.appendChild(progressBar);

    // Remove skeleton a bit after first step appears
    setTimeout(() => { if (skel && skel.parentNode) skel.parentNode.removeChild(skel); }, 600);

    sequence.forEach((step, i) => {
      const div = document.createElement("div");
      div.className = "step";
      div.innerHTML = `<div class=\"icon\">${step.icon}</div> <span>${step.text}</span>`;
      stepsContainer.appendChild(div);
      
      // Add staggered animation
      setTimeout(() => {
        div.classList.add("step-visible");
        // Update progress bar
        const progress = ((i + 1) / sequence.length) * 100;
        progressBar.style.width = `${progress}%`;
      }, 120 * i);

      setTimeout(() => {
        div.classList.add("done");
        if (i === sequence.length - 1) {
          setTimeout(() => {
            overlay.classList.remove("visible");
            overlay.classList.remove("active");
            callback();
          }, 700);
        }
      }, i * 1050);
    });
  }
  
  // Copy to clipboard functionality
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("copy-btn") || e.target.closest(".copy-btn")) {
      const button = e.target.classList.contains("copy-btn") ? e.target : e.target.closest(".copy-btn");
      const inputId = button.getAttribute("data-copy-target");
      const input = document.getElementById(inputId);
      
      if (input) {
        input.select();
        input.setSelectionRange(0, 99999);
        
        try {
          document.execCommand("copy");
          
          const originalText = button.innerHTML;
          button.innerHTML = "<i class='fas fa-check'></i> Copied!";
          
          setTimeout(() => {
            button.innerHTML = originalText;
          }, 2000);

          // toast
          const toast = document.getElementById('toast');
          if (toast) { toast.textContent = 'Copied to clipboard'; toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 1800); }
        } catch (err) {
          console.error("Failed to copy: ", err);
        }
      }
    }
  });

  // Show toast on sent page load
  window.addEventListener('DOMContentLoaded', () => {
    const toast = document.getElementById('toast');
    if (toast && toast.dataset.message) {
      toast.textContent = toast.dataset.message;
      setTimeout(() => toast.classList.add('show'), 200);
      setTimeout(() => toast.classList.remove('show'), 2500);
    }
  });

  // Countdown timer for expiry
  const countdownElement = document.getElementById("countdown");
  if (countdownElement) {
    const expiresAt = countdownElement.getAttribute("data-expires-at");
    updateCountdown(expiresAt);
    
    const countdownInterval = setInterval(() => {
      updateCountdown(expiresAt);
    }, 1000);
    
    function updateCountdown(expiryTime) {
      const now = new Date();
      const expirationDate = new Date(expiryTime);
      const timeRemaining = expirationDate - now;
      
      if (timeRemaining <= 0) {
        countdownElement.textContent = "Expired";
        clearInterval(countdownInterval);
        return;
      }
      
      const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
      
      countdownElement.textContent = `Expires in ${minutes}m ${seconds}s`;
    }
  }
  
});