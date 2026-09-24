/* ============================================================
   BMI INSIGHT
   Main frontend application logic
   ============================================================ */

const STORAGE_KEY = "bmiInsightSelectedUser";


/* ============================================================
   Global User Data
   ============================================================ */

const usersDataElement = document.getElementById("bmi-users-data");

try {
    window.BMI_USERS = usersDataElement
        ? JSON.parse(usersDataElement.textContent || "[]")
        : [];
} catch (error) {
    console.error("Unable to parse user data:", error);
    window.BMI_USERS = [];
}


/* ============================================================
   Local Storage
   ============================================================ */

function getSelectedUserId() {
    return localStorage.getItem(STORAGE_KEY) || "";
}


function setSelectedUserId(id) {
    if (id === null || id === undefined || id === "") {
        localStorage.removeItem(STORAGE_KEY);
        return;
    }

    localStorage.setItem(STORAGE_KEY, String(id));
}


/* ============================================================
   API Helper
   ============================================================ */

async function fetchJSON(url, options = {}) {
    let response;

    try {
        response = await fetch(url, options);
    } catch (error) {
        throw new Error(
            "Unable to connect to the server. Please try again."
        );
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
   Toast Notifications
   ============================================================ */

function showToast(message, isError = false) {
    const container = document.getElementById("toast-container");

    if (!container) {
        return;
    }

    const toast = document.createElement("div");

    toast.className =
        "toast" +
        (isError ? " toast-error" : "");

    toast.textContent = message;

    container.appendChild(toast);

    window.setTimeout(() => {
        toast.remove();
    }, 3200);
}


/* ============================================================
   BMI Categories
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
   User Selector
   ============================================================ */

function populateUserSelect(select, users, selectedId) {
    if (!select) {
        return;
    }

    select.innerHTML = "";

    if (!users || users.length === 0) {
        const option = document.createElement("option");

        option.value = "";
        option.textContent = "No users yet";

        select.appendChild(option);

        setSelectedUserId("");

        return;
    }

    users.forEach((user) => {
        const option = document.createElement("option");

        option.value = user.id;
        option.textContent = user.name;

        select.appendChild(option);
    });

    const matchingUser = users.find(
        (user) => String(user.id) === String(selectedId)
    );

    select.value = matchingUser
        ? String(matchingUser.id)
        : String(users[0].id);

    setSelectedUserId(select.value);

    updateAvatar();
}


function updateAvatar() {
    const select = document.getElementById("user-select");
    const avatar = document.querySelector(".mini-avatar");

    if (!select || !avatar) {
        return;
    }

    const user = (window.BMI_USERS || []).find(
        (item) => String(item.id) === String(select.value)
    );

    avatar.textContent =
        user?.name?.trim()?.charAt(0)?.toUpperCase() || "S";
}


function initUserSelect(onChange) {
    const select = document.getElementById("user-select");

    if (!select) {
        return null;
    }

    const users = Array.isArray(window.BMI_USERS)
        ? window.BMI_USERS
        : [];

    populateUserSelect(
        select,
        users,
        getSelectedUserId()
    );

    select.addEventListener("change", () => {
        setSelectedUserId(select.value);

        updateAvatar();

        if (typeof onChange === "function") {
            onChange(select.value);
        }
    });


    const addUserButton =
        document.getElementById("add-user-btn");

    if (addUserButton) {

        addUserButton.addEventListener(
            "click",
            async () => {

                const enteredName =
                    window.prompt(
                        "Enter a name for the new user:"
                    );

                if (!enteredName || !enteredName.trim()) {
                    return;
                }

                const name = enteredName.trim();

                try {

                    const user = await fetchJSON(
                        "/api/users",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                                name,
                            }),
                        }
                    );


                    if (!Array.isArray(window.BMI_USERS)) {
                        window.BMI_USERS = [];
                    }


                    const existingUser =
                        window.BMI_USERS.find(
                            (item) =>
                                String(item.id) ===
                                String(user.id)
                        );


                    if (!existingUser) {
                        window.BMI_USERS.push(user);
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

                    showToast(
                        error.message,
                        true
                    );

                }

            }
        );

    }

    return select;
}


