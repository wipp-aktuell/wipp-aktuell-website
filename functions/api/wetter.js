
export async function onRequestGet() {
  const url =
    "https://api.brightsky.dev/current_weather?lat=51.116&lon=7.397";

  try {
    const response = await fetch(url, {
      cf: { cacheTtl: 1800, cacheEverything: true }
    });

    if (!response.ok) {
      throw new Error("Wetterdaten nicht verfügbar");
    }

    const data = await response.json();
    const weather = data.weather;

    if (!weather || !Number.isFinite(weather.temperature)) {
      throw new Error("Ungültige Wetterdaten");
    }

    const iconMap = {
      "clear-day": "☀️",
      "clear-night": "🌙",
      "partly-cloudy-day": "🌤️",
      "partly-cloudy-night": "☁️",
      "cloudy": "☁️",
      "fog": "🌫️",
      "wind": "💨",
      "rain": "🌧️",
      "sleet": "🌨️",
      "snow": "❄️",
      "hail": "🌨️",
      "thunderstorm": "⛈️"
    };

    return Response.json(
      {
        temperature: Math.round(weather.temperature),
        icon: iconMap[weather.icon] || "🌡️",
        updated: weather.timestamp || null,
        source: "Deutscher Wetterdienst / Bright Sky"
      },
      {
        headers: {
          "Cache-Control": "public, max-age=1800"
        }
      }
    );
  } catch (error) {
    return Response.json(
      { error: "Wetterdaten vorübergehend nicht verfügbar" },
      { status: 503 }
    );
  }
}
