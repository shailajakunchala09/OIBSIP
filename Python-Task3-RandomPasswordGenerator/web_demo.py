from __future__ import annotations

import os

from flask import Flask, jsonify, render_template_string, request

from password_generator import (
    GeneratorSettings,
    PasswordGenerationError,
    generate_password,
)
from strength_analyzer import analyze_password
from validators import ValidationError


app = Flask(__name__)


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="description"
    content="VaultForge Secure Password Studio"
>

<title>VaultForge - Secure Password Studio</title>


<style>

/* ============================================================
   DESIGN TOKENS
   ============================================================ */

:root {

    --bg: #08111f;

    --panel: #101c2e;

    --panel-2: #0c1727;

    --border: #22324a;

    --text: #f5f7fb;

    --text-secondary: #c5cfdd;

    --muted: #91a0b5;

    --accent: #7c83ff;

    --accent-hover: #6971ff;

    --accent-2: #5fd1ff;

    --success: #4ade80;

    --warning: #fbbf24;

    --danger: #fb7185;

    --password-bg: #07101d;

    --shadow: 0 24px 70px rgba(0, 0, 0, 0.35);

    --soft-shadow: 0 12px 35px rgba(0, 0, 0, 0.18);
}


/* ============================================================
   LIGHT THEME
   ============================================================ */

:root[data-theme="light"] {

    --bg: #f3f6fb;

    --panel: #ffffff;

    --panel-2: #ffffff;

    --border: #d7dfeb;

    --text: #172033;

    --text-secondary: #334155;

    --muted: #64748b;

    --accent: #5963e8;

    --accent-hover: #4b55dc;

    --accent-2: #087ea4;

    --success: #168a46;

    --warning: #a66d00;

    --danger: #d13f59;

    --password-bg: #f8fafc;

    --shadow: 0 24px 60px rgba(30, 45, 70, 0.10);

    --soft-shadow: 0 12px 30px rgba(30, 45, 70, 0.07);
}


/* ============================================================
   RESET
   ============================================================ */

* {
    box-sizing: border-box;
}


html {
    scroll-behavior: smooth;
}


body {

    margin: 0;

    min-height: 100vh;

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:
        radial-gradient(
            circle at top right,
            rgba(124, 131, 255, 0.15),
            transparent 32%
        ),
        radial-gradient(
            circle at bottom left,
            rgba(95, 209, 255, 0.08),
            transparent 32%
        ),
        var(--bg);

    color: var(--text);

    transition:
        background 0.25s ease,
        color 0.25s ease;
}


button,
select,
input {
    font: inherit;
}


/* ============================================================
   MAIN CONTAINER
   ============================================================ */

.container {

    width: min(
        1180px,
        calc(100% - 32px)
    );

    margin: 0 auto;

    padding: 42px 0 60px;
}


/* ============================================================
   HERO
   ============================================================ */

.hero {

    display: flex;

    justify-content: space-between;

    align-items: flex-end;

    gap: 24px;

    margin-bottom: 28px;
}


.hero-left {
    min-width: 0;
}


.eyebrow {

    display: inline-flex;

    align-items: center;

    gap: 8px;

    color: var(--accent-2);

    font-size: 12px;

    font-weight: 800;

    letter-spacing: 0.12em;

    text-transform: uppercase;

    margin-bottom: 10px;
}


.dot {

    width: 8px;

    height: 8px;

    border-radius: 999px;

    background: var(--success);

    box-shadow:
        0 0 16px rgba(74, 222, 128, 0.65);
}


h1 {

    margin: 0;

    font-size:
        clamp(
            34px,
            6vw,
            64px
        );

    line-height: 0.98;

    letter-spacing: -0.045em;
}


.subtitle {

    margin: 14px 0 0;

    max-width: 700px;

    color: var(--muted);

    font-size: 16px;

    line-height: 1.65;
}


.hero-actions {

    display: flex;

    align-items: center;

    justify-content: flex-end;

    gap: 10px;

    flex-wrap: wrap;
}


/* ============================================================
   BUTTON BASE
   ============================================================ */

