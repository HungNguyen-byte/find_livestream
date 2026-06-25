# youtube_token.py
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json", SCOPES
)

credentials = flow.run_local_server(port=0)

# Lưu token để dùng sau
with open("token.pickle", "wb") as f:
    pickle.dump(credentials, f)

print("✅ Đăng nhập thành công và đã lưu token!")