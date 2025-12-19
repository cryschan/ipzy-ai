"""
CamelCase 변환 미들웨어
Python 내부는 snake_case 유지, API 응답만 camelCase로 변환
"""

import json
import logging
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

            return Response(
                content=new_body,
                status_code=response.status_code,
                media_type="application/json",
            )
        except Exception as e:
            # JSON 파싱 실패 시 원본 반환
            logger.warning("Failed to convert response to camelCase: %s", e)
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
