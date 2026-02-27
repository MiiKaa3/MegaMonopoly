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

loadUser();
