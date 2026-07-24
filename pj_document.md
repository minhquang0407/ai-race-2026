Tài liệu dưới đây thiết kế kiến trúc hệ thống giải quyết bài toán Ontological Reasoning in Medical Knowledge Retrieval. Cấu trúc được chia làm hai giai đoạn đúng với định hướng nghiên cứu: **BASELINE** tập trung vào sự an toàn, chạy offline không cần dữ liệu huấn luyện có nhãn, tuân thủ chặt chẽ định dạng JSON và lách "hình phạt nhân đôi" bằng Constrained Decoding, Semantic Chunking, Dynamic Thresholding. Hướng **NÂNG CẤP** gồm Pragmatic Graph và QLoRA trên dữ liệu synthetic/pseudo-label nhằm cải thiện khả năng nhận diện `type`/`assertions` sau khi pipeline baseline đã ổn định.

---

## PROJECT DESIGN DOCUMENT: MEDICAL ONTOLOGICAL REASONING AI

**Mục tiêu:** Xây dựng hệ thống trích xuất và ánh xạ thực thể y khoa tuân thủ giới hạn phần cứng (SLM $\le$ 9B parameters) và tối ưu hóa hàm mục tiêu có chứa Double Penalty.

---

### PHẦN I: KIẾN TRÚC BASELINE (CORE PIPELINE)

Giai đoạn Baseline thiết lập một luồng xử lý (End-to-End) vững chắc, triệt tiêu sai số định dạng và tối ưu hóa độ chính xác (Precision) thay vì cố gắng mở rộng độ phủ (Recall) một cách rủi ro.

#### 1. Pha Trích xuất Định hướng (Joint NER & Assertion)

Thay vì sử dụng pipeline chia nhỏ dễ tích lũy sai số, hệ thống sử dụng một LLM cục bộ xử lý trọn gói trong một lượt quét.

* **Mô hình nền tảng:** `Qwen2.5-7B-Instruct` (Lượng hóa NF4/4-bit để vận hành mượt mà dưới giới hạn 12GB VRAM).
* **Chiến lược suy luận Baseline:** Dùng Zero-shot/Few-shot prompting trên từng semantic chunk. Ở baseline, mô hình chỉ sinh JSON trung gian gồm `text`, `position`, `type`, `assertions`, `candidates: []`; không bắt LLM tự đoán mã ICD-10/RxNorm.
* **Giải mã Ràng buộc (Constrained Decoding):** Sử dụng `lm-format-enforcer` áp đặt JSON Schema khắt khe. Trạng thái không gian từ vựng bị ép buộc chỉ sinh ra các key chuẩn như `text`, `position`, `type`, `candidates`, và `assertions`.

#### 2. Pha Tìm kiếm Ứng viên Lai (Hybrid Retrieval)

Nhận đầu vào là chuỗi `text` từ Pha 1, hệ thống truy xuất các mã ICD-10 và RxNorm tiềm năng nhất.

* **Sparse Retrieval (Truy vấn Thưa):** Sử dụng thuật toán BM25 nâng cao, tích hợp từ điển đồng nghĩa (Synonym Dictionary) để xử lý các từ viết tắt chuyên ngành y khoa tiếng Việt.
* **Dense Retrieval (Truy vấn Dày):** Sử dụng mô hình `SapBERT` (Bi-encoder đặc thù y sinh) nhúng toàn bộ ICD-10/RxNorm vào cơ sở dữ liệu vector trên RAM tĩnh, giải phóng GPU cho LLM.

#### 3. Pha Cắt tỉa Ngưỡng động (Dynamic Thresholding)

Đây là chốt chặn toán học để tối ưu hóa metric Jaccard Similarity: 

$$J = \frac{\vert{}GT \cap Pred\vert{}}{\vert{}GT \cup Pred\vert{}}$$

