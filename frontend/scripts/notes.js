import { apiFetch } from "./api.js";

let allNotes = [];

const token = localStorage.getItem("token");
if (!token) {
  location.href = "index.html";
} else {
  loadNotes();
}

function formatDate(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

async function loadNotes() {
  const grid = document.getElementById("notesGrid");
  try {
    const data = await apiFetch("/notes/");
    if (!data || data.length === 0) {
      grid.innerHTML = `<div style="text-align: center; color: #777; width: 100%; padding: 2rem;">You haven't saved any notes yet!</div>`;
      return;
    }
    allNotes = data;
    grid.innerHTML = "";
    data.forEach((note, index) => {
      const div = document.createElement("div");
      div.className = "note-card";
      div.setAttribute("onclick", `openNote(${index})`);
      div.title = "Click to read full note";
      div.innerHTML = `
        <div class="note-date">${formatDate(note.created_at)}</div>
        <div class="note-content preview">${note.content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
      `;
      grid.appendChild(div);
    });
  } catch (error) {
    grid.innerHTML = `<div style="text-align: center; color: #ff6b6b; width: 100%;">Failed to load notes.</div>`;
  }
}

function openNote(index) {
  const note = allNotes[index];
  document.getElementById("modalDate").innerText = formatDate(note.created_at);
  document.getElementById("modalText").innerHTML = note.content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
  document.getElementById("noteModal").style.display = "flex";
}
function closeNote() {
  document.getElementById("noteModal").style.display = "none";
}
window.onclick = function(event) {
  const modal = document.getElementById("noteModal");
  if (event.target === modal) {
    closeNote();
  }
};

window.openNote = openNote;
window.closeNote = closeNote;
