/* ============================================================
   BMI INSIGHT
   Main frontend application logic

   This file is shared by:
   - Dashboard
   - History
   - Analytics

   Chart design:
   - Straight / angular line segments (tension: 0)
   - No visible point markers (pointRadius: 0)
   - Hover tooltip still works
   ============================================================ */

const STORAGE_KEY = "bmiInsightSelectedUser";

/* ============================================================
   Global user data
   ============================================================ */

(function initialiseUserData() {
    const dataElement = document.getElementById("bmi-users-data");

    if (!dataElement) {
        window.BMI_USERS = Array.isArray(window.BMI_USERS)
            ? window.BMI_USERS
            : [];
        return;
    }

    try {
        const parsed = JSON.parse(dataElement.textContent || "[]");
        window.BMI_USERS = Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        console.error("Unable to parse BMI user data:", error);
        window.BMI_USERS = [];
    }
})();

/* ============================================================
   Local storage
   ============================================================ */

function getSelectedUserId() {
    try {
        return localStorage.getItem(STORAGE_KEY) || "";
    } catch (error) {
        return "";
    }
}

function setSelectedUserId(id) {
    try {
        if (id === null || id === undefined || id === "") {
            localStorage.removeItem(STORAGE_KEY);
            return;
        }
        localStorage.setItem(STORAGE_KEY, String(id));
    } catch (error) {
        console.warn("Unable to save selected user:", error);
    }
}

/* ============================================================
   API helper
   ============================================================ */

async function fetchJSON(url, options = {}) {
    let response;

    try {
        response = await fetch(url, options);
    } catch (error) {
        throw new Error("Unable to connect to the server. Please try again.");
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.error ||
            data.message ||
            `Request failed (${response.status})`
        );
    }

    return data;
}

/* ============================================================
   Toast notifications
   ============================================================ */

function showToast(message, isError = false) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast" + (isError ? " toast-error" : "");
    toast.textContent = String(message ?? "");
    container.appendChild(toast);

    window.setTimeout(() => {
        toast.remove();
    }, 3200);
}

/* ============================================================
   BMI category helpers
   ============================================================ */

function categoryClass(category) {
    return {
        Underweight: "badge-underweight",
        Normal: "badge-normal",
        Overweight: "badge-overweight",
        Obese: "badge-obese",
    }[category] || "badge-normal";
}

function categoryColor(category) {
    return {
        Underweight: "#5CA2EE",
        Normal: "#32B889",
        Overweight: "#EFB63D",
        Obese: "#ED6677",
    }[category] || "#5468FF";
}

/* ============================================================
   User selector
   ============================================================ */

function populateUserSelect(select, users, selectedId) {
    if (!select) return;

    const safeUsers = Array.isArray(users) ? users : [];
    select.innerHTML = "";

    if (!safeUsers.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "No users yet";
        select.appendChild(option);
        setSelectedUserId("");
        updateAvatar();
        return;
    }

    safeUsers.forEach((user) => {
        const option = document.createElement("option");
        option.value = user.id;
        option.textContent = user.name;
        select.appendChild(option);
    });

    const matchingUser = safeUsers.find(
        (user) => String(user.id) === String(selectedId)
    );

    select.value = matchingUser
        ? String(matchingUser.id)
        : String(safeUsers[0].id);

    setSelectedUserId(select.value);
    updateAvatar();
}

function updateAvatar() {
    const select = document.getElementById("user-select");
    const avatar = document.querySelector(".mini-avatar");

    if (!select || !avatar) return;

    const user = (window.BMI_USERS || []).find(
        (item) => String(item.id) === String(select.value)
    );

    avatar.textContent =
        user?.name?.trim()?.charAt(0)?.toUpperCase() || "S";
}

