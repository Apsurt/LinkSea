// static/js/group.js
document.addEventListener("DOMContentLoaded", () => {
  // Set current year in footer
  const currentYearSpan = document.getElementById("currentYearGroup");
  if (currentYearSpan) {
    currentYearSpan.textContent = new Date().getFullYear();
  }

  // Rename Group Form Toggle
  const renameGroupForm = document.getElementById("rename-group-form");
  const groupTitleDisplay = document.getElementById("group-title-display");
  if (renameGroupForm && groupTitleDisplay) {
    // Populate input with current group name initially
    const renameInput = renameGroupForm.querySelector(
      'input[name="group_name"]',
    );
    if (renameInput) {
      renameInput.value = groupTitleDisplay.textContent.trim();
    }
  }

  // Drag and Drop functionality for link list
  const linkList = document.getElementById("link-list-items");
  let draggedItem = null;

  if (linkList) {
    linkList.addEventListener("dragstart", (e) => {
      let targetElement = e.target;
      // Ensure we're dragging the .link-item-card
      while (
        targetElement &&
        !targetElement.classList.contains("link-item-card")
      ) {
        targetElement = targetElement.parentElement;
      }

      if (targetElement && targetElement.getAttribute("draggable") === "true") {
        draggedItem = targetElement;
        // Timeout to allow the browser to create the drag image before adding the class
        setTimeout(() => {
          if (draggedItem) draggedItem.classList.add("dragging");
        }, 0);
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", draggedItem.dataset.linkId); // Optional: set data
      } else if (
        targetElement &&
        targetElement.getAttribute("draggable") === "false"
      ) {
        e.preventDefault(); // Prevent dragging if explicitly set to false
      }
    });

    linkList.addEventListener("dragend", () => {
      if (draggedItem) {
        draggedItem.classList.remove("dragging");
        draggedItem = null;
        // Here you would typically send the new order to the server
        // For this example, we'll assume reordering is visual only until page reload or specific save action
        // updateLinkOrder(); // A function you'd write to persist order
      }
    });

    linkList.addEventListener("dragover", (e) => {
      e.preventDefault(); // Necessary to allow dropping
      if (!draggedItem) return;

      const afterElement = getDragAfterElement(linkList, e.clientY);
      const container = linkList;

      if (draggedItem.classList.contains("link-item-card")) {
        // Ensure draggedItem is a link item
        if (afterElement == null) {
          container.appendChild(draggedItem);
        } else {
          container.insertBefore(draggedItem, afterElement);
        }
      }
    });

    // Temporarily disable draggable when interacting with buttons/forms inside link item
    linkList.addEventListener("mouseover", (e) => {
      const linkItem = e.target.closest(".link-item-card");
      if (linkItem) {
        const isInteractiveElement = e.target.closest(
          "button, input, a, form, .edit-link-form-inline.active",
        );
        if (isInteractiveElement) {
          linkItem.setAttribute("draggable", "false");
        }
      }
    });

    linkList.addEventListener("mouseout", (e) => {
      const linkItem = e.target.closest(".link-item-card");
      if (linkItem) {
        // Only re-enable draggable if not currently editing this item
        const editForm = linkItem.querySelector(".edit-link-form-inline");
        if (!editForm || !editForm.classList.contains("active")) {
          linkItem.setAttribute("draggable", "true");
        }
      }
    });
  }
});

function toggleRenameForm() {
  const renameForm = document.getElementById("rename-group-form");
  const groupTitleSection = document.querySelector(".group-title-section"); // Or the H1 itself
  const editButton = document.getElementById("edit-group-name-btn");

  if (renameForm) {
    const isActive = renameForm.classList.toggle("active");
    if (isActive) {
      renameForm.style.display = "flex"; // Or 'block' depending on layout
      if (groupTitleSection) groupTitleSection.style.display = "none";
      if (editButton) editButton.classList.add("active-edit"); // Optional: style the button when form is open
      renameForm.querySelector('input[name="group_name"]').focus();
    } else {
      renameForm.style.display = "none";
      if (groupTitleSection) groupTitleSection.style.display = "flex"; // Or 'block'
      if (editButton) editButton.classList.remove("active-edit");
    }
  }
}

