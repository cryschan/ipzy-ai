"""
스타일 매핑 모듈
퀴즈 답변(occasion + style)을 DB의 primary_style로 매핑합니다.
"""

from typing import Dict, Tuple, List


# (occasion, style) → [primary_style 리스트]
# 의류 스타일: hip_hop, minimalist, street, gorpcore, amekaji, cityboy
STYLE_MAPPING: Dict[Tuple[str, str], List[str]] = {
    # 회사 (work)
    ("work", "clean"): ["minimalist", "cityboy"],      # 회사 + 깔끔하게 → 미니멀, 시티보이
    ("work", "comfortable"): ["minimalist", "amekaji"], # 회사 + 편하게 → 미니멀, 아메카지
    ("work", "stylish"): ["cityboy", "minimalist"],     # 회사 + 멋있게 → 시티보이, 미니멀
    ("work", "hip"): ["street", "hip_hop"],             # 회사 + 힙하게 → 스트릿, 힙합

    # 데이트 (date)
    ("date", "clean"): ["minimalist", "cityboy"],       # 데이트 + 깔끔하게 → 미니멀, 시티보이
    ("date", "comfortable"): ["minimalist", "amekaji"], # 데이트 + 편하게 → 미니멀, 아메카지
    ("date", "stylish"): ["cityboy", "minimalist"],     # 데이트 + 멋있게 → 시티보이, 미니멀
    ("date", "hip"): ["street", "hip_hop"],             # 데이트 + 힙하게 → 스트릿, 힙합

    # 소개팅/모임 (meeting)
    ("meeting", "clean"): ["minimalist", "cityboy"],    # 모임 + 깔끔하게 → 미니멀, 시티보이
    ("meeting", "comfortable"): ["minimalist", "amekaji"], # 모임 + 편하게 → 미니멀, 아메카지
    ("meeting", "stylish"): ["cityboy", "minimalist"],  # 모임 + 멋있게 → 시티보이, 미니멀
    ("meeting", "hip"): ["street", "hip_hop"],          # 모임 + 힙하게 → 스트릿, 힙합

    # 외출 (outdoor)
    ("outdoor", "clean"): ["minimalist", "gorpcore"],   # 외출 + 깔끔하게 → 미니멀, 고프코어
    ("outdoor", "comfortable"): ["gorpcore", "street"], # 외출 + 편하게 → 고프코어, 스트릿
    ("outdoor", "stylish"): ["street", "cityboy"],      # 외출 + 멋있게 → 스트릿, 시티보이
    ("outdoor", "hip"): ["hip_hop", "street"],          # 외출 + 힙하게 → 힙합, 스트릿
}


# 기본 스타일 (매핑이 없을 경우)
DEFAULT_STYLES = ["minimalist", "street", "cityboy"]


def get_mapped_styles(occasion: str, style: str) -> List[str]:
    """
    occasion과 style 조합에 맞는 primary_style 리스트를 반환합니다.

    Args:
        occasion: 상황 (work, date, meeting, outdoor)
        style: 스타일 (clean, comfortable, stylish, hip)

    Returns:
        매핑된 primary_style 리스트 (예: ["minimalist"])
    """
    key = (occasion.lower(), style.lower())
    return STYLE_MAPPING.get(key, DEFAULT_STYLES.copy())


# 한글 매핑 (LLM 프롬프트용)
OCCASION_KR = {
    "work": "회사",
    "date": "데이트",
    "meeting": "소개팅/모임",
    "outdoor": "외출"
}

STYLE_KR = {
    "clean": "깔끔하게",
    "comfortable": "편하게",
    "stylish": "멋있게",
    "hip": "힙하게"
}

BODY_TYPE_KR = {
    "none": "체형 고민 없음",
    "chubby": "통통한 편",
    "thin": "마른 편",
    "height": "키 고민"
}


def format_for_llm(occasion: str, style: str, body_type: str) -> str:
    """
    LLM 프롬프트에 사용할 한글 설명을 생성합니다.

    Args:
        occasion: 상황
        style: 스타일
        body_type: 체형

    Returns:
        한글 설명 (예: "데이트에 멋있게 보이고 싶어요. 통통한 편이에요.")
    """
    occasion_kr = OCCASION_KR.get(occasion.lower(), occasion)
    style_kr = STYLE_KR.get(style.lower(), style)
    body_type_kr = BODY_TYPE_KR.get(body_type.lower(), body_type)

    return f"{occasion_kr}에 {style_kr} 보이고 싶어요. {body_type_kr}."