function initUserSelect(onChange) {
    const select = document.getElementById("user-select");
    if (!select) return null;

    populateUserSelect(
        select,
        Array.isArray(window.BMI_USERS) ? window.BMI_USERS : [],
        getSelectedUserId()
    );

    if (!select.dataset.bmiInsightBound) {
        select.addEventListener("change", () => {
            setSelectedUserId(select.value);
            updateAvatar();

            if (typeof onChange === "function") {
                onChange(select.value);
            }
        });

        select.dataset.bmiInsightBound = "1";
    }

    const addUserButton = document.getElementById("add-user-btn");

    if (addUserButton && !addUserButton.dataset.bmiInsightBound) {
        addUserButton.addEventListener("click", async () => {
            const enteredName = window.prompt(
                "Enter a name for the new user:"
            );

            if (!enteredName || !enteredName.trim()) {
                return;
            }

            const name = enteredName.trim();

            try {
                const user = await fetchJSON("/api/users", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ name }),
                });

                if (!Array.isArray(window.BMI_USERS)) {
                    window.BMI_USERS = [];
                }

                const existingIndex = window.BMI_USERS.findIndex(
                    (item) => String(item.id) === String(user.id)
                );

                if (existingIndex === -1) {
                    window.BMI_USERS.push(user);
                } else {
                    window.BMI_USERS[existingIndex] = user;
                }

                populateUserSelect(
                    select,
                    window.BMI_USERS,
                    user.id
                );

                updateAvatar();

                showToast(
                    user.existing
                        ? `${user.name} already exists`
                        : `Added ${user.name}`
                );

                if (typeof onChange === "function") {
                    onChange(select.value);
                }
            } catch (error) {
                showToast(error.message, true);
            }
        });

        addUserButton.dataset.bmiInsightBound = "1";
    }

    return select;
}

/* ============================================================
   BMI score ring
   ============================================================ */

function setRing(bmi, category) {
    const ring = document.getElementById("bmi-ring");
    if (!ring) return;

    const numericBMI = Number(bmi);

    if (!Number.isFinite(numericBMI)) {
        ring.style.setProperty("--score-progress", "0deg");
        ring.style.setProperty("--ring-color", "#5468FF");
        return;
    }

    const position = Math.max(
        0,
        Math.min((numericBMI - 15) / 25, 1)
    );

    ring.style.setProperty(
        "--score-progress",
        `${position * 360}deg`
    );

    ring.style.setProperty(
        "--ring-color",
        categoryColor(category)
    );
}

/* ============================================================
   Dashboard
   ============================================================ */

