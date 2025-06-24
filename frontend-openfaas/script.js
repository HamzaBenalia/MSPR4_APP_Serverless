const gateway = "http://127.0.0.1:8080/function";

document.getElementById("create-form").addEventListener("submit", async e => {
  e.preventDefault();
  const username = document.getElementById("create-username").value;

  const res = await fetch(`${gateway}/create-password`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },  // texte brut, pas JSON
    body: username
  });

  const result = await res.json();  // parser la réponse JSON
  const qrCodeBase64 = result.qr_code_base64;

  // Affichage du QR code sous forme d'image
  document.getElementById("result").innerHTML = `<img src="data:image/png;base64,${qrCodeBase64}" alt="QR Code" />`;
});

document.getElementById("auth-form").addEventListener("submit", async e => {
  e.preventDefault();
  const username = document.getElementById("auth-username").value;
  const password = document.getElementById("auth-password").value;
  const code_2fa = document.getElementById("auth-2fa").value;

  const res = await fetch(`${gateway}/authenticate-user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, code_2fa })
  });
  document.getElementById("result").innerHTML = await res.text();
});

document.getElementById("reset-form").addEventListener("submit", async e => {
  e.preventDefault();
  const username = document.getElementById("reset-username").value;

  // Appel création mot de passe
  const res1 = await fetch(`${gateway}/create-password`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: username
  });

  // Appel création 2FA secret et QR code
  const res2 = await fetch(`${gateway}/create-2fa-secret-and-qrcode`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: username
  });

  // On récupère les réponses JSON
  const json1 = await res1.json();
  const json2 = await res2.json();

  // On affiche les deux QR codes (ou infos) en images
  document.getElementById("result").innerHTML =
    `<p>Mot de passe généré (QR Code) :</p><img src="data:image/png;base64,${json1.qr_code_base64}" alt="QR Code Password" /><br><br>` +
    `<p>2FA Secret (QR Code) :</p><img src="data:image/png;base64,${json2.qr_code_base64}" alt="QR Code 2FA" />`;
});
