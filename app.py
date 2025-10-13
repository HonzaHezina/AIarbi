import gradio as gr
import asyncio
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import time
import os
from utils.logging_config import setup_logging, get_logger

# Initialize logging early using environment LOG_LEVEL if set
setup_logging()
logger = get_logger(__name__)

from core.main_arbitrage_system import MainArbitrageSystem
from core.ai_model import ArbitrageAI
from utils.config import *

class ArbitrageDashboard:
    def __init__(self):
        self.arbitrage_system = MainArbitrageSystem()
        self.execution_history = []
        self.performance_data = []

    def create_interface(self):
        with gr.Blocks(
            title="AI Crypto Arbitrage System",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            """
        ) as interface:

            gr.HTML("""
                <div style='text-align: center; padding: 20px;'>
                    <h1 style='color: white; font-size: 3em; margin-bottom: 10px;'>AI Crypto Arbitrage</h1>
                    <p style='color: #e0e0e0; font-size: 1.2em;'>Advanced Multi-Strategy Arbitrage Detection with Bellman-Ford & AI</p>
                </div>
            """)

            with gr.Tab("Live Arbitrage Scanner"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Configuration")

                        enabled_strategies = gr.CheckboxGroup(
                            choices=[
                                "DEX/CEX Arbitrage", 
                                "Cross-Exchange", 
                                "Triangular", 
                                "Wrapped Tokens", 
                                "Statistical AI"
                            ],
                            value=["DEX/CEX Arbitrage", "Cross-Exchange"],
                            label="Active Strategies"
                        )

                        trading_pairs = gr.CheckboxGroup(
                            choices=DEFAULT_SYMBOLS,
                            value=["BTC/USDT", "ETH/USDT", "BNB/USDT"],
                            label="Trading Pairs"
                        )

                        min_profit = gr.Slider(
                            minimum=0.1, 
                            maximum=3.0, 
                            value=0.5, 
                            step=0.1,
                            label="Minimum Profit Threshold (%)"
                        )

                        max_opportunities = gr.Slider(
                            minimum=1, 
                            maximum=20, 
                            value=5, 
                            step=1,
                            label="Max Opportunities to Show"
                        )

                        auto_refresh = gr.Checkbox(
                            label="Auto Refresh (30s)", 
                            value=True
                        )

                        demo_mode = gr.Checkbox(
                            label="Demo Mode (No Real Trading)", 
                            value=True
                        )

                        scan_button = gr.Button(
                            "Scan Opportunities",
                            variant="primary",
                            size="lg"
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("### Live Opportunities")

                        opportunities_df = gr.DataFrame(
                            headers=["Strategy", "Token", "Path", "Profit %", "AI Score", "Status"],
                            label="Detected Arbitrage Opportunities",
                            interactive=False
                        )

                        with gr.Row():
                            total_opportunities = gr.Number(
                                label="Total Found", 
                                value=0, 
                                interactive=False
                            )
                            avg_profit = gr.Number(
                                label="Avg Profit %", 
                                value=0, 
                                interactive=False
                            )
                            ai_confidence = gr.Number(
                                label="AI Confidence", 
                                value=0, 
                                interactive=False
                            )

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### AI Market Analysis")
                        ai_analysis_text = gr.Textbox(
                            lines=8,
                            label="AI Insights & Recommendations",
                            interactive=False
                        )

                    with gr.Column():
                        gr.Markdown("### Performance Chart")
                        performance_chart = gr.Plot(label="Profit Over Time")

            with gr.Tab(" Execution Center"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Manual Execution")

                        selected_opportunity = gr.Dropdown(
                            label="Select Opportunity to Execute",
                            choices=[],
                            interactive=True
                        )

                        execution_amount = gr.Number(
                            label="Execution Amount (USDT)", 
                            value=100, 
                            minimum=10, 
                            maximum=10000
                        )

                        with gr.Row():
                            execute_button = gr.Button(
                                "Execute Arbitrage",
                                variant="secondary"
                            )
                            stop_all_button = gr.Button(
                                "Stop All",
                                variant="stop"
                            )

                    with gr.Column():
                        gr.Markdown("###  Execution History")
                        execution_history_df = gr.DataFrame(
                            headers=["Time", "Strategy", "Token", "Profit", "Status"],
                            label="Recent Executions"
                        )

            with gr.Tab(" Analytics & Insights"):
                with gr.Row():
                    with gr.Column():
                        strategy_performance_chart = gr.Plot(
                            label="Strategy Performance Comparison"
                        )

                    with gr.Column():
                        market_heatmap = gr.Plot(
                            label="Market Opportunities Heatmap"
                        )

                with gr.Row():
                    risk_analysis = gr.Textbox(
                        lines=6,
                        label=" Risk Analysis & Warnings",
                        interactive=False
                    )

            # Event handlers
            scan_button.click(
                fn=self.scan_arbitrage_opportunities,
                inputs=[enabled_strategies, trading_pairs, min_profit, max_opportunities, demo_mode],
                outputs=[opportunities_df, ai_analysis_text, performance_chart, 
                        total_opportunities, avg_profit, ai_confidence, selected_opportunity]
            )

            execute_button.click(
                fn=self.execute_selected_opportunity,
                inputs=[selected_opportunity, execution_amount, demo_mode],
                outputs=[execution_history_df, ai_analysis_text]
            )

            # Auto-refresh functionality
            if auto_refresh:
                import threading
                def periodic_refresh():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    while True:
                        loop.run_until_complete(self.auto_refresh_scan(
                            enabled_strategies, trading_pairs, min_profit, max_opportunities, demo_mode
                        ))
                        time.sleep(30)  # Refresh every 30 seconds

                threading.Thread(target=periodic_refresh, daemon=True).start()

        # Debugging: Log the size of the response being returned
        logger.debug(f"Debug: Returning response of size: {len(str(interface))} characters")

        # Debugging: Log response size before sending
        def log_response_size(response):
            response_size = len(response.body) if hasattr(response, 'body') else 0
            logger.debug(f" Debug: Response size: {response_size} bytes")
            return response

        # Wrap the Gradio interface with a middleware to log response size
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import Response

        class ResponseSizeLoggerMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                if isinstance(response, Response):
                    log_response_size(response)
                return response

        # Add middleware directly to the FastAPI app
        app = interface.app
        app.add_middleware(ResponseSizeLoggerMiddleware)

        return interface

    async def scan_arbitrage_opportunities(self, strategies, pairs, min_profit, max_opps, demo_mode):
        """Main scanning function"""
        try:
            # Convert strategy names
            strategy_map = {
                "DEX/CEX Arbitrage": "dex_cex",
                "Cross-Exchange": "cross_exchange", 
                "Triangular": "triangular",
                "Wrapped Tokens": "wrapped_tokens",
                "Statistical AI": "statistical"
            }

            enabled_strategies = [strategy_map[s] for s in strategies if s in strategy_map]

            # Run arbitrage scan
            opportunities = await self.arbitrage_system.run_full_arbitrage_scan(
                enabled_strategies, pairs, min_profit
            )

            # Limit results
            opportunities = opportunities[:max_opps]

            # Prepare DataFrame
            df_data = []
            total_profit = 0
            total_confidence = 0

            for opp in opportunities:
                df_data.append([
                    opp.get('strategy', 'Unknown'),
                    opp.get('token', 'N/A'),
                    opp.get('path_summary', 'N/A'),
                    f"{opp.get('profit_pct', 0):.3f}%",
                    f"{opp.get('ai_confidence', 0):.2f}",
                    opp.get('status', 'Ready')
                ])

                total_profit += opp.get('profit_pct', 0)
                total_confidence += opp.get('ai_confidence', 0)

            # Calculate averages
            avg_profit_val = total_profit / len(opportunities) if opportunities else 0
            avg_confidence_val = total_confidence / len(opportunities) if opportunities else 0

            # Generate AI analysis
            ai_analysis = await self.generate_ai_market_analysis(opportunities)

            # Generate performance chart
            chart = self.create_performance_chart()

            # Generate dropdown choices for execution
            execution_choices = [f"{opp['strategy']} - {opp['token']} ({opp['profit_pct']:.2f}%)" 
                               for opp in opportunities]

            return (
                df_data,
                ai_analysis, 
                chart,
                len(opportunities),
                avg_profit_val,
                avg_confidence_val,
                gr.Dropdown(choices=execution_choices)
            )

        except Exception as e:
            error_msg = f"Error scanning opportunities: {str(e)}"
            return [], error_msg, go.Figure(), 0, 0, 0, gr.Dropdown(choices=[])

    async def execute_selected_opportunity(self, selected_opp, amount, demo_mode):
        """Execute selected arbitrage opportunity"""
        if not selected_opp:
            return self.execution_history, " No opportunity selected"

        try:
            # Parse selected opportunity
            parts = selected_opp.split(" - ")
            if len(parts) < 2:
                return self.execution_history, " Invalid opportunity format"

            strategy = parts[0]
            token = parts[1].split(" (")[0]

            if demo_mode:
                # Simulate execution
                result = {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'strategy': strategy,
                    'token': token,
                    'profit': f"+{amount * 0.005:.2f} USDT",  # Simulated 0.5% profit
                    'status': 'SIMULATED '
                }

                self.execution_history.append([
                    result['time'],
                    result['strategy'], 
                    result['token'],
                    result['profit'],
                    result['status']
                ])

                analysis = f" Simulated execution completed successfully!\n"
                analysis += f"Strategy: {strategy}\n"
                analysis += f"Token: {token}\n" 
                analysis += f"Simulated Profit: {result['profit']}\n"
                analysis += f" This was a DEMO execution - no real trades were made."

            else:
                # Real execution (implement with actual trading logic)
                analysis = " Real trading not implemented for safety. Enable demo mode."

            return self.execution_history, analysis

        except Exception as e:
            error_analysis = f" Execution failed: {str(e)}"
            return self.execution_history, error_analysis

    async def auto_refresh_scan(self, strategies, pairs, min_profit, max_opps, demo_mode):
        """Auto-refresh function for live updates"""
        return await self.scan_arbitrage_opportunities(strategies, pairs, min_profit, max_opps, demo_mode)

    async def generate_ai_market_analysis(self, opportunities):
        """Generate AI analysis of current market conditions"""
        if not opportunities:
            return " No arbitrage opportunities detected. Market may be efficient or low volatility period."

        analysis = f"AI Market Analysis ({datetime.now().strftime('%H:%M:%S')})\n\n"
        
        # Strategy breakdown
        strategies = {}
        for opp in opportunities:
            strategy = opp.get('strategy', 'Unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        analysis += "Strategy Distribution:\n"
        for strategy, count in strategies.items():
            analysis += f"- {strategy}: {count} opportunities\n"
        
        # Best opportunity
        if opportunities:
            best = max(opportunities, key=lambda x: x.get('profit_pct', 0))
            analysis += f"\nBest Opportunity:\n"
            analysis += f"- Strategy: {best.get('strategy', 'N/A')}\n"
            analysis += f"- Token: {best.get('token', 'N/A')}\n"
            analysis += f"- Expected Profit: {best.get('profit_pct', 0):.3f}%\n"
            analysis += f"- AI Confidence: {best.get('ai_confidence', 0):.2f}/1.0\n"
        
        # Market conditions
        avg_profit = sum(opp.get('profit_pct', 0) for opp in opportunities) / len(opportunities)
        
        analysis += f"\nMarket Conditions:\n"
        if avg_profit > 1.0:
            analysis += "High volatility - Excellent arbitrage conditions\n"
        elif avg_profit > 0.5:
            analysis += "Moderate volatility - Good opportunities available\n"
        else:
            analysis += "Low volatility - Limited opportunities\n"
        
        analysis += "\nRisk Assessment: Always verify opportunities manually before execution in live trading."
        
        return analysis

    def create_performance_chart(self):
        """Create performance chart"""
        # Generate sample performance data
        if not hasattr(self, 'chart_data'):
            import random
            times = [datetime.now().timestamp() - i*3600 for i in range(24, 0, -1)]
            profits = [random.uniform(-0.5, 2.0) for _ in times]

            self.chart_data = {
                'times': [datetime.fromtimestamp(t) for t in times],
                'profits': profits
            }

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=self.chart_data['times'],
            y=self.chart_data['profits'],
            mode='lines+markers',
            name='Profit %',
            line=dict(color='#00ff88', width=3),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title="24h Arbitrage Performance",
            xaxis_title="Time",
            yaxis_title="Profit %",
            template="plotly_dark",
            height=300
        )

        return fig

# Launch the app
if __name__ == "__main__":
    # Debugging: Log application start
    logger.info("Debug: Application is starting...")

    # Debugging: Log Gradio version
    import gradio
    logger.debug(f" Debug: Gradio version: {gradio.__version__}")

    # Debugging: Log environment variables at debug level to avoid noise
    logger.debug(" Debug: Environment variables:")
    for key, value in os.environ.items():
        logger.debug(f"{key}: {value}")

    dashboard = ArbitrageDashboard()

    # Set minimal configuration for testing
    demo_mode = True
    strategies = ['dex_cex']
    pairs = ['BTC/USDT', 'ETH/USDT']
    min_profit = 0.1
    max_opps = 5

    # Debugging: Log test configuration
    logger.debug(f" Debug: Running in demo mode: {demo_mode}")
    logger.debug(f" Debug: Strategies: {strategies}")
    logger.debug(f" Debug: Pairs: {pairs}")
    logger.debug(f" Debug: Min profit: {min_profit}")
    logger.debug(f" Debug: Max opportunities: {max_opps}")

    app = dashboard.create_interface()

    app.launch(
        server_name="0.0.0.0",        server_port=7860,
        debug=True    )