* **Cơ chế:** Thay vì trả về Top-$K$ ứng viên cố định, hệ thống tính toán khoảng cách vector (Cosine margin) giữa ứng viên thứ nhất $c_1$ và ứng viên thứ $i$ ($c_i$).
* **Hàm quyết định:** Nếu $Score(c_1) - Score(c_i) > \tau$ (với $\tau$ là ngưỡng động được tinh chỉnh), toàn bộ ứng viên từ $i$ trở đi sẽ bị gạch bỏ. Điều này giữ cho mẫu số của công thức Jaccard luôn ở mức tối thiểu, tối đa hóa điểm số trên tập test.

---

### PHẦN II (BẢN CẬP NHẬT): HƯỚNG NÂNG CẤP - PRAGMATIC GRAPH (KIẾN TRÚC TÔ-PÔ PHÂN CẤP)

*(Phần này thay thế hoàn toàn PHẦN II cũ, tập trung vào bản chất Cây phân cấp của ICD-10 và tái cấu trúc các thuật toán lấy cảm hứng từ luồng AD-GPS-RAG của người dùng)*

#### 1. Đồ thị hóa Chuẩn Y khoa thành Cây Phân cấp (Hierarchical Tree)

* **Khởi tạo:** Chuyển đổi toàn bộ danh mục ICD-10 thành một Cây phân cấp có hướng (từ Chương $\rightarrow$ Nhóm $\rightarrow$ Loại $\rightarrow$ Biến thể chi tiết) bằng thư viện `NetworkX`.
* **Tính chất:** Khác với một đồ thị mạng lưới thông thường, cấu trúc Cây đảm bảo mọi node đều có một đường đi duy nhất ngược về Node Gốc (Root). Toàn bộ thao tác chạy trên CPU RAM, đảm bảo tuyệt đối không gây tràn bộ nhớ VRAM khi Ban tổ chức chấm offline.

#### 2. Cắt tỉa Ứng viên bằng Tổ tiên chung gần nhất (LCA Pruning)

Đây là màng lọc toán học cốt lõi để bảo vệ điểm Jaccard Similarity (tối ưu hóa Precision, tránh phạt hình phạt nhân đôi).

* **Logic Toán học:** Khi Phase 2 (Hybrid Retrieval) trả về một tập ứng viên $C = \{c_1, c_2, c_3\}$, hệ thống thay vì duyệt toàn bộ đồ thị, sẽ sử dụng thuật toán **Lowest Common Ancestor (LCA)** để tính khoảng cách giữa hai node ứng viên bất kỳ (ví dụ $u$ và $v$):

$$\operatorname{dist}_{\mathcal{G}}(u, v) = \operatorname{depth}(u) + \operatorname{depth}(v) - 2 \cdot \operatorname{depth}(\operatorname{LCA}(u, v))$$

* **Thực thi:** Dựa trên hàm phạt $s_{\mathrm{ontology}} = \exp(-\lambda \operatorname{dist}_{\mathcal{G}})$. Nếu $\operatorname{dist}_{\mathcal{G}}$ lớn (tức LCA nằm tuốt trên Node gốc, đại diện cho 2 hệ cơ quan hoàn toàn khác nhau), $s_{\mathrm{ontology}}$ tiến về 0. Hệ thống ngay lập tức gạch bỏ ứng viên có xác suất vector thấp hơn, triệt tiêu hoàn toàn "ảo giác" của thuật toán Embedding.

#### 3. Lan truyền Lân cận (Graph-Neighborhood Expansion - Kế hoạch B)

*(Mô-đun này kế thừa trực tiếp tư duy gom tụ ID từ kiến trúc AD-GPS-RAG, chỉ kích hoạt khi Baseline cắt tỉa quá mạnh dẫn đến điểm Recall bị thấp).*

