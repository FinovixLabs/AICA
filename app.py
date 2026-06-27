from flask import Flask, g, jsonify, send_from_directory
from flask_cors import CORS

from config import CORS_ORIGINS, DEBUG
from db import _pool
from routes.clients import api_bp, auth_bp, client_bp, filing_bp, notice_bp


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")

    CORS(app, origins=CORS_ORIGINS)

    for bp in (api_bp, auth_bp, client_bp, filing_bp, notice_bp):
        app.register_blueprint(bp)

    @app.before_request
    def open_db():
        g.db = _pool.getconn()

    @app.teardown_request
    def close_db(exc):
        conn = g.pop("db", None)
        if conn is None:
            return
        # Always finalize the transaction before returning the connection to the
        # pool. Otherwise read requests leave it "idle in transaction" and the
        # next request inherits a stale transaction, so its writes never persist.
        try:
            if exc is None:
                conn.commit()
            else:
                conn.rollback()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        _pool.putconn(conn)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder or "static", "index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG, port=5000)
