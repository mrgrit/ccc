"""6bq5 의 backend/main.py 에 admin_auth middleware 를 idempotent 하게 주입.

deploy.sh patch-auth 가 1 회 호출.

주입 내용:
  1. `from .admin_auth import verify_admin_token` import
  2. `app = FastAPI(...)` 다음에 dependency 등록

이미 적용된 경우 (X-Admin-Token 단어 존재) skip.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


MARKER = "# === eg-admin-auth (auto-injected) ==="
INJECT_BLOCK = f"""
{MARKER}
from .admin_auth import verify_admin_token
from fastapi import Depends

@app.middleware("http")
async def admin_auth_middleware(request, call_next):
    try:
        await verify_admin_token(request)
    except Exception as e:
        from fastapi.responses import JSONResponse
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            return JSONResponse(status_code=e.status_code, content={{"detail": e.detail}})
        raise
    return await call_next(request)
{MARKER}
"""


def inject(path: Path) -> None:
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"[skip] 이미 주입됨: {path}")
        return

    # app = FastAPI(...) 라인 찾고 그 다음에 삽입
    m = re.search(r"^app\s*=\s*FastAPI\(.*?\)\s*\n", src, flags=re.MULTILINE | re.DOTALL)
    if not m:
        raise SystemExit("FastAPI() 인스턴스 생성 라인 찾기 실패")

    pos = m.end()
    new = src[:pos] + INJECT_BLOCK + src[pos:]
    path.write_text(new, encoding="utf-8")
    print(f"[OK] injected: {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용: inject_auth.py <path/to/backend/main.py>", file=sys.stderr)
        sys.exit(2)
    inject(Path(sys.argv[1]))
