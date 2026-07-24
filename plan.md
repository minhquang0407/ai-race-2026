# KẾ HOẠCH TRIỂN KHAI DỰ ÁN AI RACE 2026

Dưới đây là kế hoạch chi tiết từng bước (Step-by-step) để lập trình hệ thống. Chúng ta sẽ áp dụng phương pháp phát triển Agile: làm đến đâu, kiểm thử (test) đến đó, và check-off `[x]` sau khi hoàn thành.

---

## 📍 PHASE 1: CHUẨN HÓA DỮ LIỆU & TIỀN XỬ LÝ (PRE-PROCESSING)
**Mục tiêu:** Xử lý văn bản đầu vào dài thành các khối ngữ nghĩa (Semantic Chunks) và tracking vị trí (Offset) để đảm bảo đếm đúng 100% tọa độ `position` (Tránh phạt Word Error Rate).

- [x] **1.1. Cập nhật Schema chuẩn:** Định nghĩa lại `pydantic` models trong `src/extraction/schema.py` khớp 100% với yêu cầu `quydinh.md` (đặc biệt là biến đổi `assertions` thành List và `position` thành tọa độ thực).
- [x] **1.2. Semantic Chunking:** Viết script `src/extraction/chunking.py` sử dụng regex (hoặc `spaCy`/`underthesea`) để tách câu văn bản y khoa, đảm bảo không cắt ngang từ.
- [x] **1.3. Offset Tracking:** Đảm bảo hàm Chunking có khả năng tính toán độ lệch (offset) để phục vụ cho việc ánh xạ (Mapping) ngược lại tọa độ Global sau này.

**Checkpoint Phase 1:** Hoàn thành schema, chunking, validation và test. Lệnh kiểm thử: `python -m pytest -q` → `18 passed in 0.31s`.

---

## 📍 PHASE 2: TRÍCH XUẤT THỰC THỂ BẰNG LLM (NER & ASSERTION)
**Mục tiêu:** Chạy suy luận cục bộ (Local Inference) trên từng chunk và hợp nhất JSON.

- [x] **2.1. Tích hợp Pipeline:** Tạo file `src/extraction/llm_inference.py`, đóng gói mô hình `Qwen2.5-7B` với `lm-format-enforcer`.
- [x] **2.2. Batch Processing:** Thiết kế hàm nội tiếp đưa list các chunk từ Phase 1 vào LLM và nhận về list các JSON cục bộ.
- [x] **2.3. Global Mapping & Deduplication:** Viết hàm tịnh tiến tọa độ (từ Local + Offset = Global), so khớp lại bằng chuỗi trích xuất (Assertion matching), và khử trùng lặp các thực thể bị cắt ngang.

**Checkpoint Phase 2:** Hoàn thành prompt, LLM wrapper, postprocess/correction, pipeline, fake-extractor tests. Lệnh kiểm thử: `python -m pytest -q` → `32 passed in 0.92s`.

---

## 📍 PHASE 3: ĐỒ THỊ Y KHOA TÔ-PÔ (PRAGMATIC GRAPH)
**Mục tiêu:** Nhập dữ liệu ICD-10/RxNorm vào cây đồ thị tĩnh để chuẩn bị cho bước cắt tỉa và chống "phạt nhân đôi".

- [x] **3.1. Xây dựng Cây Phân Cấp:** Cài đặt `src/postprocessing/graph_builder.py` để đọc file danh mục ICD-10 (hoặc giả lập trước vài node) và dựng Directed Rooted Tree bằng `NetworkX`.
- [x] **3.2. LCA & Wu-Palmer Similarity:** Bổ sung thuật toán tính khoảng cách Tổ tiên chung gần nhất (LCA) và độ sâu tương đối (Wu-Palmer).
- [x] **3.3. Rule-based Pruning (Trọng tài):** Viết logic kiểm tra: nếu dự đoán của mô hình ở Phase 2 vi phạm logic đồ thị (nhãn quá xa nhau), tiến hành chặt nhánh và ép nhãn về an toàn.

**Checkpoint Phase 3:** Hoàn thành graph builder bridge, PragmaticGraphPruner, entity-level ICD pruning và tests. Lệnh kiểm thử: `python -m pytest -q` → `38 passed in 0.69s`.

---

## 📍 PHASE 4: TÌM KIẾM HỖN HỢP (HYBRID RETRIEVAL)
**Mục tiêu:** Tìm kiếm candidate `ICD-10` và `RxNorm` cho các thực thể hợp lệ từ Phase 3.

- [x] **4.1. Sparse Retrieval (BM25):** Code `src/retrieval/bm25_search.py` để xử lý các từ viết tắt chuyên ngành.
- [x] **4.2. Dense Retrieval (SapBERT):** Code `src/retrieval/dense_search.py` (chạy CPU hoặc Vector DB nhẹ) để search theo ngữ nghĩa.
- [x] **4.3. Dynamic Thresholding:** Code logic kết hợp điểm (Ensemble Score) và cắt tỉa động những candidate có Margin Score vượt ngưỡng, bảo vệ điểm Jaccard.

