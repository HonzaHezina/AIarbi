"""Integration tests for DEX endpoints configuration"""
import pytest
from utils import config
from core.data_engine import DataEngine
from strategies.dex_cex_arbitrage import DEXCEXArbitrage


def test_data_engine_has_all_dex_protocols():
    """Test that DataEngine includes all configured DEX protocols"""
    engine = DataEngine()
    
    # Check that DataEngine has the new protocols
    expected_protocols = [
        'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
        'dydx', 'curve', 'balancer', 'oneinch', 'kyber',
        'tinyman', 'pact'
    ]
    
    for protocol in expected_protocols:
        assert protocol in engine.dex_protocols, f"DataEngine missing protocol: {protocol}"


def test_dex_cex_arbitrage_has_all_protocols():
    """Test that DEXCEXArbitrage strategy includes all protocols"""
    # Mock AI model for testing
    class MockAI:
        pass
    
    strategy = DEXCEXArbitrage(MockAI())
    
    expected_protocols = [
        'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
        'dydx', 'curve', 'balancer', 'oneinch', 'kyber',
        'tinyman', 'pact'
    ]
    
    for protocol in expected_protocols:
        assert protocol in strategy.dex_protocols, f"Strategy missing protocol: {protocol}"


@pytest.mark.asyncio
async def test_gas_cost_estimation_for_all_protocols():
    """Test that gas costs can be estimated for all protocols"""
    class MockAI:
        pass
    
    strategy = DEXCEXArbitrage(MockAI())
    
    test_protocols = [
        'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
        'dydx', 'curve', 'balancer', 'oneinch', 'kyber',
        'tinyman', 'pact'
    ]
    
    for protocol in test_protocols:
        gas_cost = await strategy.estimate_dex_gas_cost(protocol, 'BTC')
        assert gas_cost > 0, f"Gas cost for {protocol} should be positive"
        assert gas_cost < 1000, f"Gas cost for {protocol} seems unreasonably high: ${gas_cost}"


def test_dex_config_consistency():
    """Test that DEX_CONFIG and DEX_ENDPOINTS are consistent"""
    # Protocols that should exist in both configurations
    common_protocols = ['uniswap', 'sushiswap', 'pancakeswap', 'dydx', 'curve', 'balancer', 'oneinch', 'kyber']
    
    for protocol in common_protocols:
        # Check DEX_ENDPOINTS
        assert protocol in config.DEX_ENDPOINTS, f"{protocol} missing from DEX_ENDPOINTS"
        endpoint = config.DEX_ENDPOINTS[protocol]
        
        # Check DEX_CONFIG
        assert protocol in config.DEX_CONFIG, f"{protocol} missing from DEX_CONFIG"
        protocol_config = config.DEX_CONFIG[protocol]
        
        # Verify network consistency
        endpoint_network = endpoint.get('network')
        config_network = protocol_config.get('network')
        assert endpoint_network == config_network, \
            f"Network mismatch for {protocol}: endpoint={endpoint_network}, config={config_network}"


def test_dex_endpoints_accessible():
    """Test that DEX endpoint URLs are properly formatted"""
    for protocol, endpoint in config.DEX_ENDPOINTS.items():
        base_url = endpoint.get('base_url')
        testnet_url = endpoint.get('testnet_url')
        
        # Verify URLs are not empty
        assert base_url, f"{protocol} missing base_url"
        assert testnet_url, f"{protocol} missing testnet_url"
        
        # Verify URLs start with http(s) or wss
        assert base_url.startswith(('http://', 'https://')), \
            f"{protocol} base_url should start with http(s)://"
        assert testnet_url.startswith(('http://', 'https://')), \
            f"{protocol} testnet_url should start with http(s)://"


def test_dex_protocol_reliability_flags():
    """Test that reliability flags are properly set"""
    reliable_protocols = [
        'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
        'dydx', 'curve', 'balancer', 'oneinch', 'kyber'
    ]
    
    for protocol in reliable_protocols:
        if protocol in config.DEX_CONFIG:
            assert config.DEX_CONFIG[protocol].get('reliable', False), \
                f"{protocol} should be marked as reliable"


def test_authentication_only_for_dydx():
    """Test that only dYdX requires authentication among the 8 main protocols"""
    main_protocols = ['uniswap', 'sushiswap', 'pancakeswap', 'dydx', 'curve', 'balancer', 'oneinch', 'kyber']
    
    for protocol in main_protocols:
        endpoint = config.DEX_ENDPOINTS[protocol]
        requires_auth = endpoint.get('requires_api_key', False)
        
        if protocol == 'dydx':
            assert requires_auth, "dYdX should require authentication"
            assert endpoint.get('auth_type') == 'hmac', "dYdX should use HMAC authentication"
        else:
            assert not requires_auth, f"{protocol} should not require authentication"


def test_network_specific_gas_costs():
    """Test that gas costs are appropriate for each network"""
    # Ethereum protocols should have higher gas costs
    ethereum_protocols = ['uniswap_v3', 'uniswap', 'sushiswap', 'curve', 'balancer', 'oneinch', 'kyber']
    for protocol in ethereum_protocols:
        if protocol in config.DEX_CONFIG:
            gas_cost = config.DEX_CONFIG[protocol].get('gas_cost_usd', 0)
            assert gas_cost >= 10.0, f"{protocol} (Ethereum) should have gas cost >= $10"
    
    # BSC protocols should have lower gas costs
    bsc_protocols = ['pancakeswap']
    for protocol in bsc_protocols:
        if protocol in config.DEX_CONFIG:
            gas_cost = config.DEX_CONFIG[protocol].get('gas_cost_usd', 0)
            assert gas_cost < 5.0, f"{protocol} (BSC) should have gas cost < $5"
    
    # Algorand protocols should have very low gas costs
    algorand_protocols = ['tinyman', 'pact']
    for protocol in algorand_protocols:
        if protocol in config.DEX_CONFIG:
            gas_cost = config.DEX_CONFIG[protocol].get('gas_cost_usd', 0)
            assert gas_cost < 0.01, f"{protocol} (Algorand) should have gas cost < $0.01"


def test_api_type_validity():
    """Test that all DEX endpoints have valid API types"""
    valid_api_types = ['rest', 'graphql', 'websocket']
    
    for protocol, endpoint in config.DEX_ENDPOINTS.items():
        api_type = endpoint.get('api_type')
        assert api_type in valid_api_types, \
            f"{protocol} has invalid api_type: {api_type}. Must be one of {valid_api_types}"


def test_websocket_availability():
    """Test WebSocket availability is properly configured"""
    # Protocols that should have WebSocket support
    ws_protocols = ['pancakeswap', 'dydx']
    
    for protocol in ws_protocols:
        endpoint = config.DEX_ENDPOINTS[protocol]
        assert endpoint.get('websocket_url'), f"{protocol} should have production WebSocket URL"
        assert endpoint.get('testnet_websocket_url'), f"{protocol} should have testnet WebSocket URL"
    
    # Protocols that should NOT have WebSocket (REST/GraphQL only)
    non_ws_protocols = ['curve', 'uniswap', 'sushiswap']
    
    for protocol in non_ws_protocols:
        endpoint = config.DEX_ENDPOINTS[protocol]
        ws_url = endpoint.get('websocket_url')
        assert ws_url is None, f"{protocol} should not have WebSocket URL (REST/GraphQL only)"
