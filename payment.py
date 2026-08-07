import requests
import uuid

from config import (
    PAYHERO_BASE_URL,
    PAYHERO_USERNAME,
    PAYHERO_PASSWORD,
    PAYHERO_ACCOUNT_ID,
    PAYHERO_CHANNEL_ID,
    CALLBACK_URL,
)

def auth():
    return (PAYHERO_USERNAME, PAYHERO_PASSWORD)


def reference():
    return f"RM-{uuid.uuid4().hex[:10]}"


def normalize_phone(phone: str):
    phone = phone.strip().replace(" ", "")

    if phone.startswith("+254"):
        return "254" + phone[4:]

    if phone.startswith("254"):
        return phone

    if phone.startswith("0"):
        return "254" + phone[1:]

    return phone
def send_stk_push(phone, amount, reference_id=None):
    phone = normalize_phone(phone)

    if reference_id is None:
        reference_id = reference()

    payload = {
        "account_id": PAYHERO_ACCOUNT_ID,
        "channel_id": PAYHERO_CHANNEL_ID,
        "phone_number": phone,
        "amount": int(amount),
        "provider": "m-pesa",
        "external_reference": reference_id,
        "callback_url": CALLBACK_URL
    }

    try:
        print("PAYLOAD:", payload)
        response = requests.post(
            PAYHERO_BASE_URL,
            json=payload,
            auth=auth(),
            timeout=30
        )

        data = response.json()

        print("Status:", response.status_code)
        print("Response:", data)

        if response.status_code in (200, 201):
            return (
                True,
                "✅ STK Push sent successfully.",
                data
            )

        return (
            False,
            data.get("message", "Payment request failed."),
            data
        )

    except Exception as e:
        return (
            False,
            str(e),
            {}
        )




