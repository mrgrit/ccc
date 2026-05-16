"""eg-6v6 portal Admin 인증 middleware.

방식: 단일 admin token 기반. EG_ADMIN_TOKEN 환경변수로 설정.
모든 요청에 `X-Admin-Token` 헤더 필수. 검증 실패 시 403.

예외 경로:
- /api/health           — 모니터링용
- /assets, /            — frontend static
- /favicon.ico

deploy.sh patch-auth 가 6bq5 의 backend/main.py 에 inject.
"""
from __future__ import annotations

import os
from fastapi import Request, HTTPException

EG_ADMIN_TOKEN = os.environ.get("EG_ADMIN_TOKEN", "")

PUBLIC_PATHS = {"/api/health", "/", "/favicon.ico"}
PUBLIC_PREFIXES = ("/assets/", "/static/")


async def verify_admin_token(request: Request):
    if not EG_ADMIN_TOKEN:
        # 토큰 미설정 시 — 운영 사고 방지 위해 즉시 거부
        raise HTTPException(status_code=503, detail="EG_ADMIN_TOKEN 미설정 — 운영자 확인 필요")

    path = request.url.path
    if path in PUBLIC_PATHS:
        return
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return

    token = request.headers.get("X-Admin-Token", "")
    if token != EG_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin 토큰 검증 실패")
