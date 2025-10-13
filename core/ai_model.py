import asyncio
import json
import re
from typing import Dict, List, Any, Optional

# Optional heavy ML deps — guarded to allow running tests/demos without transformers/torch.
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline  # type: ignore
    import torch  # type: ignore
    HAVE_TRANSFORMERS = True
except Exception:
    AutoTokenizer = None  # type: ignore
    AutoModelForCausalLM = None  # type: ignore
    pipeline = None  # type: ignore
    torch = None  # type: ignore
    HAVE_TRANSFORMERS = False

from utils.logging_config import get_logger

logger = get_logger(__name__)

class ArbitrageAI:
    """
    AI model for crypto arbitrage analysis using HuggingFace models
    """

    def __init__(self):
        self.model_id = "microsoft/DialoGPT-medium"  # Lightweight alternative
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.loaded = False

        # Try to load model
        self.load_model()

    def load_model(self):
        """Load the AI model"""
        try:
            logger.info("Loading AI model...")
 
            # Use a lighter model for HuggingFace Spaces
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
 
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
 
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=200,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id
            )
 
            self.loaded = True
            logger.info("AI model loaded successfully")
 
        except Exception as e:
            logger.exception("Failed to load AI model: %s", e)
            logger.warning("Falling back to rule-based analysis")
            self.loaded = False

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.loaded

    async def assess_opportunity_risk(self, cycle: Dict, price_data: Dict, profit_analysis: Dict) -> Dict:
        """Assess risk for an arbitrage opportunity"""
        try:
            risk_score = 0
            risk_factors = []

            # Profit-based risk
            profit_pct = profit_analysis.get('profit_pct', 0)
            if profit_pct > 5.0:
                risk_score += 3
                risk_factors.append("Suspicious high profit")
            elif profit_pct < 0.5:
                risk_score += 1
                risk_factors.append("Low profit margin")

            # Path complexity risk
            path_length = len(cycle.get('path', []))
            if path_length > 4:
                risk_score += 2
                risk_factors.append("Complex execution path")

            # Exchange risk assessment
            path = cycle.get('path', [])
            exchanges = set()
            for node in path:
                if '@' in node:
                    exchange = node.split('@')[1]
                    exchanges.add(exchange)

            # Risk by exchange type
            high_risk_exchanges = {'dex', 'uniswap', 'sushiswap'}
            for exchange in exchanges:
                if any(risky in exchange.lower() for risky in high_risk_exchanges):
                    risk_score += 1
                    risk_factors.append(f"DEX risk: {exchange}")

            # Calculate confidence and risk level
            confidence = max(0, min(1, 1 - (risk_score / 10)))

            if risk_score <= 2:
                risk_level = "LOW"
            elif risk_score <= 5:
                risk_level = "MEDIUM"  
            else:
                risk_level = "HIGH"

            return {
                'confidence': confidence,
                'risk_level': risk_level,
                'risk_score': risk_score,
                'risk_factors': risk_factors,
                'execution_time': self.estimate_execution_time(cycle),
                'recommended_capital': min(1000, profit_analysis.get('required_capital', 100))
            }

        except Exception as e:
            logger.exception("Error in risk assessment: %s", e)
            return {
                'confidence': 0.5,
                'risk_level': 'UNKNOWN',
                'risk_score': 5,
                'risk_factors': ['Analysis error'],
                'execution_time': 60,
                'recommended_capital': 100
            }

    def estimate_execution_time(self, cycle: Dict) -> int:
        """Estimate execution time in seconds"""
        path = cycle.get('path', [])
        base_time = 10  # 10 seconds base

        # Add time per hop
        additional_time = len(path) * 5

        # Add time for DEX operations (higher latency)
        dex_operations = sum(1 for node in path if any(dex in node.lower() 
                                                     for dex in ['uniswap', 'sushi', 'pancake']))
        additional_time += dex_operations * 30  # 30 seconds per DEX op

        return base_time + additional_time

    async def rank_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Rank opportunities by AI score"""
        try:
            # Calculate AI score for each opportunity
            for opp in opportunities:
                ai_score = self.calculate_ai_score(opp)
                opp['ai_score'] = ai_score

            # Sort by AI score (highest first)
            ranked_opportunities = sorted(
                opportunities, 
                key=lambda x: x.get('ai_score', 0), 
                reverse=True
            )

            return ranked_opportunities

        except Exception as e:
            logger.exception("Error ranking opportunities: %s", e)
            # Fallback to profit-based ranking
            return sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)

    def calculate_ai_score(self, opportunity: Dict) -> float:
        """Calculate AI score for opportunity"""
        try:
            score = 0.0

            # Profit weight (40%)
            profit_pct = opportunity.get('profit_pct', 0)
            profit_score = min(profit_pct / 2.0, 1.0) * 0.4
            score += profit_score

            # Risk weight (30%) - inverted
            risk_level = opportunity.get('risk_level', 'HIGH')
            if risk_level == 'LOW':
                risk_score = 0.3
            elif risk_level == 'MEDIUM':
                risk_score = 0.2
            else:
                risk_score = 0.1
            score += risk_score

            # Execution complexity (20%)
            exec_time = opportunity.get('execution_time_estimate', 60)
            complexity_score = max(0, 1 - (exec_time / 300)) * 0.2  # 5 min max
            score += complexity_score

            # Confidence weight (10%)
            confidence = opportunity.get('ai_confidence', 0.5)
            confidence_score = confidence * 0.1
            score += confidence_score

            return min(1.0, score)

        except Exception as e:
            logger.exception("Error calculating AI score: %s", e)
            return 0.5  # Default neutral score

    async def generate_market_analysis(self, opportunities: List[Dict], market_data: Dict) -> str:
        """Generate market analysis text"""
        try:
            if not opportunities:
                return " Market Analysis: No significant arbitrage opportunities detected. Market appears efficient."

            analysis_parts = []

            # Opportunity summary
            total_opps = len(opportunities)
            avg_profit = sum(opp.get('profit_pct', 0) for opp in opportunities) / total_opps

            analysis_parts.append(f" Detected {total_opps} arbitrage opportunities")
            analysis_parts.append(f" Average expected profit: {avg_profit:.2f}%")

            # Strategy breakdown
            strategies = {}
            for opp in opportunities:
                strategy = opp.get('strategy', 'unknown')
                strategies[strategy] = strategies.get(strategy, 0) + 1

            analysis_parts.append("\n Strategy Distribution:")
            for strategy, count in strategies.items():
                analysis_parts.append(f" {strategy}: {count}")

            # Best opportunity
            best_opp = max(opportunities, key=lambda x: x.get('ai_score', 0))
            analysis_parts.append(f"\n Top Opportunity:")
            analysis_parts.append(f" {best_opp.get('strategy', 'Unknown')} - {best_opp.get('token', 'N/A')}")
            analysis_parts.append(f" Expected Profit: {best_opp.get('profit_pct', 0):.2f}%")
            analysis_parts.append(f" AI Score: {best_opp.get('ai_score', 0):.2f}")

            # Market condition assessment
            if avg_profit > 1.5:
                condition = " High volatility - Excellent conditions"
            elif avg_profit > 0.8:
                condition = " Moderate volatility - Good opportunities"
            else:
                condition = " Low volatility - Limited opportunities"

            analysis_parts.append(f"\n{condition}")
            analysis_parts.append("\n Always verify before execution in live trading.")

            return "\n".join(analysis_parts)

        except Exception as e:
            logger.exception("Error generating market analysis: %s", e)
            return " Unable to generate market analysis due to technical error."

    def analyze_dex_cex_timing(self, cex_exchange: str, dex_protocol: str, token: str) -> float:
        """Analyze optimal timing for DEX/CEX arbitrage"""
        # Simple heuristic-based timing analysis
        base_weight = 1.0

        # Adjust for exchange liquidity
        high_liquidity_cex = ['binance', 'coinbase', 'kraken']
        high_liquidity_dex = ['uniswap_v3', 'sushiswap']

        if cex_exchange.lower() in high_liquidity_cex:
            base_weight *= 1.05
        if dex_protocol.lower() in high_liquidity_dex:
            base_weight *= 1.05

        # Adjust for token volatility
        volatile_tokens = ['BTC', 'ETH']
        if token in volatile_tokens:
            base_weight *= 0.98  # Slightly lower weight due to higher risk

        return base_weight

    def calculate_volatility_risk(self, token: str, transfer_time_minutes: int) -> float:
        """Calculate volatility risk during transfer"""
        base_volatility = {
            'BTC': 0.02,   # 2% per hour
            'ETH': 0.025,  # 2.5% per hour  
            'BNB': 0.03,   # 3% per hour
            'USDT': 0.001, # 0.1% per hour
            'USDC': 0.001  # 0.1% per hour
        }

        token_volatility = base_volatility.get(token, 0.035)  # Default 3.5%
        time_risk = (transfer_time_minutes / 60) * token_volatility

        return min(0.1, time_risk)  # Cap at 10%
