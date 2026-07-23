Tài liệu dưới đây thiết kế kiến trúc hệ thống giải quyết bài toán Ontological Reasoning in Medical Knowledge Retrieval. Cấu trúc được chia làm hai giai đoạn đúng với định hướng nghiên cứu: **BASELINE** tập trung vào sự an toàn, tuân thủ chặt chẽ định dạng JSON và lách "hình phạt nhân đôi" qua kỹ thuật QLoRA kết hợp Dynamic Thresholding. Hướng **NÂNG CẤP (Pragmatic Graph)** sử dụng toán học rời rạc trên cây ICD-10 để cắt tỉa ứng viên sai logic, tối đa hóa điểm Jaccard Similarity mà vẫn bảo đảm hệ thống chạy trơn tru trên môi trường phần cứng giới hạn (VRAM 12GB).

---

## PROJECT DESIGN DOCUMENT: MEDICAL ONTOLOGICAL REASONING AI

**Mục tiêu:** Xây dựng hệ thống trích xuất và ánh xạ thực thể y khoa tuân thủ giới hạn phần cứng (SLM $\le$ 9B parameters) và tối ưu hóa hàm mục tiêu có chứa Double Penalty.

---

### PHẦN I: KIẾN TRÚC BASELINE (CORE PIPELINE)

Giai đoạn Baseline thiết lập một luồng xử lý (End-to-End) vững chắc, triệt tiêu sai số định dạng và tối ưu hóa độ chính xác (Precision) thay vì cố gắng mở rộng độ phủ (Recall) một cách rủi ro.

#### 1. Pha Trích xuất Định hướng (Joint NER & Assertion)

Thay vì sử dụng pipeline chia nhỏ dễ tích lũy sai số, hệ thống sử dụng một LLM cục bộ xử lý trọn gói trong một lượt quét.

* **Mô hình nền tảng:** `Qwen2.5-7B-Instruct` (Lượng hóa NF4/4-bit để vận hành mượt mà dưới giới hạn 12GB VRAM).
* **Chiến lược Tinh chỉnh (QLoRA):**
* Huấn luyện mô hình trên tập dữ liệu tổng hợp (Synthetic Data) giả lập cấu trúc văn bản lâm sàng tiếng Việt.
* Hàm mất mát (Loss Function) trong quá trình huấn luyện được thiết lập trọng số cao (class weighting) cho việc dự đoán đúng `type` (BỆNH, TRIỆU_CHỨNG, THUỐC) nhằm né tránh hình phạt nhân đôi (0 điểm) của Ban tổ chức.


* **Giải mã Ràng buộc (Constrained Decoding):** Sử dụng `Outlines` hoặc `Instructor` áp đặt JSON Schema khắt khe. Trạng thái không gian từ vựng bị ép buộc chỉ sinh ra các key chuẩn như `text`, `position`, `type`, `candidates`, và `assertions`.

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