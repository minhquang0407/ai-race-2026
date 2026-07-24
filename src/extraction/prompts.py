"""Prompt templates for chunk-level medical entity extraction."""

from __future__ import annotations

from .schema import AssertionType, EntityType


ENTITY_TYPE_VALUES = [entity_type.value for entity_type in EntityType]
ASSERTION_VALUES = [assertion.value for assertion in AssertionType]


def build_extraction_prompt(chunk_text: str) -> str:
    """Build a strict Vietnamese prompt for one text chunk."""

    entity_types = ", ".join(f"`{value}`" for value in ENTITY_TYPE_VALUES)
    assertions = ", ".join(f"`{value}`" for value in ASSERTION_VALUES)
    return f"""Bạn là hệ thống trích xuất thực thể y khoa tiếng Việt.

Nhiệm vụ: đọc duy nhất đoạn CHUNK bên dưới và trả về JSON đúng schema.

Quy tắc bắt buộc:
- Chỉ trích xuất các type hợp lệ: {entity_types}.
- `assertions` chỉ được dùng các giá trị: {assertions}.
- Nếu không có assertion đặc biệt, dùng `assertions: []`.
- Luôn để `candidates: []`; không tự đoán ICD-10/RxNorm.
- `position` là tọa độ ký tự LOCAL trong CHUNK theo dạng half-open `[start, end)`.
- `text` phải là chuỗi xuất hiện nguyên văn trong CHUNK.
- Chỉ trả về JSON, không giải thích thêm.

Gợi ý assertion:
- Có từ phủ định như "không", "phủ nhận", "chưa ghi nhận", "âm tính" -> `isNegated`.
- Có "tiền sử", "từng", "đã dùng", "trước nhập viện" -> `isHistorical`.
- Có "bố", "mẹ", "anh", "chị", "em", "gia đình", "người thân" -> `isFamily`.

Ví dụ ngắn:
CHUNK: "Bệnh nhân có tiền sử hen suyễn, hiện không ho."
JSON:
{{
  "entities": [
    {{"text": "hen suyễn", "position": [23, 32], "type": "CHẨN_ĐOÁN", "assertions": ["isHistorical"], "candidates": []}},
    {{"text": "ho", "position": [45, 47], "type": "TRIỆU_CHỨNG", "assertions": ["isNegated"], "candidates": []}}
  ]
}}

CHUNK:
{chunk_text}

JSON:
"""


__all__ = ["ASSERTION_VALUES", "ENTITY_TYPE_VALUES", "build_extraction_prompt"]
