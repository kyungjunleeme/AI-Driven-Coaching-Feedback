from __future__ import annotations
import os, time, json, requests, jwt
from typing import Dict, Any, Optional, Callable
from fastapi import Depends, HTTPException, status, Request
from jwt import algorithms

COGNITO_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")  # e.g., ap-northeast-2_abc123
COGNITO_AUDIENCE = os.getenv("COGNITO_AUDIENCE")  # app client id or custom aud
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "0") == "1"

def _issuer() -> str:
    if not COGNITO_USER_POOL_ID:
        raise RuntimeError("COGNITO_USER_POOL_ID not set")
    return f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"

def _jwks_url() -> str:
    return _issuer() + "/.well-known/jwks.json"

class JWKSCache:
    def __init__(self, url: str, ttl: int = 3600):
        self.url = url
        self.ttl = ttl
        self.cache: Dict[str, Any] = {}
        self.exp = 0

    def get(self):
        now = int(time.time())
        if now >= self.exp:
            resp = requests.get(self.url, timeout=5)
            resp.raise_for_status()
            self.cache = resp.json()
            self.exp = now + self.ttl
        return self.cache

_jwks_cache = JWKSCache("dummy")  # will be replaced on first use

def _decode_jwt(token: str) -> Dict[str, Any]:
    global _jwks_cache
    if _jwks_cache.url == "dummy":
        _jwks_cache = JWKSCache(_jwks_url())

    jwks = _jwks_cache.get()
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="kid not found")
    public_key = algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

    opts = {"verify_aud": COGNITO_AUDIENCE is not None}
    decoded = jwt.decode(
        token,
        key=public_key,
        algorithms=["RS256"],
        audience=COGNITO_AUDIENCE,
        issuer=_issuer(),
        options=opts
    )
    # basic token_use sanity
    tu = decoded.get("token_use")
    if tu not in ("id", "access"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token_use")
    return decoded

def cognito_auth_dependency(scopes: Optional[list[str]] = None) -> Callable:
    async def verifier(request: Request) -> Dict[str, Any]:
        if not AUTH_REQUIRED:
            return {"sub": "anonymous"}
        auth = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth or not auth.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
        token = auth.split(" ", 1)[1].strip()
        claims = _decode_jwt(token)
        # optional scope check
        if scopes:
            token_scopes = set((claims.get("scope") or "").split())
            if not set(scopes).issubset(token_scopes):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient scope")
        return claims
    return verifier
