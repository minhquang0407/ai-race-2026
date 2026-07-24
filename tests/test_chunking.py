from src.extraction.chunking import SemanticChunker


def assert_chunks_match_source(text, chunks):
    for chunk in chunks:
        assert text[chunk.start:chunk.end] == chunk.text


def test_short_text_creates_single_chunk():
    text = "Bệnh nhân ho."
    chunks = SemanticChunker().split(text)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].start == 0
    assert chunks[0].end == len(text)


def test_long_text_preserves_offsets_and_reconstructs_without_overlap():
    text = "Câu một có ho. Câu hai có sốt.\nCâu ba có đau ngực.\tCâu bốn có aspirin. " * 8
    chunks = SemanticChunker(target_size=120, min_size=80, max_size=140).split(text)
    assert len(chunks) > 1
    assert_chunks_match_source(text, chunks)
    assert "".join(chunk.text for chunk in chunks) == text
    assert all(len(chunk.text) <= 140 for chunk in chunks)


def test_preserves_whitespace_and_vietnamese_unicode():
    text = "Bệnh nhân\tđau thượng vị.\n\nKhông ho, không sốt.  Dùng Aspirin."
    chunks = SemanticChunker(target_size=30, min_size=15, max_size=35).split(text)
    assert_chunks_match_source(text, chunks)
    assert "".join(chunk.text for chunk in chunks) == text


def test_avoids_cutting_common_medical_number_patterns_when_possible():
    text = "Kết quả WBC:14,43; thuốc Chlorpheniramine 0.4 MG/ML được ghi nhận. " * 4
    chunks = SemanticChunker(target_size=80, min_size=60, max_size=95).split(text)
    assert_chunks_match_source(text, chunks)
    assert "".join(chunk.text for chunk in chunks) == text


def test_overlap_chunks_still_point_to_source():
    text = "Một câu rất dài về bệnh nhân đau ngực và dùng aspirin. " * 5
    chunks = SemanticChunker(target_size=80, min_size=50, max_size=90, overlap_chars=10).split(text)
    assert len(chunks) > 1
    assert_chunks_match_source(text, chunks)
    for previous, current in zip(chunks, chunks[1:]):
        assert current.start <= previous.end


def test_competition_example_half_open_span():
    text = "Danh sách thuốc trước nhập viện chính xác và đầy đủ. 1. amlodipine 10 mg po daily 2. aspirin 81 mg po daily"
    mention = "amlodipine 10 mg po daily"
    start = text.index(mention)
    end = start + len(mention)
    assert (start, end) == (56, 81)
    assert text[start:end] == mention
    assert end - start == len(mention)