button {

    border: 1px solid var(--border);

    border-radius: 12px;

    padding: 11px 15px;

    cursor: pointer;

    color: var(--text);

    background: var(--panel-2);

    font-weight: 800;

    transition:
        transform 0.15s ease,
        border-color 0.15s ease,
        background 0.2s ease,
        color 0.2s ease,
        box-shadow 0.2s ease;
}


button:hover {

    transform: translateY(-1px);

    border-color: var(--accent);

    box-shadow:
        0 7px 18px
        rgba(89, 99, 232, 0.10);
}


button:active {
    transform: translateY(0);
}


button.primary {

    flex: 1;

    min-width: 180px;

    color: #ffffff;

    border-color: transparent;

    background:
        linear-gradient(
            135deg,
            var(--accent),
            var(--accent-hover)
        );
}


button.primary:hover {

    border-color: transparent;

    box-shadow:
        0 10px 24px
        rgba(89, 99, 232, 0.24);
}


/* ============================================================
   THEME BUTTON
   ============================================================ */

.theme-btn {

    min-width: 88px;

    white-space: nowrap;
}


/* ============================================================
   SECURITY BADGE
   ============================================================ */

.badge {

    border: 1px solid var(--border);

    background: var(--panel);

    padding: 10px 14px;

    border-radius: 999px;

    color: var(--muted);

    font-size: 12px;

    white-space: nowrap;

    box-shadow: var(--soft-shadow);
}


/* ============================================================
   TWO COLUMN GRID
   ============================================================ */

.grid {

    display: grid;

    grid-template-columns:
        1fr
        1.12fr;

    gap: 20px;
}


/* ============================================================
   CARD
   ============================================================ */

.card {

    background: var(--panel);

    border: 1px solid var(--border);

    border-radius: 22px;

    box-shadow: var(--shadow);

    padding: 22px;

    transition:
        background 0.25s ease,
        border-color 0.25s ease,
        box-shadow 0.25s ease;
}


.card h2 {

    margin: 0;

    font-size: 18px;

    letter-spacing: -0.02em;
}


.card-subtitle {

    margin: 7px 0 20px;

    color: var(--muted);

    font-size: 13px;

    line-height: 1.55;
}


/* ============================================================
   FIELD LABEL
   ============================================================ */

.field-label {

    display: block;

    color: var(--muted);

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 0.09em;

    text-transform: uppercase;

    margin: 18px 0 8px;
}


/* ============================================================
   SELECT / NUMBER
   ============================================================ */

select,
input[type="number"] {

    width: 100%;

    border: 1px solid var(--border);

    background: var(--panel-2);

    color: var(--text);

    border-radius: 12px;

    padding: 12px 13px;

    outline: none;

    transition:
        background 0.2s ease,
        border-color 0.2s ease,
        color 0.2s ease,
        box-shadow 0.2s ease;
}


select:focus,
input[type="number"]:focus {

    border-color: var(--accent);

    box-shadow:
        0 0 0 3px
        rgba(89, 99, 232, 0.10);
}


/* ============================================================
   RANGE
   ============================================================ */

input[type="range"] {

    width: 100%;

    accent-color: var(--accent);

    cursor: pointer;
}


/* ============================================================
   LENGTH
   ============================================================ */

.length-row {

    display: grid;

    grid-template-columns:
        1fr
        84px;

    gap: 12px;

    align-items: center;
}


.length-value {

    text-align: center;

    border: 1px solid var(--border);

    background: var(--panel-2);

    border-radius: 12px;

    padding: 11px 8px;

    font-weight: 800;

    box-shadow: var(--soft-shadow);
}


.length-help {

    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 10px;

    margin-top: 9px;
}


.help-text {

    display: flex;

    align-items: center;

    color: var(--muted);

    font-size: 11px;

    line-height: 1.4;
}


/* ============================================================
   CHARACTER OPTIONS
   ============================================================ */

.options {

    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 10px;
}


.option {

    display: flex;

    align-items: center;

    gap: 10px;

    padding: 13px;

    border-radius: 14px;

    border: 1px solid var(--border);

    background: var(--panel-2);

    transition:
        transform 0.15s ease,
        border-color 0.15s ease,
        background 0.2s ease,
        box-shadow 0.2s ease;
}


.option:hover {

    transform: translateY(-1px);

    border-color: var(--accent);

    box-shadow: var(--soft-shadow);
}


