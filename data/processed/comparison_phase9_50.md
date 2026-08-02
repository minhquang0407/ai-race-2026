# Output Comparison Report

- Before: `output_llm_fullkb`
- After: `output_llm_phase9_50`
- Limit: `50`

## Type Counts

| Type | Before | After | Delta |
|---|---:|---:|---:|
| CHẨN_ĐOÁN | 33 | 124 | +91 |
| KẾT_QUẢ_XÉT_NGHIỆM | 10 | 85 | +75 |
| THUỐC | 17 | 65 | +48 |
| TRIỆU_CHỨNG | 100 | 346 | +246 |
| TÊN_XÉT_NGHIỆM | 22 | 69 | +47 |
| **TOTAL** | **182** | **689** | **+507** |

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

| File | Text | Type | Span | Candidates |
|---|---|---|---:|---|
| 11.json | xơ vữa động mạch | CHẨN_ĐOÁN | (38, 54) | I70.9 |
| 11.json | tụ máu ngoài màng cứng | TRIỆU_CHỨNG | (752, 774) |  |
| 11.json | tổn thương mạn tính | TRIỆU_CHỨNG | (798, 817) |  |
| 11.json | CT | TÊN_XÉT_NGHIỆM | (867, 869) |  |
| 11.json | biểu hiện bất thường | TRIỆU_CHỨNG | (1354, 1374) |  |
| 11.json | mất định hướng | TRIỆU_CHỨNG | (1376, 1390) |  |
| 11.json | kích thích nhẹ | TRIỆU_CHỨNG | (1596, 1610) |  |
| 11.json | bàn chân bẹt | CHẨN_ĐOÁN | (1903, 1915) |  |
| 11.json | mất định hướng | TRIỆU_CHỨNG | (2343, 2357) |  |
| 11.json | CT sọ não | TÊN_XÉT_NGHIỆM | (2564, 2573) |  |
| 11.json | xuất huyết dưới nhện | TRIỆU_CHỨNG | (2592, 2612) |  |
| 11.json | dịch dưới màng cứng | TRIỆU_CHỨNG | (2688, 2707) |  |
| 11.json | nang màng nhện | TRIỆU_CHỨNG | (2743, 2757) |  |
| 11.json | tụ máu dưới màng cứng | TRIỆU_CHỨNG | (2763, 2784) |  |
| 12.json | corticoid liều cao kéo dài | CHẨN_ĐOÁN | (68, 94) |  |
| 12.json | béo phì | CHẨN_ĐOÁN | (170, 177) |  |
| 12.json | bactrim | THUỐC | (382, 389) | 151399 |
| 12.json | doxycycline | THUỐC | (430, 441) | 3640 |
| 12.json | viêm mô tế bào | CHẨN_ĐOÁN | (976, 990) | C22.1 |
| 12.json | doxycyclin | THUỐC | (953, 963) | 1101054, 1101055, 1160776 |
| 12.json | ban đỏ | TRIỆU_CHỨNG | (1008, 1014) |  |
| 12.json | dị tật thiểu sản vành tai | CHẨN_ĐOÁN | (1718, 1743) |  |
| 12.json | tịt ống tai ngoài bẩm sinh | CHẨN_ĐOÁN | (1747, 1773) | N97.9 |
| 12.json | doxycyclinebactrim | THUỐC | (2507, 2525) | 151399, 3640, 544837 |
| 13.json | bệnh dại | CHẨN_ĐOÁN | (310, 318) |  |
| 13.json | nước dãi | TRIỆU_CHỨNG | (198, 206) |  |
| 13.json | con chó | TRIỆU_CHỨNG | (140, 147) |  |
| 13.json | bệnh dại | CHẨN_ĐOÁN | (603, 611) |  |
| 13.json | bệnh dại | CHẨN_ĐOÁN | (1436, 1444) |  |
| 13.json | chó | TRIỆU_CHỨNG | (1713, 1716) |  |
| 13.json | dại | CHẨN_ĐOÁN | (1999, 2002) |  |
| 13.json | vết thương | TRIỆU_CHỨNG | (2416, 2426) |  |
| 13.json | vi rút | TRIỆU_CHỨNG | (2575, 2581) |  |
| 14.json | dấu mề đay | TRIỆU_CHỨNG | (81, 91) |  |
| 14.json | gleevec | THUỐC | (684, 691) | 282386 |
| 14.json | tăng lipid máu | CHẨN_ĐOÁN | (718, 732) | E75.6 |
| 14.json | suy kiệt | TRIỆU_CHỨNG | (1072, 1080) |  |
| 14.json | 2,5 – 5mg | TRIỆU_CHỨNG | (2500, 2509) |  |
| 15.json | corticoid liều cao kéo dài | CHẨN_ĐOÁN | (68, 94) |  |
| 15.json | béo phì | CHẨN_ĐOÁN | (170, 177) |  |
| 15.json | bactrim | THUỐC | (382, 389) | 151399 |
| 15.json | doxycycline | THUỐC | (430, 441) | 3640 |
| 15.json | viêm mô tế bào | CHẨN_ĐOÁN | (976, 990) | C22.1 |
| 15.json | doxycyclin | THUỐC | (953, 963) | 1101054, 1101055, 1160776 |
| 15.json | ban đỏ | TRIỆU_CHỨNG | (1008, 1014) |  |
| 15.json | liều | TRIỆU_CHỨNG | (916, 920) |  |
| 15.json | rỉ | TRIỆU_CHỨNG | (1175, 1177) |  |
| 15.json | dịch | TRIỆU_CHỨNG | (1178, 1182) |  |
| 15.json | mủ | TRIỆU_CHỨNG | (1198, 1200) |  |
| 15.json | viêm | TRIỆU_CHỨNG | (976, 980) |  |
| 15.json | Viêm mô tế bào | CHẨN_ĐOÁN | (2029, 2043) | C22.1 |
| 15.json | bactrim | THUỐC | (1984, 1991) | 151399 |
| 15.json | doxycycline | THUỐC | (1995, 2006) | 3640 |
| 15.json | ban đỏ | TRIỆU_CHỨNG | (1860, 1866) |  |
| 15.json | mủ | TRIỆU_CHỨNG | (1873, 1875) |  |
| 15.json | dịch tiết | TRIỆU_CHỨNG | (2096, 2105) |  |
| 15.json | Viêm mô tế bào | TRIỆU_CHỨNG | (2364, 2378) |  |
| 15.json | doxycyclinebactrim | THUỐC | (2332, 2350) | 151399, 3640, 544837 |
| 15.json | Bệnh thủy đậu/Zona | CHẨN_ĐOÁN | (2623, 2641) |  |
| 15.json | Varicella Zoster Virus | CHẨN_ĐOÁN | (2646, 2668) | B01.9, B02.0 |
| 16.json | bệnh dại | CHẨN_ĐOÁN | (327, 335) |  |
| 16.json | bệnh dại | CHẨN_ĐOÁN | (612, 620) |  |
| 16.json | Lyssavirus | TÊN_XÉT_NGHIỆM | (865, 875) |  |
| 16.json | bệnh dại | CHẨN_ĐOÁN | (1450, 1458) |  |
| 16.json | tiêm | TÊN_XÉT_NGHIỆM | (1320, 1324) |  |
| 16.json | chó | TRIỆU_CHỨNG | (1727, 1730) |  |
| 16.json | vi rút dại | TRIỆU_CHỨNG | (2275, 2285) |  |
| 16.json | bumetanide | THUỐC | (2178, 2188) | 1808 |
| 16.json | vancomycin | THUỐC | (2211, 2221) | 11124 |
| 16.json | levofloxacin | THUỐC | (2244, 2256) | 82122 |
| 17.json | vi khuẩn | TRIỆU_CHỨNG | (546, 554) |  |
| 17.json | viêm | TRIỆU_CHỨNG | (661, 665) |  |
| 17.json | viêm nha chu | CHẨN_ĐOÁN | (1083, 1095) |  |
| 17.json | vi khuẩn | TRIỆU_CHỨNG | (1778, 1786) |  |
| 17.json | viêm | TRIỆU_CHỨNG | (2186, 2190) |  |
| 17.json | men răng | TRIỆU_CHỨNG | (1734, 1742) |  |
| 17.json | gai lưỡi | TRIỆU_CHỨNG | (1744, 1752) |  |
| 17.json | niêm mạc | TRIỆU_CHỨNG | (2200, 2208) |  |
| 17.json | sưng | TRIỆU_CHỨNG | (2215, 2219) |  |
| 17.json | dương tính | TRIỆU_CHỨNG | (2068, 2078) |  |
| 17.json | biệt hóa | TRIỆU_CHỨNG | (2018, 2026) |  |
| 17.json | biểu mô tế bào vảy | TRIỆU_CHỨNG | (1977, 1995) |  |
| 17.json | mùi hôi | TRIỆU_CHỨNG | (2254, 2261) |  |
| 17.json | khoang miệng | TRIỆU_CHỨNG | (2268, 2280) |  |
| 17.json | chảy máu | TRIỆU_CHỨNG | (2292, 2300) |  |
| 17.json | chảy máu chân răng | TRIỆU_CHỨNG | (2318, 2336) |  |
| 17.json | hôi miệng | TRIỆU_CHỨNG | (2340, 2349) |  |
| 17.json | bào láng gốc răng | TRIỆU_CHỨNG | (2365, 2382) |  |
| 17.json | cao răng | TRIỆU_CHỨNG | (2414, 2422) |  |
| 17.json | vi khuẩn | TRIỆU_CHỨNG | (2441, 2449) |  |
| 17.json | viêm | TRIỆU_CHỨNG | (2454, 2458) |  |
| 17.json | mô mềm | TRIỆU_CHỨNG | (2467, 2473) |  |
| 17.json | vòm họng | TRIỆU_CHỨNG | (2476, 2484) |  |
| 17.json | nướu | TRIỆU_CHỨNG | (2494, 2498) |  |
| 18.json | ST chênh lên / chênh xuống | TRIỆU_CHỨNG | (35, 61) |  |
| 18.json | Q bệnh lý | TRIỆU_CHỨNG | (79, 88) |  |
| 18.json | dương tính | KẾT_QUẢ_XÉT_NGHIỆM | (1240, 1250) |  |
| 18.json | sốt | TRIỆU_CHỨNG | (1113, 1116) |  |
| 18.json | buồn nôn | TRIỆU_CHỨNG | (1605, 1613) |  |
| 18.json | siêu âm vùng gan mật | TÊN_XÉT_NGHIỆM | (2294, 2314) |  |
| 18.json | sỏi mật | TRIỆU_CHỨNG | (2324, 2331) |  |
| 18.json | viêm túi mật | TRIỆU_CHỨNG | (2347, 2359) |  |
| 18.json | viêm túi mật cấp | TRIỆU_CHỨNG | (2564, 2580) |  |
| 18.json | dịch quanh túi mật | TRIỆU_CHỨNG | (2539, 2557) |  |
| 18.json | sỏi ống mật | TRIỆU_CHỨNG | (2365, 2376) |  |
| 19.json | dấu mề đay | TRIỆU_CHỨNG | (81, 91) |  |
| 19.json | di truyền | TRIỆU_CHỨNG | (318, 327) |  |
| 19.json | tylenol | THUỐC | (684, 691) | 202433 |
| 19.json | 2,5 – 5mg | TRIỆU_CHỨNG | (2467, 2476) |  |
| 20.json | bệnh dại | CHẨN_ĐOÁN | (327, 335) |  |
| 20.json | bệnh dại | CHẨN_ĐOÁN | (612, 620) |  |
| 20.json | Lyssavirus | TÊN_XÉT_NGHIỆM | (865, 875) |  |
| 20.json | 130/76 mmHg | KẾT_QUẢ_XÉT_NGHIỆM | (1179, 1190) |  |
| 20.json | 93 l/p | KẾT_QUẢ_XÉT_NGHIỆM | (1197, 1203) |  |
| 20.json | 36.3 độ C | KẾT_QUẢ_XÉT_NGHIỆM | (1215, 1224) |  |
| 20.json | nước bọt | TRIỆU_CHỨNG | (1486, 1494) |  |
| 20.json | chó | TRIỆU_CHỨNG | (1656, 1659) |  |
| 20.json | hang dơi | TRIỆU_CHỨNG | (1819, 1827) |  |
| 20.json | bệnh dại | CHẨN_ĐOÁN | (1938, 1946) |  |
| 20.json | vi rút dại | TRIỆU_CHỨNG | (2222, 2232) |  |
| 21.json | Rối loạn chuyển hóa tinh bột | CHẨN_ĐOÁN | (29, 57) |  |
| 21.json | amyloidosis | CHẨN_ĐOÁN | (59, 70) | E85, E85.3, E85.8 |
| 21.json | thoái hóa tinh bột | CHẨN_ĐOÁN | (313, 331) |  |
| 21.json | protein | TRIỆU_CHỨNG | (381, 388) |  |
| 21.json | protein bất thường | TRIỆU_CHỨNG | (442, 460) |  |
| 21.json | protein amyloid | TRIỆU_CHỨNG | (521, 536) |  |
| 21.json | cấu trúc | TRIỆU_CHỨNG | (573, 581) |  |
| 21.json | chức năng sinh lý | TRIỆU_CHỨNG | (597, 614) |  |
| 21.json | suy các cơ quan | TRIỆU_CHỨNG | (713, 728) |  |
| 21.json | bệnh thoái hóa tinh bột | CHẨN_ĐOÁN | (806, 829) |  |
| 21.json | amyloidosis | CHẨN_ĐOÁN | (1444, 1455) | E85, E85.3, E85.8 |
| 21.json | viêm dạ dày | TRIỆU_CHỨNG | (2159, 2170) |  |
| 21.json | omeprazole | THUỐC | (2222, 2232) | 7646 |
| 21.json | sỏi đoạn cuối ống mật chủ | TRIỆU_CHỨNG | (2271, 2296) |  |
| 21.json | men gan | TRIỆU_CHỨNG | (2332, 2339) |  |
| 21.json | Xét nghiệm chức năng gan | TÊN_XÉT_NGHIỆM | (2298, 2322) |  |
| 21.json | men gan | KẾT_QUẢ_XÉT_NGHIỆM | (2332, 2339) |  |
| 22.json | khó chịu | TRIỆU_CHỨNG | (52, 60) |  |
| 22.json | liều cao acetaminophen | THUỐC | (162, 184) | 161 |
| 22.json | nổi | TRIỆU_CHỨNG | (1346, 1349) |  |
| 22.json | acetaminophen | THUỐC | (1183, 1196) | 161 |
| 22.json | dị ứng | TRIỆU_CHỨNG | (1652, 1658) |  |
| 22.json | thời tiết | TRIỆU_CHỨNG | (1659, 1668) |  |
| 22.json | thức ăn | TRIỆU_CHỨNG | (1673, 1680) |  |
| 22.json | ast | TÊN_XÉT_NGHIỆM | (1967, 1970) |  |
| 22.json | 421 | KẾT_QUẢ_XÉT_NGHIỆM | (1971, 1974) |  |
| 22.json | alt | TÊN_XÉT_NGHIỆM | (1977, 1980) |  |
| 22.json | 336 | KẾT_QUẢ_XÉT_NGHIỆM | (1981, 1984) |  |
| 22.json | alp | TÊN_XÉT_NGHIỆM | (1987, 1990) |  |
| 22.json | 185 | KẾT_QUẢ_XÉT_NGHIỆM | (1991, 1994) |  |
| 22.json | bilirubin toàn phần | TÊN_XÉT_NGHIỆM | (1997, 2016) |  |
| 22.json | 0.9 | KẾT_QUẢ_XÉT_NGHIỆM | (2017, 2020) |  |
| 22.json | total bili | TÊN_XÉT_NGHIỆM | (2023, 2033) |  |
| 22.json | 6.7 | KẾT_QUẢ_XÉT_NGHIỆM | (2060, 2063) |  |
| 22.json | viêm gan virus | TÊN_XÉT_NGHIỆM | (2082, 2096) |  |
| 22.json | ferritin | TÊN_XÉT_NGHIỆM | (2110, 2118) |  |
| 22.json | ceruloplasmin | TÊN_XÉT_NGHIỆM | (2136, 2149) |  |
| 22.json | siêu âm bụng | TÊN_XÉT_NGHIỆM | (2243, 2255) |  |
| 22.json | doppler | TÊN_XÉT_NGHIỆM | (2259, 2266) |  |
| 22.json | chụp hida | TÊN_XÉT_NGHIỆM | (2293, 2302) |  |
| 22.json | túi mật | TRIỆU_CHỨNG | (2319, 2326) |  |
| 22.json | giãn nở | TRIỆU_CHỨNG | (2327, 2334) |  |
| 22.json | men gan | CHẨN_ĐOÁN | (2469, 2476) | F40.290 |
| 22.json | bilirubin máu | CHẨN_ĐOÁN | (2484, 2497) | E80.7, E80 |
| 23.json | các chất kích thích | TRIỆU_CHỨNG | (65, 84) |  |
| 23.json | cà phê | TRIỆU_CHỨNG | (89, 95) |  |
| 23.json | chè | TRIỆU_CHỨNG | (97, 100) |  |
| 23.json | thuốc lá | TRIỆU_CHỨNG | (102, 110) |  |
| 23.json | thời kỳ mãn kinh | TRIỆU_CHỨNG | (181, 197) |  |
| 23.json | tăng nhãn áp | TRIỆU_CHỨNG | (848, 860) |  |
| 23.json | phẫu thuật | TRIỆU_CHỨNG | (781, 791) |  |
| 24.json | mệt mỏi | TRIỆU_CHỨNG | (49, 56) |  |
| 24.json | vàng da | TRIỆU_CHỨNG | (58, 65) |  |
| 24.json | vàng mắt | TRIỆU_CHỨNG | (67, 75) |  |
| 24.json | sốt | TRIỆU_CHỨNG | (238, 241) |  |
| 24.json | HBsAg | TÊN_XÉT_NGHIỆM | (573, 578) |  |
| 24.json | Anti HBe | TÊN_XÉT_NGHIỆM | (584, 592) |  |
| 24.json | Anti HBc IgG | TÊN_XÉT_NGHIỆM | (605, 617) |  |
| 24.json | Anti HBc IgM | TÊN_XÉT_NGHIỆM | (623, 635) |  |
| 24.json | BC | KẾT_QUẢ_XÉT_NGHIỆM | (544, 546) |  |
| 24.json | N | KẾT_QUẢ_XÉT_NGHIỆM | (557, 558) |  |
| 24.json | da niêm mạc | TRIỆU_CHỨNG | (712, 723) |  |
| 24.json | vàng da | TRIỆU_CHỨNG | (860, 867) |  |
| 24.json | nước tiểu | TRIỆU_CHỨNG | (758, 767) |  |
| 24.json | vàng sậm | TRIỆU_CHỨNG | (795, 803) |  |
| 24.json | 43 mmol/l | KẾT_QUẢ_XÉT_NGHIỆM | (1075, 1084) |  |
| 24.json | 27 mmol/l | KẾT_QUẢ_XÉT_NGHIỆM | (1097, 1106) |  |
| 24.json | 5,9 mmol/l | KẾT_QUẢ_XÉT_NGHIỆM | (1120, 1130) |  |
| 24.json | 89 micromol/l | KẾT_QUẢ_XÉT_NGHIỆM | (1143, 1156) |  |
| 24.json | 542 U/l | KẾT_QUẢ_XÉT_NGHIỆM | (1229, 1236) |  |
| 24.json | 628 U/l | KẾT_QUẢ_XÉT_NGHIỆM | (1243, 1250) |  |
| 24.json | 234 U/l | KẾT_QUẢ_XÉT_NGHIỆM | (1257, 1264) |  |
| 24.json | prothrombin | TÊN_XÉT_NGHIỆM | (1334, 1345) |  |
| 24.json | vàng da | TRIỆU_CHỨNG | (1410, 1417) |  |
| 24.json | vàng mắt | TRIỆU_CHỨNG | (1419, 1427) |  |
| 24.json | cạo râu | TRIỆU_CHỨNG | (1458, 1465) |  |
| 24.json | virus viêm gan B | CHẨN_ĐOÁN | (1572, 1588) | A08.4 |
| 24.json | mệt mỏi | TRIỆU_CHỨNG | (1712, 1719) |  |
| 25.json | sì nước | TRIỆU_CHỨNG | (255, 262) |  |
| 25.json | tắc ống dẫn trứng | TRIỆU_CHỨNG | (757, 774) |  |

... truncated 319 more rows

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