/* ============================================================
   BMI Ring
   ============================================================ */

function setRing(bmi, category) {
    const ring = document.getElementById("bmi-ring");

    if (!ring) {
        return;
    }

    const numericBMI = Number(bmi);

    const position = Math.max(
        0,
        Math.min(
            (numericBMI - 15) / 25,
            1
        )
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

    const calculateButton =
        document.getElementById("calculate-btn");

    if (!calculateButton) {
        return;
    }


    const resetButton =
        document.getElementById("reset-btn");

    const weightInput =
        document.getElementById("weight-input");

    const heightInput =
        document.getElementById("height-input");

    const formError =
        document.getElementById("form-error");

    const resultValue =
        document.getElementById("result-value");

    const resultBadge =
        document.getElementById("result-badge");

    const resultPlaceholder =
        document.getElementById("result-placeholder");

    const scaleMarker =
        document.getElementById("scale-marker");

    const recentRecords =
        document.getElementById("recent-records");

    const resultWeight =
        document.getElementById("result-weight");

    const resultHeight =
        document.getElementById("result-height");

    const resultState =
        document.getElementById("result-state");


    const userSelect =
        initUserSelect(loadRecentRecords);


    async function loadRecentRecords() {

        if (!userSelect?.value) {
            return;
        }

        try {

            const records =
                await fetchJSON(
                    `/api/records/${userSelect.value}`
                );

            renderRecentRecords(
                records.slice(0, 5)
            );

            drawDashboardTrend(records);

        } catch (error) {

            showToast(
                error.message,
                true
            );

        }
    }


    function renderRecentRecords(records) {

        if (!recentRecords) {
            return;
        }


        if (!records.length) {

            recentRecords.innerHTML =
                `<div class="empty-state">
                    No records yet. Calculate your first BMI reading.
                </div>`;

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


    calculateButton.addEventListener(
        "click",
        async () => {

            if (formError) {
                formError.textContent = "";
            }


            if (!userSelect?.value) {

                if (formError) {
                    formError.textContent =
                        "Please select or add a user first.";
                }

                return;
            }


            calculateButton.disabled = true;
            calculateButton.textContent =
                "Calculating...";


            try {

                const result =
                    await fetchJSON(
                        "/api/calculate",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json",
                            },
                            body: JSON.stringify({
                                user_id:
                                    userSelect.value,
                                weight:
                                    weightInput?.value || "",
                                height:
                                    heightInput?.value || "",
                            }),
                        }
                    );


                if (resultValue) {
                    resultValue.textContent =
                        Number(result.bmi).toFixed(2);
                }


                if (resultBadge) {

                    resultBadge.style.display =
                        "inline-flex";

                    resultBadge.textContent =
                        result.category;

                    resultBadge.className =
                        `category-badge ${categoryClass(
                            result.category
                        )}`;
                }


                if (resultPlaceholder) {

                    resultPlaceholder.textContent =
                        `Your BMI is ${Number(
                            result.bmi
                        ).toFixed(2)} and is classified as ${
                            result.category
                        }.`;
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
                    resultState.textContent =
                        "Updated";
                }


                if (scaleMarker) {

                    const position =
                        Math.max(
                            0,
                            Math.min(
                                Number(result.scale_position),
                                1
                            )
                        );

                    scaleMarker.style.display =
                        "block";

                    scaleMarker.style.left =
                        `${position * 100}%`;
                }


                setRing(
                    result.bmi,
                    result.category
                );


                showToast(
                    "BMI calculated and saved"
                );


                await loadRecentRecords();


                // Refresh analytics if the page
                // happens to contain it.
                if (
                    typeof window.refreshAnalytics ===
                    "function"
                ) {
                    await window.refreshAnalytics();
                }

            } catch (error) {

                if (formError) {
                    formError.textContent =
                        error.message;
                }

            } finally {

                calculateButton.disabled = false;
                calculateButton.textContent =
                    "Calculate BMI";
            }

        }
    );


    if (resetButton) {

        resetButton.addEventListener(
            "click",
            () => {

                if (weightInput) {
                    weightInput.value = "";
                }

                if (heightInput) {
                    heightInput.value = "";
                }

                if (formError) {
                    formError.textContent = "";
                }

                if (resultValue) {
                    resultValue.textContent = "--";
                }

                if (resultBadge) {
                    resultBadge.style.display = "none";
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

                setRing(15, "Normal");
            }
        );

    }


    loadRecentRecords();
}


/* ============================================================
   Dashboard BMI Trend
   ============================================================ */

function drawDashboardTrend(records) {

    const canvas =
        document.getElementById(
            "dashboard-bmi-chart"
        );

    if (!canvas || typeof Chart === "undefined") {
        return;
    }


    destroyChart(canvas);


    const ordered =
        sortRecordsAscending(records);


    if (!ordered.length) {
        return;
    }


    const labels =
        ordered.map((record) =>
            formatShortDate(
                record.created_at
            )
        );


    const values =
        ordered.map((record) =>
            Number(record.bmi)
        );


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
                                "rgba(84, 104, 255, 0.10)",

                            fill: true,

                            tension: 0.4,

                            pointRadius:
                                ordered.length === 1
                                    ? 6
                                    : 3.5,

                            pointHoverRadius: 7,

                            pointBackgroundColor:
                                "#FFFFFF",

                            pointBorderColor:
                                "#5468FF",

                            pointBorderWidth: 3,

                            borderWidth: 2.5,
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

                    plugins: {
                        legend: {
                            display: false,
                        },

                        tooltip: {
                            displayColors: false,

                            backgroundColor:
                                "#17213F",

                            titleColor:
                                "#FFFFFF",

                            bodyColor:
                                "#DDE4F5",

                            padding: 11,

                            callbacks: {
                                label(context) {

                                    return `BMI: ${Number(
                                        context.raw
                                    ).toFixed(2)}`;
                                },
                            },
                        },
                    },

                    scales: {
                        x: {
                            grid: {
                                display: false,
                            },

                            ticks: {
                                color: "#8E97B2",

                                font: {
                                    size: 9,
                                    weight: "600",
                                },

                                maxRotation: 0,
                            },
                        },

                        y: {
                            grid: {
                                color:
                                    "rgba(23, 33, 63, 0.07)",
                            },

                            ticks: {
                                color: "#8E97B2",

                                font: {
                                    size: 9,
                                    weight: "600",
                                },
                            },
                        },
                    },
                },
            }
        );


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


            renderHistoryTable(
                allRecords
            );

        } catch (error) {

            showToast(
                error.message,
                true
            );
        }
    }


    function renderHistoryTable(records) {

        if (!records.length) {

            tableWrap.innerHTML =
                `<div class="empty-state">
                    No records found for this profile.
                </div>`;

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

                        const confirmed =
                            window.confirm(
                                "Delete this BMI record? This cannot be undone."
                            );

                        if (!confirmed) {
                            return;
                        }


                        try {

                            await fetchJSON(
                                `/api/records/${button.dataset.id}`,
                                {
                                    method:
                                        "DELETE",
                                }
                            );


                            showToast(
                                "Record deleted"
                            );


                            await loadHistory();

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


    if (searchInput) {

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
                                record.category
                            )
                                .toLowerCase()
                                .includes(term) ||

                            String(
                                record.created_at
                            )
                                .toLowerCase()
                                .includes(term)
                    );


                renderHistoryTable(
                    filtered
                );

            }
        );

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

    let selectedRange = "all";


    const emptyBMI =
        document.getElementById(
            "bmi-empty-state"
        );


    const emptyWeight =
        document.getElementById(
            "weight-empty-state"
        );


    const chartRangeButtons =
        document.querySelectorAll(
            ".range-btn"
        );


    /*
     * Premium Analytics elements.
     * The code also supports the older analytics
     * elements where present.
     */

    const latestStatus =
        document.getElementById(
            "latest-status"
        );


    const changeLabel =
        document.getElementById(
            "bmi-change-label"
        );


    const snapshotBMI =
        document.getElementById(
            "snapshot-bmi"
        );


    const snapshotWeight =
        document.getElementById(
            "snapshot-weight"
        );


    const snapshotCategory =
        document.getElementById(
            "snapshot-category"
        );


    const snapshotCount =
        document.getElementById(
            "snapshot-count"
        );


    const averageBMI =
        document.getElementById(
            "average-bmi"
        );


    const averageWeight =
        document.getElementById(
            "average-weight"
        );


    const trendText =
        document.getElementById(
            "trend-text"
        );


    const trendDetail =
        document.getElementById(
            "trend-detail"
        );


    function loadChartRecords() {

        return getRangeRecords(
            allRecords,
            selectedRange
        );
    }


    function updateEmptyStates(
        records
    ) {

        const hasRecords =
            records.length > 0;


        if (emptyBMI) {

            emptyBMI.classList.toggle(
                "hidden",
                hasRecords
            );
        }


        if (emptyWeight) {

            emptyWeight.classList.toggle(
                "hidden",
                hasRecords
            );
        }

    }


    function calculateAverage(values) {

        if (!values.length) {
            return null;
        }

        return (
            values.reduce(
                (total, value) =>
                    total + Number(value),
                0
            ) / values.length
        );
    }


    function updateAnalyticsSummary(
        records
    ) {

        if (!records.length) {

            if (averageBMI) {
                averageBMI.textContent =
                    "--";
            }

            if (averageWeight) {
                averageWeight.textContent =
                    "--";
            }

            if (trendText) {
                trendText.textContent =
                    "No measurements yet.";
            }

            if (trendDetail) {
                trendDetail.textContent =
                    "Add a measurement to start your personal trend.";
            }

            if (snapshotBMI) {
                snapshotBMI.textContent =
                    "--";
            }

            if (snapshotWeight) {
                snapshotWeight.textContent =
                    "--";
            }

            if (snapshotCategory) {
                snapshotCategory.textContent =
                    "--";

                snapshotCategory.className =
                    "snapshot-category";
            }

            if (snapshotCount) {
                snapshotCount.textContent =
                    "0";
            }

            if (latestStatus) {
                latestStatus.textContent =
                    "No recorded measurements";
            }

            if (changeLabel) {
                changeLabel.textContent =
                    "Compare with previous";
            }

            return;
        }


        const ordered =
            sortRecordsAscending(records);


        const latest =
            ordered[ordered.length - 1];


        const previous =
            ordered.length > 1
                ? ordered[ordered.length - 2]
                : null;


        const bmiValues =
            ordered.map(
                (record) =>
                    Number(record.bmi)
            );


        const weightValues =
            ordered.map(
                (record) =>
                    Number(record.weight)
            );


        const avgBMI =
            calculateAverage(
                bmiValues
            );


        const avgWeight =
            calculateAverage(
                weightValues
            );


        if (averageBMI) {

            averageBMI.textContent =
                avgBMI !== null
                    ? avgBMI.toFixed(2)
                    : "--";
        }


        if (averageWeight) {

            averageWeight.textContent =
                avgWeight !== null
                    ? `${avgWeight.toFixed(1)} kg`
                    : "--";
        }


        /*
         * Current BMI
         */

        if (snapshotBMI) {

            snapshotBMI.textContent =
                Number(latest.bmi)
                    .toFixed(2);
        }


        /*
         * Current weight
         */

        if (snapshotWeight) {

            snapshotWeight.textContent =
                `${Number(latest.weight).toFixed(1)} kg`;
        }


        /*
         * Current category
         */

        if (snapshotCategory) {

            snapshotCategory.textContent =
                latest.category ||
                "--";


            snapshotCategory.className =
                `snapshot-category ${categoryClass(
                    latest.category
                )}`;
        }


        /*
         * Number of readings
         */

        if (snapshotCount) {

            snapshotCount.textContent =
                allRecords.length;
        }


        /*
         * Latest status
         */

        if (latestStatus) {

            latestStatus.textContent =
                latest.category
                    ? `Latest reading · ${latest.category}`
                    : "Latest recorded value";
        }


        /*
         * Change from previous reading
         */

        if (changeLabel) {

            if (!previous) {

                changeLabel.textContent =
                    "First recorded measurement";

            } else {

                const difference =
                    Number(latest.bmi) -
                    Number(previous.bmi);


                if (Math.abs(difference) < 0.005) {

                    changeLabel.textContent =
                        "No change from previous";

                } else {

                    changeLabel.textContent =
                        difference > 0
                            ? `↑ ${Math.abs(difference).toFixed(2)} from previous`
                            : `↓ ${Math.abs(difference).toFixed(2)} from previous`;
                }
            }
        }


        /*
         * Older analytics summary elements
         */

        if (trendText) {

            if (ordered.length === 1) {

                trendText.textContent =
                    "One measurement recorded.";

            } else {

                const difference =
                    Number(latest.bmi) -
                    Number(ordered[0].bmi);


                if (Math.abs(difference) < 0.01) {

                    trendText.textContent =
                        "BMI is stable across your saved readings.";

                } else if (difference < 0) {

                    trendText.textContent =
                        "Your BMI has moved downward.";

                } else {

                    trendText.textContent =
                        "Your BMI has moved upward.";
                }
            }
        }


        if (trendDetail) {

            if (ordered.length === 1) {

                trendDetail.textContent =
                    "Add another measurement to compare your BMI over time.";

            } else {

                const difference =
                    Number(latest.bmi) -
                    Number(ordered[0].bmi);


                trendDetail.textContent =
                    `Change across saved readings: ${
                        difference > 0 ? "+" : ""
                    }${difference.toFixed(2)}.`;
            }
        }

    }


    function buildChartOptions(
        ySuggestedMin,
        ySuggestedMax
    ) {

        return {

            responsive: true,

            maintainAspectRatio: false,

            animation: {
                duration: 700,
                easing: "easeOutQuart",
            },

            interaction: {
                mode: "index",
                intersect: false,
            },

            plugins: {

                legend: {
                    display: false,
                },

                tooltip: {

                    backgroundColor:
                        "#17213F",

                    titleColor:
                        "#FFFFFF",

                    bodyColor:
                        "#DDE4F5",

                    borderColor:
                        "rgba(255,255,255,0.08)",

                    borderWidth: 1,

                    padding: 12,

                    displayColors: false,

                    titleFont: {
                        family:
                            "Inter, Segoe UI, Arial, sans-serif",
                        size: 11,
                        weight: "700",
                    },

                    bodyFont: {
                        family:
                            "Inter, Segoe UI, Arial, sans-serif",
                        size: 12,
                        weight: "600",
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

                        color:
                            "#969FB9",

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

                    suggestedMin:
                        ySuggestedMin,

                    suggestedMax:
                        ySuggestedMax,

                    grid: {

                        color:
                            "#EEF1F6",

                        drawTicks:
                            false,
                    },

                    ticks: {

                        color:
                            "#969FB9",

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


    function createBMIGraph(
        records
    ) {

        destroyChart(
            bmiCanvas
        );


        if (!records.length) {
            updateEmptyStates([]);
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


        const canvasContext =
            bmiCanvas.getContext(
                "2d"
            );


        const gradient =
            canvasContext.createLinearGradient(
                0,
                0,
                0,
                bmiCanvas.height || 350
            );


        gradient.addColorStop(
            0,
            "rgba(84,104,255,0.25)"
        );


        gradient.addColorStop(
            0.6,
            "rgba(84,104,255,0.08)"
        );


        gradient.addColorStop(
            1,
            "rgba(84,104,255,0)"
        );


        const chart =
            new Chart(
                bmiCanvas,
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

                                tension: 0.42,

                                cubicInterpolationMode:
                                    "monotone",

                                borderWidth: 3,

                                pointRadius:
                                    records.length === 1
                                        ? 7
                                        : 4,

                                pointHoverRadius:
                                    8,

                                pointBackgroundColor:
                                    "#FFFFFF",

                                pointBorderColor:
                                    "#5468FF",

                                pointBorderWidth: 3,

                                spanGaps: true,
                            },
                        ],
                    },

                    options:
                        buildChartOptions(
                            lowerBound,
                            upperBound
                        ),
                }
            );


        chart.options.plugins.tooltip.callbacks = {

            title(items) {

                const index =
                    items[0]?.dataIndex ??
                    0;

                return (
                    records[index]?.created_at ||
                    ""
                );
            },


            label(context) {

                const index =
                    context.dataIndex;

                const record =
                    records[index];


                return [
                    `BMI: ${Number(
                        record.bmi
                    ).toFixed(2)}`,

                    `Category: ${record.category}`,

                    `Weight: ${Number(
                        record.weight
                    ).toFixed(1)} kg`,
                ];
            },
        };


        bmiCanvas._bmiInsightChart =
            chart;
    }


    function createWeightGraph(
        records
    ) {

        if (!weightCanvas) {
            return;
        }


        destroyChart(
            weightCanvas
        );


        if (!records.length) {
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


        const spread =
            maximum - minimum;


        const padding =
            spread === 0
                ? 3
                : Math.max(
                    1.5,
                    spread * 0.25
                );


        const lowerBound =
            Math.max(
                0,
                Math.floor(
                    minimum - padding
                )
            );


        const upperBound =
            Math.ceil(
                maximum + padding
            );


        const canvasContext =
            weightCanvas.getContext(
                "2d"
            );


        const gradient =
            canvasContext.createLinearGradient(
                0,
                0,
                0,
                weightCanvas.height || 300
            );


        gradient.addColorStop(
            0,
            "rgba(227,165,44,0.24)"
        );


        gradient.addColorStop(
            0.6,
            "rgba(227,165,44,0.08)"
        );


        gradient.addColorStop(
            1,
            "rgba(227,165,44,0)"
        );


        const chart =
            new Chart(
                weightCanvas,
                {
                    type: "line",

                    data: {

                        labels,

                        datasets: [
                            {
                                label: "Weight",

                                data: values,

                                borderColor:
                                    "#E3A52C",

                                backgroundColor:
                                    gradient,

                                fill: true,

                                tension: 0.42,

                                cubicInterpolationMode:
                                    "monotone",

                                borderWidth: 3,

                                pointRadius:
                                    records.length === 1
                                        ? 7
                                        : 4,

                                pointHoverRadius:
                                    8,

                                pointBackgroundColor:
                                    "#FFFFFF",

                                pointBorderColor:
                                    "#E3A52C",

                                pointBorderWidth: 3,

                                spanGaps: true,
                            },
                        ],
                    },

                    options:
                        buildChartOptions(
                            lowerBound,
                            upperBound
                        ),
                }
            );


        chart.options.plugins.tooltip.callbacks = {

            title(items) {

                const index =
                    items[0]?.dataIndex ??
                    0;

                return (
                    records[index]?.created_at ||
                    ""
                );
            },


            label(context) {

                return `Weight: ${Number(
                    context.raw
                ).toFixed(1)} kg`;
            },
        };


        weightCanvas._bmiInsightChart =
            chart;
    }


    async function loadAnalytics() {

        if (!userSelect?.value) {
            return;
        }


        try {

            const [
                stats,
                records
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
                    records
                );


            /*
             * Statistics
             */

            const statLatest =
                document.getElementById(
                    "stat-latest"
                );


            const statPrevious =
                document.getElementById(
                    "stat-previous"
                );


            const statHighest =
                document.getElementById(
                    "stat-highest"
                );


            const statLowest =
                document.getElementById(
                    "stat-lowest"
                );


            const statCount =
                document.getElementById(
                    "stat-count"
                );


            if (statLatest) {

                statLatest.textContent =
                    stats.latest !== null
                        ? Number(
                            stats.latest
                        ).toFixed(2)
                        : "--";
            }


            if (statPrevious) {

                statPrevious.textContent =
                    stats.previous !== null
                        ? Number(
                            stats.previous
                        ).toFixed(2)
                        : "--";
            }


            if (statHighest) {

                statHighest.textContent =
                    stats.highest !== null
                        ? Number(
                            stats.highest
                        ).toFixed(2)
                        : "--";
            }


            if (statLowest) {

                statLowest.textContent =
                    stats.lowest !== null
                        ? Number(
                            stats.lowest
                        ).toFixed(2)
                        : "--";
            }


            if (statCount) {

                statCount.textContent =
                    stats.count ??
                    allRecords.length;
            }


            /*
             * Summary
             */

            updateAnalyticsSummary(
                allRecords
            );


            /*
             * Selected date range
             */

            const chartRecords =
                loadChartRecords();


            /*
             * Empty state
             */

            updateEmptyStates(
                chartRecords
            );


            /*
             * Graphs
             */

            createBMIGraph(
                chartRecords
            );


            createWeightGraph(
                chartRecords
            );

        } catch (error) {

            showToast(
                error.message,
                true
            );
        }
    }


    chartRangeButtons.forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    chartRangeButtons.forEach(
                        (item) =>
                            item.classList.remove(
                                "active"
                            )
                    );


                    button.classList.add(
                        "active"
                    );


                    selectedRange =
                        button.dataset.range ||
                        "all";


                    const chartRecords =
                        loadChartRecords();


                    updateEmptyStates(
                        chartRecords
                    );


                    createBMIGraph(
                        chartRecords
                    );


                    createWeightGraph(
                        chartRecords
                    );
                }
            );

        }
    );


    /*
     * Expose refresh function so the
     * Dashboard can refresh Analytics.
     */

    window.refreshAnalytics =
        loadAnalytics;


    /*
     * Initial load
     */

    loadAnalytics();
}


