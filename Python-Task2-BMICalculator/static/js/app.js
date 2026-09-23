// ============================================================================
// BMI INSIGHT
// Front-end application logic
// Dashboard • History • Analytics
// Developer: Kunchala Shailaja
// ============================================================================


/* ==========================================================================
   USER DATA
   ========================================================================== */

const STORAGE_KEY = "bmiInsightSelectedUser";

const usersDataElement = document.getElementById("bmi-users-data");

window.BMI_USERS = usersDataElement
    ? JSON.parse(usersDataElement.textContent || "[]")
    : [];


/* ==========================================================================
   GENERAL HELPERS
   ========================================================================== */

function getSelectedUserId() {
    return localStorage.getItem(STORAGE_KEY) || "";
}


function setSelectedUserId(id) {
    localStorage.setItem(STORAGE_KEY, String(id));
}


function showToast(message, isError = false) {
    const container = document.getElementById("toast-container");

    if (!container) {
        return;
    }

    const toast = document.createElement("div");

    toast.className =
        "toast" + (isError ? " toast-error" : "");

    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3500);
}


async function fetchJSON(url, options = {}) {
    const response = await fetch(url, options);

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.error || "Something went wrong"
        );
    }

    return data;
}


function categoryClass(category) {
    return {
        Underweight: "badge-underweight",
        Normal: "badge-normal",
        Overweight: "badge-overweight",
        Obese: "badge-obese"
    }[category] || "badge-normal";
}


function categoryColor(category) {
    return {
        Underweight: "#62a8eb",
        Normal: "#25b476",
        Overweight: "#e3a42e",
        Obese: "#df5d6c"
    }[category] || "#4e63e8";
}


function updateProfileAvatar() {
    const select = document.getElementById("user-select");
    const avatar = document.querySelector(".profile-avatar");

    if (!select || !avatar) {
        return;
    }

    const user = (window.BMI_USERS || []).find(
        (item) => String(item.id) === String(select.value)
    );

    if (!user) {
        avatar.textContent = "S";
        return;
    }

    const name = String(user.name || "").trim();

    avatar.textContent =
        name.charAt(0).toUpperCase() || "U";
}


/* ==========================================================================
   USER SELECTOR
   ========================================================================== */

function populateUserSelect(select, users, selectedId) {
    select.innerHTML = "";

    if (!users || users.length === 0) {
        const option = document.createElement("option");

        option.value = "";
        option.textContent = "No users yet";

        select.appendChild(option);

        updateProfileAvatar();

        return;
    }

    users.forEach((user) => {
        const option = document.createElement("option");

        option.value = user.id;
        option.textContent = user.name;

        select.appendChild(option);
    });

    const matchingUser = users.find(
        (user) =>
            String(user.id) === String(selectedId)
    );

    select.value = matchingUser
        ? matchingUser.id
        : users[0].id;

    setSelectedUserId(select.value);

    updateProfileAvatar();
}


