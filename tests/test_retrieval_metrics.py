from app.eval.retrieval_metrics import mrr, precision_at_k, recall_at_k, reciprocal_rank


def _result(source):
    return {"source": source, "text": "irrelevant"}


def test_precision_at_k_all_relevant():
    retrieved = [_result("a.txt"), _result("a.txt")]
    assert precision_at_k(retrieved, {"a.txt"}, k=2) == 1.0


def test_precision_at_k_partial():
    retrieved = [_result("a.txt"), _result("b.txt"), _result("c.txt")]
    assert precision_at_k(retrieved, {"a.txt"}, k=3) == 1 / 3


def test_precision_at_k_empty_retrieval():
    assert precision_at_k([], {"a.txt"}, k=5) == 0.0


def test_recall_at_k_captures_all_relevant():
    retrieved = [_result("a.txt"), _result("b.txt")]
    assert recall_at_k(retrieved, {"a.txt", "b.txt"}, k=2) == 1.0


def test_recall_at_k_partial():
    retrieved = [_result("a.txt")]
    assert recall_at_k(retrieved, {"a.txt", "b.txt"}, k=1) == 0.5


def test_recall_at_k_no_relevant_sources():
    assert recall_at_k([_result("a.txt")], set(), k=1) == 0.0


def test_reciprocal_rank_first_hit():
    retrieved = [_result("a.txt"), _result("b.txt")]
    assert reciprocal_rank(retrieved, {"a.txt"}) == 1.0


def test_reciprocal_rank_second_hit():
    retrieved = [_result("z.txt"), _result("a.txt")]
    assert reciprocal_rank(retrieved, {"a.txt"}) == 0.5


def test_reciprocal_rank_no_hit():
    retrieved = [_result("z.txt")]
    assert reciprocal_rank(retrieved, {"a.txt"}) == 0.0


def test_mrr_averages_across_queries():
    per_query_retrieved = [
        [_result("a.txt")],  # rank 1 -> 1.0
        [_result("z.txt"), _result("b.txt")],  # rank 2 -> 0.5
    ]
    per_query_relevant = [{"a.txt"}, {"b.txt"}]
    assert mrr(per_query_retrieved, per_query_relevant) == 0.75


def test_mrr_empty_batch():
    assert mrr([], []) == 0.0
