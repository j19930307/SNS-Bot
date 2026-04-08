import base64
import json


def base64_decode(key: str) -> dict:
    """Decode a base64-encoded JSON string into a dict."""
    decoded_bytes = base64.b64decode(key)
    decoded_string = decoded_bytes.decode("utf-8")
    return json.loads(decoded_string)