**Checkpoint Phase 4:** Hoàn thành BM25/lexical retrieval, dense-search interface, dynamic thresholding, CandidateRetriever và tests. Lệnh kiểm thử: `python -m pytest -q` → `46 passed in 1.35s`.

---

## 📍 PHASE 5: LIÊN KẾT & KIỂM THỬ (PIPELINE INTEGRATION & TESTING)
**Mục tiêu:** Ghép nối các Phase thành một luồng (Pipeline) duy nhất từ Input -> Output.

- [x] **5.1. Main Pipeline:** Đóng gói toàn bộ luồng vào `main.py`. Đọc file text trong `test/input/` và tự động sinh file JSON trong thư mục `output/`.
- [x] **5.2. Jaccard & WER Tester:** Viết file `tests/test_metrics.py` giả lập công thức tính điểm của Ban tổ chức (có hàm trừ điểm phạt nhân đôi) để test nội bộ.
- [x] **5.3. Môi trường:** Đóng gói `Dockerfile` & kiểm tra lại `requirements.txt`.

**Checkpoint Phase 5:** Hoàn thành CLI end-to-end, fake extractor CI mode, output JSON writer, metrics nội bộ, Docker/requirements và integration tests. Lệnh kiểm thử: `python -m pytest -q` → `51 passed in 0.93s`. Smoke run: `python main.py --input-dir input --output-dir output --extractor fake --limit 2 --safe` → tạo `1.json`, `2.json`.

---

## 📍 PHASE 6: SUBMISSION VALIDATOR (KIỂM TRA OUTPUT TRƯỚC KHI NỘP)
**Mục tiêu:** Xây dựng bộ kiểm tra tự động để đảm bảo toàn bộ `output/*.json` hợp lệ theo quy định BTC trước khi nộp hoặc trước khi chạy scoring nội bộ.

- [x] **6.1. Schema Validator:** Tạo `src/evaluation/submission_validator.py` để kiểm tra mỗi file output là JSON array, mỗi entity có đủ 5 trường `text`, `position`, `type`, `assertions`, `candidates`.
- [x] **6.2. Span Validator:** Đối chiếu từng entity với file input tương ứng bằng quy tắc bắt buộc `source_text[start:end] == text`, phát hiện lỗi WER/position hallucination.
- [x] **6.3. Enum & Field Rules:** Kiểm tra `type` chỉ thuộc 5 nhãn hợp lệ, `assertions` chỉ thuộc `isNegated`, `isFamily`, `isHistorical`, và `candidates` chỉ được có giá trị với `CHẨN_ĐOÁN`/`THUỐC`.
- [x] **6.4. Batch Report:** Tạo báo cáo tổng hợp số file hợp lệ/lỗi, số entity lỗi, danh sách lỗi theo file để debug nhanh.
- [x] **6.5. CLI Integration:** Thêm lệnh kiểm tra nhanh, ví dụ `python -m src.evaluation.submission_validator --input-dir input --output-dir output`.
- [x] **6.6. Tests:** Viết `tests/test_submission_validator.py` để kiểm tra các case: JSON sai format, thiếu field, sai enum, sai span, sai candidate rule và output hợp lệ.

**Checkpoint Phase 6:** Hoàn thành submission validator, batch report, CLI và tests. Lệnh kiểm thử: `python -m pytest -q` → `57 passed in 1.06s`. Validator run: `python -m src.evaluation.submission_validator --input-dir input --output-dir output` → `checked_files=100, valid_files=100, invalid_files=0, issues=0`.

---

## 📍 PHASE 7: REAL LLM SMOKE TEST (CHẠY THỬ MODEL THẬT)
**Mục tiêu:** Thay `FakeExtractor` bằng `LLMExtractor` để kiểm tra Qwen2.5-7B chạy thật end-to-end trên một số file nhỏ trước khi chạy toàn bộ 100 input.

- [ ] **7.1. Single-file Smoke Test:** Chạy `python main.py --input-dir input --output-dir output_llm --extractor llm --limit 1 --safe` và kiểm tra model load, generate, parse JSON thành công.
- [ ] **7.2. VRAM & Runtime Check:** Ghi nhận thời gian load model, thời gian xử lý mỗi chunk/file, mức VRAM/RAM sử dụng và lỗi OOM nếu có.
- [ ] **7.3. Prompt Debugging:** Kiểm tra output thật có đúng `type`, `assertions`, `text`, `position` không; nếu position hallucination nhiều thì điều chỉnh prompt hoặc chuyển sang chiến lược LLM trả `text` để code tự tìm span.
- [ ] **7.4. LLM Output Validator:** Chạy Phase 6 validator trên `output_llm/` để phát hiện lỗi format/span trước khi mở rộng batch.
- [ ] **7.5. Limited Batch Test:** Chạy thử 5-10 file bằng `--extractor llm --limit 10 --safe` sau khi single-file ổn định.