* **Logic Toán học:** Nếu mô hình LLM (Phase 1) chỉ trích xuất được khái niệm y khoa ở dạng mờ nhạt (ví dụ: chỉ map được vào node cha "Bệnh dạ dày" thay vì node lá "Trào ngược"), ta áp dụng thuật toán lan truyền kích hoạt từ node cha $\hat{v}_q$.
* **Thực thi:** Duyệt đồ thị từ $\hat{v}_q$ xuống các nút con trong bán kính $r=1$ (Level 4 của ICD-10). Đối chiếu chéo các ID của nhánh con này với các "Triệu chứng" được trích xuất trong cùng một ngữ cảnh (ví dụ: "ho", "ợ hơi"). Nếu khớp, hệ thống tự động "trôi" ứng viên xuống đúng node lá chi tiết nhất, tối đa hóa điểm tuyệt đối mà không cần dùng đến các mô hình GNN nặng nề.

#### 4. Đánh giá và Đề xuất cải tiến (Hướng Nâng Cấp Cuối Cùng)

* **Đồ thị hóa Chuẩn Y khoa thành Cây Phân cấp:** Rất chuẩn xác. ICD-10 bản chất là một Directed Rooted Tree. Việc dùng `NetworkX` và nạp toàn bộ vào RAM tĩnh (chỉ tốn vài chục MB) giúp hệ thống cực kỳ an toàn khỏi lỗi Out-of-Memory (OOM).
  * 💎 **Hướng nâng cấp (Weighted Edges - Trọng số cạnh):** Hiện tại, trên một cây thuần túy, mọi cạnh đều có độ dài bằng 1. Tuy nhiên, trong y khoa, khoảng cách ngữ nghĩa (Semantic Distance) giữa *Chương (Chapter)* $\rightarrow$ *Nhóm (Block)* lớn hơn rất nhiều so với khoảng cách từ *Loại (Category)* $\rightarrow$ *Biến thể chi tiết (Variant)*.
  $\Rightarrow$ **Giải pháp:** Thay vì gán trọng số cạnh = 1, hãy gán trọng số dựa trên **Information Content (IC)**. Các node lá càng sâu thì trọng số cạnh càng nhỏ (vì ý nghĩa càng tương đồng).

* **Cắt tỉa bằng Tổ tiên chung gần nhất (LCA Pruning):** Công thức $\operatorname{dist}_{\mathcal{G}}(u, v) = \operatorname{depth}(u) + \operatorname{depth}(v) - 2 \cdot \operatorname{depth}(\operatorname{LCA}(u, v))$ là khoảng cách đường đi ngắn nhất kinh điển trên cây. Hàm phạt $s_{\mathrm{ontology}}$ xử lý triệt để được "ảo giác vector".
  * 💎 **Hướng nâng cấp (Lin/Resnik Similarity thay vì Raw Depth):** Cây ICD-10 không cân bằng. Có những nhánh rất sâu, có nhánh lại rất nông.
  $\Rightarrow$ **Giải pháp (Hệ số Wu-Palmer hoặc Lin):** Sử dụng độ sâu của chính node LCA làm thước đo độ tin cậy. Hai node có LCA nằm càng sâu (gần node lá) thì càng liên quan.
  $$Sim_{WUP}(u, v) = \frac{2 \cdot \operatorname{depth}(\operatorname{LCA}(u, v))}{\operatorname{depth}(u) + \operatorname{depth}(v)}$$
  Hàm phạt khi đó sẽ là: $s_{\mathrm{ontology}} = \exp(-\lambda \cdot (1 - Sim_{WUP}(u, v)))$. Công thức này mượt mà hơn và không bị ảnh hưởng bởi độ sâu bất đối xứng của cây ICD-10.

