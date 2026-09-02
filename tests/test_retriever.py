from app.retriever import reciprocal_rank_fusion


def _chunk(id_, source="doc.txt", text="text"):
    return {"id": id_, "source": source, "text": text}


def test_rrf_ranks_items_appearing_in_both_lists_highest():
    dense = [_chunk(1), _chunk(2), _chunk(3)]
    bm25 = [_chunk(3), _chunk(4), _chunk(1)]
    fused = reciprocal_rank_fusion([dense, bm25], k=60)
    fused_ids = [c["id"] for c in fused]
    # id 1 appears at rank 1 in dense and rank 3 in bm25; id 3 at rank 3 in dense
    # and rank 1 in bm25 -> both should outrank id 2 and id 4, which appear once each.
    assert fused_ids[0] in (1, 3)
    assert fused_ids[1] in (1, 3)
    assert set(fused_ids[:2]) == {1, 3}


def test_rrf_single_list_preserves_order():
    dense = [_chunk(1), _chunk(2), _chunk(3)]
    fused = reciprocal_rank_fusion([dense], k=60)
    assert [c["id"] for c in fused] == [1, 2, 3]


def test_rrf_empty_lists():
    assert reciprocal_rank_fusion([[], []]) == []


def test_rrf_dedupes_and_keeps_first_seen_payload():
    dense = [_chunk(1, text="dense version")]
    bm25 = [_chunk(1, text="bm25 version")]
    fused = reciprocal_rank_fusion([dense, bm25])
    assert len(fused) == 1
    assert fused[0]["text"] == "dense version"
    # score should be the sum of both lists' contributions at rank 1
    assert fused[0]["fused_score"] == 1 / 61 + 1 / 61
