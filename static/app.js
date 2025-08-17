document.addEventListener("DOMContentLoaded", () => {
  const drop = document.querySelector("#drop");
  const fileInput = document.querySelector("#file");
  const dropText = document.querySelector("#dropText");
  const form = document.querySelector("#uploadForm");
  const overlay = document.querySelector("#overlay");
  const stepsContainer = document.querySelector("#stepsContainer");
  const expirySelect = document.querySelector("#expiry");
  const emailInput = document.querySelector("#email");
  const submitBtn = document.querySelector("#submitBtn");

  // --- Drag & Drop + Click ---
  if (drop && fileInput) {
    drop.addEventListener("dragover", (e) => {
      e.preventDefault();
      drop.classList.add("dragover");
    });
    drop.addEventListener("dragleave", () => drop.classList.remove("dragover"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      drop.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        updateDropText(fileInput.files[0].name);
      }
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        updateDropText(fileInput.files[0].name);
      }
    });
    function updateDropText(filename) {
      drop.classList.add("filled");
      dropText.textContent = "📄 " + filename;
    }
  }

  // --- Step animation sequence ---
  const uploadSequence = [
    { icon: "🔑", text: "AES-256 key generated" },
    { icon: "🔐", text: "File encrypted securely" },
    { icon: "📝", text: "SHA-256 hash created" },
    { icon: "🔢", text: "OTP generated" },
    { icon: "📧", text: "Email sent to recipient" },
    { icon: "✅", text: "Upload complete" }
  ];
  const downloadSequence = [
    { icon: "🔍", text: "Verifying OTP & Secret Key" },
    { icon: "🔓", text: "Decrypting file with AES-256" },
    { icon: "📦", text: "Preparing secure download" },
    { icon: "✅", text: "Ready – starting download" }
  ];

  function validEmail(e){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e); }
  function validateBeforeSubmit() {
    if (!validEmail(emailInput.value.trim())) { alert("Please enter a valid email."); return false; }
    if (!fileInput.files || !fileInput.files[0]) { alert("Please choose a file."); return false; }
    if (fileInput.files[0].size > 10 * 1024 * 1024) { alert("File must be ≤ 10 MB."); return false; }
    if (!["5","10","60"].includes(String(expirySelect.value))) { alert("Invalid expiry."); return false; }
    return true;
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      if (!validateBeforeSubmit()) { e.preventDefault(); return; }

      if (submitBtn.disabled) {
        e.preventDefault();
        return;
      }
      submitBtn.disabled = true;
      submitBtn.textContent = "⏳ Uploading...";

      e.preventDefault();
      runSteps(uploadSequence, () => form.submit());
    });
  }

  // For verify.html form
  const verifyForm = document.querySelector("form[method='POST']");
  if (verifyForm && !form) {
    const verifyBtn = verifyForm.querySelector("button[type='submit']");
    verifyForm.addEventListener("submit", (e) => {
      if (verifyBtn.disabled) { e.preventDefault(); return; }
      verifyBtn.disabled = true;
      verifyBtn.textContent = "⏳ Verifying...";
      e.preventDefault();
      runSteps(downloadSequence, () => verifyForm.submit());
    });
  }

  function runSteps(sequence, callback) {
    overlay.classList.remove("hidden");
    stepsContainer.innerHTML = "";

    sequence.forEach((step, i) => {
      const div = document.createElement("div");
      div.className = "step";
      div.innerHTML = `<div class="icon">${step.icon}</div> <span>${step.text}</span>`;
      stepsContainer.appendChild(div);

      setTimeout(() => {
        div.classList.add("done");
        if (i === sequence.length - 1) {
          setTimeout(() => {
            overlay.classList.add("hidden");
            callback();
          }, 800);
        }
      }, i * 1100);
    });
  }
});
