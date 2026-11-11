/* Kontaktformular Wipperfürth aktuell
   Cloudflare Pages Functions + Resend + Turnstile */

const EMPFAENGER = "info@wipp-aktuell.de";
const ABSENDER = "Wipperfürth aktuell <kontaktformular@wipp-aktuell.de>";
const SITEKEY = "0x4AAAAAAF8ypEWQlgRSg-9F";

function htmlAntwort(text, status = 400) {
  return new Response(
    `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kontaktformular – Wipperfürth aktuell</title>
</head>
<body style="font-family:Arial,sans-serif;max-width:650px;margin:50px auto;padding:20px">
<h1>Kontaktformular</h1>
<p>${text}</p>
<p><a href="/kontakt/">Zurück zum Kontaktformular</a></p>
</body>
</html>`,
    {
      status,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store"
      }
    }
  );
}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.RESEND_API_KEY || !env.TURNSTILE_SECRET) {
    console.error("Kontaktformular: Konfiguration fehlt");
    return htmlAntwort(
      "Der Nachrichtenversand ist vorübergehend nicht verfügbar.",
      503
    );
  }

  const contentType = request.headers.get("content-type") || "";

  if (!contentType.includes("application/x-www-form-urlencoded") &&
      !contentType.includes("multipart/form-data")) {
    return htmlAntwort("Ungültiges Formularformat.", 415);
  }

  // Maximale Groesse der gesamten Formularanfrage: 24 KiB
  const MAX_BODY_BYTES = 24 * 1024;

  const contentLength = request.headers.get("content-length");

  if (
    contentLength !== null &&
    Number.isFinite(Number(contentLength)) &&
    Number(contentLength) > MAX_BODY_BYTES
  ) {
    return htmlAntwort("Die Formularanfrage ist zu gross.", 413);
  }

  let form;

  try {
    if (!request.body) {
      return htmlAntwort("Die Formulardaten fehlen.", 400);
    }

    const reader = request.body.getReader();
    const chunks = [];
    let totalBytes = 0;

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      totalBytes += value.byteLength;

      if (totalBytes > MAX_BODY_BYTES) {
        await reader.cancel();
        return htmlAntwort("Die Formularanfrage ist zu gross.", 413);
      }

      chunks.push(value);
    }

    const body = new Uint8Array(totalBytes);
    let offset = 0;

    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.byteLength;
    }

    form = await new Response(body, {
      headers: { "Content-Type": contentType }
    }).formData();

  } catch (error) {
    console.error("Kontaktformular: Ungueltige Formulardaten");

    return htmlAntwort(
      "Die Formulardaten konnten nicht gelesen werden.",
      400
    );
  }

  const name = String(form.get("name") || "").trim();
  const email = String(form.get("email") || "").trim();
  const betreff = String(form.get("betreff") || "").trim();
  const nachricht = String(form.get("nachricht") || "").trim();
  const honeypot = String(form.get("website") || "").trim();
  const turnstileToken = String(
    form.get("cf-turnstile-response") || ""
  );

  // Verstecktes Feld soll leer bleiben
  if (honeypot) {
    return htmlAntwort("Ihre Anfrage konnte nicht verarbeitet werden.");
  }

  if (
    name.length > 120 ||
    email.length > 254 ||
    betreff.length < 1 ||
    betreff.length > 140 ||
    nachricht.length < 10 ||
    nachricht.length > 8000 ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  ) {
    return htmlAntwort(
      "Bitte überprüfen Sie Ihre Eingaben und versuchen Sie es erneut."
    );
  }

  if (!turnstileToken || turnstileToken.length > 2048) {
    return htmlAntwort(
      "Bitte bestätigen Sie die Sicherheitsprüfung."
    );
  }

  // Turnstile serverseitig verifizieren
  let verification;

  try {
    const result = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          secret: env.TURNSTILE_SECRET,
          response: turnstileToken,
          remoteip: request.headers.get("CF-Connecting-IP")
        })
      }
    );

    verification = await result.json();
  } catch (error) {
    console.error("Turnstile-Fehler:", error);
    return htmlAntwort(
      "Die Sicherheitsprüfung ist momentan nicht verfügbar.",
      503
    );
  }

  if (
    !verification.success ||
    verification.hostname !== "wipp-aktuell.de"
  ) {
    return htmlAntwort(
      "Die Sicherheitsprüfung war nicht erfolgreich. Bitte versuchen Sie es erneut."
    );
  }

  // E-Mail über Resend versenden
  const emailText = [
    "Neue Nachricht über das Kontaktformular",
    "",
    `Name: ${name || "Nicht angegeben"}`,
    `E-Mail: ${email}`,
    `Betreff: ${betreff}`,
    "",
    "Nachricht:",
    nachricht
  ].join("\n");

  let versand;

  try {
    versand = await fetch(
      "https://api.resend.com/emails",
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.RESEND_API_KEY}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          from: ABSENDER,
          to: [EMPFAENGER],
          reply_to: email,
          subject: `Kontaktformular: ${betreff}`,
          text: emailText
        })
      }
    );
  } catch (error) {
    console.error("Resend-Verbindungsfehler:", error);
    return htmlAntwort(
      "Die Nachricht konnte derzeit nicht versendet werden.",
      503
    );
  }

  if (!versand.ok) {
    console.error(
      "Resend-Versandfehler:",
      versand.status,
      await versand.text()
    );

    return htmlAntwort(
      "Beim Nachrichtenversand ist ein Fehler aufgetreten.",
      502
    );
  }

  // Erfolgreiche Übergabe an Resend
  return new Response(null, {
    status: 303,
    headers: {
      "Location": "/kontakt/gesendet/",
      "Cache-Control": "no-store"
    }
  });
}

export function onRequestGet() {
  return new Response("Methode nicht erlaubt", {
    status: 405,
    headers: {
      "Allow": "POST"
    }
  });
}
