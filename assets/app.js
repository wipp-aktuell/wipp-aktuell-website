const search = document.querySelector('#search');
if(search){search.addEventListener('input',()=>{const val=search.value.toLocaleLowerCase('de').trim();let visible=0;document.querySelectorAll('[data-search]').forEach(item=>{const match=item.dataset.search.includes(val);item.hidden=!match;if(match)visible++});document.querySelector('#no-results').hidden=visible!==0;});}



/* Wetteranzeige Wipperfürth aktuell */

async function ladeWipperWetter() {
  const anzeige = document.getElementById("wipp-wetter");
  if (!anzeige) return;

  try {
    const antwort = await fetch("/api/wetter");
    if (!antwort.ok) throw new Error("Wetterdaten nicht erreichbar");

    const wetter = await antwort.json();

    if (
      typeof wetter.temperature !== "number" ||
      typeof wetter.icon !== "string"
    ) {
      throw new Error("Ungültige Wetterdaten");
    }

    const teile = [];

    teile.push(
      `<span class="weather-current" title="Aktuelles Wetter in Wipperfürth">` +
      `${wetter.icon} ${wetter.temperature} °C</span>`
    );

    if (Array.isArray(wetter.forecast)) {
      const tage = wetter.forecast.slice(0, 3);

      const formatter = new Intl.DateTimeFormat("de-DE", {
        weekday: "short",
        timeZone: "Europe/Berlin"
      });

      for (const tag of tage) {
        if (
          typeof tag.date !== "string" ||
          !Number.isFinite(tag.min) ||
          !Number.isFinite(tag.max) ||
          typeof tag.icon !== "string"
        ) continue;

        const datum = new Date(tag.date + "T12:00:00Z");
        if (Number.isNaN(datum.getTime())) continue;

        const wochentag = formatter.format(datum);

        teile.push(
          `<span class="weather-day">` +
          `<span class="weather-day-label">${wochentag}</span> ` +
          `<span class="weather-day-icon">${tag.icon}</span> ` +
          `<span class="weather-day-temp">${tag.max}°/${tag.min}°</span>` +
          `</span>`
        );
      }
    }

    anzeige.innerHTML = teile.join(
      '<span class="weather-divider" aria-hidden="true"></span>'
    );

    anzeige.title =
      "Wetter in Wipperfürth – Daten: DWD / Bright Sky";

    anzeige.hidden = false;
  } catch (fehler) {
    anzeige.hidden = true;
    console.warn("Wetteranzeige:", fehler.message);
  }
}

ladeWipperWetter();
setInterval(ladeWipperWetter, 30 * 60 * 1000);