function initDashboard() {
    const calculateButton = document.getElementById("calculate-btn");
    if (!calculateButton) return;

    const resetButton = document.getElementById("reset-btn");
    const weightInput = document.getElementById("weight-input");
    const heightInput = document.getElementById("height-input");
    const formError = document.getElementById("form-error");
    const resultValue = document.getElementById("result-value");
    const resultBadge = document.getElementById("result-badge");
    const resultPlaceholder = document.getElementById("result-placeholder");
    const scaleMarker = document.getElementById("scale-marker");
    const recentRecords = document.getElementById("recent-records");
    const resultWeight = document.getElementById("result-weight");
    const resultHeight = document.getElementById("result-height");
    const resultState = document.getElementById("result-state");

    const userSelect = initUserSelect(loadRecentRecords);

    async function loadRecentRecords() {
        if (!userSelect?.value) return;

        try {
            const records = await fetchJSON(
                `/api/records/${userSelect.value}`
            );

            renderRecentRecords(records.slice(0, 5));
            drawDashboardTrend(records);
        } catch (error) {
            showToast(error.message, true);
        }
    }

    function renderRecentRecords(records) {
        if (!recentRecords) return;

        if (!records.length) {
            recentRecords.innerHTML = `
                <div class="empty-state">
                    No records yet. Calculate your first BMI reading.
                </div>
            `;
            return;
        }

        recentRecords.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Date &amp; Time</th>
                        <th>Weight</th>
                        <th>Height</th>
                        <th>BMI</th>
                        <th>Category</th>
                    </tr>
                </thead>
                <tbody>
                    ${records.map((record) => `
                        <tr>
                            <td>${escapeHTML(record.created_at)}</td>
                            <td>${escapeHTML(record.weight)} kg</td>
                            <td>${escapeHTML(record.height)} m</td>
                            <td>${Number(record.bmi).toFixed(2)}</td>
                            <td>
                                <span class="category-badge ${categoryClass(record.category)}">
                                    ${escapeHTML(record.category)}
                                </span>
                            </td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    }

    if (!calculateButton.dataset.bmiInsightBound) {
        calculateButton.addEventListener("click", async () => {
            if (formError) formError.textContent = "";

            if (!userSelect?.value) {
                if (formError) {
                    formError.textContent =
                        "Please select or add a user first.";
                }
                return;
            }

            calculateButton.disabled = true;
            calculateButton.textContent = "Calculating...";

            try {
                const result = await fetchJSON("/api/calculate", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        user_id: userSelect.value,
                        weight: weightInput?.value || "",
                        height: heightInput?.value || "",
                    }),
                });

                if (resultValue) {
                    resultValue.textContent =
                        Number(result.bmi).toFixed(2);
                }

                if (resultBadge) {
                    resultBadge.style.display = "inline-flex";
                    resultBadge.textContent = result.category;
                    resultBadge.className =
                        `category-badge ${categoryClass(result.category)}`;
                }

                if (resultPlaceholder) {
                    resultPlaceholder.textContent =
                        `Your BMI is ${Number(result.bmi).toFixed(2)} and is classified as ${result.category}.`;
                }

                if (resultWeight) {
                    resultWeight.textContent =
                        `${result.weight} kg`;
                }

                if (resultHeight) {
                    resultHeight.textContent =
                        `${result.height} m`;
                }

                if (resultState) {
                    resultState.textContent = "Updated";
                }

                if (scaleMarker) {
                    const position = Math.max(
                        0,
                        Math.min(Number(result.scale_position), 1)
                    );

                    scaleMarker.style.display = "block";
                    scaleMarker.style.left =
                        `${position * 100}%`;
                }

                setRing(
                    result.bmi,
                    result.category
                );

                showToast("BMI calculated and saved");

                await loadRecentRecords();

                if (typeof window.refreshAnalytics === "function") {
                    await window.refreshAnalytics();
                }
            } catch (error) {
                if (formError) {
                    formError.textContent = error.message;
                }
            } finally {
                calculateButton.disabled = false;
                calculateButton.textContent = "Calculate BMI";
            }
        });

        calculateButton.dataset.bmiInsightBound = "1";
    }

    if (resetButton && !resetButton.dataset.bmiInsightBound) {
        resetButton.addEventListener("click", () => {
            if (weightInput) weightInput.value = "";
            if (heightInput) heightInput.value = "";
            if (formError) formError.textContent = "";

            if (resultValue) {
                resultValue.textContent = "--";
            }

            if (resultBadge) {
                resultBadge.style.display = "none";
                resultBadge.textContent = "";
            }

            if (resultPlaceholder) {
                resultPlaceholder.textContent =
                    "Fill in the form to see your BMI result and classification.";
            }

            if (resultWeight) {
                resultWeight.textContent = "--";
            }

            if (resultHeight) {
                resultHeight.textContent = "--";
            }

            if (resultState) {
                resultState.textContent = "Ready";
            }

            if (scaleMarker) {
                scaleMarker.style.display = "none";
            }

            setRing(null, null);
        });

        resetButton.dataset.bmiInsightBound = "1";
    }

    loadRecentRecords();
}

/* ============================================================
   Dashboard BMI trend
   ============================================================ */

function drawDashboardTrend(records) {
    const canvas = document.getElementById("dashboard-bmi-chart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    destroyChart(canvas);

    const ordered = sortRecordsAscending(records);

    /*
     * No standalone points.
     * A trend requires at least two measurements.
     */
    if (ordered.length < 2) {
        return;
    }

    const labels = ordered.map((record) =>
        formatShortDate(record.created_at)
    );

    const values = ordered.map((record) =>
        Number(record.bmi)
    );

    const chart = new Chart(canvas, {
        type: "line",

        data: {
            labels,

            datasets: [
                {
                    label: "BMI",
                    data: values,

                    borderColor: "#5468FF",
                    backgroundColor:
                        "rgba(84, 104, 255, 0.10)",

                    fill: true,

                    /*
                     * IMPORTANT:
                     * tension 0 = straight line segments.
                     * This creates clear peaks and dips.
                     */
                    tension: 0,
                    cubicInterpolationMode: "default",

                    /*
                     * No visible dots.
                     */
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    pointHitRadius: 12,

                    borderWidth: 3,
                    spanGaps: true,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            interaction: {
                mode: "index",
                intersect: false,
            },

            elements: {
                line: {
                    tension: 0,
                },

                point: {
                    radius: 0,
                    hoverRadius: 0,
                    hitRadius: 12,
                },
            },

            plugins: {
                legend: {
                    display: false,
                },

                tooltip: {
                    backgroundColor: "#0d1726",
                    titleColor: "#ffffff",
                    bodyColor: "#ffffff",
                    padding: 12,
                    cornerRadius: 10,
                    displayColors: false,

                    callbacks: {
                        label(context) {
                            return `BMI: ${Number(context.raw).toFixed(2)}`;
                        },
                    },
                },
            },

            scales: {
                x: {
                    border: {
                        display: false,
                    },

                    grid: {
                        display: false,
                    },

                    ticks: {
                        color: "#8793a5",
                        font: {
                            size: 10,
                        },
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 6,
                    },
                },

                y: {
                    beginAtZero: false,

                    border: {
                        display: false,
                    },

                    grid: {
                        color: "rgba(30,48,76,.08)",
                    },

                    ticks: {
                        color: "#8793a5",

                        font: {
                            size: 10,
                        },

                        callback(value) {
                            return Number(value).toFixed(0);
                        },
                    },
                },
            },
        },
    });

    canvas._bmiInsightChart = chart;
}

/* ============================================================
   History
   ============================================================ */

function initHistory() {
    const tableWrap =
        document.getElementById(
            "history-table-wrap"
        );

    if (!tableWrap) {
        return;
    }

    const searchInput =
        document.getElementById(
            "search-input"
        );

    const profileName =
        document.getElementById(
            "history-profile-name"
        );

    const exportLink =
        document.getElementById(
            "export-link"
        );

    let allRecords = [];

    const userSelect =
        initUserSelect(loadHistory);

    function updateExportLink() {
        if (
            exportLink &&
            userSelect?.value
        ) {
            exportLink.href =
                `/export/${userSelect.value}`;
        }
    }

    async function loadHistory() {
        if (!userSelect?.value) {
            return;
        }

        updateExportLink();

        try {
            allRecords =
                await fetchJSON(
                    `/api/records/${userSelect.value}`
                );

            const user =
                (window.BMI_USERS || []).find(
                    (item) =>
                        String(item.id) ===
                        String(userSelect.value)
                );

            if (profileName) {
                profileName.textContent =
                    user?.name ||
                    "Selected user";
            }

            renderHistoryTable(allRecords);
        } catch (error) {
            showToast(
                error.message,
                true
            );
        }
    }

    function renderHistoryTable(records) {
        if (!records.length) {
            tableWrap.innerHTML = `
                <div class="empty-state">
                    No records found for this profile.
                </div>
            `;
            return;
        }

        tableWrap.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Date &amp; Time</th>
                        <th>Weight</th>
                        <th>Height</th>
                        <th>BMI</th>
                        <th>Category</th>
                        <th></th>
                    </tr>
                </thead>

                <tbody>
                    ${records.map((record) => `
                        <tr>
                            <td>${escapeHTML(record.created_at)}</td>

                            <td>
                                ${escapeHTML(record.weight)} kg
                            </td>

                            <td>
                                ${escapeHTML(record.height)} m
                            </td>

                            <td>
                                ${Number(record.bmi).toFixed(2)}
                            </td>

                            <td>
                                <span class="category-badge ${categoryClass(record.category)}">
                                    ${escapeHTML(record.category)}
                                </span>
                            </td>

                            <td>
                                <button
                                    type="button"
                                    class="btn-danger delete-record-btn"
                                    data-id="${record.id}"
                                >
                                    Delete
                                </button>
                            </td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;

        tableWrap
            .querySelectorAll(
                ".delete-record-btn"
            )
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    async () => {

                        if (
                            !window.confirm(
                                "Delete this BMI record? This can't be undone."
                            )
                        ) {
                            return;
                        }

                        try {
                            await fetchJSON(
                                `/api/records/${button.dataset.id}`,
                                {
                                    method: "DELETE",
                                }
                            );

                            showToast(
                                "Record deleted"
                            );

                            await loadHistory();

                            if (
                                typeof window.refreshAnalytics ===
                                "function"
                            ) {
                                await window.refreshAnalytics();
                            }

                        } catch (error) {
                            showToast(
                                error.message,
                                true
                            );
                        }
                    }
                );
            });
    }

    if (
        searchInput &&
        !searchInput.dataset.bmiInsightBound
    ) {
        searchInput.addEventListener(
            "input",
            () => {
                const term =
                    searchInput.value
                        .trim()
                        .toLowerCase();

                const filtered =
                    allRecords.filter(
                        (record) =>
                            String(
                                record.category ||
                                ""
                            )
                                .toLowerCase()
                                .includes(term) ||

                            String(
                                record.created_at ||
                                ""
                            )
                                .toLowerCase()
                                .includes(term)
                    );

                renderHistoryTable(
                    filtered
                );
            }
        );

        searchInput.dataset.bmiInsightBound =
            "1";
    }

    loadHistory();
}

