
const gateway = "http://127.0.0.1:8080/function";

function createImageCard(title, base64) {
  return `
    <div style="border:1px solid #ccc; padding:15px; margin-bottom:15px; border-radius:8px; max-width:300px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1);">
      <h3 style="font-family:sans-serif; font-weight:600; margin-bottom:10px;">${title}</h3>
      <img src="data:image/png;base64,${base64}" alt="${title}" style="width:100%; height:auto; border-radius:4px;" />
    </div>
  `;
}

function showError(message) {
  document.getElementById("result").innerHTML = `<p style="color:red; font-weight:bold;">Erreur : ${message}</p>`;
}

async function fetchAndDisplayQRCode(url, username, title) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: username,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status} - ${text}`);
    }

    const json = await res.json();
    if (!json.qr_code_base64) {
      throw new Error("QR code non trouvé dans la réponse");
    }

    return json.qr_code_base64;
  } catch (e) {
    showError(`Erreur lors de la génération du ${title} : ${e.message}`);
    return null;
  }
}

document.getElementById("create-form").addEventListener("submit", async e => {
  e.preventDefault();
  const username = document.getElementById("create-username").value.trim();
  if (!username) return showError("Veuillez saisir un nom d'utilisateur.");

  document.getElementById("result").innerHTML = "<p>Génération en cours...</p>";

  const qrCodeBase64 = await fetchAndDisplayQRCode(`${gateway}/create-password`, username, "mot de passe");
  if (qrCodeBase64) {
    document.getElementById("result").innerHTML = createImageCard("QR Code Mot de passe", qrCodeBase64);
  }
});

document.getElementById("auth-form").addEventListener("submit", async e => {
  e.preventDefault();

  const username  = document.getElementById("auth-username").value.trim();
  const password  = document.getElementById("auth-password").value;
  const twofaCode = document.getElementById("auth-2fa").value;

  if (!username || !password || !twofaCode) {
    return showError("Tous les champs doivent être remplis.");
  }

  document.getElementById("result").innerHTML = "<p>Authentification en cours...</p>";

  // Génération du payload brut
  const payload = {
    username: username,
    password: password,
    "2fa_code": twofaCode
  };

  console.log("👉 Champs saisis :", payload);

  const jsonPayload = JSON.stringify(payload);
  console.log("📤 Payload JSON à envoyer :", jsonPayload);

  try {
    const res = await fetch("http://127.0.0.1:8080/function/authenticate-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: jsonPayload
    });

    console.log("📥 Status HTTP reçu :", res.status);

    const text = await res.text();
    console.log("📥 Réponse brute du serveur :", text);

    let data;
    try {
      data = JSON.parse(text);
    } catch (err) {
      console.error("❌ Erreur de parsing JSON :", err);
      return showError("Le serveur a répondu mais le JSON est mal formé.");
    }

    document.getElementById("result").innerHTML =
      `<pre style="white-space:pre-wrap; font-family:monospace;">${JSON.stringify(data, null, 2)}</pre>`;

  } catch (e) {
    console.error("❌ Erreur fetch :", e);
    showError(`Erreur lors de l'authentification : ${e.message}`);
  }
});



document.getElementById("reset-form").addEventListener("submit", async e => {
  e.preventDefault();
  const username = document.getElementById("reset-username").value.trim();
  if (!username) return showError("Veuillez saisir un nom d'utilisateur.");

  document.getElementById("result").innerHTML = "<p>Réinitialisation en cours...</p>";

  // Génération mot de passe et 2FA en parallèle
  const [qrPassword, qr2FA] = await Promise.all([
    fetchAndDisplayQRCode(`${gateway}/create-password`, username, "mot de passe"),
    fetchAndDisplayQRCode(`${gateway}/create-2fa-secret-and-qrcode`, username, "2FA secret"),
  ]);

  if (qrPassword && qr2FA) {
    document.getElementById("result").innerHTML =
      createImageCard("Mot de passe généré (QR Code)", qrPassword) +
      createImageCard("2FA Secret (QR Code)", qr2FA);
  }
});

