import socket


try:
    print("Looking up imap.gmail.com...")
    result = socket.gethostbyname("imap.gmail.com")
    print(f"✅ Success: {result}")
except Exception as e:
    print(f"❌ DNS lookup failed: {e}")
