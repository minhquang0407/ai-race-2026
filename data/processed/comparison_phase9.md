# Output Comparison Report

- Before: `output_llm_fullkb`
- After: `output_llm_phase9`
- Limit: `10`

## Type Counts

| Type | Before | After | Delta |
|---|---:|---:|---:|
| CHẨN_ĐOÁN | 33 | 28 | -5 |
| KẾT_QUẢ_XÉT_NGHIỆM | 10 | 7 | -3 |
| THUỐC | 17 | 17 | +0 |
| TRIỆU_CHỨNG | 100 | 96 | -4 |
| TÊN_XÉT_NGHIỆM | 22 | 22 | +0 |
| **TOTAL** | **182** | **170** | **-12** |

## Candidate Changes

| File | Text | Type | Span | Before | After |
|---|---|---|---:|---|---|
| 4.json | hội chứng ruột kích thích | CHẨN_ĐOÁN | (226, 251) | G20.C | K58.9 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (842, 867) | A08.4 | A08.4, A08.39 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (975, 1000) | A08.4 | A08.4, A08.39 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (1460, 1485) | A08.4 | A08.4, A08.39 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (2231, 2256) | A08.4 | A08.4, A08.39 |
| 5.json | ung thư biểu mô tế bào mật | CHẨN_ĐOÁN | (238, 264) | C73 | C22.1 |
| 5.json | Hội chứng buồng trứng đa nang | CHẨN_ĐOÁN | (982, 1011) | G20.C | E28.2 |
| 5.json | ung thư biểu mô tuyến | CHẨN_ĐOÁN | (1605, 1626) | C73 | C22.1 |
| 6.json | xơ vữa động mạch | CHẨN_ĐOÁN | (38, 54) |  | I70.9 |
| 8.json | hội chứng nghiện rượu | CHẨN_ĐOÁN | (129, 150) | G20.C | F10.2 |

## Added Entities

None.

## Dropped Entities

| File | Text | Type | Span | Candidates |
|---|---|---|---:|---|
| 4.json | 100 microgam | KẾT_QUẢ_XÉT_NGHIỆM | (2794, 2806) |  |
| 4.json | 75 microgam | KẾT_QUẢ_XÉT_NGHIỆM | (2727, 2738) |  |
| 4.json | 4 nanogam/mL | KẾT_QUẢ_XÉT_NGHIỆM | (3184, 3196) |  |
| 5.json | phẫu thuật cắt bỏ ống dẫn mật chung | CHẨN_ĐOÁN | (75, 110) |  |
| 5.json | cắt bỏ một phần thùy gan bên trái | CHẨN_ĐOÁN | (112, 145) |  |
| 5.json | nối mật tụy bằng ống dẫn hồi tràng | CHẨN_ĐOÁN | (149, 183) | K26.9 |
| 7.json | 20w | TRIỆU_CHỨNG | (792, 795) |  |
| 7.json | 10kg | TRIỆU_CHỨNG | (813, 817) |  |
| 9.json | 20w | TRIỆU_CHỨNG | (792, 795) |  |
| 9.json | 10kg | TRIỆU_CHỨNG | (813, 817) |  |
| 10.json | gan | CHẨN_ĐOÁN | (2511, 2514) | A18, A18.13, A18.15 |
| 10.json | cấp | CHẨN_ĐOÁN | (2515, 2518) |  |

## Suspicious After Rows

None detected by heuristic checks.
