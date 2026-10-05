"use strict";

/* =========================================================
   SkyPulse Weather App — Browser Dashboard
   ========================================================= */

const $ = (id) => document.getElementById(id);

const els = {
    localClock: $("localClock"),
    clockText: $("clockText"),
    celsiusBtn: $("celsiusBtn"),
    fahrenheitBtn: $("fahrenheitBtn"),
    refreshBtn: $("refreshBtn"),
    themeBtn: $("themeBtn"),

    cityInput: $("cityInput"),
    clearSearchBtn: $("clearSearchBtn"),
    searchBtn: $("searchBtn"),
    locationBtn: $("locationBtn"),
    searchError: $("searchError"),
    recentRow: $("recentRow"),
    recentList: $("recentList"),

    welcomeState: $("welcomeState"),
    loadingState: $("loadingState"),
    errorState: $("errorState"),
    weatherDashboard: $("weatherDashboard"),

    errorTitle: $("errorTitle"),
    errorMessage: $("errorMessage"),
    retryBtn: $("retryBtn"),

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

    hourlyGrid: $("hourlyGrid"),
    forecastLocation: $("forecastLocation"),
    dailyGrid: $("dailyGrid")
};

const state = {
    city: "",
    weather: null,
    unit: localStorage.getItem("skypulse-unit") || "C",
    theme: localStorage.getItem("skypulse-theme") || "dark",
    favorites: JSON.parse(
        localStorage.getItem("skypulse-favorites") || "[]"
    ),
    recent: JSON.parse(
        localStorage.getItem("skypulse-recent") || "[]"
    ),
    lastRequest: ""
};


/* =========================================================
   HELPERS
   ========================================================= */

function setText(element, value) {
    if (element) {
        element.textContent =
            value === null || value === undefined ? "--" : value;
    }
}

function show(element) {
    if (element) element.hidden = false;
}

function hide(element) {
    if (element) element.hidden = true;
}

function celsiusToFahrenheit(value) {
    return Number(value) * 9 / 5 + 32;
}

function temperature(value) {
    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(Number(value))
    ) {
        return "--";
    }

    const number =
        state.unit === "F"
            ? celsiusToFahrenheit(value)
            : Number(value);

    return `${Math.round(number)}°`;
}

function windSpeed(value) {
    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(Number(value))
    ) {
        return "--";
    }

    const speed = Number(value);

    if (state.unit === "F") {
        return `${Math.round(speed * 2.23694)} mph`;
    }

    return `${Math.round(speed * 3.6)} km/h`;
}

