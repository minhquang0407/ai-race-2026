import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
from pydantic import BaseModel, Field
from typing import List
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn

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

# 3. Sử dụng lm-format-enforcer để ép mô hình sinh JSON theo schema
parser = JsonSchemaParser(MedicalRecord.model_json_schema())
prefix_function = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)

# 4. Kiểm thử với một câu lâm sàng
clinical_text = "Bệnh nhân nam 45 tuổi có tiền sử đái tháo đường tuýp 2, nay vào viện vì đau tức ngực trái. Bác sĩ chỉ định dùng Aspirin."

prompt = f"Bạn là một chuyên gia y khoa. Hãy trích xuất các thực thể y tế (BỆNH, TRIỆU_CHỨNG, THUỐC) từ câu sau và trả về ĐÚNG định dạng JSON.\nCâu lâm sàng: {clinical_text}\nJSON Output:\n"

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

print("\nĐang xử lý suy luận...")
with torch.no_grad():
    output_ids = model.generate(
        **inputs,
        max_new_tokens=512,
        prefix_allowed_tokens_fn=prefix_function,
        pad_token_id=tokenizer.eos_token_id
    )

# Trích xuất phần output mới sinh ra
generated_text = tokenizer.decode(output_ids[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)

print("\n=== KẾT QUẢ TRÍCH XUẤT (JSON) ===")
print(generated_text)