/* ============================================================
   Premium Analytics
   ============================================================ */

function initAnalytics() {
    const bmiCanvas =
        document.getElementById(
            "bmi-chart"
        );

    if (
        !bmiCanvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }

    const weightCanvas =
        document.getElementById(
            "weight-chart"
        );

    const userSelect =
        initUserSelect(loadAnalytics);

    let allRecords = [];
    let activeRange = "all";

    const rangeButtons =
        Array.from(
            document.querySelectorAll(
                ".range-btn"
            )
        );

    rangeButtons.forEach(
        (button) => {

            if (
                button.dataset
                    .bmiInsightBound
            ) {
                return;
            }

            button.addEventListener(
                "click",
                () => {

                    activeRange =
                        button.dataset.range ||
                        "all";

                    rangeButtons.forEach(
                        (item) => {

                            item.classList.toggle(
                                "active",
                                item === button
                            );

                        }
                    );

                    redrawCharts();
                }
            );

            button.dataset
                .bmiInsightBound =
                "1";
        }
    );

    function setText(id, value) {
        const element =
            document.getElementById(id);

        if (element) {
            element.textContent =
                String(value);
        }
    }

    function updateOverview(records) {
        const ordered =
            sortRecordsAscending(
                records
            );

        const count =
            ordered.length;

        setText(
            "stat-count",
            count
        );

        setText(
            "snapshot-count",
            count
        );

        if (!count) {
            setText(
                "stat-latest",
                "--"
            );

            setText(
                "stat-previous",
                "--"
            );

            setText(
                "stat-lowest",
                "--"
            );

            setText(
                "stat-highest",
                "--"
            );

            setText(
                "snapshot-bmi",
                "--"
            );

            setText(
                "snapshot-weight",
                "--"
            );

            setText(
                "snapshot-category",
                "--"
            );

            setText(
                "latest-status",
                "No saved reading yet"
            );

            setText(
                "bmi-change-label",
                "No comparison available"
            );

            return;
        }

        const latest =
            ordered[count - 1];

        const previous =
            count >= 2
                ? ordered[count - 2]
                : null;

        const values =
            ordered.map(
                (record) =>
                    Number(record.bmi)
            );

        const latestBMI =
            Number(latest.bmi);

        const previousBMI =
            previous
                ? Number(previous.bmi)
                : null;

        const lowest =
            Math.min(...values);

        const highest =
            Math.max(...values);

        setText(
            "stat-latest",
            latestBMI.toFixed(2)
        );

        setText(
            "stat-previous",
            previousBMI !== null
                ? previousBMI.toFixed(2)
                : "--"
        );

        setText(
            "stat-lowest",
            lowest.toFixed(2)
        );

        setText(
            "stat-highest",
            highest.toFixed(2)
        );

        setText(
            "snapshot-bmi",
            latestBMI.toFixed(2)
        );

        setText(
            "snapshot-weight",
            `${Number(
                latest.weight
            ).toFixed(1)} kg`
        );

        setText(
            "snapshot-count",
            count
        );

        const snapshotCategory =
            document.getElementById(
                "snapshot-category"
            );

        if (snapshotCategory) {
            snapshotCategory.textContent =
                latest.category || "--";

            snapshotCategory.className =
                `snapshot-category ${categoryClass(
                    latest.category
                )}`;
        }

        setText(
            "latest-status",
            `Latest recorded on ${formatLongDate(
                latest.created_at
            )}`
        );

        if (previousBMI === null) {
            setText(
                "bmi-change-label",
                "Add another reading to compare"
            );
        } else {
            const delta =
                latestBMI -
                previousBMI;

            const sign =
                delta > 0
                    ? "+"
                    : "";

            const direction =
                delta > 0
                    ? "↑"
                    : delta < 0
                    ? "↓"
                    : "→";

            setText(
                "bmi-change-label",
                `${direction} ${sign}${delta.toFixed(2)} vs previous`
            );
        }
    }

    function updateEmptyStates(
        records
    ) {
        const bmiEmpty =
            document.getElementById(
                "bmi-empty-state"
            );

        const weightEmpty =
            document.getElementById(
                "weight-empty-state"
            );

        /*
         * No dots are used.
         * One measurement has no line trend,
         * so the friendly empty state is shown.
         */
        const showEmpty =
            records.length < 2;

        if (bmiEmpty) {
            bmiEmpty.classList.toggle(
                "hidden",
                !showEmpty
            );
        }

        if (weightEmpty) {
            weightEmpty.classList.toggle(
                "hidden",
                !showEmpty
            );
        }
    }

    function redrawCharts() {
        const filteredRecords =
            getRangeRecords(
                allRecords,
                activeRange
            );

        updateEmptyStates(
            filteredRecords
        );

        createBMIGraph(
            filteredRecords
        );

        createWeightGraph(
            filteredRecords
        );
    }

    async function loadAnalytics() {
        if (!userSelect?.value) {
            return;
        }

        try {
            const [
                stats,
                records,
            ] = await Promise.all([
                fetchJSON(
                    `/api/stats/${userSelect.value}`
                ),

                fetchJSON(
                    `/api/records/${userSelect.value}`
                ),
            ]);

            allRecords =
                sortRecordsAscending(
                    records || []
                );

            updateOverview(
                allRecords
            );

            /*
             * Only overwrite with API stats when
             * the values actually exist.
             */
            if (
                stats &&
                stats.latest !== null &&
                stats.latest !== undefined &&
                Number.isFinite(
                    Number(stats.latest)
                )
            ) {
                setText(
                    "stat-latest",
                    Number(
                        stats.latest
                    ).toFixed(2)
                );
            }

            if (
                stats &&
                stats.previous !== null &&
                stats.previous !== undefined &&
                Number.isFinite(
                    Number(stats.previous)
                )
            ) {
                setText(
                    "stat-previous",
                    Number(
                        stats.previous
                    ).toFixed(2)
                );
            }

            if (
                stats &&
                stats.lowest !== null &&
                stats.lowest !== undefined &&
                Number.isFinite(
                    Number(stats.lowest)
                )
            ) {
                setText(
                    "stat-lowest",
                    Number(
                        stats.lowest
                    ).toFixed(2)
                );
            }

            if (
                stats &&
                stats.highest !== null &&
                stats.highest !== undefined &&
                Number.isFinite(
                    Number(stats.highest)
                )
            ) {
                setText(
                    "stat-highest",
                    Number(
                        stats.highest
                    ).toFixed(2)
                );
            }

            if (
                stats &&
                Number.isFinite(
                    Number(stats.count)
                )
            ) {
                setText(
                    "stat-count",
                    Number(stats.count)
                );

                setText(
                    "snapshot-count",
                    Number(stats.count)
                );
            }

            redrawCharts();

        } catch (error) {
            showToast(
                error.message,
                true
            );
        }
    }

    window.refreshAnalytics =
        loadAnalytics;

    loadAnalytics();
}

