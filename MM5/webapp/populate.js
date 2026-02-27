const params = new URLSearchParams(location.search);
const username = params.get("username") || "";

document.getElementById("u").textContent = username || "?";

async function loadUser() {
  if (!username) return;

  const r = await fetch(`/user?username=${encodeURIComponent(username)}`);
  const j = await r.json();

  if (j.ok) {
    document.getElementById("bal").textContent = j.balance;
    document.getElementById("t").textContent = j.time_string;
  } else {
    document.getElementById("bal").textContent = "unknown";
    document.getElementById("t").textContent = "-";
  }
}

async function loadUsersForDropdown() {
  const sel = document.getElementById("sendTo");
  sel.innerHTML = "";

  const r = await fetch("/users");
  const j = await r.json();

  if (!j.ok) return;

  for (const u of j.users) {
    if (u === username) continue; // don't let people send to themselves
    const opt = document.createElement("option");
    opt.value = u;
    opt.textContent = u;
    sel.appendChild(opt);
  }
}

function setMsg(text, ok) {
  const el = document.getElementById("sendMsg");
  el.textContent = text;
  el.style.color = ok ? "green" : "crimson";
}

function toggleSendPanel() {
  const panel = document.getElementById("sendPanel");
  const btn = document.getElementById("sendBtn");
  const showing = panel.style.display !== "none";

  if (showing) {
    panel.style.display = "none";
    btn.textContent = "Send";
    setMsg("", true);
    return;
  }

  panel.style.display = "block";
  btn.textContent = "Close";
  setMsg("", true);
  loadUsersForDropdown();
}

async function doTransfer() {
  const to = document.getElementById("sendTo").value;
  const amtRaw = document.getElementById("sendAmt").value;
  const amount = parseInt(amtRaw, 10);

  if (!to) return setMsg("Pick a recipient.", false);
  if (!Number.isFinite(amount) || amount <= 0) return setMsg("Enter a positive amount.", false);

  const r = await fetch("/transfer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from: username, to, amount }),
  });

  const j = await r.json();

  if (j.ok) {
    setMsg("Transaction success.", true);
    document.getElementById("bal").textContent = j.from_balance;
    document.getElementById("sendAmt").value = "";
    await loadUser();
  } else {
    setMsg(j.error || "Transaction failed.", false);
  }
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function initNewsTicker() {
  const ticker = document.getElementById("newsTicker");
  const inner = document.getElementById("newsTickerInner");

  if (!ticker || !inner) return;

  ticker.addEventListener("click", () => {
    const u = username ? `?username=${encodeURIComponent(username)}` : "";
    window.location.href = `/news.html${u}`;
  });

  // Load the latest headlines from the backend
  let headlines = [];
  try {
    const r = await fetch("/news?limit=3");
    const j = await r.json();
    if (j.ok) headlines = (j.items || []).map(x => x.headline);
  } catch (_) {}

  if (!headlines.length) {
    headlines = ["No news yet."];
  }

  const items = headlines.map(h => `<span class="ticker-item">• ${escapeHtml(h)}</span>`).join("");
  inner.innerHTML = items + items;

  let x = 0;
  const speedPxPerFrame = 0.6;
  let contentWidth = inner.scrollWidth / 2;

  function tick() {
    x -= speedPxPerFrame;
    if (-x >= contentWidth) x = 0;
    inner.style.transform = `translateX(${x}px)`;
    requestAnimationFrame(tick);
  }

  setTimeout(() => {
    contentWidth = inner.scrollWidth / 2;
  }, 200);

  requestAnimationFrame(tick);
}

// Refresh ticker headlines occasionally (cheap + good UX)
async function refreshTickerHeadlines() {
  const inner = document.getElementById("newsTickerInner");
  if (!inner) return;

  let headlines = [];
  try {
    const r = await fetch("/news?limit=3");
    const j = await r.json();
    if (j.ok) headlines = (j.items || []).map(x => x.headline);
  } catch (_) {}

  if (!headlines.length) return;

  const items = headlines.map(h => `<span class="ticker-item">• ${escapeHtml(h)}</span>`).join("");
  inner.innerHTML = items + items;
}

document.getElementById("sendBtn").addEventListener("click", toggleSendPanel);
document.getElementById("sendConfirm").addEventListener("click", doTransfer);

// --- STOCK MARKET (dynamic from /stocks) ---
let stockElBySymbol = null;

function indexStockElements() {
  stockElBySymbol = {};
  const els = document.querySelectorAll(".stock");
  for (const el of els) {
    const tickerEl = el.querySelector(".stock-ticker");
    const sym = (tickerEl ? tickerEl.textContent : "").trim();
    if (sym) stockElBySymbol[sym] = el;
  }
}

function fmtMoney(x) {
  if (typeof x !== "number" || !isFinite(x)) return "-";
  return `$${x.toFixed(2)}`;
}

function pctChange(price, prev) {
  if (typeof price !== "number" || typeof prev !== "number" || !isFinite(price) || !isFinite(prev) || prev === 0) return null;
  return ((price - prev) / prev) * 100;
}

function applyStockToElement(stock) {
  if (!stockElBySymbol) return;
  const el = stockElBySymbol[stock.symbol];
  if (!el) return;

  const priceEl = el.querySelector(".stock-price");
  const nameEl = el.querySelector(".stock-name");
  const changeEl = el.querySelector(".stock-change");

  if (priceEl) priceEl.textContent = fmtMoney(stock.price);
  if (nameEl) nameEl.textContent = stock.name || stock.symbol;

  if (changeEl) {
    const pct = pctChange(stock.price, stock.prev_price);
    if (pct === null) {
      changeEl.textContent = "•";
      changeEl.classList.remove("up", "down");
      return;
    }

    const up = pct >= 0;
    const arrow = up ? "⌃" : "⌄";
    changeEl.textContent = `${arrow} ${Math.abs(pct).toFixed(1)}%`;
    changeEl.classList.toggle("up", up);
    changeEl.classList.toggle("down", !up);
  }
}

async function loadStocks() {
  const r = await fetch("/stocks");
  const j = await r.json();
  if (!j.ok || !Array.isArray(j.stocks)) return;
  for (const s of j.stocks) applyStockToElement(s);
}

function initStockClicks() {
  const stocks = document.querySelectorAll(".stock");
  for (const el of stocks) {
    el.classList.add("clickable");
    el.addEventListener("click", () => {
      const tickerEl = el.querySelector(".stock-ticker");
      const ticker = (tickerEl ? tickerEl.textContent : "").trim();
      if (!ticker) return;

      const u = username ? encodeURIComponent(username) : "";
      const s = encodeURIComponent(ticker);
      window.location.href = `/stock.html?username=${u}&stock=${s}`;
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initNewsTicker();
  indexStockElements();
  initStockClicks();
  loadStocks();
  setInterval(refreshTickerHeadlines, 6000);
  setInterval(loadStocks, 2000);
});
loadUser();
setInterval(loadUser, 2000);