.option input {

    width: 17px;

    height: 17px;

    accent-color: var(--accent);

    flex: 0 0 auto;
}


.option strong {

    display: block;

    font-size: 13px;

    color: var(--text);
}


.option span {

    display: block;

    color: var(--muted);

    font-size: 11px;

    margin-top: 2px;

    line-height: 1.4;
}


/* ============================================================
   ACTIONS
   ============================================================ */

.actions {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;

    margin-top: 20px;
}


/* ============================================================
   PASSWORD DISPLAY
   ============================================================ */

.password-shell {

    border: 1px solid var(--border);

    background: var(--password-bg);

    border-radius: 16px;

    padding: 16px;

    transition:
        background 0.2s ease,
        border-color 0.2s ease;
}


.password {

    min-height: 48px;

    display: flex;

    align-items: center;

    word-break: break-all;

    font-family:
        "SFMono-Regular",
        Consolas,
        "Liberation Mono",
        monospace;

    font-size:
        clamp(
            17px,
            2vw,
            23px
        );

    font-weight: 800;

    letter-spacing: 0.04em;

    line-height: 1.45;

    color: var(--text);
}


/* ============================================================
   STRENGTH
   ============================================================ */

.strength-row {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-top: 16px;
}


.strength {

    font-size: 13px;

    font-weight: 900;
}


.bar {

    height: 10px;

    margin-top: 9px;

    border-radius: 99px;

    overflow: hidden;

    background: var(--border);
}


.bar-fill {

    height: 100%;

    width: 0;

    border-radius: inherit;

    background: var(--accent);

    transition:
        width 0.25s ease,
        background 0.25s ease;
}


/* ============================================================
   STATISTICS
   ============================================================ */

.stats {

    display: grid;

    grid-template-columns:
        repeat(
            3,
            1fr
        );

    gap: 10px;

    margin-top: 16px;
}


.stat {

    border: 1px solid var(--border);

    border-radius: 14px;

    padding: 13px;

    background: var(--panel-2);

    transition:
        background 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}


.stat:hover {

    border-color: var(--accent);

    box-shadow: var(--soft-shadow);
}


.stat-label {

    color: var(--muted);

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 0.08em;

    font-weight: 800;
}


.stat-value {

    margin-top: 6px;

    font-size: 19px;

    font-weight: 900;

    color: var(--text);
}


/* ============================================================
   MESSAGE
   ============================================================ */

.message {

    margin-top: 14px;

    min-height: 20px;

    font-size: 12px;

    color: var(--muted);

    line-height: 1.5;
}


/* ============================================================
   TIPS
   ============================================================ */

.tips {

    margin-top: 18px;

    border-top: 1px solid var(--border);

    padding-top: 16px;
}


.tips h3 {

    margin: 0 0 9px;

    font-size: 13px;

    color: var(--text);
}


.tips ul {

    margin: 0;

    padding-left: 17px;

    color: var(--muted);

    font-size: 12px;

    line-height: 1.65;
}


/* ============================================================
   SECURITY NOTE
   ============================================================ */

.security-note {

    margin-top: 20px;

    padding: 14px;

    border-radius: 14px;

    background: var(--panel-2);

    border: 1px solid var(--border);

    color: var(--muted);

    font-size: 11px;

    line-height: 1.6;

    transition:
        background 0.2s ease,
        border-color 0.2s ease;
}


/* ============================================================
   HISTORY
   ============================================================ */

.history {

    margin-top: 20px;
}


.history-list {

    display: grid;

    gap: 8px;

    margin-top: 12px;
}


.history-item {

    border: 1px solid var(--border);

    background: var(--panel-2);

    border-radius: 12px;

    padding: 11px 12px;

    font-family:
        "SFMono-Regular",
        Consolas,
        "Liberation Mono",
        monospace;

    font-size: 12px;

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 12px;

    transition:
        background 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}


.history-item:hover {

    border-color: var(--accent);

    box-shadow: var(--soft-shadow);
}


.history-item span:first-child {

    min-width: 0;

    word-break: break-all;

    color: var(--text);
}


.history-item span:last-child {

    color: var(--muted);

    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        sans-serif;

    white-space: nowrap;
}


/* ============================================================
   FOOTER
   ============================================================ */

