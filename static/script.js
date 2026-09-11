const LOADING_MESSAGES = [
  "Locating suspicious corners...",
  "Consulting the laws of geometry...",
  "Questioning the chef's decisions...",
  "Calculating unnecessary mathematics...",
  "Inspecting triangular integrity...",
  "Cross-examining the pastry for corner-related crimes...",
];

const CORNER_COLORS = { A: "#E11D48", B: "#D97706", C: "#0F9B8E" };

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const removeBtn = document.getElementById("removeBtn");
const previewImg = document.getElementById("previewImg");
const dzIdle = document.getElementById("dzIdle");
const dzPreview = document.getElementById("dzPreview");

const loadingOverlay = document.getElementById("loadingOverlay");
const loadingMsg = document.getElementById("loadingMsg");

const errorCard = document.getElementById("errorCard");
const errorMessage = document.getElementById("errorMessage");
const dismissErrorBtn = document.getElementById("dismissErrorBtn");

const results = document.getElementById("results");
const scoreValue = document.getElementById("scoreValue");
const bandEmoji = document.getElementById("bandEmoji");
const bandName = document.getElementById("bandName");
const verdictLine = document.getElementById("verdictLine");
const resultCanvas = document.getElementById("resultCanvas");
const legend = document.getElementById("legend");
const totalAngle = document.getElementById("totalAngle");
const statsList = document.getElementById("statsList");
const devNote = document.getElementById("devNote");
const againBtn = document.getElementById("againBtn");

let selectedFile = null;
let lastResult = null;
let messageTimer = null;

const ACCEPTED = ["image/jpeg", "image/png"];
const MAX_BYTES = 8 * 1024 * 1024;

dropzone.addEventListener("click", () => fileInput.click());
uploadBtn.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) setFile(e.target.files[0]);
});

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) setFile(file);
});

removeBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  clearSelection();
});

analyzeBtn.addEventListener("click", () => {
  if (selectedFile) runAnalysis();
});

againBtn.addEventListener("click", resetToUpload);
dismissErrorBtn.addEventListener("click", () => {
  errorCard.hidden = true;
});

function setFile(file) {
  if (!ACCEPTED.includes(file.type)) {
    showError("That file type is not a samosa. JPG and PNG only. We don't make the rules.");
    return;
  }
  if (file.size > MAX_BYTES) {
    showError("That image is too large to judge. Please pick something under 8 MB.");
    return;
  }
  selectedFile = file;
  const url = URL.createObjectURL(file);
  previewImg.src = url;
  dzIdle.hidden = true;
  dzPreview.hidden = false;
  analyzeBtn.disabled = false;
  errorCard.hidden = true;
  results.hidden = true;
}

function clearSelection() {
  selectedFile = null;
  lastResult = null;
  previewImg.src = "";
  dzIdle.hidden = false;
  dzPreview.hidden = true;
  analyzeBtn.disabled = true;
}

async function runAnalysis() {
  showLoading();

  const form = new FormData();
  form.append("image", selectedFile, selectedFile.name);

  try {
    const response = await fetch("/api/analyze", { method: "POST", body: form });
    const data = await response.json();
    if (data.success) {
      lastResult = data;
      renderResults(data);
    } else {
      showError(data.error || "The samosa evaded detection entirely.");
    }
  } catch (err) {
    showError("The geometry department is unreachable. Is the server running?");
  } finally {
    hideLoading();
  }
}

function showLoading() {
  let index = Math.floor(Math.random() * LOADING_MESSAGES.length);
  loadingMsg.textContent = LOADING_MESSAGES[index];
  messageTimer = setInterval(() => {
    index = (index + 1) % LOADING_MESSAGES.length;
    loadingMsg.textContent = LOADING_MESSAGES[index];
  }, 1400);
  loadingOverlay.hidden = false;
}

function hideLoading() {
  clearInterval(messageTimer);
  loadingOverlay.hidden = true;
}