* **Lan truyền Lân cận (Graph-Neighborhood Expansion):** Đây chính là "killer feature". Rất nhiều LLM nhỏ (7B) sẽ trích xuất ra các từ khóa chung chung. Việc dùng các Thực thể vệ tinh để ép ứng viên trôi xuống node con là một tư duy rất giống bác sĩ lâm sàng.
  * 💎 **Hướng nâng cấp (Probabilistic Child Routing):** Biến Kế hoạch B thành một quá trình **Markov Decision Process (MDP)** đơn giản trên cây. Để quyết định sẽ "trôi" xuống node con nào, ta tính toán phân phối xác suất dựa trên độ giao thoa (Overlap) giữa vector *Triệu chứng* có trong câu và bộ từ khóa của các node con:
  $$ P(v_{ci} | \text{Context}) = \frac{\exp( \text{Cosine}(E_{symptoms}, E_{v_{ci}}) / T )}{\sum_{j} \exp( \text{Cosine}(E_{symptoms}, E_{v_{cj}}) / T )} $$
  Nếu một node con có xác suất $P > 0.8$, thuật toán mới cho phép "trôi" xuống node đó (tăng Recall). Ngược lại sẽ giữ nguyên ở node cha để đảm bảo tính an toàn (giữ vững Precision).

Bản nâng cấp này mang đậm màu sắc của Ontological Reasoning và thể hiện được cái "chất" riêng (sử dụng toán học và cấu trúc dữ liệu rời rạc) để giải quyết bài toán NLP, thay vì chỉ nhồi nhét mọi thứ vào Neural Network.

---

### PHẦN III: QUY TRÌNH KIỂM THỬ VÀ ĐÁNH GIÁ (CI/CD & TESTING)

Để ngăn chặn việc mất quyền thi đấu do Ban tổ chức không chạy được Source Code.

* **Quản lý Môi trường:** Cung cấp `requirements.txt` và `Dockerfile` đóng gói môi trường chuẩn (CUDA 12.x, PyTorch), tách bạch rõ ràng giữa phân vùng chạy LLM (GPU) và phân vùng lưu trữ Graph/Vector (CPU RAM).
* **Unit Tests:** Xây dựng hệ thống test kiểm tra ngẫu nhiên 1000 chuỗi sinh từ LLM để đảm bảo tỷ lệ lỗi cấu trúc (JSON Parsing Error) luôn duy trì ở mức 0%, đồng thời giả lập hành vi phạt nhân đôi để tính toán trực tiếp điểm Jaccard mô phỏng trong quá trình huấn luyện.

---

### PHẦN BỔ SUNG: PIPELINE TIỀN XỬ LÝ VĂN BẢN DÀI (LONG-FORM DATA PIPELINE)

Quy trình trích xuất từ Giai đoạn 1 (Joint NER & Assertion) sẽ không đọc toàn bộ văn bản cùng lúc mà được đặt trong một luồng băm nhỏ và hợp nhất (Chunking & Merging) bao gồm 4 bước:

#### Bước 1: Băm nhỏ Ngữ nghĩa (Semantic Chunking & Offset Tracking)

* **Cơ chế:** Không chia văn bản một cách cơ học (hard cut) làm đứt gãy từ vựng. Sử dụng thư viện NLP (`spaCy` hoặc regex tiếng Việt) để tách bài viết dài thành các câu đơn hoặc đoạn văn nhỏ (khoảng 150 - 250 ký tự).
* **Lưu vết (Tracking):** Khởi tạo biến `offset` để ghi nhớ vị trí bắt đầu của mỗi đoạn chunk so với văn bản gốc ban đầu. Giữ nguyên tuyệt đối mọi ký tự khoảng trắng (\n, \t) trong quá trình cắt.

#### Bước 2: Suy luận Cục bộ (Local Inference)

* **Cơ chế:** Đưa từng đoạn chunk ngắn lần lượt qua mô hình LLM self-host ở chế độ Zero-shot/Few-shot hoặc mô hình QLoRA nếu Phase nâng cấp đã được huấn luyện.
* **Lợi ích:** Không gian ngữ cảnh ngắn ép LLM đếm chính xác hơn tọa độ `position` của thực thể bên trong đoạn chunk đó, triệt tiêu hiện tượng "quên lãng ở giữa" (Lost-in-the-Middle) và giới hạn Token sinh ra của file JSON. Tọa độ vẫn phải được kiểm chứng lại bằng `source_text[start:end] == text`.