/* ============================================================
   Chart option builders
   ============================================================ */

function buildTrendChartOptions(
    unitLabel
) {
    return {
        responsive: true,
        maintainAspectRatio: false,

        interaction: {
            mode: "index",
            intersect: false,
        },

        /*
         * Global no-dot / straight-line settings.
         */
        elements: {
            line: {
                tension: 0,
            },

            point: {
                radius: 0,
                hoverRadius: 0,
                hitRadius: 12,
            },
        },

        plugins: {
            legend: {
                display: false,
            },

            tooltip: {
                displayColors: false,
                backgroundColor: "#17213F",
                titleColor: "#FFFFFF",
                bodyColor: "#DDE4F5",
                padding: 11,
                cornerRadius: 10,

                callbacks: {
                    title(items) {
                        return items?.[0]?.label || "";
                    },

                    label(context) {
                        const value =
                            Number(
                                context.raw
                            );

                        if (
                            !Number.isFinite(
                                value
                            )
                        ) {
                            return `${unitLabel}: --`;
                        }

                        return (
                            unitLabel === "Weight"
                                ? `Weight: ${value.toFixed(2)} kg`
                                : `BMI: ${value.toFixed(2)}`
                        );
                    },
                },
            },
        },

        scales: {
            x: {
                border: {
                    display: false,
                },

                grid: {
                    display: false,
                },

                ticks: {
                    color: "#969FB9",
                    maxRotation: 0,
                    autoSkip: true,
                    autoSkipPadding: 24,

                    font: {
                        family:
                            "Inter, Segoe UI, Arial, sans-serif",
                        size: 10,
                        weight: "600",
                    },
                },
            },

            y: {
                border: {
                    display: false,
                },

                grid: {
                    color: "#EEF1F6",
                    drawTicks: false,
                },

                ticks: {
                    color: "#969FB9",
                    padding: 9,

                    font: {
                        family:
                            "Inter, Segoe UI, Arial, sans-serif",
                        size: 10,
                        weight: "600",
                    },
                },
            },
        },
    };
}

