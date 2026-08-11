from flask import Flask, request, jsonify
import os

from database import execute

app = Flask(__name__)


@app.route("/")
def home():
    return "RAJUL MOVIES BOT RUNNING"


@app.route("/payhero/callback", methods=["POST"])
def payhero_callback():

    data = request.get_json(silent=True) or {}

    print("========== PAYHERO CALLBACK ==========", flush=True)
    print("CALLBACK DATA:", data, flush=True)

    reference = (
        data.get("external_reference")
        or data.get("reference")
        or ""
    )

    status = str(
        data.get("status")
        or data.get("payment_status")
        or ""
    ).upper()

    print("REFERENCE:", reference, flush=True)
    print("STATUS:", status, flush=True)

    if status in ("SUCCESS", "TRUE", "PAID", "COMPLETED"):

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

        print("PAYMENT MARKED PAID:", reference, flush=True)

    return jsonify({"success": True}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