.footer {

    text-align: center;

    color: var(--muted);

    font-size: 11px;

    margin-top: 24px;

    letter-spacing: 0.04em;
}


/* ============================================================
   LIGHT THEME REFINEMENTS
   ============================================================ */

:root[data-theme="light"] .card {

    background: #ffffff;

    border-color: #d7dfeb;

    box-shadow:
        0 18px 45px
        rgba(30, 45, 70, 0.08);
}


:root[data-theme="light"] .option,
:root[data-theme="light"] .stat,
:root[data-theme="light"] .security-note,
:root[data-theme="light"] select,
:root[data-theme="light"] input[type="number"],
:root[data-theme="light"] .length-value,
:root[data-theme="light"] .badge,
:root[data-theme="light"] .history-item {

    background: #ffffff;

    color: #172033;

    border-color: #d7dfeb;
}


:root[data-theme="light"] .password-shell {

    background: #f8fafc;

    border-color: #d7dfeb;
}


:root[data-theme="light"] .security-note {

    background: #f6fbff;

    border-color: #cfe3ef;
}


:root[data-theme="light"] .bar {

    background: #dfe5ef;
}


/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 900px) {

    .grid {

        grid-template-columns: 1fr;

    }


    .hero {

        align-items: flex-start;

        flex-direction: column;

    }


    .hero-actions {

        justify-content: flex-start;

    }


    .badge {

        white-space: normal;

    }

}


@media (max-width: 520px) {

    .container {

        width:
            min(
                100% - 20px,
                1180px
            );

        padding-top: 25px;

    }


    .card {

        padding: 17px;

        border-radius: 17px;

    }


    .options {

        grid-template-columns: 1fr;

    }


    .stats {

        grid-template-columns: 1fr;

    }


    .length-help {

        grid-template-columns: 1fr;

    }


    .history-item {

        flex-direction: column;

        align-items: flex-start;

    }


    .hero-actions {

        width: 100%;

        justify-content: flex-start;

    }


    .theme-btn {

        min-width: 100px;

    }


    .badge {

        width: 100%;

        text-align: center;

    }

}

</style>

</head>


<body>


