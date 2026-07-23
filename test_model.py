import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import outlines
from pydantic import BaseModel, Field
from typing import List

# 1. Định nghĩa JSON Schema cực kỳ chặt chẽ (để không bị phạt nhân đôi)
class Entity(BaseModel):
    text: str = Field(description="Đoạn text trích xuất từ câu")
    position: List[int] = Field(description="Vị trí [start, end] của text")
    type: str = Field(description="Chỉ được chọn 1 trong 3: BỆNH, TRIỆU_CHỨNG, THUỐC")
    candidates: List[str] = Field(description="Để trống ở bước này, hệ thống Retrieval sẽ điền sau")
    assertions: str = Field(description="Trạng thái: Hiện tại, Tiền sử, Gia đình, Phủ định")

class MedicalRecord(BaseModel):
    entities: List[Entity]

# 2. Tải Model Qwen2.5-7B với 4-bit Quantization (vừa vặn 12GB VRAM)
model_id = "Qwen/Qwen2.5-7B-Instruct"

# Cấu hình 4-bit để tiết kiệm RAM
quantization_config = transformers.BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

print("Đang tải model (lần đầu có thể mất vài phút)...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map="auto",
    quantization_config=quantization_config
)

# 3. Sử dụng Outlines để ép mô hình chỉ sinh ra JSON theo schema
generator = outlines.models.transformers(model, tokenizer)
json_generator = outlines.generate.json(generator, MedicalRecord)

# 4. Kiểm thử với một câu lâm sàng
clinical_text = "Bệnh nhân nam 45 tuổi có tiền sử đái tháo đường tuýp 2, nay vào viện vì đau tức ngực trái. Bác sĩ chỉ định dùng Aspirin."

prompt = f"""Bạn là một chuyên gia y khoa. Hãy trích xuất các thực thể y tế (BỆNH, TRIỆU_CHỨNG, THUỐC) từ câu sau và trả về ĐÚNG định dạng JSON.
Câu lâm sàng: {clinical_text}
"""

print("\nĐang xử lý suy luận...")
result = json_generator(prompt)

# In kết quả chuẩn JSON
print("\n=== KẾT QUẢ TRÍCH XUẤT (JSON) ===")
print(result.model_dump_json(indent=2))