**Checkpoint Phase 7:** Hoàn thành khi LLM thật chạy được ít nhất 1-10 file, output parse được, validator báo lỗi rõ ràng, và có ghi nhận runtime/VRAM để quyết định cấu hình chạy toàn bộ.

---

## 📍 PHASE 8: REAL KNOWLEDGE DATA (THAY DATA ICD/RXNORM MẪU)
**Mục tiêu:** Thay `icd10_sample.csv` và `rxnorm_sample.csv` bằng dữ liệu thật để retrieval/candidates có ý nghĩa khi nộp bài.

- [ ] **8.1. ICD-10 Full Data:** Tìm/tải nguồn ICD-10 phù hợp với quy định BTC, chuẩn hóa thành schema `code,name,parent_code,level` hoặc bổ sung loader suy luận parent.
- [ ] **8.2. RxNorm Full Data:** Tải/chuẩn hóa RxNorm concept names và synonyms thành schema `rxcui,name,tty,synonyms`.
- [ ] **8.3. Configurable Data Paths:** Thêm cấu hình/CLI cho `CandidateRetriever` để chọn sample data hoặc full data, ví dụ `--icd-path`, `--rxnorm-path`.
- [ ] **8.4. Index Build & Cache:** Build index processed nếu data lớn, lưu vào `data/processed/` để lần chạy sau không phải parse lại toàn bộ raw data.
- [ ] **8.5. Retrieval Quality Check:** Tạo test/smoke query cho bệnh và thuốc phổ biến để kiểm tra top candidates hợp lý.

**Checkpoint Phase 8:** Hoàn thành khi pipeline dùng được ICD/RxNorm full data, retrieval trả candidate thật, không vỡ RAM, và test retrieval/smoke query pass.

---

## 📍 PHASE 9: TYPE GUARDRAIL & ERROR ANALYSIS
**Mục tiêu:** Giảm lỗi sai `type`, vì đây là lỗi bị phạt nặng nhất theo cơ chế double penalty.

- [ ] **9.1. Type Guardrail Module:** Tạo `src/postprocessing/type_guardrail.py` để kiểm tra type LLM bằng evidence từ ICD/RxNorm retrieval và regex xét nghiệm.
- [ ] **9.2. High-confidence Correction Only:** Chỉ sửa type khi chênh lệch evidence rất lớn, ví dụ RxNorm score cao nhưng ICD score gần 0 thì `CHẨN_ĐOÁN -> THUỐC`.
- [ ] **9.3. Lab Pattern Rules:** Nhận diện pattern `số + đơn vị`, `dương tính/âm tính`, `HbA1c`, `glucose`, `X-quang`, `CT`, `MRI` để hỗ trợ `TÊN_XÉT_NGHIỆM` và `KẾT_QUẢ_XÉT_NGHIỆM`.
- [ ] **9.4. Error Report:** Tạo báo cáo các entity bị guardrail sửa/drop để review thủ công.
- [ ] **9.5. Regression Tests:** Thêm test đảm bảo guardrail không sửa bừa các case mơ hồ.

**Checkpoint Phase 9:** Hoàn thành khi guardrail giảm lỗi type trong smoke output mà không làm tăng lỗi false positive đáng kể, và full test suite pass.

---

## 📍 PHASE 10: OPTIONAL QLORA UPGRADE
**Mục tiêu:** Nếu baseline LLM zero/few-shot chưa đủ ổn định, dùng synthetic/pseudo-label data để fine-tune QLoRA nhằm cải thiện NER, `type`, `assertions` và format discipline.

- [ ] **10.1. Synthetic Data Generator:** Tạo dữ liệu câu y khoa tiếng Việt có nhãn JSON trung gian, tập trung vào phủ định, tiền sử, người nhà, thuốc, xét nghiệm.
- [ ] **10.2. Pseudo-label Filtering:** Dùng validator để lọc pseudo-label có span chính xác và schema hợp lệ.
- [ ] **10.3. QLoRA Training Script:** Tạo script train adapter cho Qwen2.5-7B-Instruct 4-bit, không học candidate ID.
- [ ] **10.4. Adapter Inference:** Cho `LLMExtractor` load LoRA adapter tùy chọn.
- [ ] **10.5. Before/After Evaluation:** So sánh zero-shot vs QLoRA bằng validator, runtime và sample metrics nội bộ.

**Checkpoint Phase 10:** Hoàn thành khi adapter QLoRA chạy được offline, cải thiện type/assertion trên bộ smoke test, và không phá schema/position validation.
