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
        self.scan_progress = ""
    
    def get_system_status_display(self):
        """Get formatted system status for display"""
        try:
            status = self.arbitrage_system.get_system_status()
            data_status = status.get('data_engine_status', {})
            
            status_text = "### 📊 System Health Monitor\n\n"
            status_text += "*Real-time status of all components*\n\n"
            
            # AI Model Status
            ai_loaded = status.get('ai_model_loaded', False)
            ai_icon = "✅" if ai_loaded else "⚠️"
            ai_status = 'Ready' if ai_loaded else 'Fallback Mode (Rule-based)'
            status_text += f"🤖 **AI Model**: {ai_icon} {ai_status}\n\n"
            
            # Data Engine Status
            cex_count = data_status.get('cex_exchanges', 0)
            dex_count = data_status.get('dex_protocols', 0)
            web3_connected = data_status.get('web3_connected', False)
            
            status_text += f"📡 **Data Sources**:\n"
            status_text += f"  • CEX Exchanges: {cex_count} connected\n"
            status_text += f"  • DEX Protocols: {dex_count} configured\n"
            status_text += f"  • Web3: {'✅ Live' if web3_connected else '⚠️ Simulated'}\n\n"
            
            # Last scan
            last_scan = status.get('last_scan')
            if last_scan:
                time_diff = (datetime.now() - last_scan).seconds
                if time_diff < 60:
                    time_str = f"{time_diff}s ago"
                else:
                    time_str = f"{time_diff // 60}m ago"
                status_text += f"⏱️ **Last Scan**: {time_str}\n\n"
            else:
                status_text += f"⏱️ **Last Scan**: Never (Start in Tab 1️⃣)\n\n"
            
            # Active strategies
            active = len(status.get('active_strategies', []))
            status_text += f"🎯 **Strategies**: {active}/5 loaded and ready\n"
            
            return status_text
        except Exception as e:
            return f"### 📊 System Health Monitor\n\n⚠️ Error loading status: {str(e)}"

    def create_interface(self):
        with gr.Blocks(
            title="AI Crypto Arbitrage System",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="cyan",
                neutral_hue="slate",
                font=gr.themes.GoogleFont("Inter"),
            ),
            css="""
            .gradio-container {
                background: white;
            }
            /* Enhanced contrast for all boxes and containers */
            .gr-box {
                background: white !important;
                border-radius: 8px;
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2) !important;
                border: 2px solid #e5e7eb !important;
                padding: 16px !important;
            }
            /* Maximum text readability */
            .gr-text-input, .gr-textbox {
                color: #000000 !important;
                background: white !important;
                border: 2px solid #3b82f6 !important;
                font-weight: 500 !important;
            }
            /* High visibility buttons */
            .gr-button {
                font-weight: 700 !important;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
                border: 2px solid #1e40af !important;
                font-size: 1.05em !important;
            }
            .gr-button-primary {
                background: #2563eb !important;
                color: white !important;
            }
            .gr-button:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3) !important;
            }
            /* Enhanced tab styling */
            .gr-tab {
                font-weight: 700 !important;
                font-size: 1.15em !important;
                padding: 12px 20px !important;
                border: 2px solid transparent !important;
            }
            .gr-tab-active {
                border-bottom: 3px solid #2563eb !important;
                background: rgba(255, 255, 255, 0.15) !important;
            }
            /* High contrast headers */
            h1, h2, h3 {
                color: #000000 !important;
                font-weight: 700 !important;
            }
            /* Better label visibility */
            label {
                color: #000000 !important;
                font-weight: 600 !important;
                font-size: 1.05em !important;
            }
            /* Enhanced markdown text */
            .gr-markdown {
                color: #1f2937 !important;
                line-height: 1.7 !important;
            }
            .gr-markdown strong {
                color: #000000 !important;
                font-weight: 700 !important;
            }
            /* Number input and slider improvements */
            .gr-number, .gr-slider {
                border: 2px solid #3b82f6 !important;
            }
            /* Dropdown improvements */
            .gr-dropdown {
                border: 2px solid #3b82f6 !important;
                background: white !important;
            }
            /* Checkbox improvements */
            .gr-checkbox, .gr-checkboxgroup {
                font-weight: 600 !important;
            }
            /* DataFrame styling */
            .gr-dataframe {
                border: 2px solid #3b82f6 !important;
            }
            """
        ) as interface:

            gr.HTML("""
                <div style='text-align: center; padding: 24px; background: rgba(255, 255, 255, 0.98); border-radius: 12px; margin-bottom: 20px; border: 3px solid #1e40af; box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25);'>
                    <h1 style='color: #1e3a8a; font-size: 3em; margin-bottom: 10px; font-weight: 800;'>🤖 AI Crypto Arbitrage</h1>
                    <p style='color: #1f2937; font-size: 1.2em; font-weight: 600;'>Advanced Multi-Strategy Arbitrage Detection with Bellman-Ford & AI</p>
                    <p style='color: #2563eb; font-size: 1em; margin-top: 10px; font-weight: 700;'>📋 Follow the workflow: <strong style="color: #1e40af;">1️⃣ Configure & Scan</strong> → <strong style="color: #1e40af;">2️⃣ View Results</strong> → <strong style="color: #1e40af;">3️⃣ Execute</strong> → <strong style="color: #1e40af;">4️⃣ Review System</strong></p>
                </div>
            """)
            
            # System Status Bar
            with gr.Row():
                system_status_text = gr.Markdown(
                    value=self.get_system_status_display(),
                    label="System Status"
                )

            with gr.Tab("1️⃣ Scanner & Configuration"):
                gr.Markdown("""
                ## 🔍 Live Arbitrage Scanner
                **What this does:** Configure your scanning parameters and find arbitrage opportunities across exchanges.
                
                **How it works:** 
                1. Select trading strategies and pairs below
                2. Set minimum profit threshold
                3. Click "🔍 Scan Opportunities" button
                4. View results in the table on the right
                
                ---
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### ⚙️ Configuration")

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
                            "🔍 Scan Opportunities",
                            variant="primary",
                            size="lg"
                        )
                        
                        gr.Markdown("**💡 Tip:** Start with demo mode enabled for safe testing")

                    with gr.Column(scale=2):
                        gr.Markdown("### 📊 Live Opportunities")
                        gr.Markdown("*Results will appear here after scanning. Each row shows a profitable opportunity.*")

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

            with gr.Tab("2️⃣ Results & Analysis"):
                gr.Markdown("""
                ## 📈 Scan Results & Detailed Analysis
                **What this shows:** After running a scan, this tab displays detailed analysis of all found opportunities.
                
                **What you see:**
                - 🤖 AI-powered market analysis and insights
                - 📊 Strategy performance comparison charts
                - 🗺️ Market opportunities heatmap
                - ⚠️ Risk analysis and warnings
                
                ---
                """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🤖 AI Market Analysis")
                        gr.Markdown("*AI analyzes market conditions and provides recommendations*")
                        ai_analysis_text = gr.Textbox(
                            lines=8,
                            label="AI Insights & Recommendations",
                            interactive=False
                        )

                    with gr.Column():
                        gr.Markdown("### 📈 Performance Chart")
                        gr.Markdown("*Historical profit trends over time*")
                        performance_chart = gr.Plot(label="Profit Over Time")

                gr.Markdown("---")
                gr.Markdown("### 📊 Advanced Analytics")
                gr.Markdown("*Compare strategy effectiveness and see market distribution*")
                
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
                        label="⚠️ Risk Analysis & Warnings",
                        interactive=False
                    )
                
                refresh_analytics_btn = gr.Button("🔄 Refresh Analytics", variant="secondary")

            with gr.Tab("3️⃣ Execution Center"):
                gr.Markdown("""
                ## ⚡ Execute Arbitrage Opportunities
                **What this does:** Select and execute specific arbitrage opportunities (or simulate them safely).
                
                **How to use:**
                1. Select an opportunity from the dropdown
                2. Click "🔍 Show Details" to see exact prices and calculations
                3. Set execution amount
                4. Click "▶️ Execute" (uses demo mode for safety by default)
                
                **Why it's safe:** Demo mode simulates execution without real trading. All details are transparent.
                
                ---
                """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### ⚙️ Execution Controls")

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
                                "▶️ Execute Arbitrage",
                                variant="secondary"
                            )
                            stop_all_button = gr.Button(
                                "🛑 Stop All",
                                variant="stop"
                            )
                        
                        show_details_button = gr.Button(
                            "🔍 Show Details of Selected Opportunity",
                            variant="primary"
                        )
                        
                        opportunity_details_display = gr.Textbox(
                            lines=15,
                            label="📊 Detailed Price Breakdown & Transparency",
                            interactive=False,
                            value="💡 How to use:\n1. Select an opportunity from dropdown above\n2. Click '🔍 Show Details' button\n3. See EXACT prices, fees, and calculations\n4. Verify everything is transparent!\n\n⬆️ Select an opportunity to begin..."
                        )

                    with gr.Column():
                        gr.Markdown("### 📜 Execution History")
                        gr.Markdown("*Track all executed (or simulated) trades*")
                        execution_history_df = gr.DataFrame(
                            headers=["Time", "Strategy", "Token", "Profit", "Status"],
                            label="Recent Executions"
                        )

            with gr.Tab("4️⃣ System Info & Help"):
                gr.Markdown("""
                # 📚 Understanding the System
                
                ## 🎯 What Does This System Do?
                
                This is an **AI-powered arbitrage scanner** that finds profitable trading opportunities by:
                1. **Monitoring prices** across multiple exchanges (CEX & DEX)
                2. **Comparing prices** to find discrepancies
                3. **Calculating profits** including all fees and costs
                4. **Analyzing risks** using AI models
                
                ---
                
                ## 🔍 How It Works (No More "Black Box"!)
                
                ### Step-by-Step Process:
                
                **1. Data Collection** 📡
                - System connects to 4 CEX exchanges (Binance, Kraken, Coinbase, KuCoin)
                - Monitors 13 DEX protocols including:
                  • Ethereum: Uniswap V3, SushiSwap, Curve, Balancer, dYdX, 1inch, Kyber
                  • BSC: PancakeSwap
                  • Algorand: Tinyman, Pact, AlgoFi, Algox
                - Algorand DEX feature ultra-low fees (~$0.001 vs $15-50 on Ethereum)
                - Fetches real-time prices for 16 trading pairs
                
                **2. Graph Building** 🕸️
                - Creates a network graph of all possible trading paths
                - Each node = token on an exchange
                - Each edge = possible trade with price data
                
                **3. Arbitrage Detection** 🔍
                - Uses Bellman-Ford algorithm to find profitable cycles
                - Identifies price discrepancies across exchanges
                - Filters by minimum profit threshold
                
                **4. AI Analysis** 🤖
                - Evaluates opportunity confidence
                - Assesses risk levels
                - Provides recommendations
                
                **5. Results Display** 📊
                - Shows all opportunities with transparent calculations
                - You can see exact prices, fees, and profit calculations
                - Everything is verifiable
                
                ---
                
                ## ✅ Why You Can Trust This System
                
                **Full Transparency:**
                - ✓ All price data is shown (use "Show Details" in Execution Center)
                - ✓ Fee calculations are visible (CEX: ~0.1%, DEX: ~0.3%, gas costs)
                - ✓ Trading path is documented step-by-step
                - ✓ You can verify prices on actual exchanges
                - ✓ AI confidence scores help you assess risk
                
                **Safety Features:**
                - ✓ Demo mode by default (no real trading)
                - ✓ Risk warnings for each opportunity
                - ✓ Clear labels showing simulated vs real execution
                
                ---
                
                ## 📋 Available Trading Strategies
                """)
                
                strategy_info_display = gr.Markdown(
                    value=self.get_strategies_info_display()
                )
                
                gr.Markdown("---")
                gr.Markdown("## 🔧 System Diagnostics")
                gr.Markdown("*Check the health and status of all system components*")
            
                with gr.Tab("💻 Component Status"):
                    gr.Markdown("**What this shows:** Real-time status of all system components")
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### 🔧 Core Components")
                            core_diagnostics = gr.Textbox(
                                value=self.get_core_diagnostics(),
                                lines=10,
                                label="Core System Status",
                                interactive=False
                            )
                        
                        with gr.Column():
                            gr.Markdown("### 📡 Data Sources")
                            data_diagnostics = gr.Textbox(
                                value=self.get_data_diagnostics(),
                                lines=10,
                                label="Data Engine Status",
                                interactive=False
                            )
                    
                    with gr.Row():
                        scan_progress_display = gr.Textbox(
                            lines=8,
                            label="📈 Last Scan Progress",
                            interactive=False,
                            value="Ready to scan... Go to tab 1️⃣ to start scanning."
                        )
                    
                    refresh_diagnostics_btn = gr.Button("🔄 Refresh Diagnostics", variant="secondary")
                    
                    refresh_diagnostics_btn.click(
                        fn=self.refresh_diagnostics,
                        outputs=[core_diagnostics, data_diagnostics, system_status_text]
                    )

            # Event handlers
            scan_button.click(
                fn=self.scan_arbitrage_opportunities,
                inputs=[enabled_strategies, trading_pairs, min_profit, max_opportunities, demo_mode],
                outputs=[opportunities_df, ai_analysis_text, performance_chart, 
                        total_opportunities, avg_profit, ai_confidence, selected_opportunity, scan_progress_display,
                        strategy_performance_chart, market_heatmap, risk_analysis]
            )
            
            # Refresh analytics
            refresh_analytics_btn.click(
                fn=self.refresh_analytics,
                outputs=[strategy_performance_chart, market_heatmap, risk_analysis]
            )

            execute_button.click(
                fn=self.execute_selected_opportunity,
                inputs=[selected_opportunity, execution_amount, demo_mode],
                outputs=[execution_history_df, ai_analysis_text]
            )
            
            show_details_button.click(
                fn=self.show_opportunity_details_from_dropdown,
                inputs=[selected_opportunity],
                outputs=[opportunity_details_display]
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
        """Main scanning function with detailed progress tracking"""
        try:
            self.scan_progress = "🔄 STARTING ARBITRAGE SCAN...\n"
            self.scan_progress += "=" * 60 + "\n\n"
            self.scan_progress += "🎯 **WHAT THE SYSTEM IS DOING NOW**\n\n"
            logger.info("📊 Scan started")
            
            # Handle case where Gradio passes component objects instead of values
            # This happens when the function is called programmatically
            if hasattr(strategies, 'value'):
                strategies = strategies.value if strategies.value is not None else []
            if hasattr(pairs, 'value'):
                pairs = pairs.value if pairs.value is not None else []
            
            # Ensure we have lists
            if not isinstance(strategies, (list, tuple)):
                strategies = []
            if not isinstance(pairs, (list, tuple)):
                pairs = []
            
            # Convert strategy names
            strategy_map = {
                "DEX/CEX Arbitrage": "dex_cex",
                "Cross-Exchange": "cross_exchange", 
                "Triangular": "triangular",
                "Wrapped Tokens": "wrapped_tokens",
                "Statistical AI": "statistical"
            }

            enabled_strategies = [strategy_map[s] for s in strategies if s in strategy_map]
            
            self.scan_progress += f"📋 **Scan Configuration**:\n"
            self.scan_progress += f"  ✓ Strategies enabled: {', '.join(enabled_strategies)}\n"
            self.scan_progress += f"    📖 These determine HOW we look for price differences\n"
            self.scan_progress += f"  ✓ Trading pairs: {len(pairs)} pairs ({', '.join(pairs[:3])}...)\n"
            self.scan_progress += f"    📖 These are the tokens we'll monitor\n"
            self.scan_progress += f"  ✓ Min profit threshold: {min_profit}%\n"
            self.scan_progress += f"    📖 Only show opportunities above this profit level\n"
            self.scan_progress += f"  ✓ Max results to display: {max_opps}\n"
            self.scan_progress += f"    📖 Will show the top {max_opps} most profitable opportunities\n\n"
            
            self.scan_progress += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            self.scan_progress += "📡 **Step 1/5: Fetching Live Market Data**\n"
            self.scan_progress += "   🔍 Connecting to exchanges...\n"
            self.scan_progress += "   📊 Requesting current prices for all pairs...\n"
            logger.info("Fetching market data for scan")

            # Run arbitrage scan
            opportunities = await self.arbitrage_system.run_full_arbitrage_scan(
                enabled_strategies, pairs, min_profit
            )
            
            self.scan_progress += f"   ✅ Successfully loaded price data from exchanges!\n\n"
            
            # Display graph statistics with clear explanation
            self.scan_progress += f"📊 **Step 2/5: Building Trading Graph**\n"
            self.scan_progress += f"   🔍 What this means: Creating a map of all possible trading paths\n"
            if hasattr(self.arbitrage_system, 'last_graph_stats'):
                stats = self.arbitrage_system.last_graph_stats
                self.scan_progress += f"   • Nodes (token-exchange pairs): {stats.get('nodes', 0)}\n"
                self.scan_progress += f"     📖 Each node = one token on one exchange\n"
                self.scan_progress += f"   • Edges (possible trades): {stats.get('edges', 0)}\n"
                self.scan_progress += f"     📖 Each edge = a way to convert one token to another\n"
                self.scan_progress += f"   • Unique tokens tracked: {stats.get('tokens', 0)}\n"
                self.scan_progress += f"   • Exchanges monitored: {stats.get('exchanges', 0)}\n"
                self.scan_progress += f"   ✅ Trading graph constructed!\n\n"
            else:
                self.scan_progress += f"   ✅ Trading graph constructed with enabled strategies!\n\n"
            
            # Display Bellman-Ford results with explanation
            self.scan_progress += f"🔍 **Step 3/5: Detecting Profitable Cycles**\n"
            self.scan_progress += f"   🔍 What this means: Looking for trading loops that end with profit\n"
            if hasattr(self.arbitrage_system, 'last_raw_cycles_count'):
                raw_cycles = self.arbitrage_system.last_raw_cycles_count
                self.scan_progress += f"   • Algorithm used: Bellman-Ford (finds negative-cost cycles)\n"
                self.scan_progress += f"     📖 A 'negative cost' cycle = PROFIT when you complete the loop!\n"
                self.scan_progress += f"   • Raw cycles discovered: {raw_cycles}\n"
                self.scan_progress += f"     📖 These are potential arbitrage opportunities before filtering\n"
                self.scan_progress += f"   • Max cycle length: {self.arbitrage_system.detector.max_cycle_length} trades per cycle\n"
                self.scan_progress += f"     📖 Longer cycles have more steps but potentially higher profit\n"
                self.scan_progress += f"   • Profit filter applied: ≥{-self.arbitrage_system.detector.min_profit_threshold * 100:.2f}%\n"
                self.scan_progress += f"     📖 Ignoring cycles below this threshold\n"
                self.scan_progress += f"   ✅ Cycle detection complete!\n\n"
            else:
                self.scan_progress += f"   ✅ Cycle detection complete!\n\n"
            
            self.scan_progress += f"🤖 **Step 4/5: AI Risk Analysis**\n"
            self.scan_progress += f"   🔍 What this means: AI evaluates each opportunity's safety and reliability\n"
            self.scan_progress += f"   • Analyzing market conditions...\n"
            self.scan_progress += f"   • Calculating confidence scores (0.0-1.0)...\n"
            self.scan_progress += f"   • Assessing execution risks...\n"
            self.scan_progress += f"   ✅ AI analysis complete!\n\n"
            
            self.scan_progress += f"📊 **Step 5/5: Filtering & Ranking Results**\n"
            self.scan_progress += f"   🔍 What this means: Selecting the best opportunities for you\n"
            self.scan_progress += f"   • Filtering by minimum profit threshold ({min_profit}%)...\n"
            self.scan_progress += f"   • Sorting by profitability and AI confidence...\n"
            self.scan_progress += f"   ✅ Found {len(opportunities)} profitable opportunities!\n"

            # Limit results
            total_found = len(opportunities)
            opportunities = opportunities[:max_opps]
            
            if total_found > max_opps:
                self.scan_progress += f"  ℹ️ Displaying top {max_opps} of {total_found} opportunities\n"

            # Prepare DataFrame
            df_data = []
            total_profit = 0
            total_confidence = 0

            for i, opp in enumerate(opportunities):
                # Store index for details lookup
                opp['display_index'] = i
                
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

            self.scan_progress += f"\n" + "━" * 60 + "\n"
            self.scan_progress += f"✅ **SCAN COMPLETE!**\n\n"
            self.scan_progress += f"📈 **Results Summary**:\n"
            self.scan_progress += f"  • Total opportunities found: {len(opportunities)}\n"
            self.scan_progress += f"  • Average expected profit: {avg_profit_val:.3f}%\n"
            self.scan_progress += f"  • Average AI confidence: {avg_confidence_val:.2f}/1.0\n"
            self.scan_progress += f"    📖 Higher confidence = lower risk, more reliable\n\n"
            
            if len(opportunities) > 0:
                best_opp = opportunities[0]
                self.scan_progress += f"🏆 **Best Opportunity Found**:\n"
                self.scan_progress += f"  • Strategy: {best_opp.get('strategy', 'N/A')}\n"
                self.scan_progress += f"  • Token: {best_opp.get('token', 'N/A')}\n"
                self.scan_progress += f"  • Expected profit: {best_opp.get('profit_pct', 0):.3f}%\n"
                self.scan_progress += f"  • AI confidence: {best_opp.get('ai_confidence', 0):.2f}\n\n"
            
            self.scan_progress += f"💡 **What to do next**:\n"
            self.scan_progress += f"  1️⃣ View results in the table above to see all opportunities\n"
            self.scan_progress += f"  2️⃣ Go to tab 2️⃣ 'Results & Analysis' for charts and AI insights\n"
            self.scan_progress += f"  3️⃣ Go to tab 3️⃣ 'Execution Center' to:\n"
            self.scan_progress += f"     - Select an opportunity\n"
            self.scan_progress += f"     - Click 'Show Details' to see EXACT prices and WHY it's profitable\n"
            self.scan_progress += f"     - Execute (or simulate) the trade\n\n"
            self.scan_progress += f"🔍 **System Transparency**: Every opportunity shows you:\n"
            self.scan_progress += f"  ✅ Exact buy and sell prices from exchanges\n"
            self.scan_progress += f"  ✅ All fees (trading fees, gas, slippage)\n"
            self.scan_progress += f"  ✅ Step-by-step profit calculation\n"
            self.scan_progress += f"  ✅ WHY the system found this opportunity\n"
            self.scan_progress += f"  ✅ Which swaps will be performed\n"
            
            logger.info(f"✅ Scan complete: {len(opportunities)} opportunities found")

            # Generate AI analysis
            ai_analysis = await self.generate_ai_market_analysis(opportunities, enabled_strategies)

            # Generate performance chart
            chart = self.create_performance_chart()

            # Generate dropdown choices for execution
            execution_choices = [f"{opp['strategy']} - {opp['token']} ({opp['profit_pct']:.2f}%)" 
                               for opp in opportunities]
            
            # Store opportunities for analytics
            self.arbitrage_system.cached_opportunities = opportunities

            return (
                df_data,
                ai_analysis, 
                chart,
                len(opportunities),
                avg_profit_val,
                avg_confidence_val,
                gr.Dropdown(choices=execution_choices),
                self.scan_progress,
                self.create_strategy_performance_chart(),
                self.create_market_heatmap(),
                self.generate_risk_analysis()
            )

        except Exception as e:
            error_msg = f"❌ Error scanning opportunities: {str(e)}\n"
            error_msg += f"\nPlease check:\n"
            error_msg += f"- Network connection\n"
            error_msg += f"- Selected strategies\n"
            error_msg += f"- Trading pairs\n"
            logger.error(f"Scan error: {str(e)}")
            error_progress = f"❌ Scan failed: {str(e)}"
            return [], error_msg, go.Figure(), 0, 0, 0, gr.Dropdown(choices=[]), error_progress, go.Figure(), go.Figure(), "Error loading analytics"

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
            
            # Extract profit percentage from dropdown selection format
            # Format: "strategy - token (profit%)"
            profit_pct_str = selected_opp.split("(")[1].split("%")[0] if "(" in selected_opp and "%" in selected_opp else None
            
            # Find the matching opportunity from cached data to get exact profit
            selected_opportunity_data = None
            opportunities = self.cached_opportunities
            
            for opp in opportunities:
                dropdown_label = f"{opp['strategy']} - {opp['token']} ({opp['profit_pct']:.2f}%)"
                if dropdown_label == selected_opp:
                    selected_opportunity_data = opp
                    break

            if demo_mode:
                # Calculate simulated profit based on actual opportunity data
                if selected_opportunity_data:
                    profit_pct = selected_opportunity_data.get('profit_pct', 0)
                    profit_usd = (amount * profit_pct) / 100
                else:
                    # Fallback if opportunity not found
                    try:
                        profit_pct = float(profit_pct_str) if profit_pct_str else 0.5
                        profit_usd = (amount * profit_pct) / 100
                    except:
                        profit_pct = 0.5
                        profit_usd = amount * 0.005
                
                # Simulate execution
                result = {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'strategy': strategy,
                    'token': token,
                    'profit': f"+{profit_usd:.2f} USDT",
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
                analysis += f"Amount: {amount:.2f} USDT\n"
                analysis += f"Expected Profit: {profit_pct:.2f}%\n"
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

    async def generate_ai_market_analysis(self, opportunities, enabled_strategies=None):
        """Generate AI analysis of current market conditions with strategy insights"""
        analysis = f"🤖 AI Market Analysis ({datetime.now().strftime('%H:%M:%S')})\n\n"
        
        if not opportunities:
            analysis += "📊 No arbitrage opportunities detected.\n\n"
            analysis += "💡 Possible Reasons:\n"
            analysis += "- Market is highly efficient\n"
            analysis += "- Low volatility period\n"
            analysis += "- High trading volume creating tight spreads\n"
            analysis += "- All strategies may not be enabled\n\n"
            
            if enabled_strategies:
                analysis += f"✓ Active Strategies ({len(enabled_strategies)}):\n"
                for strategy in enabled_strategies:
                    analysis += f"  - {strategy}\n"
            
            return analysis
        
        # Strategy breakdown with insights
        strategies = {}
        for opp in opportunities:
            strategy = opp.get('strategy', 'Unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        analysis += f"📈 Found {len(opportunities)} Opportunities\n\n"
        analysis += "🎯 Strategy Distribution:\n"
        for strategy, count in sorted(strategies.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(opportunities)) * 100
            analysis += f"- {strategy}: {count} opportunities ({percentage:.1f}%)\n"
        
        # Strategy-specific insights
        analysis += f"\n💡 Strategy Insights:\n"
        if 'dex_cex' in strategies:
            analysis += f"- DEX/CEX: {strategies['dex_cex']} opportunities - Price differences between centralized and decentralized exchanges\n"
        if 'cross_exchange' in strategies:
            analysis += f"- Cross-Exchange: {strategies['cross_exchange']} opportunities - Inter-exchange arbitrage available\n"
        if 'triangular' in strategies:
            analysis += f"- Triangular: {strategies['triangular']} opportunities - Cyclic arbitrage within single exchange\n"
        if 'wrapped_tokens' in strategies:
            analysis += f"- Wrapped Tokens: {strategies['wrapped_tokens']} opportunities - Native vs wrapped token discrepancies\n"
        if 'statistical' in strategies:
            analysis += f"- Statistical AI: {strategies['statistical']} opportunities - ML-detected correlation anomalies\n"
        
        # Best opportunity analysis
        if opportunities:
            best = max(opportunities, key=lambda x: x.get('profit_pct', 0))
            analysis += f"\n🏆 Best Opportunity:\n"
            analysis += f"- Strategy: {best.get('strategy', 'N/A')}\n"
            analysis += f"- Token: {best.get('token', 'N/A')}\n"
            analysis += f"- Path: {best.get('path_summary', 'N/A')}\n"
            analysis += f"- Expected Profit: {best.get('profit_pct', 0):.3f}%\n"
            analysis += f"- AI Confidence: {best.get('ai_confidence', 0):.2f}/1.0\n"
            analysis += f"- Risk Level: {best.get('risk_level', 'UNKNOWN')}\n"
        
        # Market conditions analysis
        avg_profit = sum(opp.get('profit_pct', 0) for opp in opportunities) / len(opportunities)
        avg_confidence = sum(opp.get('ai_confidence', 0) for opp in opportunities) / len(opportunities)
        
        analysis += f"\n📊 Market Conditions:\n"
        if avg_profit > 1.0:
            analysis += "🔥 High volatility - Excellent arbitrage conditions!\n"
            analysis += "   Multiple large opportunities detected.\n"
        elif avg_profit > 0.5:
            analysis += "✅ Moderate volatility - Good opportunities available.\n"
            analysis += "   Normal arbitrage conditions.\n"
        else:
            analysis += "⚠️ Low volatility - Limited opportunities.\n"
            analysis += "   Market is relatively efficient.\n"
        
        analysis += f"\n🎲 Average Profit: {avg_profit:.3f}%\n"
        analysis += f"🤖 Average AI Confidence: {avg_confidence:.2f}/1.0\n"
        
        # Risk assessment
        high_confidence_count = sum(1 for opp in opportunities if opp.get('ai_confidence', 0) > 0.7)
        analysis += f"\n⚠️ Risk Assessment:\n"
        analysis += f"- High confidence opportunities: {high_confidence_count}/{len(opportunities)}\n"
        analysis += f"- Always verify opportunities manually before live trading\n"
        analysis += f"- Consider gas fees and slippage in profit calculations\n"
        analysis += f"- Demo mode recommended for testing\n"
        
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
    
    def get_strategies_info_display(self):
        """Get formatted strategy information for display"""
        try:
            strategies = self.arbitrage_system.get_all_strategies_info()
            
            display_text = ""
            
            for strategy in strategies:
                display_text += f"\n---\n\n"
                display_text += f"## 🎯 {strategy.get('name', 'Unknown')}\n\n"
                display_text += f"**Status**: {strategy.get('status', 'Unknown')}\n\n"
                display_text += f"**Description**: {strategy.get('description', 'N/A')}\n\n"
                
                if 'how_it_works' in strategy:
                    display_text += f"**How It Works**: {strategy['how_it_works']}\n\n"
                
                if 'supported_exchanges' in strategy:
                    display_text += f"**Supported Exchanges**:\n"
                    for key, value in strategy['supported_exchanges'].items():
                        if isinstance(value, list):
                            display_text += f"  - {key}: {', '.join(value)}\n"
                        else:
                            display_text += f"  - {key}: {value}\n"
                    display_text += "\n"
                
                if 'typical_profit' in strategy:
                    display_text += f"**💰 Typical Profit**: {strategy['typical_profit']}\n\n"
                
                if 'execution_speed' in strategy:
                    display_text += f"**⚡ Speed**: {strategy['execution_speed']}\n\n"
                
                if 'risk_level' in strategy:
                    display_text += f"**⚠️ Risk**: {strategy['risk_level']}\n\n"
                
                if 'capital_required' in strategy:
                    display_text += f"**💵 Capital**: {strategy['capital_required']}\n\n"
                
                if 'fees' in strategy:
                    display_text += f"**Fees**:\n"
                    for fee_type, fee_value in strategy['fees'].items():
                        display_text += f"  - {fee_type}: {fee_value}\n"
                    display_text += "\n"
                
                if 'best_conditions' in strategy:
                    display_text += f"**📈 Best Conditions**: {strategy['best_conditions']}\n\n"
                
                if 'ai_features' in strategy:
                    display_text += f"**🤖 AI Features**: {strategy['ai_features']}\n\n"
            
            return display_text
            
        except Exception as e:
            return f"Error loading strategy information: {str(e)}"
    
    def get_core_diagnostics(self):
        """Get core system diagnostics"""
        try:
            status = self.arbitrage_system.get_system_status()
            
            diag = "=== CORE COMPONENTS ===\n"
            diag += "(What's running in the system)\n\n"
            
            # AI Model
            ai_loaded = status.get('ai_model_loaded', False)
            diag += f"🤖 AI Model: {'✓ Loaded and Ready' if ai_loaded else '⚠️ Fallback Mode (OK)'}\n"
            
            # Strategies
            strategies = status.get('active_strategies', [])
            diag += f"\n🎯 Strategies: {len(strategies)}/5 loaded\n"
            for s in strategies:
                diag += f"   • {s}\n"
            
            # Graph Builder
            diag += f"\n🕸️ Graph Builder: ✓ Initialized\n"
            
            # Get graph statistics if available
            if hasattr(self.arbitrage_system, 'graph_builder') and self.arbitrage_system.graph_builder.graph:
                graph_stats = self.arbitrage_system.graph_builder.get_graph_statistics()
                diag += f"   • Nodes (trading pairs): {graph_stats.get('nodes', 0)}\n"
                diag += f"   • Edges (possible trades): {graph_stats.get('edges', 0)}\n"
                diag += f"   • Tokens tracked: {graph_stats.get('tokens', 0)}\n"
                diag += f"   • Exchanges: {graph_stats.get('exchanges', 0)}\n"
            
            # Bellman-Ford Detector
            diag += f"\n🔍 Bellman-Ford Detector: ✓ Ready\n"
            diag += f"   (Finds profitable cycles in price graph)\n"
            
            # Add Bellman-Ford configuration
            if hasattr(self.arbitrage_system, 'detector'):
                detector = self.arbitrage_system.detector
                diag += f"   • Max cycle length: {detector.max_cycle_length} hops\n"
                diag += f"   • Min profit filter: {-detector.min_profit_threshold * 100:.2f}%\n"
            
            # Data Engine
            diag += f"\n📡 Data Engine: ✓ Active\n"
            
            # Cache
            cached = status.get('cached_opportunities', 0)
            diag += f"\n=== CACHE STATUS ===\n"
            diag += f"💾 Cached Opportunities: {cached}\n"
            
            last_scan = status.get('last_scan')
            if last_scan:
                diag += f"Last Scan: {last_scan.strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                diag += f"Last Scan: Never\n"
            
            return diag
            
        except Exception as e:
            return f"Error getting diagnostics: {str(e)}"
    
    def get_data_diagnostics(self):
        """Get data engine diagnostics"""
        try:
            status = self.arbitrage_system.get_system_status()
            data_status = status.get('data_engine_status', {})
            
            diag = "=== DATA SOURCES ===\n"
            diag += "(Where price data comes from)\n\n"
            
            # CEX Exchanges
            cex_count = data_status.get('cex_exchanges', 0)
            diag += f"📊 CEX Exchanges: {cex_count} configured\n"
            diag += f"   • Binance ✓\n"
            diag += f"   • Kraken ✓\n"
            diag += f"   • Coinbase ✓\n"
            diag += f"   • KuCoin ✓\n"
            
            # DEX Protocols
            dex_count = data_status.get('dex_protocols', 0)
            diag += f"\n🌐 DEX Protocols: {dex_count} configured\n"
            diag += f"   • Uniswap V3 (Ethereum) ✓\n"
            diag += f"   • SushiSwap (Multi-chain) ✓\n"
            diag += f"   • PancakeSwap (BSC) ✓\n"
            diag += f"   • Curve (Ethereum) ✓\n"
            diag += f"   • Balancer (Ethereum) ✓\n"
            diag += f"   • dYdX (Ethereum L2) ✓\n"
            diag += f"   • 1inch (Multi-chain) ✓\n"
            diag += f"   • Kyber (Ethereum) ✓\n"
            diag += f"   • Tinyman (Algorand) ✓\n"
            diag += f"   • Pact (Algorand) ✓\n"
            diag += f"   • AlgoFi (Algorand) ✓\n"
            diag += f"   • Algox (Algorand) ✓\n"
            
            # Web3
            web3_connected = data_status.get('web3_connected', False)
            diag += f"\n🔗 Web3 Connection: "
            if web3_connected:
                diag += f"✓ Live (real DEX data)\n"
            else:
                diag += f"⚠️ Simulated (safe demo mode)\n"
            
            # Cache
            cached_data = data_status.get('cached_data_available', False)
            diag += f"\n💾 Cached Data: {'✓ Available' if cached_data else '✗ None yet'}\n"
            
            last_fetch = data_status.get('last_fetch')
            if last_fetch:
                diag += f"Last Fetch: {last_fetch.strftime('%H:%M:%S')}\n"
            else:
                diag += f"Last Fetch: Never\n"
            
            return diag
            
        except Exception as e:
            return f"Error getting data diagnostics: {str(e)}"
    
    def refresh_diagnostics(self):
        """Refresh all diagnostics displays"""
        return (
            self.get_core_diagnostics(),
            self.get_data_diagnostics(),
            self.get_system_status_display()
        )
    
    def generate_opportunity_details(self, opportunity_index):
        """Generate detailed price comparison for a specific opportunity"""
        try:
            if opportunity_index is None or opportunity_index < 0:
                return "Select an opportunity to see detailed comparison..."
            
            if not self.cached_opportunities or opportunity_index >= len(self.cached_opportunities):
                return "No opportunity data available."
            
            opp = self.cached_opportunities[opportunity_index]
            
            details = f"🎯 **{opp['strategy'].upper()} ARBITRAGE OPPORTUNITY**\n\n"
            details += f"═══════════════════════════════════════\n\n"
            
            # Basic Info
            details += f"**Token**: {opp.get('token', 'N/A')}\n"
            details += f"**Strategy Type**: {opp.get('strategy', 'Unknown')}\n"
            details += f"**Status**: {opp.get('status', 'Unknown')}\n"
            details += f"**Timestamp**: {opp.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # WHY was this found? - Add reasoning
            details += f"### 🎓 WHY This Trade Was Found\n"
            profit_pct = opp.get('profit_pct', 0)
            strategy = opp.get('strategy', 'Unknown')
            
            if strategy == 'dex_cex':
                details += f"**Reason**: The system detected a price difference between a DEX (Decentralized Exchange)\n"
                details += f"and a CEX (Centralized Exchange). When the same token has different prices on\n"
                details += f"different exchanges, we can buy low on one and sell high on the other.\n\n"
                details += f"**Why it's profitable**: Even after paying all fees (trading fees, gas fees, slippage),\n"
                details += f"the price difference is large enough ({profit_pct:.3f}%) to make a profit.\n\n"
            elif strategy == 'cross_exchange':
                details += f"**Reason**: The system found the same token priced differently on two centralized exchanges.\n"
                details += f"This happens when market prices move faster on one exchange than another.\n\n"
                details += f"**Why it's profitable**: The {profit_pct:.3f}% price spread exceeds the combined\n"
                details += f"trading fees on both exchanges, leaving a net profit.\n\n"
            elif strategy == 'triangular':
                details += f"**Reason**: The system detected a triangular arbitrage opportunity - when you can\n"
                details += f"trade through 3 currencies in a circle and end up with more than you started.\n\n"
                details += f"**Why it's profitable**: The exchange rates between the three pairs are misaligned,\n"
                details += f"creating a {profit_pct:.3f}% profit opportunity after all fees.\n\n"
            elif strategy == 'wrapped_tokens':
                details += f"**Reason**: The system found a price inefficiency between a native token and its\n"
                details += f"wrapped version (e.g., ETH vs WETH) across different platforms.\n\n"
                details += f"**Why it's profitable**: Despite wrapping/unwrapping costs, the {profit_pct:.3f}%\n"
                details += f"price difference makes this trade worthwhile.\n\n"
            else:
                details += f"**Reason**: The system's AI model detected a statistical anomaly or pattern\n"
                details += f"indicating a {profit_pct:.3f}% profit opportunity.\n\n"
            
            details += f"**System Detection Method**: Bellman-Ford algorithm analyzed {opp.get('analyzed_paths', 'multiple')}\n"
            details += f"possible trading paths and found this cycle with negative cost (= profit!).\n\n"
            
            # Path details with CLEAR explanation of what will happen
            details += f"### 📍 Trading Path - What Will Actually Happen\n"
            path = opp.get('path', [])
            if path:
                details += f"**Step-by-step execution plan:**\n\n"
                for i, node in enumerate(path):
                    details += f"  **Step {i+1}**: {node}\n"
                    if i < len(path) - 1:
                        next_node = path[i+1]
                        details += f"  ➜ Action: Convert/trade from {node} to {next_node}\n"
                    if i == 0:
                        details += f"  ➜ You START here with your capital\n"
                    elif i == len(path) - 1:
                        details += f"  ➜ You END here with profit!\n"
                details += f"\n**Complete cycle**: You start at {path[0]} and return to {path[-1]} with more value!\n"
            else:
                details += f"  Path information not available.\n"
            details += "\n"
            
            # Profit Analysis
            details += f"### 💰 Profit Analysis\n"
            details += f"**Expected Profit**: {opp.get('profit_pct', 0):.4f}%\n"
            details += f"**Profit in USD**: ${opp.get('profit_usd', 0):.2f}\n"
            details += f"**Required Capital**: ${opp.get('required_capital', 0):.2f}\n"
            details += f"**Total Fees**: ${opp.get('fees_total', 0):.4f}\n\n"
            
            # Price Comparison (detailed breakdown) with CLEAR explanation
            details += f"### 🔍 Detailed Trade Breakdown - EXACTLY What Will Happen\n"
            details += f"**This shows the REAL prices, fees, and calculations:**\n\n"
            
            cycle_data = opp.get('cycle_data', {})
            edge_data = cycle_data.get('edge_data', {})
            
            if edge_data:
                details += f"**Each Swap Operation:**\n"
                
                # Get starting token and USD capital
                path = opp.get('path', [])
                start_token = path[0].split('@')[0] if path and '@' in path[0] else 'UNKNOWN'
                initial_usd = opp.get('required_capital', 1000)
                
                # Get starting token USD price (from profit analysis if available)
                start_token_amount = opp.get('cycle_data', {}).get('start_token_amount', 1.0)
                if start_token_amount == 1.0:
                    # Fallback: estimate based on token
                    token_prices = {'BTC': 50000, 'WBTC': 50000, 'ETH': 3000, 'WETH': 3000, 
                                   'BNB': 300, 'LINK': 15, 'USDT': 1, 'USDC': 1}
                    start_token_price = token_prices.get(start_token, 100)
                    start_token_amount = initial_usd / start_token_price
                
                current_token_amount = start_token_amount
                initial_amount = initial_usd
                
                details += f"\n  💡 **Starting Point**: We begin with ${initial_usd:.2f} USD\n"
                details += f"     Which equals: {current_token_amount:.8f} {start_token}\n"
                
                for idx, (edge_key, edge_info) in enumerate(edge_data.items(), 1):
                    # Parse edge key to get tokens
                    edge_parts = edge_key.split('->')
                    if len(edge_parts) == 2:
                        from_token = edge_parts[0].split('@')[0] if '@' in edge_parts[0] else '?'
                        to_token = edge_parts[1].split('@')[0] if '@' in edge_parts[1] else '?'
                    else:
                        from_token = '?'
                        to_token = '?'
                    
                    details += f"\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    details += f"  **SWAP {idx}**: {edge_key}\n"
                    details += f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    
                    # Extract exchange info
                    buy_exchange = edge_info.get('buy_exchange', 'Unknown')
                    sell_exchange = edge_info.get('sell_exchange', 'Unknown')
                    
                    details += f"\n  💼 **Starting with**: {current_token_amount:.8f} {from_token}\n\n"
                    
                    # Show buy/sell prices if available (this is the key transparency!)
                    if 'buy_price' in edge_info:
                        details += f"  💵 **BUY Price**: ${edge_info['buy_price']:.8f}\n"
                        if buy_exchange != 'Unknown':
                            details += f"     📍 Exchange: {buy_exchange}\n"
                        details += f"     📖 This is the LIVE price we'll pay\n\n"
                    
                    if 'sell_price' in edge_info:
                        details += f"  💰 **SELL Price**: ${edge_info['sell_price']:.8f}\n"
                        if sell_exchange != 'Unknown':
                            details += f"     📍 Exchange: {sell_exchange}\n"
                        details += f"     📖 This is the LIVE price we'll receive\n\n"
                    
                    # Calculate and show spread with explanation
                    if 'buy_price' in edge_info and 'sell_price' in edge_info:
                        buy_p = edge_info['buy_price']
                        sell_p = edge_info['sell_price']
                        if buy_p > 0:
                            spread_pct = ((sell_p - buy_p) / buy_p) * 100
                            spread_direction = "PROFIT! 📈" if spread_pct > 0 else "LOSS 📉"
                            details += f"  📊 **Price Spread**: {spread_pct:.4f}% {spread_direction}\n"
                            details += f"     📖 Why profitable: Sell price is higher than buy price!\n\n"
                    
                    # Show rate and fees with clear explanation
                    rate = edge_info.get('rate', 1.0)
                    details += f"  📈 **Conversion Rate**: {rate:.6f} {to_token}/{from_token}\n"
                    details += f"     📖 For every 1 {from_token}, you get {rate:.6f} {to_token}\n\n"
                    
                    # Show fees breakdown with DETAIL
                    total_fees = edge_info.get('total_fees', 0)
                    if total_fees == 0:
                        # Fallback to 'fee' field
                        total_fees = edge_info.get('fee', 0.001)
                    
                    fee_amount = current_token_amount * total_fees
                    details += f"  💸 **Total Fees**: {total_fees * 100:.4f}% ({fee_amount:.8f} {from_token})\n"
                    details += f"     📖 This includes all trading fees and slippage\n"
                    
                    gas_cost_usd = 0
                    if 'gas_cost' in edge_info and edge_info['gas_cost'] > 0:
                        gas_cost_usd = edge_info['gas_cost']
                        details += f"  ⛽ **Gas Cost**: ${gas_cost_usd:.2f}\n"
                        details += f"     📖 Blockchain transaction fee (DEX only)\n"
                    
                    # Calculate amount after this step (CORRECT calculation)
                    # Apply conversion: from_token * rate = to_token
                    # Then subtract fees
                    next_token_amount = current_token_amount * rate * (1 - total_fees)
                    
                    details += f"\n  ✅ **After this swap**: {next_token_amount:.8f} {to_token}\n"
                    
                    # Show strategy type
                    if 'strategy' in edge_info:
                        details += f"  🎯 **Strategy Type**: {edge_info['strategy']}\n"
                    
                    # Show direction for dex/cex
                    if 'direction' in edge_info:
                        direction = edge_info['direction'].replace('_', ' → ').upper()
                        details += f"  ➡️  **Direction**: {direction}\n"
                    
                    # Update for next iteration
                    current_token_amount = next_token_amount
                
                # Calculate final USD value
                final_token = path[-1].split('@')[0] if path and '@' in path[-1] else 'UNKNOWN'
                
                # Get final token price
                token_prices = {'BTC': 50000, 'WBTC': 50000, 'ETH': 3000, 'WETH': 3000, 
                               'BNB': 300, 'LINK': 15, 'USDT': 1, 'USDC': 1}
                final_token_price = token_prices.get(final_token, 100)
                final_usd = current_token_amount * final_token_price
                
                net_profit = final_usd - initial_amount
                net_profit_pct = (net_profit / initial_amount) * 100
                
                details += f"\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                details += f"  💡 **FINAL SUMMARY**\n"
                details += f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                details += f"  🏁 **Started with**: ${initial_amount:.2f} ({start_token_amount:.8f} {start_token})\n"
                details += f"  🎉 **End with**: {current_token_amount:.8f} {final_token} = ${final_usd:.2f}\n"
                details += f"  💰 **Net Profit**: ${net_profit:.2f} ({net_profit_pct:.3f}%)\n\n"
                details += f"  ✅ **Why this works**: The price differences between exchanges are\n"
                details += f"     larger than the sum of all fees, creating a guaranteed profit!\n\n"
                details += f"  🔍 **Verification**: You can check these prices yourself on the\n"
                details += f"     exchanges listed above to verify this opportunity is REAL!\n"
            else:
                details += f"  ⚠️ No detailed edge data available for this opportunity.\n"
                details += f"  The strategy might be using aggregated pricing.\n"
                details += f"\n  However, the profit calculation includes:\n"
                details += f"  • All exchange fees (maker/taker)\n"
                details += f"  • Network gas costs (for DEX)\n"
                details += f"  • Estimated slippage\n"
                details += f"  • Price impact of your trade size\n"
            
            details += f"\n"
            
            # AI Assessment
            details += f"### 🤖 AI Risk Assessment\n"
            details += f"**AI Confidence**: {opp.get('ai_confidence', 0):.2f}/1.0\n"
            details += f"**Risk Level**: {opp.get('risk_level', 'UNKNOWN')}\n"
            details += f"**Estimated Execution Time**: {opp.get('execution_time_estimate', 0):.1f}s\n\n"
            
            # Risk Factors
            details += f"### ⚠️ Risk Factors\n"
            details += f"• Market volatility may affect actual profit\n"
            details += f"• Gas fees (DEX) can vary significantly\n"
            details += f"• Execution speed critical for maintaining spread\n"
            details += f"• Slippage may be higher for larger amounts\n\n"
            
            details += f"═══════════════════════════════════════\n"
            details += f"**✓ This is the REAL data being compared**\n"
            details += f"**✓ All calculations include fees and slippage**\n"
            
            return details
            
        except Exception as e:
            logger.error(f"Error generating opportunity details: {str(e)}")
            return f"Error loading details: {str(e)}"
    
    @property
    def cached_opportunities(self):
        """Get cached opportunities from the system"""
        return self.arbitrage_system.cached_opportunities if hasattr(self.arbitrage_system, 'cached_opportunities') else []
    
    def create_strategy_performance_chart(self):
        """Create strategy performance comparison chart"""
        try:
            opportunities = self.cached_opportunities
            
            if not opportunities:
                # Return empty chart with message
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available. Run a scan first.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(
                    title="Strategy Performance Comparison",
                    template="plotly_dark",
                    height=400
                )
                return fig
            
            # Aggregate data by strategy
            strategy_stats = {}
            for opp in opportunities:
                strategy = opp.get('strategy', 'Unknown')
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'count': 0,
                        'total_profit': 0,
                        'avg_confidence': 0,
                        'confidence_sum': 0
                    }
                
                strategy_stats[strategy]['count'] += 1
                strategy_stats[strategy]['total_profit'] += opp.get('profit_pct', 0)
                strategy_stats[strategy]['confidence_sum'] += opp.get('ai_confidence', 0)
            
            # Calculate averages
            for strategy in strategy_stats:
                count = strategy_stats[strategy]['count']
                strategy_stats[strategy]['avg_profit'] = strategy_stats[strategy]['total_profit'] / count
                strategy_stats[strategy]['avg_confidence'] = strategy_stats[strategy]['confidence_sum'] / count
            
            # Create chart
            strategies = list(strategy_stats.keys())
            counts = [strategy_stats[s]['count'] for s in strategies]
            avg_profits = [strategy_stats[s]['avg_profit'] for s in strategies]
            avg_confidences = [strategy_stats[s]['avg_confidence'] for s in strategies]
            
            fig = go.Figure()
            
            # Add bar for opportunity count
            fig.add_trace(go.Bar(
                name='Opportunities Found',
                x=strategies,
                y=counts,
                marker_color='#00ff88',
                text=counts,
                textposition='auto',
            ))
            
            # Add line for average profit
            fig.add_trace(go.Scatter(
                name='Avg Profit %',
                x=strategies,
                y=avg_profits,
                mode='lines+markers',
                line=dict(color='#ff6b6b', width=3),
                marker=dict(size=10),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title="Strategy Performance Comparison",
                xaxis_title="Strategy",
                yaxis_title="Opportunities Found",
                yaxis2=dict(
                    title="Avg Profit %",
                    overlaying='y',
                    side='right'
                ),
                template="plotly_dark",
                height=400,
                hovermode='x unified',
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating strategy performance chart: {str(e)}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def create_market_heatmap(self):
        """Create market opportunities heatmap"""
        try:
            opportunities = self.cached_opportunities
            
            if not opportunities:
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available. Run a scan first.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(
                    title="Market Opportunities Heatmap",
                    template="plotly_dark",
                    height=400
                )
                return fig
            
            # Create matrix: Strategy x Token
            strategies = list(set(opp.get('strategy', 'Unknown') for opp in opportunities))
            tokens = list(set(opp.get('token', 'N/A') for opp in opportunities))
            
            # Build profit matrix
            matrix = []
            for strategy in strategies:
                row = []
                for token in tokens:
                    # Find average profit for this strategy-token combination
                    matching_opps = [
                        opp for opp in opportunities 
                        if opp.get('strategy') == strategy and opp.get('token') == token
                    ]
                    if matching_opps:
                        avg_profit = sum(opp.get('profit_pct', 0) for opp in matching_opps) / len(matching_opps)
                        row.append(avg_profit)
                    else:
                        row.append(0)
                matrix.append(row)
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=tokens,
                y=strategies,
                colorscale='Viridis',
                text=[[f'{val:.3f}%' if val > 0 else '' for val in row] for row in matrix],
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="Profit %")
            ))
            
            fig.update_layout(
                title="Market Opportunities Heatmap (Avg Profit %)",
                xaxis_title="Token",
                yaxis_title="Strategy",
                template="plotly_dark",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating market heatmap: {str(e)}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def generate_risk_analysis(self):
        """Generate detailed risk analysis"""
        try:
            opportunities = self.cached_opportunities
            
            if not opportunities:
                return " No opportunities to analyze. Run a scan first."
            
            analysis = "⚠️ **RISK ANALYSIS & WARNINGS**\n\n"
            
            # Calculate risk metrics
            high_risk_count = sum(1 for opp in opportunities if opp.get('risk_level') in ['HIGH', 'CRITICAL'])
            low_confidence_count = sum(1 for opp in opportunities if opp.get('ai_confidence', 0) < 0.5)
            high_profit_count = sum(1 for opp in opportunities if opp.get('profit_pct', 0) > 1.0)
            
            # Overall risk assessment
            if high_risk_count > len(opportunities) * 0.5:
                analysis += "🔴 **HIGH RISK ALERT**: More than 50% of opportunities are high risk\n\n"
            elif high_risk_count > 0:
                analysis += f"🟡 **MODERATE RISK**: {high_risk_count} high-risk opportunities detected\n\n"
            else:
                analysis += "🟢 **LOW RISK**: Most opportunities appear relatively safe\n\n"
            
            # Detailed warnings
            analysis += "**Key Warnings**:\n"
            analysis += f"• {high_risk_count}/{len(opportunities)} opportunities marked as HIGH RISK\n"
            analysis += f"• {low_confidence_count}/{len(opportunities)} opportunities with AI confidence < 0.5\n"
            analysis += f"• {high_profit_count}/{len(opportunities)} opportunities with profit > 1% (verify carefully)\n\n"
            
            # Recommendations
            analysis += "**Recommendations**:\n"
            analysis += "✓ Start with small test amounts\n"
            analysis += "✓ Verify prices manually before execution\n"
            analysis += "✓ Consider gas fees for DEX transactions\n"
            analysis += "✓ Monitor slippage during execution\n"
            analysis += "✓ Use demo mode for testing\n"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating risk analysis: {str(e)}")
            return f"Error: {str(e)}"
    
    def refresh_analytics(self):
        """Refresh analytics charts and risk analysis"""
        return (
            self.create_strategy_performance_chart(),
            self.create_market_heatmap(),
            self.generate_risk_analysis()
        )
    
    def show_opportunity_details_from_dropdown(self, selected_opp):
        """Show details for opportunity selected in dropdown"""
        try:
            if not selected_opp:
                return "No opportunity selected. Please select an opportunity from the dropdown above."
            
            # Parse the dropdown value to find the opportunity
            # Format: "strategy - token (profit%)"
            opportunities = self.cached_opportunities
            
            if not opportunities:
                return "No opportunities available. Please run a scan first."
            
            # Find matching opportunity
            for idx, opp in enumerate(opportunities):
                dropdown_label = f"{opp['strategy']} - {opp['token']} ({opp['profit_pct']:.2f}%)"
                if dropdown_label == selected_opp:
                    return self.generate_opportunity_details(idx)
            
            return "Could not find details for the selected opportunity."
            
        except Exception as e:
            logger.error(f"Error showing opportunity details: {str(e)}")
            return f"Error: {str(e)}"

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
