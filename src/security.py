from hmac import compare_digest
import os

def api_key_check(request):
    api_key = request.json.get("api_key")
    if not api_key:
        return {"message": "Please provide an API key"}, 400
    # Check if API key is correct and valid
    local_key = os.getenv('AIPROXY_KEY') # Get API Key
    if local_key and compare_digest(local_key, api_key):
        return True
    else:
        return {"message": "The provided API key is not valid"}, 403
