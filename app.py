from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pathlib import Path
import json
import os
import subprocess
import tempfile
from functools import wraps

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "brand": "Gravoso Voucher WIFI",
    "duration": "1 Day",
    "price": "₱20",
    "paper_width": "58",
    "printer_name": "",
    "admin_password": "",
    "port": 5000
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg)
    return merged

def save_config(cfg):
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        cfg = load_config()
        password = cfg.get("admin_password", "")
        if password and not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def clean_codes(raw):
    lines = []
    for line in raw.replace("\r", "").split("\n"):
        code = line.strip()
        if code:
            lines.append(code)
    return lines

def build_print_html(codes, cfg):
    width = "58mm" if str(cfg.get("paper_width")) == "58" else "80mm"
    voucher_max = "54mm" if width == "58mm" else "76mm"

    voucher_blocks = []
    for code in codes:
        voucher_blocks.append(f"""
        <div class="voucher">
          <div class="brand">{escape_html(cfg.get('brand',''))}</div>
          <div class="code">{escape_html(code)}</div>
          <div class="duration">{escape_html(cfg.get('duration',''))}</div>
          <div class="price">{escape_html(cfg.get('price',''))}</div>
        </div>
        """)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: {width} auto;
  margin: 2mm;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  width: {width};
  font-family: Arial, sans-serif;
  color: #000;
}}
.voucher {{
  width: {voucher_max};
  margin: 0 auto 2mm;
  border: 1px solid #000;
  text-align: center;
  page-break-inside: avoid;
}}
.brand {{
  background: #000;
  color: #fff;
  font-weight: 700;
  font-size: 11px;
  padding: 2mm 1mm;
}}
.code {{
  font-weight: 700;
  font-size: 24px;
  letter-spacing: 1px;
  padding-top: 3mm;
}}
.duration {{
  font-size: 13px;
  margin-top: 1mm;
}}
.price {{
  font-size: 20px;
  font-weight: 700;
  padding: 1mm 0 3mm;
}}
</style>
</head>
<body>
{''.join(voucher_blocks)}
</body>
</html>"""

def escape_html(value):
    return (str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

@app.route("/login", methods=["GET", "POST"])
def login():
    cfg = load_config()
    if not cfg.get("admin_password"):
        session["logged_in"] = True
        return redirect(url_for("index"))

    error = ""
    if request.method == "POST":
        if request.form.get("password", "") == cfg.get("admin_password"):
            session["logged_in"] = True
            return redirect(request.args.get("next") or url_for("index"))
        error = "Wrong password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    cfg = load_config()
    return render_template("index.html", config=cfg)

@app.route("/preview", methods=["POST"])
@login_required
def preview():
    cfg = load_config()
    raw = request.form.get("codes", "")
    codes = clean_codes(raw)
    return render_template("preview.html", codes=codes, config=cfg)

@app.route("/api/upload", methods=["POST"])
@login_required
def upload_codes():
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "No file uploaded."}), 400

    text = f.read().decode("utf-8", errors="ignore")
    codes = clean_codes(text)
    return jsonify({"ok": True, "codes": codes, "count": len(codes)})

@app.route("/api/settings", methods=["POST"])
@login_required
def update_settings():
    cfg = load_config()
    data = request.get_json(force=True)

    for key in ["brand", "duration", "price", "paper_width", "printer_name", "admin_password"]:
        if key in data:
            cfg[key] = str(data[key]).strip()

    if cfg["paper_width"] not in ("58", "80"):
        cfg["paper_width"] = "58"

    save_config(cfg)
    return jsonify({"ok": True, "config": cfg})

@app.route("/api/printers")
@login_required
def printers():
    try:
        result = subprocess.run(
            ["lpstat", "-p"],
            capture_output=True,
            text=True,
            timeout=5
        )
        names = []
        for line in result.stdout.splitlines():
            if line.startswith("printer "):
                parts = line.split()
                if len(parts) >= 2:
                    names.append(parts[1])
        return jsonify({"ok": True, "printers": names})
    except Exception as e:
        return jsonify({"ok": False, "printers": [], "error": str(e)})

@app.route("/api/print", methods=["POST"])
@login_required
def print_vouchers():
    cfg = load_config()
    data = request.get_json(force=True)
    raw = data.get("codes", "")
    codes = clean_codes(raw)

    if not codes:
        return jsonify({"ok": False, "error": "No voucher codes."}), 400

    printer = cfg.get("printer_name", "").strip()
    if not printer:
        return jsonify({
            "ok": False,
            "error": "No printer selected. Open Settings and choose a CUPS printer."
        }), 400

    html = build_print_html(codes, cfg)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
        tf.write(html)
        temp_path = tf.name

    try:
        cmd = ["lp", "-d", printer, "-o", "fit-to-page", temp_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

        if result.returncode != 0:
            return jsonify({
                "ok": False,
                "error": (result.stderr or result.stdout or "Printing failed.").strip()
            }), 500

        return jsonify({
            "ok": True,
            "message": result.stdout.strip() or f"Sent {len(codes)} vouchers to {printer}."
        })
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

@app.route("/printable", methods=["POST"])
@login_required
def printable():
    cfg = load_config()
    raw = request.form.get("codes", "")
    codes = clean_codes(raw)
    html = build_print_html(codes, cfg)
    return html

if __name__ == "__main__":
    cfg = load_config()
    app.run(host="0.0.0.0", port=int(cfg.get("port", 5000)), debug=False)
