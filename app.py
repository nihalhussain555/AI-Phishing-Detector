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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
