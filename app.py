from flask import Flask, render_template, request, redirect, url_for, flash
import os
import subprocess
import threading
import json
from logger import get_logger
import config
from collections import defaultdict
from dateutil import parser

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages
logger = get_logger(__name__)

DATA_FILE = "data.json"
STATUS_FILE = "status.json"

def run_main_script():
    """Runs the main.py script in a separate process."""
    try:
        subprocess.run(["python", "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running main.py: {e}")

def format_date(date_str):
    if not date_str:
        return ""
    try:
        return parser.parse(date_str).strftime('%Y-%m-%d %H:%M:%S')
    except parser.ParserError:
        logger.warning(f"Could not parse date: {date_str}")
        return date_str

@app.route("/")
def index():
    """Displays the main page with replied and ignored mails."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"replied_mails": [], "ignored_mails": []}

    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            status = json.load(f).get("status", "stopped")
    else:
        status = "stopped"

    search_replied = request.args.get("search_replied", "")
    search_ignored = request.args.get("search_ignored", "")

    if search_replied:
        data["replied_mails"] = [
            mail for mail in data["replied_mails"]
            if search_replied.lower() in mail.get("to", "").lower() or
               search_replied.lower() in mail.get("subject", "").lower() or
               search_replied.lower() in mail.get("reply", "").lower()
        ]

    if search_ignored:
        data["ignored_mails"] = [
            mail for mail in data["ignored_mails"]
            if search_ignored.lower() in mail.get("from", "").lower() or
               search_ignored.lower() in mail.get("subject", "").lower()
        ]

    # Format dates
    for mail in data["replied_mails"]:
        mail["date"] = format_date(mail.get("date"))
    for mail in data["ignored_mails"]:
        mail["date"] = format_date(mail.get("date"))

    # Summary statistics
    total_replied = len(data["replied_mails"])
    total_ignored = len(data["ignored_mails"])
    
    # Recent activity
    recent_replied = data["replied_mails"][-1] if data["replied_mails"] else None
    recent_ignored = data["ignored_mails"][-1] if data["ignored_mails"] else None


    return render_template("index.html", 
                           replied_mails=data["replied_mails"], 
                           ignored_mails=data["ignored_mails"],
                           status=status,
                           total_replied=total_replied,
                           total_ignored=total_ignored,
                           recent_replied=recent_replied,
                           recent_ignored=recent_ignored)

@app.route("/start", methods=["POST"])
def start_script():
    """Starts the main.py script in a background thread."""
    try:
        thread = threading.Thread(target=run_main_script)
        thread.daemon = True
        thread.start()
        flash("Script started successfully!", "success")
    except Exception as e:
        logger.error(f"Failed to start script: {e}")
        flash("Failed to start script.", "error")
    return redirect(url_for("index"))

@app.route("/charts")
def charts():
    """Displays the charts page."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"replied_mails": [], "ignored_mails": []}

    # Prepare data for daily chart
    daily_counts = defaultdict(lambda: {"replied": 0, "ignored": 0})
    for mail in data["replied_mails"]:
        date_str = mail.get("date", "")
        if date_str:
            try:
                date = parser.parse(date_str).strftime('%Y-%m-%d')
                daily_counts[date]["replied"] += 1
            except parser.ParserError:
                logger.warning(f"Could not parse date: {date_str}")
    for mail in data["ignored_mails"]:
        date_str = mail.get("date", "")
        if date_str:
            try:
                date = parser.parse(date_str).strftime('%Y-%m-%d')
                daily_counts[date]["ignored"] += 1
            except parser.ParserError:
                logger.warning(f"Could not parse date: {date_str}")

    sorted_dates = sorted(daily_counts.keys())
    daily_chart_labels = sorted_dates
    replied_chart_data = [daily_counts[date]["replied"] for date in sorted_dates]
    ignored_chart_data = [daily_counts[date]["ignored"] for date in sorted_dates]

    # Prepare data for category pie charts
    replied_category_counts = defaultdict(int)
    for mail in data["replied_mails"]:
        replied_category_counts[mail.get("category", "Other")] += 1
        
    ignored_category_counts = defaultdict(int)
    for mail in data["ignored_mails"]:
        ignored_category_counts[mail.get("category", "Other")] += 1

    replied_pie_labels = list(replied_category_counts.keys())
    replied_pie_data = list(replied_category_counts.values())
    ignored_pie_labels = list(ignored_category_counts.keys())
    ignored_pie_data = list(ignored_category_counts.values())

    return render_template("charts.html",
                           daily_chart_labels=daily_chart_labels,
                           replied_chart_data=replied_chart_data,
                           ignored_chart_data=ignored_chart_data,
                           replied_pie_labels=replied_pie_labels,
                           replied_pie_data=replied_pie_data,
                           ignored_pie_labels=ignored_pie_labels,
                           ignored_pie_data=ignored_pie_data)

@app.route("/config", methods=["GET", "POST"])
def edit_config():
    """Displays and edits the configuration."""
    if request.method == "POST":
        try:
            keywords = request.form.get("keywords")
            reply_template = request.form.get("reply_template")
            use_ai = request.form.get("use_ai") == "on"

            with open("config.py", "w") as f:
                f.write(f'SCOPES = {config.SCOPES}\n')
                f.write(f'KEYWORDS = {[keyword.strip() for keyword in keywords.split(",")]}\n')
                f.write(f'MAILTEMPLATE = "{reply_template}"\n')
                f.write(f'SECRET_TOKEN = "{config.SECRET_TOKEN}"\n')
                f.write(f'OPENAI_API_KEY = "{config.OPENAI_API_KEY}"\n')
                f.write(f'USE_AI = {use_ai}\n')
            
            flash("Configuration saved successfully!", "success")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            flash("Failed to save configuration.", "error")
        return redirect(url_for("edit_config"))

    return render_template("config.html", keywords=", ".join(config.KEYWORDS), reply_template=config.MAILTEMPLATE, use_ai=config.USE_AI)

if __name__ == "__main__":
    app.run(debug=True)
