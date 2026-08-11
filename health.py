from flask import Flask, request, jsonify
import os

from database import execute

app = Flask(__name__)


@app.route("/")
def home():
    return "RAJUL MOVIES BOT RUNNING"


@app.route("/payhero/callback", methods=["POST"])
def payhero_callback():

    data = request.get_json(force=True) or {}

    print("PAYHERO CALLBACK:", data)

    reference = (
        data.get("external_reference")
        or data.get("reference")
        or ""
    )

    status = str(data.get("status") or "").upper()

    if status in ("SUCCESS", "TRUE", "PAID"):

        execute(
            """
            UPDATE orders
            SET status='PAID'
            WHERE checkout_id=?
            """,
            (reference,)
        )

        execute(
            """
            UPDATE wallet_topups
            SET status='PAID'
            WHERE reference=?
            """,
            (reference,)
        )

    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
