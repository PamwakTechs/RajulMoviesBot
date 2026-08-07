from flask import Flask, request, jsonify

from database import execute

app = Flask(__name__)


@app.route("/payhero/callback", methods=["POST"])
def payhero_callback():

    data = request.get_json(force=True)

    reference = (
        data.get("external_reference")
        or data.get("reference")
        or ""
    )

    status = str(
        data.get("status")
        or ""
    ).upper()

    if status == "SUCCESS" or status == "TRUE":

        # Movie payment
        execute(
            """
            UPDATE orders
            SET status='PAID'
            WHERE checkout_id=?
            """,
            (reference,)
        )

        # Wallet top up payment
        execute(
            """
            UPDATE wallet_topups
            SET status='PAID'
            WHERE reference=?
            """,
            (reference,)
        )

    return jsonify(
        {
            "success": True
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000
    )
