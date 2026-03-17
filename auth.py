# ============================================================
# AUTH - Add these to your api3.py
# ============================================================
# 1. Add these imports at the top of api3.py:
#
#    import secrets
#    from fastapi import Header
#
# 2. Add this block after your existing imports/setup:
# ============================================================

import secrets
from fastapi import Header

# ── Hardcoded users (username: password) ─────────────────────────────────────
USERS = {
    "admin":   "admin123",
    "demo":    "demo123",
}

# ── Active tokens store (token -> username) ───────────────────────────────────
# In production, use Redis or a database instead
active_tokens: dict = {}


# ── Request model ─────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: POST /api/login
# login.html sends: { username, password }
# Returns: { success, token, username }
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/login")
def login(request: LoginRequest):
    """Validate credentials and return a session token."""
    expected_password = USERS.get(request.username)

    if not expected_password or expected_password != request.password:
        return {
            "success": False,
            "error": "Incorrect username or password."
        }

    # Generate a secure random token
    token = secrets.token_hex(32)
    active_tokens[token] = request.username

    logger.info(f"✅ User '{request.username}' logged in")
    return {
        "success": True,
        "token": token,
        "username": request.username
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: POST /api/logout
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/logout")
def logout(authorization: str = Header(None)):
    """Invalidate a session token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if token in active_tokens:
            user = active_tokens.pop(token)
            logger.info(f"User '{user}' logged out")

    return {"success": True, "message": "Logged out"}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: GET /api/verify
# Called by index.html on load to check if token is still valid
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/verify")
def verify_token(authorization: str = Header(None)):
    """Check if a token is valid."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"success": False, "error": "No token provided"}

    token = authorization.split(" ")[1]
    username = active_tokens.get(token)

    if not username:
        return {"success": False, "error": "Invalid or expired token"}

    return {"success": True, "username": username}