/* ============================================================
   BMI graph
   ============================================================ */

function createBMIGraph(
    records
) {
    const canvas =
        document.getElementById(
            "bmi-chart"
        );

    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }

    destroyChart(canvas);

    /*
     * Do NOT turn one reading into a dot.
     * The user requested trend structure,
     * so a minimum of two readings is required.
     */
    if (
        !records ||
        records.length < 2
    ) {
        return;
    }

    const labels =
        records.map(
            (record) =>
                formatShortDate(
                    record.created_at
                )
        );

    const values =
        records.map(
            (record) =>
                Number(record.bmi)
        );

    const minimum =
        Math.min(...values);

    const maximum =
        Math.max(...values);

    const lowerBound =
        Math.max(
            0,
            Math.floor(
                Math.min(
                    minimum - 2,
                    15
                )
            )
        );

    const upperBound =
        Math.max(
            32,
            Math.ceil(
                maximum + 3
            )
        );

    const context =
        canvas.getContext(
            "2d"
        );

    const gradient =
        context.createLinearGradient(
            0,
            0,
            0,
            canvas.height || 350
        );

    gradient.addColorStop(
        0,
        "rgba(84,104,255,0.24)"
    );

    gradient.addColorStop(
        0.6,
        "rgba(84,104,255,0.08)"
    );

    gradient.addColorStop(
        1,
        "rgba(84,104,255,0)"
    );

    const options =
        buildTrendChartOptions(
            "BMI"
        );

    options.scales.y.suggestedMin =
        lowerBound;

    options.scales.y.suggestedMax =
        upperBound;

    const chart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels,

                    datasets: [
                        {
                            label: "BMI",
                            data: values,

                            borderColor:
                                "#5468FF",

                            backgroundColor:
                                gradient,

                            fill: true,

                            borderWidth: 3,

                            /*
                             * STRAIGHT LINES.
                             * No smooth curves.
                             */
                            tension: 0,

                            cubicInterpolationMode:
                                "default",

                            /*
                             * NO DOTS.
                             */
                            pointRadius: 0,

                            pointHoverRadius: 0,

                            pointHitRadius: 12,

                            spanGaps: true,
                        },
                    ],
                },

                options,
            }
        );

    canvas._bmiInsightChart =
        chart;
}

