const search = document.querySelector('#search');
if(search){search.addEventListener('input',()=>{const val=search.value.toLocaleLowerCase('de').trim();let visible=0;document.querySelectorAll('[data-search]').forEach(item=>{const match=item.dataset.search.includes(val);item.hidden=!match;if(match)visible++});document.querySelector('#no-results').hidden=visible!==0;});}

/* Wetteranzeige Wipperfürth aktuell */
async function ladeWipperWetter() {
  const anzeige = document.getElementById("wipp-wetter");
  if (!anzeige) return;

  try {
    const antwort = await fetch("/api/wetter");

    if (!antwort.ok) {
      throw new Error("Wetterdaten nicht erreichbar");
    }

    const wetter = await antwort.json();

    if (
      typeof wetter.temperature !== "number" ||
      typeof wetter.icon !== "string"
    ) {
      throw new Error("Ungültige Wetterdaten");
    }

    anzeige.textContent =
      wetter.icon + " " + wetter.temperature + " °C";

    anzeige.title =
      "Aktuelles Wetter in Wipperfürth – Daten: DWD / Bright Sky";

    anzeige.hidden = false;
  } catch (fehler) {
    anzeige.hidden = true;
    console.warn("Wetteranzeige:", fehler.message);
  }
}

ladeWipperWetter();
setInterval(ladeWipperWetter, 30 * 60 * 1000);
