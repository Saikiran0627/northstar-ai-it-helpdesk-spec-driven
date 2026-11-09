from northstar_helpdesk.rag import KnowledgeBase


def test_t_rag_001_vpn_retrieval_returns_citation():
    kb = KnowledgeBase("knowledge_base")
    results, latency = kb.search("VPN keeps disconnecting remote presentation")
    assert latency >= 0
    assert results
    assert any("vpn" in chunk.source.lower() for chunk in results)
    assert all(chunk.citation_id.startswith("N") for chunk in results)


def test_t_rag_002_empty_query_returns_no_results():
    kb = KnowledgeBase("knowledge_base")
    results, _ = kb.search("")
    assert results == []
