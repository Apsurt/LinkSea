function toggleLinkEditForm(linkId) {
  const editForm = document.getElementById(`edit-link-form-${linkId}`);
  editForm.style.display = editForm.style.display === "none" ? "flex" : "none";

  const linkItem = document.querySelector(
    `.link-item[data-link-id="${linkId}"]`,
  );
  if (editForm.style.display === "flex") {
    linkItem.setAttribute("draggable", false);
  } else {
    linkItem.setAttribute("draggable", true);
  }
}

function toggleRenameForm() {
  const renameForm = document.getElementById("rename-group-form");
  renameForm.style.display =
    renameForm.style.display === "none" ? "flex" : "none";
}

function copyGroupId(groupId) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(groupId)
      .then(() => {
        showToast("Group ID copied to clipboard!");
      })
      .catch((err) => {
        console.error("Failed to copy using clipboard API: ", err);
        fallbackCopyTextToClipboard(groupId);
      });
  } else {
    fallbackCopyTextToClipboard(groupId);
  }
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;

  // Avoid scrolling to bottom
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.position = "fixed";

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    const successful = document.execCommand("copy");
    const msg = successful ? "successful" : "unsuccessful";
    console.log("Fallback: Copying text command was " + msg);
    showToast("Group ID copied to clipboard!");
  } catch (err) {
    console.error("Fallback: Unable to copy", err);
    alert("Unable to copy Group ID to clipboard.");
  }

  document.body.removeChild(textArea);
}

function showToast(message) {
  const toast = document.getElementById("copy-toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2000); // Hide toast after 2 seconds
}

const linkList = document.querySelector(".link-list");
let draggedItem = null;

linkList.addEventListener("dragstart", (e) => {
  let targetElement = e.target;
  // Traverse up the DOM tree to find the .link-item
  while (targetElement && !targetElement.classList.contains("link-item")) {
    targetElement = targetElement.parentElement;
  }

  if (targetElement && targetElement.getAttribute("draggable") !== "false") {
    // Check if draggable is not explicitly false
    draggedItem = targetElement;
    draggedItem.classList.add("dragging");
  }
  // Importantly, prevent default drag behavior on draggable children
  if (e.target !== draggedItem && e.target.draggable !== true) {
    e.preventDefault();
  }
});

linkList.addEventListener("dragend", (e) => {
  if (draggedItem) {
    draggedItem.classList.remove("dragging");
    draggedItem = null;
  }
});

linkList.addEventListener("dragover", (e) => {
  e.preventDefault();
  const afterElement = getDragAfterElement(linkList, e.clientY);
  if (afterElement == null) {
    linkList.appendChild(draggedItem);
  } else {
    linkList.insertBefore(draggedItem, afterElement);
  }
});

function getDragAfterElement(container, y) {
  const draggableElements = [
    ...container.querySelectorAll(".link-item:not(.dragging)"),
  ];
  return draggableElements.reduce(
    (closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;

      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
      return closest;
    },
    { offset: Number.NEGATIVE_INFINITY },
  ).element;
}
