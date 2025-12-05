import sys
try:
    import app.services.auth
    print("Import app.services.auth SUCCESS")
    import app.repositories.user
    print("Import app.repositories.user SUCCESS")
    import app.repositories.tenant
    print("Import app.repositories.tenant SUCCESS")
except Exception as e:
    print(f"Import FAILED: {e}")
    sys.exit(1)
