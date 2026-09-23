"""
BMI Insight - Flask web application.

This module provides the live web interface for BMI Insight.
It reuses the same BMI calculation, validation, and SQLite database
logic as the desktop application so both interfaces behave consistently.
"""

from datetime import datetime

from flask import Flask, jsonify, render_template, request

from bmi_calculator import calculate_bmi, categorize_bmi, category_position
from config import BMI_DISCLAIMER, DEBUG, FLASK_SECRET_KEY, PORT
from database import (
    DatabaseError,
    add_record,
    add_user,
    delete_record,
    get_records,
    get_stats,
    get_user_by_name,
    get_users,
    init_db,
)
from validators import validate_height, validate_name, validate_weight


app = Flask(__name__)
app.config["SECRET_KEY"] = FLASK_SECRET_KEY

# Create the SQLite database and required tables when the app starts.
try:
    init_db()
except DatabaseError as exc:
    # Keep the application importable; individual routes will return
    # useful database errors if the database is unavailable.
    print(f"Database initialization warning: {exc}")


def row_to_dict(row):
    """Convert a sqlite3.Row into a regular dictionary."""
    return {key: row[key] for key in row.keys()}


@app.route("/")
def dashboard():
    """Render the main BMI dashboard."""
    try:
        users = get_users()
        user_data = [row_to_dict(user) for user in users]

        return render_template(
            "index.html",
            users=user_data,
            db_error=None,
            disclaimer=BMI_DISCLAIMER,
        )

    except DatabaseError as exc:
        return render_template(
            "index.html",
            users=[],
            db_error=str(exc),
            disclaimer=BMI_DISCLAIMER,
        ), 500


@app.route("/history")
def history_page():
    """Render the BMI history page."""
    try:
        users = get_users()

        return render_template(
            "history.html",
            users=[row_to_dict(user) for user in users],
            db_error=None,
        )

    except DatabaseError as exc:
        return render_template(
            "history.html",
            users=[],
            db_error=str(exc),
        ), 500


@app.route("/analytics")
def analytics_page():
    """Render the analytics page."""
    try:
        users = get_users()

        return render_template(
            "analytics.html",
            users=[row_to_dict(user) for user in users],
            db_error=None,
        )

    except DatabaseError as exc:
        return render_template(
            "analytics.html",
            users=[],
            db_error=str(exc),
        ), 500


# ----------------------------------------------------------------------
# User API
# ----------------------------------------------------------------------

@app.route("/api/users", methods=["GET", "POST"])
def api_users():
    """Get all users or create a new user."""

    if request.method == "GET":
        try:
            users = get_users()
            return jsonify([row_to_dict(user) for user in users])

        except DatabaseError as exc:
            return jsonify({"error": str(exc)}), 500

    payload = request.get_json(silent=True) or {}

    ok, result = validate_name(payload.get("name", ""))

    if not ok:
        return jsonify({"error": result}), 400

    try:
        # If the name already exists, reuse the existing user.
        existing_user = get_user_by_name(result)

        if existing_user:
            return jsonify(
                {
                    "id": existing_user["id"],
                    "name": existing_user["name"],
                    "existing": True,
                }
            )

        user_id = add_user(result)

        return jsonify(
            {
                "id": user_id,
                "name": result,
                "existing": False,
            }
        ), 201

    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500


# ----------------------------------------------------------------------
# BMI calculation API
# ----------------------------------------------------------------------

@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    """Validate input, calculate BMI, and save the measurement."""

    payload = request.get_json(silent=True) or {}

    raw_user_id = payload.get("user_id")

    if raw_user_id in (None, ""):
        return jsonify(
            {"error": "Please select or add a user first."}
        ), 400

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user selected."}), 400

    # Confirm that the selected user actually exists.
    try:
        users = get_users()
    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500

    valid_user_ids = {int(user["id"]) for user in users}

    if user_id not in valid_user_ids:
        return jsonify({"error": "Selected user was not found."}), 404

    # Validate weight.
    weight_ok, weight_result = validate_weight(
        payload.get("weight")
    )

    if not weight_ok:
        return jsonify({"error": weight_result}), 400

    # Validate height.
    height_ok, height_result = validate_height(
        payload.get("height")
    )

    if not height_ok:
        return jsonify({"error": height_result}), 400

    # Calculate BMI.
    try:
        bmi = calculate_bmi(weight_result, height_result)
        category = categorize_bmi(bmi)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # Save measurement.
    try:
        record_id = add_record(
            user_id=user_id,
            weight=weight_result,
            height=height_result,
            bmi=bmi,
            category=category,
        )

    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify(
        {
            "id": record_id,
            "bmi": bmi,
            "category": category,
            "scale_position": category_position(bmi),
            "weight": weight_result,
            "height": height_result,
            "created_at": datetime.now().strftime(
                "%d %b %Y, %H:%M"
            ),
        }
    )


# ----------------------------------------------------------------------
# History API
# ----------------------------------------------------------------------

@app.route("/api/records/<int:user_id>", methods=["GET"])
def api_records(user_id):
    """Return BMI history for a specific user."""

    try:
        records = get_records(user_id)

        return jsonify(
            [row_to_dict(record) for record in records]
        )

    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/records/<int:record_id>", methods=["DELETE"])
def api_delete_record(record_id):
    """Delete one BMI history record."""

    try:
        deleted = delete_record(record_id)

    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500

    if not deleted:
        return jsonify({"error": "Record not found."}), 404

    return jsonify(
        {
            "deleted": True,
            "record_id": record_id,
        }
    )


# ----------------------------------------------------------------------
# Analytics API
# ----------------------------------------------------------------------

@app.route("/api/stats/<int:user_id>", methods=["GET"])
def api_stats(user_id):
    """Return summary statistics for a specific user."""

    try:
        stats = get_stats(user_id)
        return jsonify(stats)

    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/chart/<int:user_id>", methods=["GET"])
def api_chart_data(user_id):
    """
    Return historical values needed by the web analytics charts.

    The frontend can use this JSON data to render BMI and weight trends.
    """
    try:
        records = list(reversed(get_records(user_id)))

    except DatabaseError as exc:
        return jsonify({"error": str(exc)}), 500

    chart_data = {
        "dates": [record["created_at"] for record in records],
        "bmi": [record["bmi"] for record in records],
        "weight": [record["weight"] for record in records],
    }

    return jsonify(chart_data)


# ----------------------------------------------------------------------
# Health / application status
# ----------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health endpoint useful for deployment monitoring."""

    try:
        get_users()

        return jsonify(
            {
                "status": "healthy",
                "service": "BMI Insight",
            }
        )

    except DatabaseError:
        return jsonify(
            {
                "status": "unhealthy",
                "service": "BMI Insight",
            }
        ), 500


# ----------------------------------------------------------------------
# Error handling
# ----------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_error):
    """Render a friendly 404 page using the main application layout."""

    try:
        users = get_users()
    except DatabaseError:
        users = []

    return render_template(
        "index.html",
        users=[row_to_dict(user) for user in users],
        db_error="The requested page could not be found.",
        disclaimer=BMI_DISCLAIMER,
    ), 404


@app.errorhandler(500)
def internal_server_error(_error):
    """Render a friendly server error page."""

    try:
        users = get_users()
    except DatabaseError:
        users = []

    return render_template(
        "index.html",
        users=[row_to_dict(user) for user in users],
        db_error="Something went wrong while processing your request.",
        disclaimer=BMI_DISCLAIMER,
    ), 500


# ----------------------------------------------------------------------
# Local development
# ----------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=DEBUG,
    )