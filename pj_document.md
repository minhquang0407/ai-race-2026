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

### PHẦN II: HƯỚNG NÂNG CẤP - PRAGMATIC GRAPH (POST-BASELINE)

Sau khi Baseline đạt điểm số an toàn và hệ thống vận hành không lỗi, thuật toán Đồ thị Thực dụng (Pragmatic Graph) được gắn thêm vào Pha 3 nhằm tái xếp hạng (Re-ranking) các ca lâm sàng phức tạp dựa trên logic hình thức.

#### 1. Đồ thị hóa Chuẩn Y khoa

* **Khởi tạo:** Biểu diễn danh mục ICD-10 thành một Đồ thị có hướng không chu trình (Directed Acyclic Graph - DAG) $G = (V, E)$ bằng thư viện `NetworkX`.
* **Tính chất:** Khối lượng xử lý đồ thị được đẩy hoàn toàn sang CPU. Thao tác trên $G$ sử dụng đại số tuyến tính cơ bản, không tiêu tốn VRAM, đảm bảo hệ thống có thể được Ban tổ chức dựng lại (reproduce) offline mà không gây lỗi Out-of-Memory.

#### 2. Graph Distance Pruning (Cắt tỉa bằng Khoảng cách Hình học)

Sử dụng cấu trúc đồ thị như một màng lọc kiểm chứng chéo (Cross-validation).

* **Logic Toán học:** Giả sử tập ứng viên ban đầu của thực thể $e_1$ là $C = \{c_1, c_2, c_3\}$. Nếu ngữ cảnh có tồn tại một thực thể mỏ neo $e_{anchor}$ (ví dụ: một thuốc đã map chắc chắn vào RxNorm), hệ thống tính khoảng cách đường đi ngắn nhất $d(c_i, c_{anchor})$ trên đồ thị liên kết chéo.
* **Thực thi:** Bất kỳ ứng viên $c_i$ nào nằm ở nhánh đồ thị hoàn toàn xa lạ (khoảng cách $d$ lớn hơn một ngưỡng $\epsilon$) so với cụm thực thể còn lại trong câu sẽ bị gạch bỏ lập tức. Loại trừ hiện tượng suy diễn nhầm bệnh hệ hô hấp sang bệnh hệ tiêu hóa do lỗi của mô hình Vector.

#### 3. Activation Spreading (Lan truyền Kích hoạt)

Sử dụng khi Baseline quá "bảo thủ", dẫn đến bỏ sót mã chuẩn (Recall thấp).

* **Cơ chế:** Khi thuật toán nhận diện được một mã $v_{root}$ (ví dụ: K21.0 - Bệnh trào ngược), năng lượng kích hoạt sẽ được lan truyền dọc theo các cạnh xuống các node con trực tiếp của nó trong cây phân cấp ICD-10.
* **Thực thi:** Cộng một lượng điểm ưu tiên nhỏ (Bias) cho các node con này. Nếu quá trình Hybrid Retrieval trả về các mã con này ở thứ hạng thấp, chúng sẽ được "kéo" lên nhờ điểm lan truyền đồ thị, khôi phục lại các ứng viên bị chìm lấp mà vẫn tuân thủ đúng định lý nội suy y khoa.

---

### PHẦN III: QUY TRÌNH KIỂM THỬ VÀ ĐÁNH GIÁ (CI/CD & TESTING)

Để ngăn chặn việc mất quyền thi đấu do Ban tổ chức không chạy được Source Code.

* **Quản lý Môi trường:** Cung cấp `requirements.txt` và `Dockerfile` đóng gói môi trường chuẩn (CUDA 12.x, PyTorch), tách bạch rõ ràng giữa phân vùng chạy LLM (GPU) và phân vùng lưu trữ Graph/Vector (CPU RAM).
* **Unit Tests:** Xây dựng hệ thống test kiểm tra ngẫu nhiên 1000 chuỗi sinh từ LLM để đảm bảo tỷ lệ lỗi cấu trúc (JSON Parsing Error) luôn duy trì ở mức 0%, đồng thời giả lập hành vi phạt nhân đôi để tính toán trực tiếp điểm Jaccard mô phỏng trong quá trình huấn luyện.