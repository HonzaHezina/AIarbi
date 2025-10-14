"""
Test UI functionality to ensure all components work properly
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import ArbitrageDashboard


def test_dashboard_initialization():
    """Test that ArbitrageDashboard can be initialized"""
    dashboard = ArbitrageDashboard()
    assert dashboard is not None
    assert dashboard.arbitrage_system is not None
    assert dashboard.execution_history == []
    assert dashboard.performance_data == []
    print("✓ Dashboard initialization works")


def test_system_status_display():
    """Test system status display generation"""
    dashboard = ArbitrageDashboard()
    status = dashboard.get_system_status_display()
    
    assert status is not None
    assert isinstance(status, str)
    assert len(status) > 0
    assert "System Status" in status or "AI Model" in status
    print("✓ System status display works")


def test_strategies_info_display():
    """Test strategies information display"""
    dashboard = ArbitrageDashboard()
    info = dashboard.get_strategies_info_display()
    
    assert info is not None
    assert isinstance(info, str)
    assert len(info) > 0
    print("✓ Strategies info display works")


def test_core_diagnostics():
    """Test core diagnostics generation"""
    dashboard = ArbitrageDashboard()
    diag = dashboard.get_core_diagnostics()
    
    assert diag is not None
    assert isinstance(diag, str)
    assert len(diag) > 0
    assert "CORE COMPONENTS" in diag or "AI Model" in diag
    print("✓ Core diagnostics works")


def test_data_diagnostics():
    """Test data diagnostics generation"""
    dashboard = ArbitrageDashboard()
    diag = dashboard.get_data_diagnostics()
    
    assert diag is not None
    assert isinstance(diag, str)
    assert len(diag) > 0
    assert "DATA ENGINE" in diag or "CEX" in diag or "DEX" in diag
    print("✓ Data diagnostics works")


def test_refresh_diagnostics():
    """Test diagnostics refresh"""
    dashboard = ArbitrageDashboard()
    result = dashboard.refresh_diagnostics()
    
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert all(isinstance(r, str) for r in result)
    print("✓ Refresh diagnostics works")


def test_strategy_performance_chart():
    """Test strategy performance chart generation"""
    dashboard = ArbitrageDashboard()
    chart = dashboard.create_strategy_performance_chart()
    
    assert chart is not None
    # It should return a plotly Figure object
    assert hasattr(chart, 'data')
    print("✓ Strategy performance chart works")


def test_market_heatmap():
    """Test market heatmap generation"""
    dashboard = ArbitrageDashboard()
    heatmap = dashboard.create_market_heatmap()
    
    assert heatmap is not None
    assert hasattr(heatmap, 'data')
    print("✓ Market heatmap works")


def test_risk_analysis():
    """Test risk analysis generation"""
    dashboard = ArbitrageDashboard()
    analysis = dashboard.generate_risk_analysis()
    
    assert analysis is not None
    assert isinstance(analysis, str)
    assert len(analysis) > 0
    print("✓ Risk analysis works")


def test_refresh_analytics():
    """Test analytics refresh"""
    dashboard = ArbitrageDashboard()
    result = dashboard.refresh_analytics()
    
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 3
    # First two should be charts, last should be string
    assert hasattr(result[0], 'data')  # Chart
    assert hasattr(result[1], 'data')  # Chart
    assert isinstance(result[2], str)  # Risk analysis
    print("✓ Refresh analytics works")


def test_opportunity_details_generation():
    """Test opportunity details generation with no data"""
    dashboard = ArbitrageDashboard()
    details = dashboard.generate_opportunity_details(-1)
    
    assert details is not None
    assert isinstance(details, str)
    assert "Select an opportunity" in details or "No opportunity data" in details
    print("✓ Opportunity details generation works")


def test_show_opportunity_details_from_dropdown():
    """Test showing opportunity details from dropdown with no selection"""
    dashboard = ArbitrageDashboard()
    details = dashboard.show_opportunity_details_from_dropdown(None)
    
    assert details is not None
    assert isinstance(details, str)
    assert "No opportunity" in details
    print("✓ Show opportunity details from dropdown works")


def test_performance_chart_creation():
    """Test performance chart creation"""
    dashboard = ArbitrageDashboard()
    chart = dashboard.create_performance_chart()
    
    assert chart is not None
    assert hasattr(chart, 'data')
    print("✓ Performance chart creation works")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING UI FUNCTIONALITY")
    print("="*70 + "\n")
    
    test_dashboard_initialization()
    test_system_status_display()
    test_strategies_info_display()
    test_core_diagnostics()
    test_data_diagnostics()
    test_refresh_diagnostics()
    test_strategy_performance_chart()
    test_market_heatmap()
    test_risk_analysis()
    test_refresh_analytics()
    test_opportunity_details_generation()
    test_show_opportunity_details_from_dropdown()
    test_performance_chart_creation()
    
    print("\n" + "="*70)
    print("ALL UI TESTS PASSED! ✓")
    print("="*70)
