import os
import google_crc32c

from google.oauth2 import id_token
from google.auth.transport import requests
from google.cloud import secretmanager

_CLIENT_ID = "286558389986-q4mvp792a8lltd7kqlka4560dm6j5b86.apps.googleusercontent.com"
_PROJECT_ID = "eng-braid-419916"
_PROJECT_NUMBER = "286558389986"

class Secret:

    def __init__(self, token): 
        ## Pega ID do token
        self.id = self.validade_token_get_id(token)
        self.client = secretmanager.SecretManagerServiceClient()

    def validade_token_get_id(self, token):
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), _CLIENT_ID)
            return idinfo['sub']
        except ValueError:
            pass

    def create_secret_version(self, refresh_token):
        ## Checa se o "secret" existe
        if self.does_secret_exist() is False:
            parent = f"projects/{_PROJECT_ID}"

            ## Se não, cria um
            self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": self.id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

        ## Cria o "secret"
        parent = client.secret_path(_PROJECT_ID, self.id)

        # Convert the string payload into a bytes. This step can be omitted if you
        # pass in bytes instead of a str for the payload argument.
        payload_bytes = refresh_token.encode("UTF-8")

        # Calculate payload checksum. Passing a checksum in add-version request
        # is optional.
        crc32c = google_crc32c.Checksum()
        crc32c.update(payload_bytes)

        # Add the secret version.
        self.client.add_secret_version(
            request={
                "parent": parent,
                "payload": {
                    "data": payload_bytes,
                    "data_crc32c": int(crc32c.hexdigest(), 16),
                },
            }
        )

    def does_secret_exist(self):
        parent = f"projects/{_PROJECT_ID}"

        # List all secrets.
        for secret in self.client.list_secrets(request={"parent": parent}):
            secret_name = f"projects/{_PROJECT_NUMBER}/secrets/{self.id}"
            if secret.name == secret_name:
                return True

        return False

    def get_secret_version(self):
        name = f"projects/{_PROJECT_ID}/secrets/{self.id}/versions/latest"

        # Access the secret version.
        response = self.client.access_secret_version(request={"name": name})

        # Verify payload checksum.
        crc32c = google_crc32c.Checksum()
        crc32c.update(response.payload.data)
        if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
            print("Data corruption detected.")
            return response

        # Print the secret payload.
        #
        # WARNING: Do not print the secret in a production environment - this
        # snippet is showing how to access the secret material.
        return response.payload.data.decode("UTF-8")