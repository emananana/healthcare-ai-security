"""Eman's shared-demo wrapper, separate from teammate authentication modules.

One process only. Basic auth protects the entire research console over HTTPS.
This is a shared team login, not individual customer authentication.
"""
import base64
import binascii
import secrets
from collections import deque
from time import monotonic

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TeamAccessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, password, requests_per_minute=10):
        super().__init__(app)
        self.password = password
        self.requests_per_minute = requests_per_minute
        self.attempts = deque()

    async def dispatch(self, request, call_next):
        if request.url.path == '/healthz':
            return await call_next(request)
        try:
            scheme, token = request.headers.get('authorization', '').split(' ', 1)
            if scheme.lower() != 'basic':
                raise ValueError()
            username, password = base64.b64decode(token, validate=True).decode().split(':', 1)
            valid = secrets.compare_digest(username.encode(), b'cometcare') and secrets.compare_digest(
                password.encode(), self.password.encode())
        except (ValueError, UnicodeError, binascii.Error):
            valid = False
        if not valid:
            return JSONResponse({'detail': 'Team login required.'}, status_code=401,
                                headers={'WWW-Authenticate': 'Basic realm="CometCare team", charset="UTF-8"',
                                         'Cache-Control': 'no-store'})
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            # Block cross-site browser submissions with ambient Basic credentials.
            origin = request.headers.get('origin')
            from urllib.parse import urlsplit
            if origin and urlsplit(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Cross-site requests are not allowed.'}, status_code=403)
        if request.method == 'POST' and request.url.path in {'/api/chat', '/api/attacks'}:
            now = monotonic()
            while self.attempts and now - self.attempts[0] >= 60:
                self.attempts.popleft()
            if len(self.attempts) >= self.requests_per_minute:
                return JSONResponse({'detail': 'Team demo limit reached (10 actions/minute). Please wait.'},
                                    status_code=429, headers={'Retry-After': '60'})
            self.attempts.append(now)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response
