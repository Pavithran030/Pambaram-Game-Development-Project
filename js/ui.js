// ═══════════════════════════════════════
//  PAMBARAM - ui.js
//  DOM screen builder / updater helpers
// ═══════════════════════════════════════

function buildTopGrid(container, p1Name, p2Name) {
  container.innerHTML = "";
  Object.entries(TOP_PRESETS).forEach(([name, p]) => {
    const card = document.createElement("div");
    card.className = "top-card" +
      (name === p1Name ? " sel-p1" : "") +
      (name === p2Name ? " sel-p2" : "");
    card.dataset.name = name;

    const statBar = (label, val, max) => `
      <div class="mini-row">
        <span>${label}</span>
        <div class="mini-track"><div class="mini-fill" style="width:${Math.round(val/max*100)}%"></div></div>
      </div>`;

    card.innerHTML = `
      <div class="card-icon" style="background:${p.color}">
        <div class="card-icon-inner"></div>
      </div>
      <div class="card-title">${name}</div>
      <div class="card-subtitle">${p.type} Type</div>
      <div class="card-stats">
        ${statBar("Mass",p.mass,4.8)}
        ${statBar("Spin",p.spin_speed,2400)}
        ${statBar("Grip",p.grip,1.6)}
      </div>
      <div class="card-special">★ ${p.special}</div>
      <div class="card-subtitle" style="margin-top:4px;font-size:.72rem">${p.desc}</div>
    `;
    container.appendChild(card);
  });
}

function buildArenaGrid(container, selectedKey) {
  container.innerHTML = "";
  Object.entries(ARENA_PRESETS).forEach(([key, p]) => {
    const card = document.createElement("div");
    card.className = "arena-card" + (key === selectedKey ? " sel-arena" : "");
    card.dataset.key = key;
    card.innerHTML = `
      <div class="arena-floor-preview" style="background:${p.floor};border:3px solid ${p.ring};border-radius:50%;width:80px;height:80px"></div>
      <div class="card-title">${p.name}</div>
      <div class="card-subtitle">${key}</div>
      <div class="card-special">Grip: ${p.grip}×${p.hazards.length?` · ${p.hazards.join(", ")}`:" · No hazards"}</div>
      <div class="card-subtitle" style="margin-top:4px;font-size:.72rem">${p.desc}</div>
    `;
    container.appendChild(card);
  });
}

function updateHUD(p1, p2, matchTime) {
  const r1 = p1.maxSpin > 0 ? Math.max(0, p1.spin / p1.maxSpin) : 0;
  const r2 = p2.maxSpin > 0 ? Math.max(0, p2.spin / p2.maxSpin) : 0;

  document.getElementById("barP1Spin").style.width    = `${r1*100}%`;
  document.getElementById("pctP1Spin").textContent    = `${Math.floor(r1*100)}%`;
  document.getElementById("barP2Spin").style.width    = `${r2*100}%`;
  document.getElementById("pctP2Spin").textContent    = `${Math.floor(r2*100)}%`;

  document.getElementById("barP1Special").style.width  = `${p1.specialMeter}%`;
  document.getElementById("pctP1Special").textContent  = `${Math.floor(p1.specialMeter)}%`;
  document.getElementById("barP2Special").style.width  = `${p2.specialMeter}%`;
  document.getElementById("pctP2Special").textContent  = `${Math.floor(p2.specialMeter)}%`;

  // Spin bar color by level
  const spinColor = r => r > 0.5 ? "#48c982" : r > 0.2 ? "#f5b947" : "#e64652";
  document.getElementById("barP1Spin").style.background = spinColor(r1);
  document.getElementById("barP2Spin").style.background = spinColor(r2);

  // Special bar pulse when ready
  const s1el = document.getElementById("barP1Special");
  const s2el = document.getElementById("barP2Special");
  s1el.style.boxShadow = p1.specialMeter >= 100 ? "0 0 8px #f5b947" : "none";
  s2el.style.boxShadow = p2.specialMeter >= 100 ? "0 0 8px #f5b947" : "none";

  const t   = Math.max(0, matchTime);
  const mm  = String(Math.floor(t / 60)).padStart(2, "0");
  const ss  = String(Math.floor(t % 60)).padStart(2, "0");
  document.getElementById("hudTimer").textContent = `${mm}:${ss}`;
  document.getElementById("hudTimer").style.color = t < 30 ? "#e64652" : "#eef1f8";
}

function showGameOver(winner, p1, p2, reason, elapsed, points) {
  const titleEl = document.getElementById("goTitle");
  if (!winner) {
    titleEl.textContent = "DRAW!";
    titleEl.className   = "go-title draw";
    document.getElementById("goTopName").textContent = "";
  } else {
    const pid = winner.playerId;
    titleEl.textContent = `Player ${pid} Wins!`;
    titleEl.className   = `go-title${pid === 2 ? " p2-wins" : ""}`;
    document.getElementById("goTopName").textContent = `「${winner.name}」`;
  }
  document.getElementById("goReason").textContent = reason;
  document.getElementById("goP1Spin").textContent = Math.floor(p1.spin);
  document.getElementById("goP2Spin").textContent = Math.floor(p2.spin);

  const em = String(Math.floor(elapsed/60)).padStart(2,"0");
  const es = String(Math.floor(elapsed%60)).padStart(2,"0");
  document.getElementById("goTime").textContent  = `Time elapsed: ${em}:${es}`;
  document.getElementById("goScore").textContent = points > 0 ? `+${points} PTS` : "";

  showScreen("screen-gameover");
}

function showCountdown(val) {
  const el = document.getElementById("hudCountdown");
  if (val === null || val < 0) { el.classList.add("hidden"); return; }
  el.classList.remove("hidden");
  el.textContent = val === 0 ? "GO!" : String(val);
  // re-trigger animation
  el.style.animation = "none";
  void el.offsetHeight;
  el.style.animation = "";
}

function setLaunchHint(text) {
  const el = document.getElementById("hudLaunchHint");
  el.textContent    = text;
  el.style.opacity  = text ? "1" : "0";
}

function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => {
    s.classList.remove("active");
    if (s.classList.contains("modal-screen")) s.classList.add("hidden");
  });
  const target = document.getElementById(id);
  if (!target) return;
  target.classList.remove("hidden");
  target.classList.add("active");
}
