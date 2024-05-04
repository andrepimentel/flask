import hashlib
import os

from google_auth_oauthlib.flow import Flow
from .secret import Secret

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

_CLIENT_SECRETS_PATH = "cliente.json"
_SCOPE = "https://www.googleapis.com/auth/adwords"
_SERVER = "https://flask-production-81a2.up.railway.app/"
_PORT = 5000
_REDIRECT_URI = "https://flask-production-81a2.up.railway.app/oauth2callback"

def authorize():
    flow = Flow.from_client_secrets_file(_CLIENT_SECRETS_PATH, scopes=[_SCOPE])
    flow.redirect_uri = _REDIRECT_URI

    # Create an anti-forgery state token as described here:
    # https://developers.google.com/identity/protocols/OpenIDConnect#createxsrftoken
    passthrough_val = hashlib.sha256(os.urandom(1024)).hexdigest()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        state=passthrough_val,
        prompt="consent",
        include_granted_scopes="true",
    )

    return {"authorization_url": authorization_url, "passthrough_val": passthrough_val}   

def oauth2callback(passthrough_val, state, code, token):
    if passthrough_val != state:
        message = "State token tá errado"
        raise ValueError(message)

    flow = Flow.from_client_secrets_file(_CLIENT_SECRETS_PATH, scopes=[_SCOPE])
    flow.redirect_uri = _REDIRECT_URI
    flow.fetch_token(code=code)
    refresh_token = flow.credentials.refresh_token
    print(f"\nYour refresh token is: {refresh_token}\n")
    print(
        "Add your refresh token to your client library configuration as "
        "described here: "
        "https://developers.google.com/google-ads/api/docs/client-libs/python/configuration"
    )
       
    secret = Secret(token)
    secret.create_secret_version(refresh_token)