// ═══════════════════════════════════════
//  PAMBARAM - config.js
//  All shared constants, presets, enums
// ═══════════════════════════════════════

// Project a 3D point (x, y, z) to isometric screen coordinates with a rotation angle (radians)
function projectPoint(x, y, z, angle) {
    const cx = ARENA_CX, cy = ARENA_CY;
    const dx = x - cx, dy = y - cy;
    const cosA = Math.cos(angle);
    const sinA = Math.sin(angle);
    const rx = dx * cosA - dy * sinA;
    const ry = dx * sinA + dy * cosA;
    const scale = 1.0;
    const isoX = (rx - ry) * Math.cos(Math.PI/6) * scale + cx;
    const isoY = (rx + ry) * Math.sin(Math.PI/6) * scale - z * scale + cy;
    return { x: isoX, y: isoY };
}

const SCREEN_W = 1200;
const SCREEN_H = 800;
const FPS      = 60;
const ARENA_CX = 600;
const ARENA_CY = 450;
const ARENA_R  = 280;
const RINGOUT_R = 320;
const MATCH_TIME = 180; // seconds

const GameState = Object.freeze({
  MENU:        "MENU",
  TOP_SELECT:  "TOP_SELECT",
  ARENA_SELECT:"ARENA_SELECT",
  PLAYING:     "PLAYING",
  PAUSED:      "PAUSED",
  GAME_OVER:   "GAME_OVER",
});

const TopType = Object.freeze({
  ATTACK:  "Attack",
  DEFENSE: "Defense",
  BALANCE: "Balance",
  SPEED:   "Speed",
});

const Difficulty = Object.freeze({
  EASY:   "Easy",
  MEDIUM: "Medium",
  HARD:   "Hard",
});

const AIState = Object.freeze({
  IDLE:    "IDLE",
  APPROACH:"APPROACH",
  ATTACK:  "ATTACK",
  RETREAT: "RETREAT",
  DEFEND:  "DEFEND",
  SPECIAL: "SPECIAL",
});

// rgb() strings used on canvas
const COLORS = {
  bg_dark:     "#0a0b0e",
  arena_floor: "#deb887",
  arena_ring:  "#8b4513",
  arena_void:  "#1a0f0a",
  gold:        "#f5b947",
  p1:          "#4294f5",
  p2:          "#e64652",
  green:       "#48c982",
  purple:      "#a26deb",
  text:        "#eef1f8",
};

const TOP_PRESETS = {
  "Velu Vettaikaran":{
    type:TopType.ATTACK, mass:3.5, spin_speed:1800, spin_decay:15,
    grip:1.2, color:"#dc3c3c", accent:"#ffc832", special:"Ram Strike",
    desc:"High mass, strong collision damage",
  },
  "Kottai Veeran":{
    type:TopType.DEFENSE, mass:4.5, spin_speed:1400, spin_decay:9,
    grip:1.5, color:"#3c64b4", accent:"#96b4dc", special:"Iron Wall",
    desc:"Heavy, resistant to knockback",
  },
  "Thiruvalluvar":{
    type:TopType.BALANCE, mass:2.5, spin_speed:1700, spin_decay:12,
    grip:1.3, color:"#50b464", accent:"#c8ffc8", special:"Spin Boost",
    desc:"Balanced stats for all situations",
  },
  "Puyal Kaalai":{
    type:TopType.SPEED, mass:1.8, spin_speed:2200, spin_decay:18,
    grip:1.0, color:"#c850c8", accent:"#ffb4ff", special:"Whirlwind",
    desc:"Fast and agile, quick direction changes",
  },
  "Maruthuvar":{
    type:TopType.BALANCE, mass:2.8, spin_speed:1600, spin_decay:6.5,
    grip:1.4, color:"#ff8c32", accent:"#ffdca0", special:"Spin Boost",
    desc:"Stable and reliable all-rounder",
  },
  "Sooravali":{
    type:TopType.SPEED, mass:1.6, spin_speed:2400, spin_decay:12,
    grip:0.9, color:"#00c8dc", accent:"#b4ffff", special:"Whirlwind",
    desc:"Blazing fast, hardest to control",
  },
  "Kallazhagar":{
    type:TopType.DEFENSE, mass:4.8, spin_speed:1300, spin_decay:4.5,
    grip:1.6, color:"#64503c", accent:"#c8b478", special:"Iron Wall",
    desc:"Immovable object, slow decay",
  },
  "Veerapandiya":{
    type:TopType.ATTACK, mass:3.8, spin_speed:1900, spin_decay:10,
    grip:1.1, color:"#b41414", accent:"#ff6432", special:"Ram Strike",
    desc:"Aggressive, devastating strikes",
  },
};

const ARENA_PRESETS = {
  "Gramam Thidal":{
    name:"Village Ground", floor:"#deb887", ring:"#8b4513",
    void:"#1a0f0a", grip:1.0, hazards:[],
    desc:"Flat, no hazards – pure skill",
  },
  "Kovil Prangaram":{
    name:"Temple Courtyard", floor:"#c8aa96", ring:"#a0501e",
    void:"#280f05", grip:1.05, hazards:["pillars"],
    desc:"Stone pillars at centre",
  },
  "Aaru Paarai":{
    name:"River Bed", floor:"#d2be9e", ring:"#967850",
    void:"#6496c8", grip:0.70, hazards:[],
    desc:"Sandy terrain, low grip",
  },
  "Neon Arangam":{
    name:"Neon Arena", floor:"#1e1440", ring:"#ff32c8",
    void:"#0a0520", grip:1.10, hazards:["boost_pads"],
    desc:"Cyberpunk with speed boost zones",
  },
};