#### Bước 3: Chiếu Tọa độ Toàn cục (Global Position Mapping)

* **Cơ chế:** Khi nhận JSON đầu ra từ Bước 2, hệ thống dùng thuật toán tịnh tiến để ánh xạ lại tọa độ cục bộ về tọa độ của văn bản gốc.
* **Công thức Toán học:**
Với mỗi thực thể được trích xuất trong một đoạn chunk:

$$\text{Position}_{\text{Global}} = [ \text{Start}_{\text{Local}} + \text{Offset}, \text{End}_{\text{Local}} + \text{Offset} ]$$

* **Kiểm chứng (Assertion):** Dùng chuỗi `text` cắt từ văn bản gốc theo $\text{Position}_{\text{Global}}$ đối chiếu với chuỗi `text` do LLM sinh ra. Nếu khớp khớp 100%, tọa độ hợp lệ.

#### Bước 4: Khử trùng lặp và Hợp nhất (Deduplication & Merge)

* **Cơ chế:** Gộp toàn bộ các JSON cục bộ lại thành một mảng JSON duy nhất đại diện cho cả văn bản.
* **Xử lý biên (Boundary Handling):** Nếu có một thực thể vô tình bị cắt ngang giữa hai đoạn chunk (rất hiếm nếu dùng Semantic Chunking), thuật toán sẽ dò sự trùng lặp tọa độ để ghép nối lại hoặc giữ lại thực thể có độ dài ý nghĩa nguyên vẹn nhất.

---

### TÁC ĐỘNG ĐẾN CÁC GIAI ĐOẠN SAU (DOWNSTREAM IMPACT)

* **Đẩy mạnh Giai đoạn 2 (Hybrid Retrieval):** Vì văn bản Wiki chứa rất nhiều thông tin đa chủ đề, việc chia nhỏ (Chunking) giúp ngữ cảnh xung quanh thực thể trở nên cô đọng. Vector ngữ nghĩa (Dense Retrieval) khi nhúng các đoạn ngắn này sẽ đạt độ chính xác cosine cao hơn rất nhiều so với việc nhúng một đoạn văn dài lan man.
* **Phát huy tối đa Giai đoạn 3 (Pragmatic Graph Pruning):** Bài viết Wiki thường đề cập chéo đến các bệnh lý và thuốc đối lập nhau (VD: nói về G6PD nhưng nhắc đến thuốc sốt rét để cấm dùng). Đồ thị ICD-10 và RxNorm lúc này sẽ đóng vai trò trọng tài thép, đo khoảng cách đường đi (LCA) để chặt đứt các liên kết sai lệch do văn phong liệt kê của bài viết gây ra.

---

### PHẦN IV: RÀNG BUỘC KỸ THUẬT VÀ LUẬT THI ĐẤU (COMPETITION CONSTRAINTS)

Dựa trên quy định (`quydinh.md`), để đảm bảo giải pháp không vi phạm luật và tối ưu hóa điểm số tuyệt đối, hệ thống được thiết kế bám sát các ràng buộc cốt lõi sau:

#### 1. Ràng buộc Mô hình và Tài nguyên (Model Constraints)
* **Giới hạn tham số:** Nếu triển khai self-host, mô hình LLM được sử dụng không được vượt quá **9 tỷ tham số (9B params)**. Việc lựa chọn `Qwen2.5-7B` (7 tỷ tham số) với 4-bit Quantization hoàn toàn hợp lệ và là lựa chọn State-of-the-Art trong giới hạn này.
* **Cấm API ngoài:** Không được sử dụng các External APIs (như OpenAI, Anthropic, Gemini). Toàn bộ Pipeline (NER, Inference, Graph Reasoning) phải có khả năng chạy cục bộ (Offline).

