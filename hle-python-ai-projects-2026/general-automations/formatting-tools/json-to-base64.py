import base64
import json


def json_to_base64(json_data):
    # Convert dictionary to a JSON string
    json_string = json.dumps(json_data)
    
    # Encode the string to bytes, then to base64
    base64_bytes = base64.b64encode(json_string.encode('utf-8'))
    
    # Convert base64 bytes back to string
    base64_string = base64_bytes.decode('utf-8')
    
    return base64_string

# Example usage
if __name__ == "__main__":
    sample_json = {
    "client_id": "client_id_value",
    "client_secret": "client_secret_value",
    "refresh_token": "refresh_token_value"
}

    base64_result = json_to_base64(sample_json)
    print("Base64 Encoded JSON:")
    print(base64_result)