/* ============================================================
   Weight graph
   ============================================================ */

function createWeightGraph(
    records
) {
    const canvas =
        document.getElementById(
            "weight-chart"
        );

    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }

    destroyChart(canvas);

    if (
        !records ||
        records.length < 2
    ) {
        return;
    }

    const labels =
        records.map(
            (record) =>
                formatShortDate(
                    record.created_at
                )
        );

    const values =
        records.map(
            (record) =>
                Number(record.weight)
        );

    const minimum =
        Math.min(...values);

    const maximum =
        Math.max(...values);

    const lowerBound =
        Math.max(
            0,
            Math.floor(
                minimum - 3
            )
        );

    const upperBound =
        Math.ceil(
            maximum + 3
        );

    const context =
        canvas.getContext(
            "2d"
        );

    const gradient =
        context.createLinearGradient(
            0,
            0,
            0,
            canvas.height || 300
        );

    gradient.addColorStop(
        0,
        "rgba(240,178,60,0.24)"
    );

    gradient.addColorStop(
        0.6,
        "rgba(240,178,60,0.08)"
    );

    gradient.addColorStop(
        1,
        "rgba(240,178,60,0)"
    );

    const options =
        buildTrendChartOptions(
            "Weight"
        );

    options.scales.y.suggestedMin =
        lowerBound;

    options.scales.y.suggestedMax =
        upperBound;

    const chart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels,

                    datasets: [
                        {
                            label:
                                "Weight",

                            data:
                                values,

                            borderColor:
                                "#F0B23C",

                            backgroundColor:
                                gradient,

                            fill:
                                true,

                            borderWidth:
                                3,

                            /*
                             * STRAIGHT /
                             * ANGULAR TREND.
                             */
                            tension: 0,

                            cubicInterpolationMode:
                                "default",

                            /*
                             * NO DOTS.
                             */
                            pointRadius:
                                0,

                            pointHoverRadius:
                                0,

                            pointHitRadius:
                                12,

                            spanGaps:
                                true,
                        },
                    ],
                },

                options,
            }
        );

    canvas._bmiInsightChart =
        chart;
}