/* ============================================================
   Date Helpers
   ============================================================ */

function parseRecordDate(value) {

    if (!value) {
        return null;
    }


    const raw =
        String(value).trim();


    /*
     * Try the normal browser parser first.
     */

    let date =
        new Date(raw);


    if (!Number.isNaN(
        date.getTime()
    )) {
        return date;
    }


    /*
     * Handle database date strings
     * containing commas.
     */

    const normalized =
        raw.replace(
            ",",
            ""
        );


    date =
        new Date(
            normalized
        );


    if (!Number.isNaN(
        date.getTime()
    )) {
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


        if (!Number.isNaN(
            date.getTime()
        )) {
            return date;
        }
    }


    return null;
}


function formatShortDate(value) {

    const date =
        parseRecordDate(
            value
        );


    if (!date) {

        return String(value || "")
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


function sortRecordsAscending(
    records
) {

    return [...(records || [])].sort(
        (a, b) => {

            const dateA =
                parseRecordDate(
                    a.created_at
                );

            const dateB =
                parseRecordDate(
                    b.created_at
                );


            if (!dateA && !dateB) {
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


    const cutoff =
        new Date(
            latest.getTime()
        );


    cutoff.setDate(
        cutoff.getDate() -
        Number(range)
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
   Chart Cleanup
   ============================================================ */

function destroyChart(
    canvas
) {

    if (!canvas) {
        return;
    }


    /*
     * Remove any previous chart
     * created by this application.
     */

    if (canvas._bmiInsightChart) {

        try {
            canvas._bmiInsightChart.destroy();
        } catch (error) {
            console.warn(
                "Unable to destroy chart:",
                error
            );
        }

        canvas._bmiInsightChart =
            null;
    }


    /*
     * Also detect Chart.js charts
     * created by another script.
     */

    if (
        typeof Chart !== "undefined" &&
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
   HTML Safety
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
   Application Startup
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initDashboard();

        initHistory();

        initAnalytics();

    }
);
