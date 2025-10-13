import pytest
import asyncio

class DummyAI:
    """Deterministic AI stub for ranking tests."""
    async def rank_opportunities(self, opportunities):
        # Deterministic scoring similar to production but simplified
        for opp in opportunities:
            profit_pct = opp.get('profit_pct', 0)
            risk_level = opp.get('risk_level', 'HIGH')
            exec_time = opp.get('execution_time_estimate', 60)
            confidence = opp.get('ai_confidence', 0.5)
    
            profit_score = min(profit_pct / 2.0, 1.0) * 0.4
            if risk_level == 'LOW':
                risk_score = 0.3
            elif risk_level == 'MEDIUM':
                risk_score = 0.2
            else:
                risk_score = 0.1
            complexity_score = max(0, 1 - (exec_time / 300)) * 0.2
            confidence_score = confidence * 0.1
    
            ai_score = min(1.0, profit_score + risk_score + complexity_score + confidence_score)
            opp['ai_score'] = ai_score
    
        # Stable sort by ai_score desc, tie-breaker profit_pct desc
        return sorted(opportunities, key=lambda x: (x['ai_score'], x.get('profit_pct', 0)), reverse=True)

@pytest.mark.asyncio
async def test_dummy_ai_ranks_deterministically():
    ai = DummyAI()

    opportunities = [
        {'id': 'a', 'profit_pct': 1.0, 'risk_level': 'MEDIUM', 'execution_time_estimate': 60, 'ai_confidence': 0.5},
        {'id': 'b', 'profit_pct': 0.5, 'risk_level': 'LOW', 'execution_time_estimate': 30, 'ai_confidence': 0.9},
        {'id': 'c', 'profit_pct': 2.0, 'risk_level': 'HIGH', 'execution_time_estimate': 120, 'ai_confidence': 0.4},
        {'id': 'd', 'profit_pct': 1.5, 'risk_level': 'LOW', 'execution_time_estimate': 10, 'ai_confidence': 0.8},
    ]

    ranked = await ai.rank_opportunities(list(opportunities))  # pass a copy

    assert isinstance(ranked, list)
    # Ensure ai_score present and descending
    scores = [r['ai_score'] for r in ranked]
    assert scores == sorted(scores, reverse=True)

    # Ensure deterministic order: run again and compare
    ranked2 = await ai.rank_opportunities(list(opportunities))
    order1 = [r['id'] for r in ranked]
    order2 = [r['id'] for r in ranked2]
    assert order1 == order2, "Ranking should be deterministic between runs"

    # Sanity: expect one of the low-risk high-confidence items to rank high
    assert 'd' in order1[:2] or 'b' in order1[:2]