#### 2. Quy tắc Tính điểm và "Phạt nhân đôi" (Double Penalty Rule)
Điểm cuối cùng được tính bằng công thức:  
`Final Score = 0.3 * text_score(WER) + 0.3 * assertions_score(Jaccard) + 0.4 * candidates_score(Jaccard)`

* **Vị trí (Position) & WER:** Trường `text` phải được trích xuất hoàn hảo (giảm thiểu Word Error Rate). Việc ứng dụng **Semantic Chunking** ở khâu tiền xử lý giúp LLM định vị mảng `position` chính xác 100%.
* **Phạt nặng lỗi sai loại (Type Error):** Đây là bẫy lớn nhất của giải. Nếu đoán đúng `text` nhưng sai `type` (Ví dụ: đoán `CHẨN_ĐOÁN` nhưng nhãn gốc là `TRIỆU_CHỨNG`), thực thể đó sẽ bị **đếm làm 2 lần** (vì bị coi là tạo ra 1 thực thể mới hoàn toàn so với Ground Truth) và nhận 0 điểm ở cả 3 hạng mục.
  $\Rightarrow$ **Chiến lược:** *Precision (độ chính xác) quan trọng hơn Recall (độ phủ).* Hệ thống dùng thuật toán *LCA Pruning* và *Graph-Neighborhood Expansion* để làm trọng tài, chặt đứt các dự đoán có nguy cơ sai nhãn cao.

#### 3. Cấu trúc Đầu ra (JSON Schema Strictness)
Đầu ra cho mỗi file `.txt` bắt buộc là một mảng JSON (Array of Objects) với 5 trường nghiêm ngặt:
1. `text`: Chuỗi ký tự trích xuất chính xác từ văn bản gốc.
2. `position`: Mảng 2 phần tử `[start, end]` (0-indexed).
3. `type`: Chỉ được thuộc 5 loại (`CHẨN_ĐOÁN`, `TRIỆU_CHỨNG`, `THUỐC`, `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`).
4. `assertions`: Mảng chứa các chuỗi trạng thái (Giới hạn trong `isNegated`, `isFamily`, `isHistorical`).
5. `candidates`: Mảng ID ánh xạ ICD-10 hoặc RxNorm (Chỉ dùng cho `CHẨN_ĐOÁN` và `THUỐC`).

#### 4. Cơ chế Đóng gói và Kiểm tra Chéo (Anti-Cheat & Private Test)
* **Tái lập môi trường:** Code phải được đóng gói kỹ lưỡng kèm theo file `requirements.txt` / `Dockerfile` cùng tài liệu hướng dẫn cài đặt.
* **Minh bạch mã nguồn:** Nộp toàn bộ Model Weights, Data Processing và Inference Script để BTC chạy chéo trên tập **Private Test**. Việc này ngăn chặn tuyệt đối chiêu trò Hardcode `output.json` khớp với `input.txt`. Kiến trúc chia tách rạch ròi CPU (cho Graph/Vector) và GPU (cho LLM) của chúng ta sẽ giúp BTC dễ dàng clone và run dự án mà không gặp lỗi OOM.

---

### PHẦN V: HƯỚNG NÂNG CẤP QLORA KHI KHÔNG CÓ LABEL THẬT

Do BTC chỉ cung cấp `test/input/*.txt` mà không cung cấp nhãn ground truth JSON, QLoRA **không nằm trong baseline bắt buộc**. Fine-tune có giám sát chỉ hợp lệ khi ta có cặp dữ liệu `(input_text, expected_json)`. Vì vậy, QLoRA được định vị là một hướng nâng cấp sau khi pipeline inference + retrieval + graph pruning đã chạy ổn định.

#### 1. Mục tiêu của QLoRA