function initUserSelect(onChange) {
    const select = document.getElementById("user-select");

    if (!select) {
        return null;
    }

    populateUserSelect(
        select,
        window.BMI_USERS || [],
        getSelectedUserId()
    );

    select.addEventListener("change", () => {
        setSelectedUserId(select.value);

        updateProfileAvatar();

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

                const name = prompt(
                    "Enter a name for the new user:"
                );

                if (!name || !name.trim()) {
                    return;
                }

                try {
                    const user = await fetchJSON(
                        "/api/users",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                name: name.trim()
                            })
                        }
                    );

                    if (!Array.isArray(window.BMI_USERS)) {
                        window.BMI_USERS = [];
                    }

                    const existingIndex =
                        window.BMI_USERS.findIndex(
                            (item) =>
                                String(item.id) ===
                                String(user.id)
                        );

                    if (existingIndex === -1) {
                        window.BMI_USERS.push(user);
                    }

                    populateUserSelect(
                        select,
                        window.BMI_USERS,
                        user.id
                    );

                    updateProfileAvatar();

                    showToast(
                        user.existing
                            ? `${user.name} already exists`
                            : `Added ${user.name}`
                    );

                    if (
                        typeof onChange ===
                        "function"
                    ) {
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

    updateProfileAvatar();

    return select;
}


/* ==========================================================================
   DASHBOARD
   ========================================================================== */

function initDashboard() {
    const calculateButton =
        document.getElementById(
            "calculate-btn"
        );

    if (!calculateButton) {
        return;
    }

    const resetButton =
        document.getElementById(
            "reset-btn"
        );

    const weightInput =
        document.getElementById(
            "weight-input"
        );

    const heightInput =
        document.getElementById(
            "height-input"
        );

    const errorText =
        document.getElementById(
            "form-error"
        );

    const resultValue =
        document.getElementById(
            "result-value"
        );

    const resultBadge =
        document.getElementById(
            "result-badge"
        );

    const resultPlaceholder =
        document.getElementById(
            "result-placeholder"
        );

    const resultStatus =
        document.getElementById(
            "result-status"
        );

    const resultWeight =
        document.getElementById(
            "result-weight"
        );

    const resultHeight =
        document.getElementById(
            "result-height"
        );

    const resultCategoryText =
        document.getElementById(
            "result-category-text"
        );

    const scaleMarker =
        document.getElementById(
            "scale-marker"
        );

    const bmiRing =
        document.getElementById(
            "bmi-ring"
        );

    const recentRecords =
        document.getElementById(
            "recent-records"
        );


    const userSelect =
        initUserSelect(
            () => loadRecentRecords()
        );


    async function loadRecentRecords() {
        if (!userSelect || !userSelect.value) {
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

        if (!records || records.length === 0) {
            recentRecords.innerHTML = `
                <div class="empty-state">
                    No records yet. Calculate your first BMI measurement.
                </div>
            `;

            return;
        }

        const rows = records
            .map((record) => {
                return `
                    <tr>
                        <td>${record.created_at}</td>
                        <td>${record.weight} kg</td>
                        <td>${record.height} m</td>
                        <td>${Number(record.bmi).toFixed(2)}</td>
                        <td>
                            <span class="category-badge ${categoryClass(record.category)}">
                                ${record.category}
                            </span>
                        </td>
                    </tr>
                `;
            })
            .join("");

        recentRecords.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Weight</th>
                        <th>Height</th>
                        <th>BMI</th>
                        <th>Category</th>
                    </tr>
                </thead>

                <tbody>
                    ${rows}
                </tbody>
            </table>
        `;
    }


    function resetResultVisuals() {

        if (resultValue) {
            resultValue.textContent = "--";
        }

        if (resultBadge) {
            resultBadge.style.display = "none";
        }

        if (resultPlaceholder) {
            resultPlaceholder.textContent =
                "Your BMI is calculated from your current weight and height.";
        }

        if (resultStatus) {
            resultStatus.textContent = "READY";
        }

        if (resultWeight) {
            resultWeight.textContent = "--";
        }

        if (resultHeight) {
            resultHeight.textContent = "--";
        }

        if (resultCategoryText) {
            resultCategoryText.textContent = "--";
        }

        if (scaleMarker) {
            scaleMarker.style.display = "none";
        }

        if (bmiRing) {
            bmiRing.style.setProperty(
                "--ring-angle",
                "0deg"
            );

            bmiRing.style.setProperty(
                "--ring-color",
                "#4e63e8"
            );
        }
    }


    calculateButton.addEventListener(
        "click",
        async () => {

            if (errorText) {
                errorText.textContent = "";
            }

            if (!userSelect || !userSelect.value) {

                if (errorText) {
                    errorText.textContent =
                        "Please add or select a user first.";
                }

                return;
            }


            calculateButton.disabled = true;
            calculateButton.innerHTML =
                `<span>Calculating...</span>`;


            try {

                const result =
                    await fetchJSON(
                        "/api/calculate",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                user_id:
                                    userSelect.value,

                                weight:
                                    weightInput.value,

                                height:
                                    heightInput.value
                            })
                        }
                    );


                const bmi =
                    Number(result.bmi);


                const position = Math.max(
                    0,
                    Math.min(
                        Number(result.scale_position),
                        1
                    )
                );


                /* ------------------------------------------------------
                   Main BMI result
                   ------------------------------------------------------ */

                if (resultValue) {
                    resultValue.textContent =
                        bmi.toFixed(2);
                }


                if (resultBadge) {

                    resultBadge.style.display =
                        "inline-flex";

                    resultBadge.textContent =
                        result.category;

                    resultBadge.className =
                        "category-badge " +
                        categoryClass(
                            result.category
                        );
                }


                if (resultPlaceholder) {

                    resultPlaceholder.textContent =
                        `Your BMI is ${bmi.toFixed(2)}, classified as ${result.category}.`;
                }


                if (resultStatus) {

                    resultStatus.textContent =
                        result.category.toUpperCase();
                }


                /* ------------------------------------------------------
                   Supporting result information
                   ------------------------------------------------------ */

                if (resultWeight) {

                    resultWeight.textContent =
                        `${Number(result.weight).toFixed(1)} kg`;
                }


                if (resultHeight) {

                    resultHeight.textContent =
                        `${Number(result.height).toFixed(2)} m`;
                }


                if (resultCategoryText) {

                    resultCategoryText.textContent =
                        result.category;
                }


                /* ------------------------------------------------------
                   BMI scale marker
                   ------------------------------------------------------ */

                if (scaleMarker) {

                    scaleMarker.style.display =
                        "block";

                    scaleMarker.style.left =
                        `${position * 100}%`;
                }


                /* ------------------------------------------------------
                   Premium BMI ring
                   ------------------------------------------------------ */

                if (bmiRing) {

                    bmiRing.style.setProperty(
                        "--ring-angle",
                        `${Math.max(
                            12,
                            position * 360
                        )}deg`
                    );

                    bmiRing.style.setProperty(
                        "--ring-color",
                        categoryColor(
                            result.category
                        )
                    );
                }


                showToast(
                    "BMI calculated and saved"
                );


                await loadRecentRecords();


            } catch (error) {

                if (errorText) {
                    errorText.textContent =
                        error.message;
                }

            } finally {

                calculateButton.disabled =
                    false;

                calculateButton.innerHTML =
                    `<span>Calculate BMI</span><span class="button-arrow">→</span>`;
            }
        }
    );


    if (resetButton) {

        resetButton.addEventListener(
            "click",
            () => {

                weightInput.value = "";
                heightInput.value = "";

                if (errorText) {
                    errorText.textContent = "";
                }

                resetResultVisuals();
            }
        );
    }


    loadRecentRecords();
}


/* ==========================================================================
   HISTORY PAGE
   ========================================================================== */

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


    let allRecords = [];


    const userSelect =
        initUserSelect(
            () => loadHistory()
        );


    async function loadHistory() {

        if (!userSelect ||
            !userSelect.value) {
            return;
        }


        try {

            allRecords =
                await fetchJSON(
                    `/api/records/${userSelect.value}`
                );


            renderTable(
                allRecords
            );

        } catch (error) {

            showToast(
                error.message,
                true
            );

        }
    }


    function renderTable(records) {

        if (!records ||
            records.length === 0) {

            tableWrap.innerHTML =
                `
                <div class="empty-state">
                    No records found for this profile.
                </div>
                `;

            return;
        }


        const rows =
            records
                .map((record) => {

                    return `
                        <tr data-record-id="${record.id}">

                            <td>
                                ${record.created_at}
                            </td>

                            <td>
                                ${record.weight} kg
                            </td>

                            <td>
                                ${record.height} m
                            </td>

                            <td>
                                ${Number(record.bmi).toFixed(2)}
                            </td>

                            <td>
                                <span class="category-badge ${categoryClass(record.category)}">
                                    ${record.category}
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
                    `;

                })
                .join("");


        tableWrap.innerHTML =
            `
            <table>

                <thead>

                    <tr>
                        <th>Date</th>
                        <th>Weight</th>
                        <th>Height</th>
                        <th>BMI</th>
                        <th>Category</th>
                        <th></th>
                    </tr>

                </thead>

                <tbody>
                    ${rows}
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
                            confirm(
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
                                        "DELETE"
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
                        (record) => {

                            return (
                                String(
                                    record.category
                                )
                                .toLowerCase()
                                .includes(term)

                                ||

                                String(
                                    record.created_at
                                )
                                .toLowerCase()
                                .includes(term)
                            );

                        }
                    );


                renderTable(
                    filtered
                );

            }
        );

    }


    loadHistory();
}


