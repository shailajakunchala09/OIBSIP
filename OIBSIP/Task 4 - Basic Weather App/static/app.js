"use strict";

/* =========================================================
   SkyPulse Weather App — Browser Dashboard
   Matches the SkyPulse desktop dashboard structure
   ========================================================= */

const $ = (id) => document.getElementById(id);

const els = {
    // Header
    localClock: $("localClock"),
    clockText: $("clockText"),
    celsiusBtn: $("celsiusBtn"),
    fahrenheitBtn: $("fahrenheitBtn"),
    refreshBtn: $("refreshBtn"),
    themeBtn: $("themeBtn"),

    // Search
    cityInput: $("cityInput"),
    clearSearchBtn: $("clearSearchBtn"),
    searchBtn: $("searchBtn"),
    locationBtn: $("locationBtn"),
    searchError: $("searchError"),
    recentRow: $("recentRow"),
    recentList: $("recentList"),

    // States
    welcomeState: $("welcomeState"),
    loadingState: $("loadingState"),
    errorState: $("errorState"),
    weatherDashboard: $("weatherDashboard"),

    // Error
    errorTitle: $("errorTitle"),
    errorMessage: $("errorMessage"),
    retryBtn: $("retryBtn"),

    // Hero
    heroCard: $("heroCard"),
    heroStars: $("heroStars"),
    heroRain: $("heroRain"),
    weatherStatus: $("weatherStatus"),
    favoriteBtn: $("favoriteBtn"),
    cityName: $("cityName"),
    countryName: $("countryName"),
    temperature: $("temperature"),
    feelsLike: $("feelsLike"),
    condition: $("condition"),
    highTemp: $("highTemp"),
    lowTemp: $("lowTemp"),
    heroWeatherIcon: $("heroWeatherIcon"),
    updatedTime: $("updatedTime"),
    heroLocalTime: $("heroLocalTime"),

    // Metrics
    humidityValue: $("humidityValue"),
    humiditySub: $("humiditySub"),
    windValue: $("windValue"),
    windSub: $("windSub"),
    pressureValue: $("pressureValue"),
    pressureSub: $("pressureSub"),
    visibilityValue: $("visibilityValue"),
    visibilitySub: $("visibilitySub"),
    cloudsValue: $("cloudsValue"),
    cloudsSub: $("cloudsSub"),
    sunriseValue: $("sunriseValue"),
    sunriseSub: $("sunriseSub"),
    sunsetValue: $("sunsetValue"),
    sunsetSub: $("sunsetSub"),
    daylightValue: $("daylightValue"),
    daylightSub: $("daylightSub"),

    // Forecast
    hourlyGrid: $("hourlyGrid"),
    forecastLocation: $("forecastLocation"),
    dailyGrid: $("dailyGrid")
};


/* =========================================================
   Application state
   ========================================================= */

const state = {
    city: "",
    weather: null,
    unit: localStorage.getItem("skypulse-unit") || "C",
    theme: localStorage.getItem("skypulse-theme") || "dark",
    favorites: JSON.parse(localStorage.getItem("skypulse-favorites") || "[]"),
    recent: JSON.parse(localStorage.getItem("skypulse-recent") || "[]"),
    lastRequest: ""
};


/* =========================================================
   Utility helpers
   ========================================================= */

function setText(element, value) {
    if (element) {
        element.textContent = value ?? "--";
    }
}


function show(element) {
    if (element) {
        element.hidden = false;
    }
}


function hide(element) {
    if (element) {
        element.hidden = true;
    }
}


function celsiusToFahrenheit(value) {
    return (Number(value) * 9 / 5) + 32;
}


function temperature(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "--";
    }

    const number = state.unit === "F"
        ? celsiusToFahrenheit(Number(value))
        : Number(value);

    return `${Math.round(number)}°`;
}


function temperatureWithUnit(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "--";
    }

    const number = state.unit === "F"
        ? celsiusToFahrenheit(Number(value))
        : Number(value);

    return `${Math.round(number)}°${state.unit}`;
}


function windSpeed(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "--";
    }

    // OpenWeather wind speed is m/s.
    const speed = Number(value);

    if (state.unit === "F") {
        return `${Math.round(speed * 2.23694)} mph`;
    }

    return `${speed.toFixed(1)} m/s`;
}