<div class="container">


    <!-- ========================================================
         HEADER
         ======================================================== -->

    <header class="hero">


        <div class="hero-left">


            <div class="eyebrow">

                <span class="dot"></span>

                Secure Password Studio

            </div>


            <h1>
                VaultForge
            </h1>


            <p class="subtitle">

                Generate high-diversity passwords from your own
                criteria, analyse their strength, and keep your
                recent generations available only for the current
                browser session.

            </p>


        </div>


        <div class="hero-actions">


            <button
                id="themeToggle"
                class="theme-btn"
                type="button"
            >
                Light
            </button>


            <div class="badge">

                Python
                <b>secrets</b>
                powered

            </div>


        </div>


    </header>



    <!-- ========================================================
         MAIN GRID
         ======================================================== -->

    <main class="grid">


        <!-- ====================================================
             GENERATOR CONTROLS
             ==================================================== -->

        <section class="card">


            <h2>
                Generator Controls
            </h2>


            <p class="card-subtitle">

                Configure the password exactly the way you need it.

            </p>



            <!-- PRESET -->

            <label
                class="field-label"
                for="preset"
            >
                Password preset
            </label>


            <select id="preset">


                <option value="Quick Secure">
                    Quick Secure
                </option>


                <option
                    value="Strong"
                    selected
                >
                    Strong
                </option>


                <option value="Maximum Security">
                    Maximum Security
                </option>


                <option value="Custom">
                    Custom
                </option>


            </select>



            <!-- LENGTH -->

            <label
                class="field-label"
                for="length"
            >
                Password length
            </label>


            <div class="length-row">


                <input
                    id="length"
                    type="range"
                    min="8"
                    max="128"
                    value="16"
                >


                <div
                    class="length-value"
                    id="lengthValue"
                >
                    16
                </div>


            </div>


            <div class="length-help">


                <input
                    id="lengthNumber"
                    type="number"
                    min="8"
                    max="128"
                    value="16"
                    aria-label="Password length"
                >


                <div class="help-text">

                    Minimum 8 characters.
                    Maximum 128 characters.

                </div>


            </div>



            <!-- CHARACTER TYPES -->

            <label class="field-label">

                Character types

            </label>


            <div class="options">


                <label class="option">


                    <input
                        id="upper"
                        type="checkbox"
                        checked
                    >


                    <div>


                        <strong>
                            Uppercase
                        </strong>


                        <span>
                            A-Z
                        </span>


                    </div>


                </label>



                <label class="option">


                    <input
                        id="lower"
                        type="checkbox"
                        checked
                    >


                    <div>


                        <strong>
                            Lowercase
                        </strong>


                        <span>
                            a-z
                        </span>


                    </div>


                </label>



                <label class="option">


                    <input
                        id="digits"
                        type="checkbox"
                        checked
                    >


                    <div>


                        <strong>
                            Numbers
                        </strong>


                        <span>
                            0-9
                        </span>


                    </div>


                </label>



                <label class="option">


                    <input
                        id="symbols"
                        type="checkbox"
                        checked
                    >


                    <div>


                        <strong>
                            Symbols
                        </strong>


                        <span>
                            !@#$%^&*
                        </span>


                    </div>


                </label>


            </div>



            <!-- AMBIGUOUS -->

            <label
                class="option"
                style="margin-top:10px;"
            >


                <input
                    id="ambiguous"
                    type="checkbox"
                    checked
                >


                <div>


                    <strong>
                        Exclude ambiguous characters
                    </strong>


                    <span>

                        Reduce visually similar characters such as
                        0, O, 1 and l.

                    </span>


                </div>


            </label>



            <!-- ACTIONS -->

            <div class="actions">


                <button
                    class="primary"
                    id="generate"
                    type="button"
                >
                    Generate Password
                </button>


                <button
                    id="regenerate"
                    type="button"
                >
                    Regenerate
                </button>


            </div>


            <div
                class="message"
                id="message"
            >
                Select at least two character types.
            </div>


        </section>



        <!-- ====================================================
             SECURITY ANALYSIS
             ==================================================== -->

        <section class="card">


            <h2>
                Security Analysis
            </h2>


            <p class="card-subtitle">

                The same Python password-generation and analysis
                logic used by VaultForge is used for this public
                demonstration.

            </p>



            <!-- PASSWORD -->

            <div class="password-shell">


                <div
                    class="password"
                    id="password"
                >
                    Click Generate Password
                </div>


            </div>



            <!-- COPY -->

            <div class="actions">


                <button
                    class="primary"
                    id="copy"
                    type="button"
                >
                    Copy to Clipboard
                </button>


            </div>



            <!-- STRENGTH -->

            <div class="strength-row">


                <strong>
                    Password Strength
                </strong>


                <span
                    class="strength"
                    id="strength"
                >
                    -
                </span>


            </div>


            <div class="bar">


                <div
                    class="bar-fill"
                    id="strengthBar"
                ></div>


            </div>



            <!-- STATS -->

            <div class="stats">


                <div class="stat">


                    <div class="stat-label">
                        Length
                    </div>


                    <div
                        class="stat-value"
                        id="statLength"
                    >
                        -
                    </div>


                </div>



                <div class="stat">


                    <div class="stat-label">
                        Types
                    </div>


                    <div
                        class="stat-value"
                        id="statTypes"
                    >
                        -
                    </div>


                </div>



                <div class="stat">


                    <div class="stat-label">
                        Entropy
                    </div>


                    <div
                        class="stat-value"
                        id="statEntropy"
                    >
                        -
                    </div>


                </div>


            </div>



            <!-- TIPS -->

            <div class="tips">


                <h3>
                    Security Tips
                </h3>


                <ul id="tips">


                    <li>
                        Generate a password to see its analysis.
                    </li>


                </ul>


            </div>



            <!-- SECURITY NOTE -->

            <div class="security-note">


                Passwords are generated using Python's
                cryptographically secure
                <b>secrets</b>
                module.


                This public demo does not persist generated
                passwords on the server.


            </div>


        </section>


    </main>



    <!-- ========================================================
         HISTORY
         ======================================================== -->

    <section class="card history">


        <h2>
            Recent Generation History
        </h2>


        <p class="card-subtitle">


            The latest five passwords remain in browser memory only.
            Refreshing the page clears this list.


        </p>


        <div
            class="history-list"
            id="history"
        >


            <div
                style="
                    color:var(--muted);
                    font-size:12px;
                "
            >
                No passwords generated yet this session.
            </div>


        </div>


    </section>



    <!-- ========================================================
         FOOTER
         ======================================================== -->

    <div class="footer">

        VAULTFORGE -
        SECURE PASSWORD STUDIO -
        OIBSIP PYTHON TASK 3

    </div>


