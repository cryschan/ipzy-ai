"""
CamelCase 변환 미들웨어
Python 내부는 snake_case 유지, API 응답만 camelCase로 변환
"""

import json
import logging
import hashlib
from typing import Any, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)


def snake_to_camel(snake_str: str) -> str:
    """snake_case를 camelCase로 변환"""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def convert_keys_to_camel(data: Any) -> Any:
    """재귀적으로 모든 키를 camelCase로 변환"""
    if isinstance(data, dict):
        return {snake_to_camel(k): convert_keys_to_camel(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_keys_to_camel(item) for item in data]
    return data


class CamelCaseMiddleware(BaseHTTPMiddleware):
    """모든 JSON 응답을 camelCase로 변환하는 미들웨어"""

    @staticmethod
    def _header_name(raw_name: bytes) -> str:
        return raw_name.decode("latin-1").lower()

    def _copy_headers(
        self,
        source: Response,
        destination: Response,
        *,
        keep_etag: bool,
        new_body: bytes | None,
    ) -> None:
        """
        원본 응답의 헤더를 목적 응답에 보존합니다.

        - content-length/content-type은 목적 응답이 새로 계산/설정하도록 제외합니다.
        - 본문이 변경된 경우(etag가 있으면) 기본적으로 제거하며, keep_etag=True이면 재계산합니다.
        - raw_headers 기반으로 복사하여 Set-Cookie 같은 중복 헤더도 보존합니다.
        """
        drop = {"content-length", "content-type"}
        had_etag = False

        preserved = []
        for name, value in getattr(source, "raw_headers", []):
            lname = self._header_name(name)
            if lname in drop:
                continue
            if lname == "etag":
                had_etag = True
                continue
            preserved.append((name, value))

        # 목적 응답에 기본 헤더(content-type/content-length 등)를 먼저 둔 뒤, 보존 헤더를 앞에 붙입니다.
        destination.raw_headers = preserved + destination.raw_headers

        if keep_etag and had_etag and new_body is not None:
            digest = hashlib.sha256(new_body).hexdigest()
            destination.headers["etag"] = f"\"{digest}\""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        response: Response = await call_next(request)

        # JSON 응답만 변환
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # StreamingResponse 처리
        if isinstance(response, StreamingResponse):
            # 응답 본문 읽기
            body_parts = []
            async for chunk in response.body_iterator:
                body_parts.append(chunk)
            body = b"".join(body_parts)
        else:
            body = response.body

        try:
            # JSON 파싱
            data = json.loads(body)

            # camelCase로 변환
            camel_data = convert_keys_to_camel(data)

            # 새 응답 생성
            new_body = json.dumps(camel_data, ensure_ascii=False).encode("utf-8")

            new_response = Response(
                content=new_body,
                status_code=response.status_code,
                media_type="application/json",
                background=response.background,
            )
            self._copy_headers(
                response,
                new_response,
                keep_etag=True,
                new_body=new_body,
            )
            return new_response
        except Exception as e:
            # JSON 파싱 실패 시 원본 반환
            logger.warning("Failed to convert response to camelCase: %s", e)
            passthrough = Response(
                content=body,
                status_code=response.status_code,
                media_type=content_type,
                background=response.background,
            )
            self._copy_headers(
                response,
                passthrough,
                keep_etag=True,
                new_body=body,
            )
            return passthrough
