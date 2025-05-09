const codeInputs = document.querySelectorAll(".join-code-input");
const joinForm = document.getElementById("join-group");

codeInputs.forEach((input, index) => {
  input.addEventListener("input", (e) => {
    const value = e.target.value.toUpperCase();
    e.target.value = value;

    if (value.length === 1 && index < codeInputs.length - 1) {
      codeInputs[index + 1].focus();
    }

    // Check if all inputs have values
    let fullCode = "";
    codeInputs.forEach((input) => {
      fullCode += input.value;
    });
    if (fullCode.length === 6) {
      submitJoinCode();
    }
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Backspace" && e.target.value.length === 0 && index > 0) {
      codeInputs[index - 1].focus();
    }
  });
});

joinForm.addEventListener("paste", (e) => {
  const pasteData = (e.clipboardData || window.clipboardData).getData("text");
  const code = pasteData.trim().substring(0, 6);

  for (let i = 0; i < Math.min(code.length, codeInputs.length); i++) {
    codeInputs[i].value = code[i];
  }

  // If 6 characters are pasted, focus the join button
  if (code.length === 6) {
    document.querySelector(".join-btn").focus();
  }
  e.preventDefault(); // Prevent default paste action
});

function submitJoinCode() {
  let fullCode = "";
  codeInputs.forEach((input) => {
    fullCode += input.value;
  });
  window.location.href = `/${fullCode}`; // Redirect directly to the group URL
}

// Prevent the default form submission
joinForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitJoinCode();
});