</div>



<script>

/* ============================================================
   STATE
   ============================================================ */

const state = {

    history: [],

    lastPassword: ""

};



/* ============================================================
   ELEMENT HELPER
   ============================================================ */

const $ = (id) =>
    document.getElementById(id);



/* ============================================================
   PRESETS
   ============================================================ */

const presets = {

    "Quick Secure": {

        length: 12,

        upper: true,

        lower: true,

        digits: true,

        symbols: false,

        ambiguous: true

    },


    "Strong": {

        length: 16,

        upper: true,

        lower: true,

        digits: true,

        symbols: true,

        ambiguous: true

    },


    "Maximum Security": {

        length: 24,

        upper: true,

        lower: true,

        digits: true,

        symbols: true,

        ambiguous: false

    }

};



/* ============================================================
   LENGTH
   ============================================================ */

function syncLength(value) {

    let safe = Number(value);


    if (!Number.isFinite(safe)) {

        safe = 16;

    }


    safe = Math.round(safe);


    safe = Math.max(
        8,
        Math.min(128, safe)
    );


    $("length").value = safe;

    $("lengthNumber").value = safe;

    $("lengthValue").textContent = safe;

}



/* ============================================================
   SELECTED CHARACTER TYPES
   ============================================================ */

function selectedTypes() {

    return {

        upper:
            $("upper").checked,

        lower:
            $("lower").checked,

        digits:
            $("digits").checked,

        symbols:
            $("symbols").checked

    };

}



/* ============================================================
   TYPE COUNT
   ============================================================ */

function typeCount() {

    return Object
        .values(selectedTypes())
        .filter(Boolean)
        .length;

}



/* ============================================================
   MESSAGE
   ============================================================ */

function setMessage(
    text,
    success = false
) {

    $("message").textContent = text;


    $("message").style.color =
        success
            ? "var(--success)"
            : "var(--muted)";

}



/* ============================================================
   APPLY PRESET
   ============================================================ */

function applyPreset(name) {

    const preset =
        presets[name];


    if (!preset) {

        return;

    }


    syncLength(
        preset.length
    );


    $("upper").checked =
        preset.upper;


    $("lower").checked =
        preset.lower;


    $("digits").checked =
        preset.digits;


    $("symbols").checked =
        preset.symbols;


    $("ambiguous").checked =
        preset.ambiguous;


    setMessage(
        "Preset applied."
    );

}



/* ============================================================
   STRENGTH
   ============================================================ */

function renderStrength(strength) {

    const widths = {

        "Weak":
            "25%",

        "Medium":
            "50%",

        "Strong":
            "78%",

        "Very Strong":
            "100%"

    };


    $("strength").textContent =
        strength || "-";


    $("strengthBar").style.width =
        widths[strength] || "0%";


    let barColor =
        "var(--accent)";


    if (strength === "Weak") {

        barColor =
            "var(--danger)";

    }


    if (strength === "Medium") {

        barColor =
            "var(--warning)";

    }


    if (
        strength === "Strong" ||
        strength === "Very Strong"
    ) {

        barColor =
            "var(--success)";

    }


    $("strengthBar").style.background =
        barColor;

}



/* ============================================================
   SECURITY TIPS
   ============================================================ */

function renderTips(tips) {

    const list =
        Array.isArray(tips)
            ? tips
            : [];


    if (!list.length) {

        $("tips").innerHTML =
            "<li>No additional security tips.</li>";

        return;

    }


    $("tips").innerHTML =
        list
            .map(
                tip =>
                    `<li>${escapeHtml(tip)}</li>`
            )
            .join("");

}



/* ============================================================
   HISTORY
   ============================================================ */