function formatTime(timestamp, timezoneOffset = 0) {
    if (!timestamp) {
        return "--";
    }

    const date = new Date((Number(timestamp) + Number(timezoneOffset)) * 1000);

    const hours = date.getUTCHours();
    const minutes = date.getUTCMinutes();

    const suffix = hours >= 12 ? "PM" : "AM";
    const hour12 = hours % 12 || 12;

    return `${hour12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}


function formatUpdatedTime(timestamp) {
    if (!timestamp) {
        return "--";
    }

    const date = new Date(Number(timestamp) * 1000);

    return date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit"
    });
}


function formatDay(dateString) {
    if (!dateString) {
        return "--";
    }

    const date = new Date(`${dateString}T12:00:00`);

    return date.toLocaleDateString([], {
        weekday: "short"
    });
}


function formatDate(dateString) {
    if (!dateString) {
        return "--";
    }

    const date = new Date(`${dateString}T12:00:00`);

    return date.toLocaleDateString([], {
        month: "short",
        day: "numeric"
    });
}


function capitalize(value) {
    if (!value) {
        return "";
    }

    return String(value)
        .toLowerCase()
        .replace(/\b\w/g, letter => letter.toUpperCase());
}


function weatherIcon(icon) {
    const icons = {
        sun: "\u2600\uFE0F",
        moon: "\uD83C\uDF19",
        "partly-day": "\u26C5",
        "partly-night": "\u263E",
        cloud: "\u2601\uFE0F",
        rain: "\uD83C\uDF27\uFE0F",
        storm: "\u26C8\uFE0F",
        snow: "\u2744\uFE0F",
        fog: "\uD83C\uDF2B\uFE0F"
    };

    return icons[icon] || "\u2601\uFE0F";
}


function weatherKind(kind) {
    return String(kind || "clouds").toLowerCase();
}


/* =========================================================
   State switching
   ========================================================= */

function showWelcome() {
    hide(els.loadingState);
    hide(els.errorState);
    hide(els.weatherDashboard);
    show(els.welcomeState);
}


function showLoading() {
    hide(els.welcomeState);
    hide(els.errorState);
    hide(els.weatherDashboard);
    show(els.loadingState);
}


function showDashboard() {
    hide(els.welcomeState);
    hide(els.loadingState);
    hide(els.errorState);
    show(els.weatherDashboard);
}


function showError(title, message) {
    hide(els.welcomeState);
    hide(els.loadingState);
    hide(els.weatherDashboard);

    setText(els.errorTitle, title || "Weather unavailable");
    setText(
        els.errorMessage,
        message || "Unable to load weather information."
    );

    show(els.errorState);
}


/* =========================================================
   Theme
   ========================================================= */

function applyTheme() {
    document.documentElement.dataset.theme = state.theme;
    document.body.dataset.theme = state.theme;

    if (els.themeBtn) {
        els.themeBtn.textContent = state.theme === "dark" ? "☀" : "☾";
        els.themeBtn.title =
            state.theme === "dark"
                ? "Switch to light mode"
                : "Switch to dark mode";
    }

    localStorage.setItem("skypulse-theme", state.theme);
}


/* =========================================================
   Unit switch
   ========================================================= */

function updateUnitButtons() {
    if (els.celsiusBtn) {
        els.celsiusBtn.classList.toggle(
            "active",
            state.unit === "C"
        );
    }

    if (els.fahrenheitBtn) {
        els.fahrenheitBtn.classList.toggle(
            "active",
            state.unit === "F"
        );
    }

    localStorage.setItem("skypulse-unit", state.unit);
}


/* =========================================================
   Header clock
   ========================================================= */

function updateClock() {
    if (!els.clockText) {
        return;
    }

    const now = new Date();

    setText(
        els.clockText,
        now.toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit"
        })
    );
}


/* =========================================================
   Recent searches
   ========================================================= */

function saveRecent(city) {
    if (!city) {
        return;
    }

    const normalized = city.trim();

    state.recent = [
        normalized,
        ...state.recent.filter(
            item => item.toLowerCase() !== normalized.toLowerCase()
        )
    ].slice(0, 6);

    localStorage.setItem(
        "skypulse-recent",
        JSON.stringify(state.recent)
    );

    renderRecent();
}


function renderRecent() {
    if (!els.recentList || !els.recentRow) {
        return;
    }

    els.recentList.innerHTML = "";

    if (!state.recent.length) {
        hide(els.recentRow);
        return;
    }

    show(els.recentRow);

    state.recent.forEach(city => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "recent-chip";
        button.textContent = city;

        button.addEventListener("click", () => {
            if (els.cityInput) {
                els.cityInput.value = city;
            }

            fetchWeather(city);
        });

        els.recentList.appendChild(button);
    });
}


/* =========================================================
   Favorites
   ========================================================= */

function isFavorite(city) {
    return state.favorites.some(
        item => item.toLowerCase() === String(city).toLowerCase()
    );
}


function updateFavoriteButton() {
    if (!els.favoriteBtn || !state.city) {
        return;
    }

    const favorite = isFavorite(state.city);

    els.favoriteBtn.textContent = favorite ? "★" : "☆";
    els.favoriteBtn.classList.toggle("active", favorite);
    els.favoriteBtn.title = favorite
        ? "Remove from favorites"
        : "Add to favorites";
}


function toggleFavorite() {
    if (!state.city) {
        return;
    }

    if (isFavorite(state.city)) {
        state.favorites = state.favorites.filter(
            item => item.toLowerCase() !== state.city.toLowerCase()
        );
    } else {
        state.favorites.push(state.city);
    }

    localStorage.setItem(
        "skypulse-favorites",
        JSON.stringify(state.favorites)
    );

    updateFavoriteButton();
}


/* =========================================================
   Hero
   ========================================================= */

function updateHeroAtmosphere(kind, current) {
    if (!els.heroCard) {
        return;
    }

    const atmosphere = weatherKind(kind);

    els.heroCard.dataset.weather = atmosphere;

    if (els.heroStars) {
        els.heroStars.hidden = !(
            current &&
            String(current.icon_code || "").endsWith("n")
        );
    }

    if (els.heroRain) {
        els.heroRain.hidden = !(
            atmosphere === "rain" ||
            atmosphere === "storm"
        );
    }
}


function renderHero(current) {
    if (!current) {
        return;
    }

    state.city = current.city || state.city;

    setText(els.cityName, current.city || "--");
    setText(
        els.countryName,
        current.country_name || current.country || "--"
    );

    setText(
        els.temperature,
        temperature(current.temperature)
    );

    setText(
        els.feelsLike,
        `Feels like ${temperature(current.feels_like)}`
    );

    setText(
        els.condition,
        capitalize(current.condition)
    );

    setText(
        els.highTemp,
        `H ${temperature(current.temp_max)}`
    );

    setText(
        els.lowTemp,
        `L ${temperature(current.temp_min)}`
    );

    if (els.heroWeatherIcon) {
        els.heroWeatherIcon.textContent =
            weatherIcon(current.icon);
    }

    setText(
        els.updatedTime,
        formatUpdatedTime(current.timestamp)
    );

    setText(
        els.heroLocalTime,
        formatTime(
            Math.floor(Date.now() / 1000),
            current.timezone || 0
        )
    );

    setText(
        els.weatherStatus,
        capitalize(current.main_condition || current.condition)
    );

    updateHeroAtmosphere(current.kind, current);
    updateFavoriteButton();
}


/* =========================================================
   Metrics
   ========================================================= */

function renderMetrics(current) {
    if (!current) {
        return;
    }

    const humidity = Number(current.humidity);
    const pressure = Number(current.pressure);
    const visibility = Number(current.visibility);
    const clouds = Number(current.clouds);

    // Humidity
    setText(
        els.humidityValue,
        Number.isFinite(humidity) ? `${humidity}%` : "--"
    );

    if (Number.isFinite(humidity)) {
        if (humidity < 30) {
            setText(els.humiditySub, "Dry");
        } else if (humidity <= 60) {
            setText(els.humiditySub, "Comfortable");
        } else if (humidity <= 80) {
            setText(els.humiditySub, "Humid");
        } else {
            setText(els.humiditySub, "Very humid");
        }
    }

    // Wind
    setText(
        els.windValue,
        windSpeed(current.wind_speed)
    );

    setText(
        els.windSub,
        `${current.wind_label || "Wind"} • ${current.wind_compass || "--"}`
    );

    // Pressure
    setText(
        els.pressureValue,
        Number.isFinite(pressure)
            ? `${pressure} hPa`
            : "--"
    );

    if (Number.isFinite(pressure)) {
        if (pressure < 1000) {
            setText(els.pressureSub, "Low");
        } else if (pressure <= 1020) {
            setText(els.pressureSub, "Normal");
        } else {
            setText(els.pressureSub, "High");
        }
    }

    // Visibility
    const visibilityKm = visibility / 1000;

    setText(
        els.visibilityValue,
        Number.isFinite(visibility)
            ? `${visibilityKm.toFixed(1)} km`
            : "--"
    );

    if (Number.isFinite(visibility)) {
        if (visibility >= 10000) {
            setText(els.visibilitySub, "Excellent");
        } else if (visibility >= 5000) {
            setText(els.visibilitySub, "Good");
        } else if (visibility >= 2000) {
            setText(els.visibilitySub, "Moderate");
        } else {
            setText(els.visibilitySub, "Poor");
        }
    }

    // Clouds
    setText(
        els.cloudsValue,
        Number.isFinite(clouds)
            ? `${clouds}%`
            : "--"
    );

    if (Number.isFinite(clouds)) {
        if (clouds < 20) {
            setText(els.cloudsSub, "Clear sky");
        } else if (clouds < 60) {
            setText(els.cloudsSub, "Partly cloudy");
        } else if (clouds < 90) {
            setText(els.cloudsSub, "Mostly cloudy");
        } else {
            setText(els.cloudsSub, "Overcast");
        }
    }

    // Sunrise
    setText(
        els.sunriseValue,
        formatTime(
            current.sunrise,
            current.timezone || 0
        )
    );

    setText(
        els.sunriseSub,
        "Local time"
    );

    // Sunset
    setText(
        els.sunsetValue,
        formatTime(
            current.sunset,
            current.timezone || 0
        )
    );

    setText(
        els.sunsetSub,
        "Local time"
    );

    // Daylight
    if (current.sunrise && current.sunset) {
        const seconds =
            Number(current.sunset) - Number(current.sunrise);

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor(
            (seconds % 3600) / 60
        );

        setText(
            els.daylightValue,
            `${hours}h ${minutes}m`
        );

        setText(
            els.daylightSub,
            "Daylight"
        );
    } else {
        setText(els.daylightValue, "--");
        setText(els.daylightSub, "Daylight");
    }
}


/* =========================================================
   Hourly forecast
   ========================================================= */

function renderHourly(hourly) {
    if (!els.hourlyGrid) {
        return;
    }

    els.hourlyGrid.innerHTML = "";

    if (!Array.isArray(hourly) || !hourly.length) {
        els.hourlyGrid.innerHTML =
            `<div class="forecast-empty">Hourly forecast unavailable.</div>`;
        return;
    }

    hourly.slice(0, 6).forEach(item => {
        const card = document.createElement("article");
        card.className = "hour-card";

        const rain =
            Number(item.pop || 0) * 100;

        card.innerHTML = `
            <div class="hour-time">
                ${item.time || "--"}
            </div>

            <div class="hour-icon">
                ${weatherIcon(item.icon)}
            </div>

            <div class="hour-temp">
                ${temperature(item.temperature)}
            </div>

            <div class="hour-condition">
                ${capitalize(item.condition)}
            </div>

            ${
                rain >= 20
                    ? `<div class="hour-rain">💧 ${Math.round(rain)}%</div>`
                    : `<div class="hour-rain muted">No rain</div>`
            }
        `;

        els.hourlyGrid.appendChild(card);
    });
}


/* =========================================================
   Daily forecast
   ========================================================= */

function renderDaily(daily) {
    if (!els.dailyGrid) {
        return;
    }

    els.dailyGrid.innerHTML = "";

    if (!Array.isArray(daily) || !daily.length) {
        els.dailyGrid.innerHTML =
            `<div class="forecast-empty">Five-day forecast unavailable.</div>`;
        return;
    }

    daily.slice(0, 5).forEach((item, index) => {
        const card = document.createElement("article");
        card.className = "day-card";

        const high = Number(item.high);
        const low = Number(item.low);
        const pop = Math.round(Number(item.pop || 0) * 100);

        const range =
            Number.isFinite(high) && Number.isFinite(low)
                ? Math.max(1, high - low)
                : 1;

        const min = Number.isFinite(low) ? low : 0;
        const max = Number.isFinite(high) ? high : 1;

        const lowPosition = 0;
        const highPosition = 100;

        card.innerHTML = `
            <div class="day-header">
                <div>
                    <div class="day-name">
                        ${item.day || formatDay(item.date)}
                    </div>

                    <div class="day-date">
                        ${item.date_label || formatDate(item.date)}
                    </div>
                </div>

                ${
                    index === 0
                        ? `<span class="today-badge">TODAY</span>`
                        : ""
                }
            </div>

            <div class="day-main">
                <div class="day-icon">
                    ${weatherIcon(item.icon)}
                </div>

                <div class="day-condition">
                    ${capitalize(item.condition)}
                </div>
            </div>

            <div class="day-temperatures">
                <strong>${temperature(high)}</strong>
                <span>${temperature(low)}</span>
            </div>

            <div class="day-range">
                <span
                    class="range-fill"
                    style="
                        left:${lowPosition}%;
                        width:${highPosition - lowPosition}%;
                    "
                ></span>
            </div>

            <div class="day-footer">
                <span>
                    💧 ${pop}%
                </span>

                <span>
                    ${temperature(min)} — ${temperature(max)}
                </span>
            </div>
        `;

        els.dailyGrid.appendChild(card);
    });
}


/* =========================================================
   Complete dashboard
   ========================================================= */

function renderWeather(data) {
    if (!data || !data.ok || !data.current) {
        showError(
            "Weather unavailable",
            "The weather service did not return valid weather data."
        );
        return;
    }

    state.weather = data;
    state.city = data.current.city || state.city;

    renderHero(data.current);
    renderMetrics(data.current);
    renderHourly(data.hourly);
    renderDaily(data.daily);

    setText(
        els.forecastLocation,
        `${data.current.city || ""}, ${
            data.current.country_name ||
            data.current.country ||
            ""
        }`
    );

    showDashboard();
}


/* =========================================================
   Fetch weather by city
   ========================================================= */

async function fetchWeather(city) {
    const query = String(city || "").trim();

    if (!query) {
        setText(
            els.searchError,
            "Please enter a city name."
        );

        if (els.cityInput) {
            els.cityInput.focus();
        }

        return;
    }

    hide(els.searchError);

    state.lastRequest = query;

    showLoading();

    try {
        const response = await fetch(
            `/api/weather?city=${encodeURIComponent(query)}`,
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(
                data.error ||
                data.message ||
                "Unable to retrieve weather information."
            );
        }

        saveRecent(data.current?.city || query);

        if (els.cityInput) {
            els.cityInput.value =
                data.current?.city || query;
        }

        renderWeather(data);

    } catch (error) {
        console.error("SkyPulse weather error:", error);

        showError(
            "Weather unavailable",
            error.message ||
            "Unable to retrieve weather information. Please try again."
        );
    }
}


/* =========================================================
   My Location
   ========================================================= */

function fetchLocationWeather() {
    if (!navigator.geolocation) {
        showError(
            "Location unavailable",
            "Your browser does not support location detection."
        );

        return;
    }

    showLoading();

    navigator.geolocation.getCurrentPosition(
        async position => {
            try {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                const response = await fetch(
                    `/api/weather/location?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`,
                    {
                        method: "GET",
                        headers: {
                            "Accept": "application/json"
                        },
                        cache: "no-store"
                    }
                );

                const data = await response.json();

                if (!response.ok || !data.ok) {
                    throw new Error(
                        data.error ||
                        "Unable to retrieve weather for your location."
                    );
                }

                state.city = data.current?.city || "";

                if (els.cityInput) {
                    els.cityInput.value =
                        data.current?.city || "";
                }

                saveRecent(data.current?.city || "My Location");

                renderWeather(data);

            } catch (error) {
                console.error(
                    "SkyPulse location weather error:",
                    error
                );

                showError(
                    "Weather unavailable",
                    error.message ||
                    "Unable to retrieve weather for your location."
                );
            }
        },

        error => {
            console.error(
                "SkyPulse geolocation error:",
                error
            );

            let message =
                "Unable to detect your location.";

            if (error.code === 1) {
                message =
                    "Location permission was denied. Please allow location access and try again.";
            } else if (error.code === 2) {
                message =
                    "Your location could not be determined.";
            } else if (error.code === 3) {
                message =
                    "Location detection timed out.";
            }

            showError(
                "Location unavailable",
                message
            );
        },

        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}


/* =========================================================
   Event handlers
   ========================================================= */

function performSearch() {
    const city = els.cityInput
        ? els.cityInput.value.trim()
        : "";

    if (!city) {
        if (els.searchError) {
            els.searchError.textContent =
                "Please enter a city name.";
            show(els.searchError);
        }

        if (els.cityInput) {
            els.cityInput.focus();
        }

        return;
    }

    fetchWeather(city);
}


function clearSearch() {
    if (els.cityInput) {
        els.cityInput.value = "";
        els.cityInput.focus();
    }

    hide(els.searchError);
}


function refreshWeather() {
    if (state.city) {
        fetchWeather(state.city);
    } else {
        showWelcome();
    }
}


/* =========================================================
   Keyboard shortcuts
   ========================================================= */

document.addEventListener("keydown", event => {
    // Enter in search
    if (
        event.key === "Enter" &&
        document.activeElement === els.cityInput
    ) {
        event.preventDefault();
        performSearch();
        return;
    }

    // F5 / Ctrl + R
    if (
        event.key === "F5" ||
        (
            event.ctrlKey &&
            event.key.toLowerCase() === "r"
        )
    ) {
        event.preventDefault();
        refreshWeather();
        return;
    }

    // Ctrl + L
    if (
        event.ctrlKey &&
        event.key.toLowerCase() === "l"
    ) {
        event.preventDefault();

        if (els.cityInput) {
            els.cityInput.focus();
            els.cityInput.select();
        }

        return;
    }

    // Ctrl + T
    if (
        event.ctrlKey &&
        event.key.toLowerCase() === "t"
    ) {
        event.preventDefault();

        state.theme =
            state.theme === "dark"
                ? "light"
                : "dark";

        applyTheme();
    }
});


/* =========================================================
   Initialize
   ========================================================= */

function initialize() {
    applyTheme();
    updateUnitButtons();
    updateClock();
    renderRecent();

    setInterval(updateClock, 1000);

    if (els.searchBtn) {
        els.searchBtn.addEventListener(
            "click",
            performSearch
        );
    }

    if (els.cityInput) {
        els.cityInput.addEventListener(
            "input",
            () => {
                if (els.cityInput.value.trim()) {
                    hide(els.searchError);
                }
            }
        );
    }

    if (els.clearSearchBtn) {
        els.clearSearchBtn.addEventListener(
            "click",
            clearSearch
        );
    }

    if (els.locationBtn) {
        els.locationBtn.addEventListener(
            "click",
            fetchLocationWeather
        );
    }

    if (els.refreshBtn) {
        els.refreshBtn.addEventListener(
            "click",
            refreshWeather
        );
    }

    if (els.retryBtn) {
        els.retryBtn.addEventListener(
            "click",
            () => {
                if (state.lastRequest) {
                    fetchWeather(state.lastRequest);
                } else {
                    showWelcome();
                }
            }
        );
    }

    if (els.themeBtn) {
        els.themeBtn.addEventListener(
            "click",
            () => {
                state.theme =
                    state.theme === "dark"
                        ? "light"
                        : "dark";

                applyTheme();
            }
        );
    }

    if (els.celsiusBtn) {
        els.celsiusBtn.addEventListener(
            "click",
            () => {
                state.unit = "C";
                updateUnitButtons();

                if (state.weather) {
                    renderWeather(state.weather);
                }
            }
        );
    }

    if (els.fahrenheitBtn) {
        els.fahrenheitBtn.addEventListener(
            "click",
            () => {
                state.unit = "F";
                updateUnitButtons();

                if (state.weather) {
                    renderWeather(state.weather);
                }
            }
        );
    }

    if (els.favoriteBtn) {
        els.favoriteBtn.addEventListener(
            "click",
            toggleFavorite
        );
    }

    showWelcome();
}


if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initialize
    );
} else {
    initialize();
}


/* =========================================================
   FINAL SKYPULSE THEME CONTROLLER
   ========================================================= */

(function () {

    const button = document.getElementById("themeBtn");

    function applyTheme(theme) {

        if (theme !== "light" && theme !== "dark") {
            theme = "dark";
        }

        document.documentElement.setAttribute("data-theme", theme);
        document.body.setAttribute("data-theme", theme);

        localStorage.setItem("skypulse-theme", theme);

        if (button) {
            button.textContent = theme === "dark" ? "☀" : "☾";
            button.title =
                theme === "dark"
                    ? "Switch to light mode"
                    : "Switch to dark mode";
            button.setAttribute(
                "aria-label",
                theme === "dark"
                    ? "Switch to light mode"
                    : "Switch to dark mode"
            );
        }
    }

    document.addEventListener("DOMContentLoaded", function () {

        const saved =
            localStorage.getItem("skypulse-theme") || "dark";

        applyTheme(saved);

        if (!button) return;

        /* Remove previous click handlers by replacing the button */
        const cleanButton = button.cloneNode(true);
        button.parentNode.replaceChild(cleanButton, button);

        cleanButton.addEventListener("click", function () {

            const current =
                document.documentElement.getAttribute("data-theme") || "dark";

            applyTheme(current === "dark" ? "light" : "dark");

        });

        applyTheme(saved);
    });

})();