function toggleLinkEditForm(linkId, buttonElement) {
  const linkItem = document.querySelector(
    `.link-item-card[data-link-id="${linkId}"]`,
  );
  if (!linkItem) return;

  const editForm = linkItem.querySelector(`#edit-link-form-${linkId}`);
  const linkContent = linkItem.querySelector(".link-item-content"); // The div holding title, favicon, note
  const linkActions = linkItem.querySelector(".link-actions"); // The div holding edit/remove buttons

  if (editForm && linkContent && linkActions) {
    const isActive = editForm.classList.toggle("active");
    if (isActive) {
      editForm.style.display = "flex";
      linkContent.style.display = "none"; // Hide normal content
      linkActions.style.display = "none"; // Hide action buttons
      linkItem.setAttribute("draggable", "false"); // Disable drag when editing
      editForm.querySelector('input[name="title"]').focus();
      editForm.querySelector('input[name="title"]').select();
    } else {
      editForm.style.display = "none";
      linkContent.style.display = "flex"; // Show normal content
      linkActions.style.display = "flex"; // Show action buttons
      linkItem.setAttribute("draggable", "true"); // Re-enable drag
    }
  }
}

function copyGroupId(groupId) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(groupId)
      .then(() => showToast("Group ID copied to clipboard!", "success"))
      .catch((err) => {
        console.error("Failed to copy using clipboard API: ", err);
        fallbackCopyTextToClipboard(groupId); // Try fallback
      });
  } else {
    fallbackCopyTextToClipboard(groupId); // Use fallback if clipboard API not supported
  }
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  // Make sure it's not visible
  textArea.style.position = "fixed";
  textArea.style.top = "-9999px";
  textArea.style.left = "-9999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    const successful = document.execCommand("copy");
    if (successful) {
      showToast("Group ID copied (fallback method)!", "success");
    } else {
      showToast("Failed to copy Group ID.", "error");
    }
  } catch (err) {
    console.error("Fallback: Unable to copy", err);
    showToast("Failed to copy Group ID.", "error");
  }
  document.body.removeChild(textArea);
}

function showToast(message, type = "info") {
  // type can be 'info', 'success', 'error', 'warning'
  const container = document.getElementById("toast-container");
  if (!container) {
    console.error("Toast container not found!");
    alert(message); // Fallback to alert
    return;
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`; // Apply type for styling
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");
  toast.setAttribute("aria-atomic", "true");
  toast.textContent = message;

  container.appendChild(toast); // Add new toast to container

  // Trigger the show animation
  setTimeout(() => {
    toast.classList.add("show");
  }, 10); // Small delay to ensure transition is applied

  // Hide and remove toast after a few seconds
  setTimeout(() => {
    toast.classList.remove("show");
    // Remove the element after the fade-out transition completes
    toast.addEventListener(
      "transitionend",
      () => {
        if (toast.parentElement) {
          // Check if it's still in the DOM
          toast.remove();
        }
      },
      { once: true },
    ); // Ensure event listener is removed after firing once
  }, 3000); // Toast visible for 3 seconds
}

function getDragAfterElement(container, y) {
  const draggableElements = [
    ...container.querySelectorAll(".link-item-card:not(.dragging)"),
  ];

  return draggableElements.reduce(
    (closest, child) => {
      const box = child.getBoundingClientRect();
      // Midpoint of the draggable child element
      const offset = y - box.top - box.height / 2;
      // We are looking for an element that is *below* the cursor (negative offset)
      // and is the closest one (largest negative offset, i.e., smallest absolute value but negative)
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    },
    { offset: Number.NEGATIVE_INFINITY },
  ).element;
}

// Potentially add function to get and display last_accessed time if not handled by backend templating.
// Example:
// async function fetchAndUpdateLastAccessed(groupId) {
//     try {
//         const response = await fetch(`/api/group/${groupId}/last-accessed`); // Example API endpoint
//         if (!response.ok) throw new Error('Failed to fetch');
//         const data = await response.json();
//         const lastAccessedSpan = document.getElementById('last-accessed-time');
//         if (lastAccessedSpan && data.last_accessed_formatted) {
//             lastAccessedSpan.textContent = data.last_accessed_formatted;
//         }
//     } catch (error) {
//         console.error("Could not update last accessed time:", error);
//     }
// }
// if (document.body.dataset.groupId) { // Assume groupId is available e.g. in a data attribute on body
//     fetchAndUpdateLastAccessed(document.body.dataset.groupId);
// }

// Add a filter to Jinja2 environment in app.py for formatting datetime
// This would require modifying app.py if you want to format datetime in the template
// e.g. app.jinja_env.filters['format_datetime_ago'] = format_datetime_ago_filter
// And then define the filter function in Python.
// For client-side, you'd use a JS library like moment.js or date-fns, or write custom logic.