function renderHistory() {

    const box =
        $("history");


    if (!state.history.length) {

        box.innerHTML = `

            <div
                style="
                    color:var(--muted);
                    font-size:12px;
                "
            >
                No passwords generated yet this session.
            </div>

        `;

        return;

    }


    box.innerHTML =
        state.history

            .map(
                entry => `

                    <div class="history-item">

                        <span>
                            ${escapeHtml(entry.password)}
                        </span>

                        <span>
                            ${escapeHtml(entry.strength)}
                        </span>

                    </div>

                `
            )

            .join("");

}



/* ============================================================
   HTML ESCAPING
   ============================================================ */

function escapeHtml(text) {

    return String(text)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}



/* ============================================================
   GENERATE
   ============================================================ */

async function generate() {

    if (typeCount() < 2) {

        setMessage(
            "At least two character types must be selected."
        );

        return;

    }


    const payload = {

        length:
            Number(
                $("lengthNumber").value
            ),

        upper:
            $("upper").checked,

        lower:
            $("lower").checked,

        digits:
            $("digits").checked,

        symbols:
            $("symbols").checked,

        ambiguous:
            $("ambiguous").checked

    };


    setMessage(
        "Generating securely..."
    );


    try {


        const response =
            await fetch(
                "/api/generate",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(payload)

                }
            );


        let data;


        try {

            data =
                await response.json();

        } catch {

            throw new Error(
                "The server returned an invalid response."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Password generation failed."
            );

        }


        state.lastPassword =
            data.password;


        $("password").textContent =
            data.password;


        $("statLength").textContent =
            data.length;


        $("statTypes").textContent =
            data.category_count;


        $("statEntropy").textContent =
            `${data.entropy_bits} bits`;


        renderStrength(
            data.strength
        );


        renderTips(
            data.tips
        );


        state.history.unshift({

            password:
                data.password,

            strength:
                data.strength

        });


        state.history =
            state.history.slice(
                0,
                5
            );


        renderHistory();



        /* --------------------------------------------------------
           Automatic clipboard copy
           -------------------------------------------------------- */

        try {

            await navigator.clipboard.writeText(
                data.password
            );


            setMessage(
                "Password generated and copied to clipboard.",
                true
            );

        } catch {

            setMessage(
                "Password generated. Clipboard permission was unavailable."
            );

        }


    } catch (error) {

        setMessage(
            error.message ||
            "Something went wrong."
        );

    }

}



/* ============================================================
   THEME
   ============================================================ */

function applyTheme(theme) {

    document.documentElement.setAttribute(
        "data-theme",
        theme
    );


    const button =
        $("themeToggle");


    if (!button) {

        return;

    }


    if (theme === "light") {

        button.textContent =
            "Dark";


        button.setAttribute(
            "aria-label",
            "Switch to dark theme"
        );

    } else {

        button.textContent =
            "Light";


        button.setAttribute(
            "aria-label",
            "Switch to light theme"
        );

    }


    localStorage.setItem(
        "vaultforge-theme",
        theme
    );

}



/* ============================================================
   INITIALIZE THEME
   ============================================================ */

function initializeTheme() {

    let savedTheme =
        localStorage.getItem(
            "vaultforge-theme"
        );


    if (
        savedTheme !== "light" &&
        savedTheme !== "dark"
    ) {

        savedTheme =
            "dark";

    }


    applyTheme(
        savedTheme
    );

}



/* ============================================================
   THEME BUTTON EVENT
   ============================================================ */

$("themeToggle")
    .addEventListener(
        "click",
        () => {


            const currentTheme =
                document.documentElement
                    .getAttribute(
                        "data-theme"
                    )
                || "dark";


            const nextTheme =
                currentTheme === "dark"
                    ? "light"
                    : "dark";


            applyTheme(
                nextTheme
            );

        }
    );



/* ============================================================
   PRESET EVENT
   ============================================================ */

$("preset")
    .addEventListener(
        "change",
        event => {


            const selected =
                event.target.value;


            if (
                selected ===
                "Custom"
            ) {

                setMessage(
                    "Custom settings selected."
                );

            } else {

                applyPreset(
                    selected
                );

            }

        }
    );



/* ============================================================
   LENGTH SLIDER
   ============================================================ */

$("length")
    .addEventListener(
        "input",
        event => {

            syncLength(
                event.target.value
            );

            $("preset").value =
                "Custom";

        }
    );