QLoRA không dùng để bắt LLM học thuộc mã ICD-10/RxNorm. Việc ánh xạ mã vẫn thuộc Hybrid Retrieval và Pragmatic Graph. QLoRA chỉ tối ưu các năng lực sau:

* **NER:** nhận diện đúng span `text` của thực thể y khoa.
* **Type Classification:** phân biệt chuẩn 5 nhãn `TRIỆU_CHỨNG`, `TÊN_XÉT_NGHIỆM`, `KẾT_QUẢ_XÉT_NGHIỆM`, `CHẨN_ĐOÁN`, `THUỐC`.
* **Assertion Detection:** gán đúng `isNegated`, `isFamily`, `isHistorical` hoặc `[]`.
* **Format Discipline:** sinh JSON trung gian ổn định, giảm lỗi format trước khi qua validator.

#### 2. Nguồn dữ liệu huấn luyện khả thi

* **Synthetic Data:** Tạo câu lâm sàng tiếng Việt bằng template từ danh mục ICD-10/RxNorm, synonym, viết tắt, liều thuốc, kết quả xét nghiệm và các trigger assertion như `không`, `phủ nhận`, `tiền sử`, `từng dùng`, `bố/mẹ/gia đình`.
* **Pseudo-labeling:** Dùng chính LLM self-host sinh nhãn trên văn bản y khoa/Wiki, sau đó lọc bằng exact span validator, schema validator, dictionary matching và retrieval confidence. Chỉ giữ sample đạt điều kiện nghiêm ngặt.
* **Rule-generated Labels:** Với các pattern chắc chắn như `không <triệu chứng>`, `tiền sử <bệnh>`, `trước nhập viện <thuốc>`, có thể tự sinh nhãn assertion chính xác cao.

#### 3. Định dạng training sample

Mỗi sample dùng cho QLoRA gồm prompt và JSON trung gian, trong đó `candidates` để rỗng:

```json
{
  "input": "Bệnh nhân có tiền sử hen phế quản, hiện không ho, được kê Aspirin.",
  "output": {
    "entities": [
      {
        "text": "hen phế quản",
        "position": [19, 32],
        "type": "CHẨN_ĐOÁN",
        "assertions": ["isHistorical"],
        "candidates": []
      },
      {
        "text": "ho",
        "position": [45, 47],
        "type": "TRIỆU_CHỨNG",
        "assertions": ["isNegated"],
        "candidates": []
      },
      {
        "text": "Aspirin",
        "position": [57, 64],
        "type": "THUỐC",
        "assertions": [],
        "candidates": []
      }
    ]
  }
}
```

#### 4. Chiến lược huấn luyện an toàn

* **Base model:** `Qwen2.5-7B-Instruct`, vẫn dưới giới hạn 9B params.
* **Kỹ thuật:** QLoRA 4-bit NF4, LoRA rank nhỏ để tiết kiệm VRAM.
* **Loss weighting:** tăng trọng số cho token thuộc trường `type` và `assertions` vì sai loại bị phạt nhân đôi.
* **Không học candidate ID:** tránh overfit vào synthetic mapping; candidate thật được xử lý bởi BM25/SapBERT/RxNorm/ICD-10 ở downstream.
* **Giữ validator sau fine-tune:** dù đã QLoRA, output vẫn phải qua Constrained Decoding, span validation và correction.

#### 5. Tiêu chí kích hoạt QLoRA

Chỉ triển khai QLoRA khi baseline đã có metric nội bộ rõ ràng và gặp một trong các vấn đề sau:

* Sai `type` nhiều trên các câu có bệnh/triệu chứng dễ nhầm.
* Sai assertion với phủ định, tiền sử hoặc người nhà.
* Zero-shot/Few-shot prompt quá dài, tốc độ inference chậm hoặc format chưa ổn định.

Nói cách khác, **QLoRA là Phase tối ưu hóa**, không phải điều kiện tiên quyết để nộp bài. Baseline phải chạy tốt ngay cả khi không có dữ liệu nhãn thật.