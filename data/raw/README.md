# Sample Medical Knowledge Data

Đây là dữ liệu mẫu nhỏ để test logic graph/retrieval trước khi thay bằng dữ liệu ICD-10/RxNorm chính thức.

## Files

- `icd10_sample.csv`: cây ICD-10 giả lập gồm root, chapter, block, category và code.
- `rxnorm_sample.csv`: dictionary RxNorm mẫu gồm `rxcui`, `name`, `tty`, `synonyms`.

## Ghi chú

- ICD-10 phù hợp để build `NetworkX.DiGraph` và tính LCA/Wu-Palmer.
- RxNorm baseline nên dùng dictionary/search index trước, chưa cần ép thành cây.
- Khi có data thật, giữ schema CSV tương tự để thay thế loader ít nhất có thể.