/* ==========================================================================
   ANALYTICS PAGE
   ========================================================================== */

function initAnalytics() {

    const bmiCanvas =
        document.getElementById(
            "bmi-chart"
        );


    if (!bmiCanvas) {
        return;
    }


    const weightCanvas =
        document.getElementById(
            "weight-chart"
        );


    let bmiChart = null;
    let weightChart = null;


    const userSelect =
        initUserSelect(
            () => loadAnalytics()
        );


    function formatDate(rawValue) {

        const raw =
            String(rawValue || "");


        const isoMatch =
            raw.match(
                /^(\d{4})-(\d{2})-(\d{2})/
            );


        if (isoMatch) {

            return `${isoMatch[3]} ${getMonthName(
                Number(isoMatch[2])
            )}`;

        }


        return raw.split(",")[0];
    }


    function getMonthName(month) {

        const months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec"
        ];


        return months[month - 1] || "";
    }


    function calculateAverage(values) {

        if (!values.length) {
            return null;
        }


        return values.reduce(
            (sum, value) =>
                sum + Number(value),
            0
        ) / values.length;
    }


    function updateAnalyticsStats(
        stats,
        records
    ) {

        const latest =
            document.getElementById(
                "stat-latest"
            );

        const previous =
            document.getElementById(
                "stat-previous"
            );

        const highest =
            document.getElementById(
                "stat-highest"
            );

        const lowest =
            document.getElementById(
                "stat-lowest"
            );

        const count =
            document.getElementById(
                "stat-count"
            );


        if (latest) {

            latest.textContent =
                stats.latest !== null
                    ? Number(
                        stats.latest
                    ).toFixed(2)
                    : "--";
        }


        if (previous) {

            previous.textContent =
                stats.previous !== null
                    ? Number(
                        stats.previous
                    ).toFixed(2)
                    : "--";
        }


        if (highest) {

            highest.textContent =
                stats.highest !== null
                    ? Number(
                        stats.highest
                    ).toFixed(2)
                    : "--";
        }


        if (lowest) {

            lowest.textContent =
                stats.lowest !== null
                    ? Number(
                        stats.lowest
                    ).toFixed(2)
                    : "--";
        }


        if (count) {

            count.textContent =
                stats.count ?? 0;
        }


        updateTrendSummary(
            records
        );
    }


    function updateTrendSummary(records) {

        const trendText =
            document.getElementById(
                "trend-text"
            );

        const trendDetail =
            document.getElementById(
                "trend-detail"
            );

        const averageBmi =
            document.getElementById(
                "average-bmi"
            );

        const averageWeight =
            document.getElementById(
                "average-weight"
            );


        if (!records ||
            records.length === 0) {

            if (trendText) {
                trendText.textContent =
                    "Build your history to see a trend.";
            }


            if (trendDetail) {
                trendDetail.textContent =
                    "Your BMI trend will be summarized from your saved measurements.";
            }


            if (averageBmi) {
                averageBmi.textContent =
                    "--";
            }


            if (averageWeight) {
                averageWeight.textContent =
                    "--";
            }


            return;
        }


        const ordered =
            [...records].reverse();


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


        const avgBmi =
            calculateAverage(
                bmiValues
            );


        const avgWeight =
            calculateAverage(
                weightValues
            );


        if (averageBmi !== null &&
            averageBmi) {

            averageBmi.textContent =
                avgBmi.toFixed(2);
        }


        if (averageWeight &&
            avgWeight !== null) {

            averageWeight.textContent =
                `${avgWeight.toFixed(1)} kg`;
        }


        if (bmiValues.length < 2) {

            if (trendText) {
                trendText.textContent =
                    "One measurement recorded.";
            }


            if (trendDetail) {
                trendDetail.textContent =
                    "Add another measurement to compare your BMI over time.";
            }


            return;
        }


        const first =
            bmiValues[0];


        const latest =
            bmiValues[
                bmiValues.length - 1
            ];


        const difference =
            latest - first;


        if (Math.abs(difference) < 0.01) {

            if (trendText) {
                trendText.textContent =
                    "BMI is stable across your saved readings.";
            }


            if (trendDetail) {
                trendDetail.textContent =
                    `Latest BMI: ${latest.toFixed(2)}.`;
            }


            return;
        }


        if (difference < 0) {

            if (trendText) {
                trendText.textContent =
                    "Your BMI has moved downward.";
            }


            if (trendDetail) {
                trendDetail.textContent =
                    `Change from first to latest reading: ${difference.toFixed(2)}.`;
            }


        } else {

            if (trendText) {
                trendText.textContent =
                    "Your BMI has moved upward.";
            }


            if (trendDetail) {
                trendDetail.textContent =
                    `Change from first to latest reading: +${difference.toFixed(2)}.`;
            }

        }

    }


    function commonChartOptions() {

        return {

            responsive: true,

            maintainAspectRatio: false,

            interaction: {
                mode: "index",
                intersect: false
            },

            plugins: {

                legend: {
                    display: false
                },

                tooltip: {

                    backgroundColor:
                        "#0d1726",

                    titleColor:
                        "#ffffff",

                    bodyColor:
                        "#dce5f3",

                    borderColor:
                        "rgba(255,255,255,.08)",

                    borderWidth: 1,

                    padding: 11,

                    cornerRadius: 10,

                    displayColors: false

                }

            },

            scales: {

                x: {

                    grid: {
                        display: false
                    },

                    ticks: {

                        color:
                            "#8490a3",

                        font: {
                            size: 9
                        },

                        maxRotation: 0,

                        autoSkip: true,

                        maxTicksLimit: 7

                    }

                },

                y: {

                    beginAtZero: false,

                    border: {
                        display: false
                    },

                    grid: {

                        color:
                            "rgba(30,48,76,.07)"
                    },

                    ticks: {

                        color:
                            "#8490a3",

                        font: {
                            size: 9
                        }

                    }

                }

            },

            elements: {

                line: {
                    tension: 0.35,
                    borderWidth: 2.5
                },

                point: {

                    radius: 4,

                    hoverRadius: 6,

                    borderWidth: 2

                }

            }

        };
    }


    const bmiReferencePlugin = {

        id: "bmiReferencePlugin",

        afterDraw(chart) {

            if (!chart.scales ||
                !chart.scales.y ||
                !chart.chartArea) {

                return;
            }


            const yScale =
                chart.scales.y;

            const area =
                chart.chartArea;


            const referenceValues = [
                18.5,
                24.9,
                29.9
            ];


            const ctx =
                chart.ctx;


            ctx.save();


            referenceValues.forEach(
                (value) => {

                    const y =
                        yScale.getPixelForValue(
                            value
                        );


                    if (
                        y < area.top ||
                        y > area.bottom
                    ) {
                        return;
                    }


                    ctx.beginPath();

                    ctx.moveTo(
                        area.left,
                        y
                    );

                    ctx.lineTo(
                        area.right,
                        y
                    );

                    ctx.setLineDash([
                        4,
                        5
                    ]);

                    ctx.strokeStyle =
                        "rgba(78,99,232,.12)";

                    ctx.lineWidth = 1;

                    ctx.stroke();

                }
            );


            ctx.restore();
        }

    };


    function showChartMessage(
        canvas,
        message
    ) {

        if (!canvas) {
            return;
        }


        const parent =
            canvas.parentElement;


        if (!parent) {
            return;
        }


        canvas.style.display =
            "none";


        let messageBox =
            parent.querySelector(
                ".chart-empty-message"
            );


        if (!messageBox) {

            messageBox =
                document.createElement(
                    "div"
                );

            messageBox.className =
                "chart-empty-message";

            messageBox.style.height =
                "100%";

            messageBox.style.display =
                "flex";

            messageBox.style.alignItems =
                "center";

            messageBox.style.justifyContent =
                "center";

            messageBox.style.color =
                "#98a2b0";

            messageBox.style.fontSize =
                "10px";

            parent.appendChild(
                messageBox
            );
        }


        messageBox.textContent =
            message;
    }


    function clearChartMessage(
        canvas
    ) {

        if (!canvas) {
            return;
        }


        const parent =
            canvas.parentElement;


        if (!parent) {
            return;
        }


        const messageBox =
            parent.querySelector(
                ".chart-empty-message"
            );


        if (messageBox) {
            messageBox.remove();
        }


        canvas.style.display =
            "block";
    }


    async function loadAnalytics() {

        if (!userSelect ||
            !userSelect.value) {

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
                )

            ]);


            updateAnalyticsStats(
                stats,
                records
            );


            const ordered =
                [...records].reverse();


            const labels =
                ordered.map(
                    (record) =>
                        formatDate(
                            record.created_at
                        )
                );


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


            if (bmiChart) {

                bmiChart.destroy();

                bmiChart = null;
            }


            if (weightChart) {

                weightChart.destroy();

                weightChart = null;
            }


            if (
                labels.length === 0 ||
                bmiValues.length === 0
            ) {

                showChartMessage(
                    bmiCanvas,
                    "No BMI history available yet."
                );


                showChartMessage(
                    weightCanvas,
                    "No weight history available yet."
                );


                return;
            }


            if (
                typeof Chart ===
                "undefined"
            ) {

                showToast(
                    "Chart.js could not be loaded.",
                    true
                );

                return;
            }


            clearChartMessage(
                bmiCanvas
            );


            clearChartMessage(
                weightCanvas
            );


            /* ----------------------------------------------------------
               BMI Chart
               ---------------------------------------------------------- */

            bmiChart =
                new Chart(
                    bmiCanvas,
                    {

                        type: "line",

                        data: {

                            labels,

                            datasets: [

                                {

                                    label:
                                        "BMI",

                                    data:
                                        bmiValues,

                                    borderColor:
                                        "#4e63e8",

                                    backgroundColor:
                                        "rgba(78,99,232,.09)",

                                    pointBackgroundColor:
                                        "#4e63e8",

                                    pointBorderColor:
                                        "#ffffff",

                                    pointHoverBackgroundColor:
                                        "#ffffff",

                                    pointHoverBorderColor:
                                        "#4e63e8",

                                    fill: true

                                }

                            ]

                        },

                        options:
                            commonChartOptions(),

                        plugins: [
                            bmiReferencePlugin
                        ]

                    }
                );


            /* ----------------------------------------------------------
               Weight Chart
               ---------------------------------------------------------- */

            if (weightCanvas) {

                weightChart =
                    new Chart(
                        weightCanvas,
                        {

                            type: "line",

                            data: {

                                labels,

                                datasets: [

                                    {

                                        label:
                                            "Weight",

                                        data:
                                            weightValues,

                                        borderColor:
                                            "#d79a20",

                                        backgroundColor:
                                            "rgba(215,154,32,.09)",

                                        pointBackgroundColor:
                                            "#d79a20",

                                        pointBorderColor:
                                            "#ffffff",

                                        pointHoverBackgroundColor:
                                            "#ffffff",

                                        pointHoverBorderColor:
                                            "#d79a20",

                                        fill: true

                                    }

                                ]

                            },

                            options:
                                commonChartOptions()

                        }
                    );

            }

        } catch (error) {

            showToast(
                error.message,
                true
            );

        }

    }


    loadAnalytics();
}


/* ==========================================================================
   START APPLICATION
   ========================================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initDashboard();

        initHistory();

        initAnalytics();

    }
);