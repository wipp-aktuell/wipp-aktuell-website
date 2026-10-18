
const ICONS = {
  "clear-day": "☀️",
  "clear-night": "🌙",
  "partly-cloudy-day": "🌤️",
  "partly-cloudy-night": "☁️",
  cloudy: "☁️",
  fog: "🌫️",
  wind: "💨",
  rain: "🌧️",
  sleet: "🌨️",
  snow: "❄️",
  hail: "🌨️",
  thunderstorm: "⛈️"
};

const TZ = "Europe/Berlin";

function berlinDate(date) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(date);

  const get = type =>
    parts.find(part => part.type === type).value;

  return `${get("year")}-${get("month")}-${get("day")}`;
}

function nextDates() {
  const today = berlinDate(new Date());
  const [y, m, d] = today.split("-").map(Number);

  return [1, 2, 3, 4].map(offset => {
    const date = new Date(
      Date.UTC(y, m - 1, d + offset, 12)
    );
    return date.toISOString().slice(0, 10);
  });
}

function dailyForecast(records, date) {
  const hours = records.filter(item =>
    item &&
    item.timestamp &&
    berlinDate(new Date(item.timestamp)) === date &&
    Number.isFinite(item.temperature)
  );

  if (hours.length < 12) return null;

  const temperatures = hours.map(h => h.temperature);

  const daytime = hours.filter(h => {
    const hour = Number(
      new Intl.DateTimeFormat("en-GB", {
        timeZone: TZ,
        hour: "2-digit",
        hourCycle: "h23"
      }).format(new Date(h.timestamp))
    );
    return hour >= 10 && hour <= 16;
  });

  const icons = daytime
    .map(h => (h.icon || "").replace("-night", "-day"))
    .filter(Boolean);

  const frequency = {};
  for (const icon of icons) {
    frequency[icon] = (frequency[icon] || 0) + 1;
  }

  const icon = Object.keys(frequency).sort(
    (a, b) => frequency[b] - frequency[a]
  )[0];

  return {
    date,
    min: Math.round(Math.min(...temperatures)),
    max: Math.round(Math.max(...temperatures)),
    icon: ICONS[icon] || "🌡️"
  };
}

export async function onRequestGet() {
  const currentUrl =
    "https://api.brightsky.dev/current_weather?lat=51.116&lon=7.397";

  try {
    const response = await fetch(currentUrl, {
      cf: { cacheTtl: 1800, cacheEverything: true }
    });

    if (!response.ok) {
      throw new Error("Aktuelles Wetter nicht verfügbar");
    }

    const data = await response.json();
    const weather = data.weather;

    if (!weather || !Number.isFinite(weather.temperature)) {
      throw new Error("Ungültige Wetterdaten");
    }

    const result = {
      temperature: Math.round(weather.temperature),
      icon: ICONS[weather.icon] || "🌡️",
      updated: weather.timestamp || null,
      source: "Deutscher Wetterdienst / Bright Sky",
      forecast: []
    };

    try {
      const dates = nextDates();
      const forecastUrl =
        "https://api.brightsky.dev/weather" +
        "?lat=51.116&lon=7.397" +
        "&date=" + dates[0] +
        "&last_date=" + dates[3] +
        "&tz=Europe%2FBerlin";

      const forecastResponse = await fetch(forecastUrl, {
        cf: { cacheTtl: 1800, cacheEverything: true }
      });

      if (forecastResponse.ok) {
        const forecastData = await forecastResponse.json();
        const records = Array.isArray(forecastData.weather)
          ? forecastData.weather
          : [];

        result.forecast = dates
          .slice(0, 3)
          .map(date => dailyForecast(records, date))
          .filter(Boolean);
      }
    } catch (error) {
      console.warn("Wettervorhersage:", error.message);
    }

    return Response.json(result, {
      headers: {
        "Cache-Control": "public, max-age=1800"
      }
    });
  } catch (error) {
    return Response.json(
      { error: "Wetterdaten vorübergehend nicht verfügbar" },
      { status: 503 }
    );
  }
}
