import os
from flask import Flask, render_template

from routes.scan_routes import scan_bp
from routes.verify_routes import verify_bp
from routes.dashboard_routes import dashboard_bp
from routes.history_routes import history_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(scan_bp)
app.register_blueprint(verify_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(history_bp)


@app.route("/")
def home():
    """Main landing page"""
    return render_template("index.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("result.html", error="Page not found."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("result.html", error="Something went wrong on our end. Please try again."), 500


if __name__ == "__main__":
    # Local development only. On Render, gunicorn runs this via the Procfile.
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)