function showError(message) {
  errorMessage.textContent = message;
  errorCard.hidden = false;
  errorCard.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderResults(data) {
  scoreValue.textContent = data.score.toFixed(1);
  bandEmoji.textContent = data.band_emoji;
  bandName.textContent = data.band;
  verdictLine.textContent = `“${data.verdict}”`;

  totalAngle.textContent = `${data.stats.total_angle.toFixed(1)}°`;

  legend.innerHTML = data.corners
    .map(
      (c) =>
        `<span class="legend-item"><span class="legend-dot" style="background:${CORNER_COLORS[c.label]}"></span>Corner ${c.label} — ${c.angle.toFixed(1)}°</span>`
    )
    .join("");

  const stats = {
    "Total angle": `${data.stats.total_angle.toFixed(1)}°`,
    "Sharpest corner": `${data.stats.sharpest.label}: ${data.stats.sharpest.angle.toFixed(1)}°`,
    "Widest corner": `${data.stats.widest.label}: ${data.stats.widest.angle.toFixed(1)}°`,
    "Average angle": `${data.stats.average_angle.toFixed(1)}°`,
    "Deviation from perfect 60°": `${data.stats.deviation.toFixed(2)}° average`,
    "Symmetry": `${data.stats.symmetry.toFixed(1)}%`,
  };
  statsList.innerHTML = Object.entries(stats)
    .map(([label, value]) => `<li><span>${label}</span><span>${value}</span></li>`)
    .join("");

  const signed = data.corners
    .map((c) => `${c.label}: ${c.angle - 60 >= 0 ? "+" : "−"}${Math.abs(c.angle - 60).toFixed(1)}°`)
    .join(", ");
  devNote.innerHTML = `Each corner vs. the perfect 60°: <b>${signed}</b>. The corners have been notified of their shortcomings.`;

  drawOverlay(data);

  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

function drawOverlay(data) {
  const canvas = resultCanvas;
  const ctx = canvas.getContext("2d");
  const img = previewImg;

  const render = () => {
    const panel = results.querySelector(".image-panel");
    const maxW = (panel.clientWidth || 640) - 10;
    const W = data.image_width;
    const H = data.image_height;
    const displayW = Math.min(maxW, W);
    const k = displayW / W;

    canvas.width = Math.round(W * k);
    canvas.height = Math.round(H * k);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    const pts = data.corners.map((c) => ({ x: c.x * k, y: c.y * k }));

    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    pts.slice(1).forEach((p) => ctx.lineTo(p.x, p.y));
    ctx.closePath();
    ctx.fillStyle = "rgba(245, 183, 35, 0.22)";
    ctx.fill();
    ctx.strokeStyle = "#E8590C";
    ctx.lineWidth = 4;
    ctx.lineJoin = "round";
    ctx.stroke();

    const cx = (pts[0].x + pts[1].x + pts[2].x) / 3;
    const cy = (pts[0].y + pts[1].y + pts[2].y) / 3;

    data.corners.forEach((c, i) => {
      const p = pts[i];
      const angle = Math.atan2(p.y - cy, p.x - cx);
      const labelX = p.x + Math.cos(angle) * 34;
      const labelY = p.y + Math.sin(angle) * 34;
      const color = CORNER_COLORS[c.label];

      ctx.beginPath();
      ctx.arc(p.x, p.y, 9, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#fff";
      ctx.stroke();

      ctx.font = "800 15px 'Baloo 2', 'Nunito', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const text = `${c.label} · ${c.angle.toFixed(1)}°`;
      const metrics = ctx.measureText(text);
      const boxW = metrics.width + 14;
      const boxH = 22;
      const bx = labelX - boxW / 2;
      const by = labelY - boxH / 2;

      ctx.fillStyle = "rgba(59, 43, 26, 0.88)";
      const r = 7;
      ctx.beginPath();
      ctx.moveTo(bx + r, by);
      ctx.lineTo(bx + boxW - r, by);
      ctx.quadraticCurveTo(bx + boxW, by, bx + boxW, by + r);
      ctx.lineTo(bx + boxW, by + boxH - r);
      ctx.quadraticCurveTo(bx + boxW, by + boxH, bx + boxW - r, by + boxH);
      ctx.lineTo(bx + r, by + boxH);
      ctx.quadraticCurveTo(bx, by + boxH, bx, by + boxH - r);
      ctx.lineTo(bx, by + r);
      ctx.quadraticCurveTo(bx, by, bx + r, by);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = "#fff";
      ctx.fillText(text, labelX, labelY + 1);
    });
  };

  if (img.complete && img.naturalWidth) {
    requestAnimationFrame(render);
  } else {
    img.onload = () => requestAnimationFrame(render);
  }
}

function resetToUpload() {
  clearSelection();
  results.hidden = true;
  errorCard.hidden = true;
  window.scrollTo({ top: 0, behavior: "smooth" });
}