/* ============================================================
   Date helpers
   ============================================================ */

function parseRecordDate(
    value
) {
    if (!value) {
        return null;
    }

    const raw =
        String(value).trim();

    /*
     * Try normal browser parser.
     */
    let date =
        new Date(raw);

    if (
        !Number.isNaN(
            date.getTime()
        )
    ) {
        return date;
    }

    /*
     * Handle database strings
     * containing commas.
     */
    date =
        new Date(
            raw.replace(
                ",",
                ""
            )
        );

    if (
        !Number.isNaN(
            date.getTime()
        )
    ) {
        return date;
    }

    /*
     * Handle YYYY-MM-DD manually.
     */
    const match =
        raw.match(
            /^(\d{4})-(\d{2})-(\d{2})/
        );

    if (match) {
        const year =
            Number(match[1]);

        const month =
            Number(match[2]) - 1;

        const day =
            Number(match[3]);

        date =
            new Date(
                year,
                month,
                day
            );

        if (
            !Number.isNaN(
                date.getTime()
            )
        ) {
            return date;
        }
    }

    return null;
}

function formatShortDate(
    value
) {
    const date =
        parseRecordDate(
            value
        );

    if (!date) {
        return String(
            value || ""
        )
            .split(",")[0]
            .trim();
    }

    return date.toLocaleDateString(
        "en-US",
        {
            month: "short",
            day: "numeric",
        }
    );
}

function formatLongDate(
    value
) {
    const date =
        parseRecordDate(
            value
        );

    if (!date) {
        return String(
            value || ""
        )
            .replace(
                ",",
                ""
            )
            .trim();
    }

    return date.toLocaleDateString(
        "en-US",
        {
            month: "short",
            day: "numeric",
            year: "numeric",
        }
    );
}

function sortRecordsAscending(
    records
) {
    return [
        ...(records || [])
    ].sort(
        (a, b) => {

            const dateA =
                parseRecordDate(
                    a.created_at
                );

            const dateB =
                parseRecordDate(
                    b.created_at
                );

            if (
                !dateA &&
                !dateB
            ) {
                return 0;
            }

            if (!dateA) {
                return -1;
            }

            if (!dateB) {
                return 1;
            }

            return (
                dateA.getTime() -
                dateB.getTime()
            );
        }
    );
}

function getRangeRecords(
    records,
    range
) {
    const ordered =
        sortRecordsAscending(
            records
        );

    if (
        range === "all" ||
        !range ||
        ordered.length === 0
    ) {
        return ordered;
    }

    const latest =
        parseRecordDate(
            ordered[
                ordered.length - 1
            ].created_at
        );

    if (!latest) {
        return ordered;
    }

    const days =
        Number(range);

    if (
        !Number.isFinite(
            days
        )
    ) {
        return ordered;
    }

    const cutoff =
        new Date(
            latest.getTime()
        );

    cutoff.setDate(
        cutoff.getDate() -
        days
    );

    return ordered.filter(
        (record) => {

            const date =
                parseRecordDate(
                    record.created_at
                );

            return (
                date &&
                date >= cutoff
            );
        }
    );
}

/* ============================================================
   Chart cleanup
   ============================================================ */

function destroyChart(
    canvas
) {
    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }

    if (
        canvas._bmiInsightChart
    ) {
        try {
            canvas._bmiInsightChart.destroy();
        } catch (error) {
            console.warn(
                "Unable to destroy BMI Insight chart:",
                error
            );
        }

        canvas._bmiInsightChart =
            null;
    }

    /*
     * Also detect charts created
     * by another script.
     */
    if (
        typeof Chart.getChart ===
        "function"
    ) {
        const existingChart =
            Chart.getChart(
                canvas
            );

        if (existingChart) {
            try {
                existingChart.destroy();
            } catch (error) {
                console.warn(
                    "Unable to destroy existing Chart.js instance:",
                    error
                );
            }
        }
    }
}

/* ============================================================
   HTML safety
   ============================================================ */

function escapeHTML(
    value
) {
    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}

/* ============================================================
   Page startup
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {
        initDashboard();
        initHistory();
        initAnalytics();
    }
);