/* ============================================================
   LENGTH NUMBER
   ============================================================ */

$("lengthNumber")
    .addEventListener(
        "input",
        event => {

            syncLength(
                event.target.value
            );

            $("preset").value =
                "Custom";

        }
    );



/* ============================================================
   CHARACTER CHECKBOX EVENTS
   ============================================================ */

[
    "upper",
    "lower",
    "digits",
    "symbols"
]
.forEach(
    id => {


        $(id)
            .addEventListener(
                "change",
                () => {


                    $("preset").value =
                        "Custom";


                    const count =
                        typeCount();


                    if (count >= 2) {

                        setMessage(
                            `${count} character types selected.`
                        );

                    } else {

                        setMessage(
                            "At least two character types must be selected."
                        );

                    }

                }
            );

    }
);



/* ============================================================
   AMBIGUOUS CHARACTERS
   ============================================================ */

$("ambiguous")
    .addEventListener(
        "change",
        () => {

            $("preset").value =
                "Custom";

        }
    );



/* ============================================================
   BUTTON EVENTS
   ============================================================ */

$("generate")
    .addEventListener(
        "click",
        generate
    );


$("regenerate")
    .addEventListener(
        "click",
        generate
    );



/* ============================================================
   COPY BUTTON
   ============================================================ */

$("copy")
    .addEventListener(
        "click",
        async () => {


            if (!state.lastPassword) {

                setMessage(
                    "Generate a password before copying."
                );

                return;

            }


            try {

                await navigator.clipboard.writeText(
                    state.lastPassword
                );


                setMessage(
                    "Password copied to clipboard.",
                    true
                );

            } catch {

                setMessage(
                    "Clipboard permission was unavailable."
                );

            }

        }
    );



/* ============================================================
   KEYBOARD SHORTCUT
   ============================================================ */

document.addEventListener(
    "keydown",
    event => {


        if (
            event.ctrlKey &&
            event.key === "Enter"
        ) {

            event.preventDefault();

            generate();

        }


        if (
            event.ctrlKey &&
            (
                event.key === "r" ||
                event.key === "R"
            )
        ) {

            event.preventDefault();

            generate();

        }

    }
);



/* ============================================================
   INITIAL STATE
   ============================================================ */

initializeTheme();

applyPreset(
    "Strong"
);

renderHistory();

</script>


</body>
</html>
"""


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def add_security_headers(response):

    response.headers[
        "Cache-Control"
    ] = "no-store"

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "Permissions-Policy"
    ] = "clipboard-write=(self)"

    return response


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return render_template_string(
        PAGE
    )


# ============================================================
# PASSWORD GENERATION API
# ============================================================

@app.post("/api/generate")
def api_generate():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    try:

        settings = GeneratorSettings(

            length=int(
                data.get(
                    "length",
                    16
                )
            ),

            use_upper=bool(
                data.get(
                    "upper",
                    True
                )
            ),

            use_lower=bool(
                data.get(
                    "lower",
                    True
                )
            ),

            use_digits=bool(
                data.get(
                    "digits",
                    True
                )
            ),

            use_symbols=bool(
                data.get(
                    "symbols",
                    True
                )
            ),

            exclude_ambiguous=bool(
                data.get(
                    "ambiguous",
                    True
                )
            )

        )


        password = generate_password(
                settings
            )


        report = analyze_password(
                password
            )


        return jsonify({

            "password":
                password,

            "length":
                report.length,

            "category_count":
                report.category_count,

            "entropy_bits":
                round(
                    report.entropy_bits,
                    1
                ),

            "strength":
                report.strength,

            "tips":
                report.tips

        })


    except (
        ValidationError,
        PasswordGenerationError
    ) as exc:

        return (

            jsonify({
                "error":
                    str(exc)
            }),

            400

        )


    except (
        TypeError,
        ValueError
    ):

        return (

            jsonify({

                "error":
                    "Invalid generator settings."

            }),

            400

        )


    except Exception:

        return (

            jsonify({

                "error":
                    "Unable to generate the password right now."

            }),

            500

        )


# ============================================================
# LOCAL SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )


    app.run(

        host="0.0.0.0",

        port=port

    )