function formatTime(timestamp, timezoneOffset = 0) {
    if (!timestamp) return "--";

    const date = new Date(
        (Number(timestamp) + Number(timezoneOffset)) * 1000
    );

    const hours = date.getUTCHours();
    const minutes = date.getUTCMinutes();

    const suffix = hours >= 12 ? "PM" : "AM";
    const hour12 = hours % 12 || 12;

    return `${hour12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

function formatUpdatedTime(timestamp) {
    if (!timestamp) return "--";

    return new Date(Number(timestamp) * 1000).toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit"
    });
}

function formatDay(dateString) {
    if (!dateString) return "--";

    return new Date(`${dateString}T12:00:00`).toLocaleDateString([], {
        weekday: "short"
    });
}

function formatDate(dateString) {
    if (!dateString) return "--";

    return new Date(`${dateString}T12:00:00`).toLocaleDateString([], {
        month: "short",
        day: "numeric"
    });
}

function capitalize(value) {
    if (!value) return "";

    return String(value)
        .toLowerCase()
        .replace(/\b\w/g, letter => letter.toUpperCase());
}


/* =========================================================
   SKYPULSE WEATHER IMAGES
   ========================================================= */

function weatherIconFile(icon) {
    const files = {
        sun: "sun.png",
        moon: "moon.png",
        "partly-day": "partly-day.png",
        "partly-night": "partly-night.png",
        cloud: "cloud.png",
        rain: "rain.png",
        storm: "storm.png",
        snow: "snow.png",
        fog: "fog.png"
    };

    return files[icon] || "cloud.png";
}

function weatherIconHTML(icon, className = "") {
    return `
        <img
            class="${className}"
            src="/static/weather_icons/${weatherIconFile(icon)}"
            alt=""
            aria-hidden="true"
            onerror="this.style.display='none'"
        >
    `;
}


/* =========================================================
   STATES
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
   THEME
   ========================================================= */

function applyTheme() {
    const theme =
        state.theme === "light"
            ? "light"
            : "dark";

    state.theme = theme;

    document.documentElement.dataset.theme = theme;
    document.body.dataset.theme = theme;

    localStorage.setItem("skypulse-theme", theme);

    if (els.themeBtn) {
        els.themeBtn.textContent =
            theme === "dark" ? "☀" : "☾";

        els.themeBtn.title =
            theme === "dark"
                ? "Switch to light mode"
                : "Switch to dark mode";

        els.themeBtn.setAttribute(
            "aria-label",
            els.themeBtn.title
        );
    }
}


/* =========================================================
   UNITS
   ========================================================= */

function updateUnitButtons() {
    els.celsiusBtn?.classList.toggle(
        "active",
        state.unit === "C"
    );

    els.fahrenheitBtn?.classList.toggle(
        "active",
        state.unit === "F"
    );

    localStorage.setItem(
        "skypulse-unit",
        state.unit
    );
}


/* =========================================================
   CLOCK
   ========================================================= */

function updateClock() {
    if (!els.clockText) return;

    setText(
        els.clockText,
        new Date().toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit"
        })
    );
}


/* =========================================================
   RECENT SEARCHES
   ========================================================= */

function saveRecent(city) {
    if (!city) return;

    const normalized = city.trim();

    state.recent = [
        normalized,
        ...state.recent.filter(
            item =>
                item.toLowerCase() !==
                normalized.toLowerCase()
        )
    ].slice(0, 6);

    localStorage.setItem(
        "skypulse-recent",
        JSON.stringify(state.recent)
    );

    renderRecent();
}

function renderRecent() {
    if (!els.recentList || !els.recentRow) return;

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
   FAVORITES
   ========================================================= */

function isFavorite(city) {
    return state.favorites.some(
        item =>
            item.toLowerCase() ===
            String(city).toLowerCase()
    );
}

function updateFavoriteButton() {
    if (!els.favoriteBtn || !state.city) return;

    const favorite = isFavorite(state.city);

    els.favoriteBtn.textContent =
        favorite ? "★" : "☆";

    els.favoriteBtn.classList.toggle(
        "active",
        favorite
    );

    els.favoriteBtn.title =
        favorite
            ? "Remove from favorites"
            : "Add to favorites";
}

function toggleFavorite() {
    if (!state.city) return;

    if (isFavorite(state.city)) {
        state.favorites =
            state.favorites.filter(
                item =>
                    item.toLowerCase() !==
                    state.city.toLowerCase()
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
   HERO ATMOSPHERE
   ========================================================= */

function updateHeroAtmosphere(kind, current) {
    if (!els.heroCard) return;

    const atmosphere =
        String(kind || "clouds").toLowerCase();

    els.heroCard.dataset.weather = atmosphere;
    els.heroCard.dataset.kind = atmosphere;

    const isNight =
        String(current?.icon_code || "").endsWith("n");

    els.heroCard.classList.toggle(
        "night",
        isNight
    );

    if (els.heroStars) {
        els.heroStars.hidden = !isNight;
    }

    if (els.heroRain) {
        els.heroRain.hidden =
            atmosphere !== "rain" &&
            atmosphere !== "storm";
    }
}


/* =========================================================
   HERO
   ========================================================= */

function renderHero(current) {
    if (!current) return;

    state.city =
        current.city ||
        state.city;

    setText(
        els.cityName,
        current.city || "--"
    );

    setText(
        els.countryName,
        current.country_name ||
        current.country ||
        "--"
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
        els.heroWeatherIcon.innerHTML =
            weatherIconHTML(
                current.icon,
                "hero-weather-image"
            );
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
        capitalize(
            current.main_condition ||
            current.condition
        )
    );

    updateHeroAtmosphere(
        current.kind,
        current
    );

    updateFavoriteButton();
}


/* =========================================================
   METRICS
   ========================================================= */

function renderMetrics(current) {
    if (!current) return;

    const humidity = Number(current.humidity);
    const pressure = Number(current.pressure);
    const visibility = Number(current.visibility);
    const clouds = Number(current.clouds);

    setText(
        els.humidityValue,
        Number.isFinite(humidity)
            ? `${humidity}%`
            : "--"
    );

    if (Number.isFinite(humidity)) {
        setText(
            els.humiditySub,
            humidity < 30
                ? "Dry"
                : humidity <= 60
                    ? "Comfortable"
                    : humidity <= 80
                        ? "Humid"
                        : "Very humid"
        );
    }

    setText(
        els.windValue,
        windSpeed(current.wind_speed)
    );

    setText(
        els.windSub,
        `${current.wind_label || "Wind"} • ${current.wind_compass || "--"}`
    );

    setText(
        els.pressureValue,
        Number.isFinite(pressure)
            ? `${pressure} hPa`
            : "--"
    );

    if (Number.isFinite(pressure)) {
        setText(
            els.pressureSub,
            pressure < 1000
                ? "Low"
                : pressure <= 1020
                    ? "Normal"
                    : "High"
        );
    }

    if (Number.isFinite(visibility)) {
        setText(
            els.visibilityValue,
            `${(visibility / 1000).toFixed(1)} km`
        );

        setText(
            els.visibilitySub,
            visibility >= 10000
                ? "Excellent"
                : visibility >= 5000
                    ? "Good"
                    : visibility >= 2000
                        ? "Moderate"
                        : "Poor"
        );
    } else {
        setText(els.visibilityValue, "--");
    }

    setText(
        els.cloudsValue,
        Number.isFinite(clouds)
            ? `${clouds}%`
            : "--"
    );

    if (Number.isFinite(clouds)) {
        setText(
            els.cloudsSub,
            clouds < 20
                ? "Clear sky"
                : clouds < 60
                    ? "Partly cloudy"
                    : clouds < 90
                        ? "Mostly cloudy"
                        : "Overcast"
        );
    }

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

    if (current.sunrise && current.sunset) {
        const seconds =
            Number(current.sunset) -
            Number(current.sunrise);

        const hours =
            Math.floor(seconds / 3600);

        const minutes =
            Math.floor(
                (seconds % 3600) / 60
            );

        setText(
            els.daylightValue,
            `${hours}h ${minutes}m`
        );
    } else {
        setText(
            els.daylightValue,
            "--"
        );
    }

    setText(
        els.daylightSub,
        "Daylight"
    );
}


/* =========================================================
   HOURLY FORECAST
   ========================================================= */

function renderHourly(hourly) {
    if (!els.hourlyGrid) return;

    els.hourlyGrid.innerHTML = "";

    if (
        !Array.isArray(hourly) ||
        !hourly.length
    ) {
        els.hourlyGrid.innerHTML =
            `<div class="forecast-empty">
                Hourly forecast unavailable.
            </div>`;
        return;
    }

    hourly.slice(0, 6).forEach(item => {
        const card =
            document.createElement("article");

        card.className = "hour-card";

        const rain =
            Number(item.pop || 0) * 100;

        card.innerHTML = `
            <div class="hour-time">
                ${item.time || "--"}
            </div>

            <div class="hour-icon">
                ${weatherIconHTML(item.icon, "forecast-weather-image")}
            </div>

            <div class="hour-temp">
                ${temperature(item.temperature)}
            </div>

            <div class="hour-condition">
                ${capitalize(item.condition)}
            </div>

            <div class="hour-rain ${
                rain >= 20 ? "" : "muted"
            }">
                ${rain >= 20
                    ? `💧 ${Math.round(rain)}%`
                    : "No rain"}
            </div>
        `;

        els.hourlyGrid.appendChild(card);
    });
}


/* =========================================================
   DAILY FORECAST
   ========================================================= */

function renderDaily(daily) {
    if (!els.dailyGrid) return;

    els.dailyGrid.innerHTML = "";

    if (
        !Array.isArray(daily) ||
        !daily.length
    ) {
        els.dailyGrid.innerHTML =
            `<div class="forecast-empty">
                Five-day forecast unavailable.
            </div>`;
        return;
    }

    daily.slice(0, 5).forEach((item, index) => {
        const card =
            document.createElement("article");

        card.className = "day-card";

        const high = Number(item.high);
        const low = Number(item.low);
        const pop =
            Math.round(
                Number(item.pop || 0) * 100
            );

        card.innerHTML = `
            <div class="day-header">
                <div>
                    <div class="day-name">
                        ${
                            item.day ||
                            formatDay(item.date)
                        }
                    </div>

                    <div class="day-date">
                        ${
                            item.date_label ||
                            formatDate(item.date)
                        }
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
                    ${weatherIconHTML(
                        item.icon,
                        "forecast-weather-image"
                    )}
                </div>

                <div class="day-condition">
                    ${capitalize(item.condition)}
                </div>
            </div>

            <div class="day-temperatures">
                <strong>
                    ${temperature(high)}
                </strong>

                <span>
                    ${temperature(low)}
                </span>
            </div>

            <div class="day-range">
                <span class="range-fill"></span>
            </div>

            <div class="day-footer">
                <span>
                    💧 ${pop}%
                </span>

                <span>
                    ${temperature(low)}
                    —
                    ${temperature(high)}
                </span>
            </div>
        `;

        els.dailyGrid.appendChild(card);
    });
}


/* =========================================================
   COMPLETE DASHBOARD
   ========================================================= */

function renderWeather(data) {
    if (
        !data ||
        !data.ok ||
        !data.current
    ) {
        showError(
            "Weather unavailable",
            "The weather service did not return valid weather data."
        );
        return;
    }

    state.weather = data;
    state.city =
        data.current.city ||
        state.city;

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
   CITY SEARCH
   ========================================================= */

async function fetchWeather(city) {
    const query =
        String(city || "").trim();

    if (!query) {
        if (els.searchError) {
            setText(
                els.searchError,
                "Please enter a city name."
            );
            show(els.searchError);
        }

        els.cityInput?.focus();
        return;
    }

    hide(els.searchError);

    state.lastRequest = query;

    showLoading();

    try {
        const response =
            await fetch(
                `/api/weather?city=${encodeURIComponent(query)}`,
                {
                    method: "GET",
                    headers: {
                        Accept:
                            "application/json"
                    },
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.ok
        ) {
            throw new Error(
                data.error ||
                data.message ||
                "Unable to retrieve weather information."
            );
        }

        saveRecent(
            data.current?.city ||
            query
        );

        if (els.cityInput) {
            els.cityInput.value =
                data.current?.city ||
                query;
        }

        renderWeather(data);

    } catch (error) {
        console.error(
            "SkyPulse weather error:",
            error
        );

        showError(
            "Weather unavailable",
            error.message ||
            "Unable to retrieve weather information. Please try again."
        );
    }
}


/* =========================================================
   MY LOCATION
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
                const latitude =
                    position.coords.latitude;

                const longitude =
                    position.coords.longitude;

                const response =
                    await fetch(
                        `/api/weather/location?lat=${encodeURIComponent(latitude)}&lon=${encodeURIComponent(longitude)}`,
                        {
                            method: "GET",
                            headers: {
                                Accept:
                                    "application/json"
                            },
                            cache: "no-store"
                        }
                    );

                const data =
                    await response.json();

                if (
                    !response.ok ||
                    !data.ok
                ) {
                    throw new Error(
                        data.error ||
                        "Unable to retrieve weather for your location."
                    );
                }

                state.city =
                    data.current?.city || "";

                if (els.cityInput) {
                    els.cityInput.value =
                        data.current?.city || "";
                }

                saveRecent(
                    data.current?.city ||
                    "My Location"
                );

                renderWeather(data);

            } catch (error) {
                console.error(
                    "SkyPulse location error:",
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
   SEARCH
   ========================================================= */

function performSearch() {
    const city =
        els.cityInput?.value.trim() || "";

    if (!city) {
        if (els.searchError) {
            setText(
                els.searchError,
                "Please enter a city name."
            );
            show(els.searchError);
        }

        els.cityInput?.focus();
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
   TRY CITY BUTTONS
   ========================================================= */

function setupTryCities() {
    document
        .querySelectorAll(".try-city")
        .forEach(button => {
            button.addEventListener(
                "click",
                () => {
                    const city =
                        button.dataset.city ||
                        button.textContent.trim();

                    if (els.cityInput) {
                        els.cityInput.value =
                            city;
                    }

                    fetchWeather(city);
                }
            );
        });
}


/* =========================================================
   KEYBOARD SHORTCUTS
   ========================================================= */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            document.activeElement ===
                els.cityInput
        ) {
            event.preventDefault();
            performSearch();
            return;
        }

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

        if (
            event.ctrlKey &&
            event.key.toLowerCase() === "l"
        ) {
            event.preventDefault();

            els.cityInput?.focus();
            els.cityInput?.select();

            return;
        }

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
    }
);


/* =========================================================
   INITIALIZE
   ========================================================= */

function initialize() {

    applyTheme();
    updateUnitButtons();
    updateClock();
    renderRecent();
    setupTryCities();

    setInterval(
        updateClock,
        1000
    );

    els.searchBtn?.addEventListener(
        "click",
        performSearch
    );

    els.cityInput?.addEventListener(
        "input",
        () => {
            if (
                els.cityInput.value.trim()
            ) {
                hide(els.searchError);
            }
        }
    );

    els.clearSearchBtn?.addEventListener(
        "click",
        clearSearch
    );

    els.locationBtn?.addEventListener(
        "click",
        fetchLocationWeather
    );

    els.refreshBtn?.addEventListener(
        "click",
        refreshWeather
    );

    els.retryBtn?.addEventListener(
        "click",
        () => {
            if (state.lastRequest) {
                fetchWeather(
                    state.lastRequest
                );
            } else {
                showWelcome();
            }
        }
    );

    els.themeBtn?.addEventListener(
        "click",
        () => {
            state.theme =
                state.theme === "dark"
                    ? "light"
                    : "dark";

            applyTheme();
        }
    );

    els.celsiusBtn?.addEventListener(
        "click",
        () => {
            state.unit = "C";
            updateUnitButtons();

            if (state.weather) {
                renderWeather(
                    state.weather
                );
            }
        }
    );

    els.fahrenheitBtn?.addEventListener(
        "click",
        () => {
            state.unit = "F";
            updateUnitButtons();

            if (state.weather) {
                renderWeather(
                    state.weather
                );
            }
        }
    );

    els.favoriteBtn?.addEventListener(
        "click",
        toggleFavorite
    );

    showWelcome();
}


if (
    document.readyState ===
    "loading"
) {
    document.addEventListener(
        "DOMContentLoaded",
        initialize
    );
} else {
    initialize();
}