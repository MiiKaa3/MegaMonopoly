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
  const showing = panel.style.display !== "none";

  if (showing) {
    panel.style.display = "none";
    setMsg("", true);
    return;
  }

  panel.style.display = "block";
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

document.getElementById("sendBtn").addEventListener("click", toggleSendPanel);
document.getElementById("sendConfirm").addEventListener("click", doTransfer);

loadUser();
setInterval(loadUser, 2000);

