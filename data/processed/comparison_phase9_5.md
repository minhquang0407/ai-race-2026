# Output Comparison Report

- Before: `output_llm_phase9_50`
- After: `output_llm_phase9_5_50`
- Limit: `50`

## Type Counts

| Type | Before | After | Delta |
|---|---:|---:|---:|
| CHẨN_ĐOÁN | 124 | 124 | +0 |
| KẾT_QUẢ_XÉT_NGHIỆM | 85 | 85 | +0 |
| THUỐC | 65 | 65 | +0 |
| TRIỆU_CHỨNG | 346 | 346 | +0 |
| TÊN_XÉT_NGHIỆM | 69 | 69 | +0 |
| **TOTAL** | **689** | **689** | **+0** |

## Candidate Changes

| File | Text | Type | Span | Before | After |
|---|---|---|---:|---|---|
| 3.json | hội chứng Parkinson | CHẨN_ĐOÁN | (510, 529) | G20.C | G20.C, G20, G21 |
| 4.json | viêm dạ dày ruột | CHẨN_ĐOÁN | (144, 160) | A08.4 | K29.5, K29.6, K29.0 |
| 4.json | hội chứng ruột kích thích | CHẨN_ĐOÁN | (226, 251) | K58.9 | K58.9, K58, K58.2 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (842, 867) | A08.4, A08.39 | A08.4, A08.3, A08.39 |
| 4.json | loét tá tràng | CHẨN_ĐOÁN | (1314, 1327) | K26.9 | K26.9, K26 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (975, 1000) | A08.4, A08.39 | A08.4, A08.3, A08.39 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (1460, 1485) | A08.4, A08.39 | A08.4, A08.3, A08.39 |
| 4.json | viêm dạ dày ruột do virus | CHẨN_ĐOÁN | (2231, 2256) | A08.4, A08.39 | A08.4, A08.3, A08.39 |
| 4.json | loét thực quản | CHẨN_ĐOÁN | (3557, 3571) | K26.9 | D00 |
| 5.json | vô sinh | CHẨN_ĐOÁN | (356, 363) | N97.9 | N97.9, N97 |
| 6.json | xơ vữa động mạch | CHẨN_ĐOÁN | (38, 54) | I70.9 | I70.9, I70, I70.90 |
| 7.json | viêm bao tử | CHẨN_ĐOÁN | (1517, 1528) | K29.70 | K29.70, K29.5, K29.6 |
| 8.json | hội chứng nghiện rượu | CHẨN_ĐOÁN | (129, 150) | F10.2 | F10.2, F10.25, F10.28 |
| 9.json | viêm bao tử | CHẨN_ĐOÁN | (1517, 1528) | K29.70 | K29.70, K29.5, K29.6 |
| 11.json | xơ vữa động mạch | CHẨN_ĐOÁN | (38, 54) | I70.9 | I70.9, I70, I70.90 |
| 11.json | bàn chân bẹt | CHẨN_ĐOÁN | (1903, 1915) |  | Q66.5 |
| 12.json | béo phì | CHẨN_ĐOÁN | (170, 177) |  | E66, E66.8, E66.81 |
| 12.json | viêm mô tế bào | CHẨN_ĐOÁN | (976, 990) | C22.1 | L03.213 |
| 12.json | dị tật thiểu sản vành tai | CHẨN_ĐOÁN | (1718, 1743) |  | A34 |
| 12.json | tịt ống tai ngoài bẩm sinh | CHẨN_ĐOÁN | (1747, 1773) | N97.9 | H60 |
| 13.json | bệnh dại | CHẨN_ĐOÁN | (310, 318) |  | A82, A82.0, A82.1 |
| 13.json | bệnh dại | CHẨN_ĐOÁN | (603, 611) |  | A82, A82.0, A82.1 |
| 13.json | bệnh dại | CHẨN_ĐOÁN | (1436, 1444) |  | A82, A82.0, A82.1 |
| 13.json | dại | CHẨN_ĐOÁN | (1999, 2002) |  | A82 |
| 14.json | tăng lipid máu | CHẨN_ĐOÁN | (718, 732) | E75.6 | E78, E78.49, E78.4 |
| 15.json | béo phì | CHẨN_ĐOÁN | (170, 177) |  | E66, E66.8, E66.81 |
| 15.json | viêm mô tế bào | CHẨN_ĐOÁN | (976, 990) | C22.1 | L03.213 |
| 15.json | Viêm mô tế bào | CHẨN_ĐOÁN | (2029, 2043) | C22.1 | L03.213 |
| 15.json | Bệnh thủy đậu/Zona | CHẨN_ĐOÁN | (2623, 2641) |  | B01, B01.9, B02.0 |
| 16.json | bệnh dại | CHẨN_ĐOÁN | (327, 335) |  | A82, A82.0, A82.1 |
| 16.json | bệnh dại | CHẨN_ĐOÁN | (612, 620) |  | A82, A82.0, A82.1 |
| 16.json | bệnh dại | CHẨN_ĐOÁN | (1450, 1458) |  | A82, A82.0, A82.1 |
| 17.json | viêm nha chu | CHẨN_ĐOÁN | (1083, 1095) |  | K05.3, K04.4, K04.5 |
| 20.json | bệnh dại | CHẨN_ĐOÁN | (327, 335) |  | A82, A82.0, A82.1 |
| 20.json | bệnh dại | CHẨN_ĐOÁN | (612, 620) |  | A82, A82.0, A82.1 |
| 20.json | bệnh dại | CHẨN_ĐOÁN | (1938, 1946) |  | A82, A82.0, A82.1 |
| 21.json | Rối loạn chuyển hóa tinh bột | CHẨN_ĐOÁN | (29, 57) |  | E85, E85.3, E85.8 |
| 21.json | thoái hóa tinh bột | CHẨN_ĐOÁN | (313, 331) |  | E85, E85.3, E85.8 |
| 21.json | bệnh thoái hóa tinh bột | CHẨN_ĐOÁN | (806, 829) |  | E85, E85.3, E85.8 |
| 22.json | bilirubin máu | CHẨN_ĐOÁN | (2484, 2497) | E80.7, E80 | E80, E80.7 |
| 24.json | virus viêm gan B | CHẨN_ĐOÁN | (1572, 1588) | A08.4 | B16, B18.1, B19.1 |
| 26.json | Bệnh mạch vành | CHẨN_ĐOÁN | (52, 66) | I70.9 | H34 |
| 26.json | viêm tụy | CHẨN_ĐOÁN | (1517, 1525) |  | G04 |
| 26.json | rung nhĩ | CHẨN_ĐOÁN | (1561, 1569) |  | H72, H73 |
| 27.json | viêm phổi | CHẨN_ĐOÁN | (68, 77) |  | P23 |
| 29.json | hội chứng bàn chân bẹt bẩm sinh | CHẨN_ĐOÁN | (1309, 1340) |  | Q66.5 |
| 29.json | bàn chân bẹt | CHẨN_ĐOÁN | (1705, 1717) |  | Q66.5 |
| 29.json | thuyên tắc phổi | CHẨN_ĐOÁN | (2218, 2233) |  | P23 |
| 30.json | bệnh mãn tính | CHẨN_ĐOÁN | (8, 21) |  | B15, B16, B17 |
| 31.json | giãn thừng tinh | CHẨN_ĐOÁN | (240, 255) |  | A38 |
| 31.json | giãn thừng tinh | CHẨN_ĐOÁN | (873, 888) |  | A38 |
| 31.json | vô sinh thứ phát | CHẨN_ĐOÁN | (643, 659) | N97.9 | N97.9, N97 |
| 32.json | Rối loạn chuyển hóa tinh bột | CHẨN_ĐOÁN | (29, 57) |  | E85, E85.3, E85.8 |
| 32.json | thoái hóa tinh bột | CHẨN_ĐOÁN | (313, 331) |  | E85, E85.3, E85.8 |
| 32.json | tăng lipid máu | CHẨN_ĐOÁN | (841, 855) | E75.6 | E78, E78.49, E78.4 |
| 33.json | rung nhĩ | CHẨN_ĐOÁN | (39, 47) |  | H72, H73 |
| 33.json | tăng huyết áp | CHẨN_ĐOÁN | (50, 63) |  | I1A.0 |
| 33.json | suy tim | CHẨN_ĐOÁN | (66, 73) |  | I11.0 |
| 33.json | béo phì | CHẨN_ĐOÁN | (92, 99) |  | E66, E66.8, E66.81 |
| 36.json | cầu thận mạn tính | CHẨN_ĐOÁN | (568, 585) | N20.0 | B18 |
| 36.json | thiếu máu | CHẨN_ĐOÁN | (874, 883) | D55.0 | D52, D50 |
| 37.json | Viêm mô tế bào | CHẨN_ĐOÁN | (1256, 1270) | C22.1 | L03.213 |
| 37.json | Tai mũi họng nhi | CHẨN_ĐOÁN | (1864, 1880) |  | J00 |
| 38.json | tăng lipid máu | CHẨN_ĐOÁN | (133, 147) | E75.6 | E78, E78.49, E78.4 |
| 39.json | bệnh phổi tắc nghẽn mạn tính | CHẨN_ĐOÁN | (73, 101) |  | B18 |
| 39.json | Viêm phổi bệnh viện | CHẨN_ĐOÁN | (557, 576) |  | P23 |
| 39.json | rung nhĩ | CHẨN_ĐOÁN | (580, 588) |  | H72, H73 |
| 39.json | nhịp nhanh trên thất | CHẨN_ĐOÁN | (592, 612) |  | G11 |
| 39.json | bàn chân bẹt | CHẨN_ĐOÁN | (1078, 1090) |  | Q66.5 |
| 41.json | mụn trứng cá | CHẨN_ĐOÁN | (80, 92) | E28.2 | B07 |
| 41.json | trứng cá | CHẨN_ĐOÁN | (1250, 1258) | E28.2 | C56 |
| 41.json | mụn trứng cá | CHẨN_ĐOÁN | (1333, 1345) | E28.2 | B07 |
| 41.json | sức khỏe sinh sản | CHẨN_ĐOÁN | (1878, 1895) | N97.9 | A34 |
| 42.json | giãn phế quản | CHẨN_ĐOÁN | (1381, 1394) |  | D00 |
| 42.json | viêm phổi thùy dưới phải | CHẨN_ĐOÁN | (1924, 1948) |  | P23 |
| 43.json | tăng cholesterol máu đơn thuần | CHẨN_ĐOÁN | (95, 125) | E78.7, E78.70, E78.6 | A82, A82.0, A82.1 |
| 43.json | tăng huyết áp | CHẨN_ĐOÁN | (132, 145) |  | I1A.0 |
| 46.json | suy tim | CHẨN_ĐOÁN | (71, 78) |  | I11.0 |
| 46.json | tăng huyết áp | CHẨN_ĐOÁN | (82, 95) |  | I1A.0 |
| 46.json | phù phổi cấp | CHẨN_ĐOÁN | (303, 315) |  | P23 |
| 46.json | Phù phổi cấp | CHẨN_ĐOÁN | (1192, 1204) |  | P23 |
| 47.json | bệnh phổi tắc nghẽn mạn tính | CHẨN_ĐOÁN | (73, 101) |  | B18 |
| 48.json | dị tật thiểu sản vành tai | CHẨN_ĐOÁN | (1042, 1067) |  | A34 |
| 48.json | tịt ống tai ngoài bẩm sinh | CHẨN_ĐOÁN | (1071, 1097) | N97.9 | H60 |
| 48.json | cấu trúc tai trong | CHẨN_ĐOÁN | (1112, 1130) | C22.1 | H83 |
| 48.json | thần kinh thính giác | CHẨN_ĐOÁN | (1150, 1170) |  | H47 |
| 49.json | bệnh rụng tóc | CHẨN_ĐOÁN | (30, 43) |  | B79 |
| 49.json | tràn dịch màng phổi trái tái phát | CHẨN_ĐOÁN | (214, 247) |  | A20 |

## Added Entities

None.

## Dropped Entities

None.

## Suspicious After Rows

None detected by heuristic checks.
