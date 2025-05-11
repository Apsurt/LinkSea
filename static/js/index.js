// static/js/index.js
document.addEventListener("DOMContentLoaded", () => {
  const joinForm = document.getElementById("join-group-form");
  const groupIdInput = document.getElementById("group_id_input");

  if (joinForm && groupIdInput) {
    joinForm.addEventListener("submit", function (event) {
      event.preventDefault(); // Prevent default form submission
      const groupId = groupIdInput.value.trim().toUpperCase();
      if (groupId.length === 6 && /^[A-Z0-9]{6}$/.test(groupId)) {
        // If validation passes, redirect
        window.location.href = `/${groupId}`;
      } else {
        // Basic feedback if needed, though HTML5 validation should largely cover this
        alert(
          "Please enter a valid 6-character Group ID (uppercase letters and numbers).",
        );
        groupIdInput.focus();
      }
    });

    // Optional: Auto-uppercase and filter input
    groupIdInput.addEventListener("input", function () {
      let value = this.value.toUpperCase();
      value = value.replace(/[^A-Z0-9]/g, ""); // Remove non-alphanumeric characters
      this.value = value.substring(0, 6); // Ensure it's not longer than 6 chars
    });
  } else {
    console.error("Join form or group ID input not found.");
  }

  // Set current year in footer
  const currentYearSpan = document.getElementById("currentYear");
  if (currentYearSpan) {
    currentYearSpan.textContent = new Date().getFullYear();
  }
});
