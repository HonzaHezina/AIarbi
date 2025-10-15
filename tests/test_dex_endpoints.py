import pytest
from utils import config

def test_dex_endpoints_present():
    """Test that all 8 DEX endpoints are configured"""
    expected = {
        'uniswap', 'sushiswap', 'pancakeswap', 'dydx',
        'curve', 'balancer', 'oneinch', 'kyber'
    }
    configured = set(config.DEX_ENDPOINTS.keys())
    assert expected.issubset(configured), f"Missing DEX endpoints: {expected - configured}"

def test_dex_endpoints_structure():
    """Test that DEX endpoints have required fields"""
    required_fields = ['name', 'base_url', 'testnet_url', 'api_type', 'rate_limit', 'requires_api_key', 'network', 'key_data', 'docs']
    
    for name, entry in config.DEX_ENDPOINTS.items():
        assert isinstance(entry, dict), f"Entry for {name} must be a dict"
        for field in required_fields:
            # rate_limit can be per_day, per_hour, per_minute, or per_second
            if field == 'rate_limit':
                has_rate_limit = any(k.startswith('rate_limit_per_') for k in entry.keys())
                assert has_rate_limit, f"{name} missing rate_limit field"
            else:
                assert field in entry, f"{name} missing required field: {field}"
        
        # Verify base_url is not empty
        assert entry.get('base_url'), f"{name} missing base_url"
        
        # Verify testnet_url is not empty
        assert entry.get('testnet_url'), f"{name} missing testnet_url"
        
        # Verify API type is valid
        assert entry.get('api_type') in ['rest', 'graphql', 'websocket'], f"{name} has invalid api_type"

def test_dex_config_enhanced():
    """Test that DEX_CONFIG includes all protocols with enhanced metadata"""
    expected = {
        'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
        'dydx', 'curve', 'balancer', 'oneinch', 'kyber',
        'tinyman', 'pact'
    }
    configured = set(config.DEX_CONFIG.keys())
    assert expected.issubset(configured), f"Missing DEX protocols in DEX_CONFIG: {expected - configured}"

def test_dex_config_fields():
    """Test that DEX_CONFIG entries have required fields"""
    required_fields = ['name', 'fee', 'gas_cost_usd', 'network', 'rate_limit', 'reliable']
    
    for name, entry in config.DEX_CONFIG.items():
        assert isinstance(entry, dict), f"Entry for {name} must be a dict"
        for field in required_fields:
            assert field in entry, f"{name} missing required field: {field}"
        
        # Verify fee is a valid percentage (0-1)
        assert 0 <= entry.get('fee', 0) <= 1, f"{name} has invalid fee"
        
        # Verify gas_cost_usd is positive
        assert entry.get('gas_cost_usd', 0) >= 0, f"{name} has invalid gas_cost_usd"
        
        # Verify rate_limit is positive
        assert entry.get('rate_limit', 0) > 0, f"{name} has invalid rate_limit"

def test_dex_rate_limits():
    """Test that rate limits are properly configured"""
    for name, entry in config.DEX_ENDPOINTS.items():
        # At least one rate limit field should be present
        has_rate_limit = any(k.startswith('rate_limit_per_') for k in entry.keys())
        assert has_rate_limit, f"{name} missing rate limit configuration"
        
        # Verify rate limit values are positive
        for key, value in entry.items():
            if key.startswith('rate_limit_per_'):
                assert value > 0, f"{name} has invalid rate limit: {key}={value}"

def test_dex_authentication_config():
    """Test authentication configuration for DEX endpoints"""
    for name, entry in config.DEX_ENDPOINTS.items():
        requires_key = entry.get('requires_api_key', False)
        
        if requires_key:
            # If API key is required, auth_type should be specified
            if 'auth_type' in entry:
                assert entry['auth_type'] in ['api_key', 'hmac', 'oauth'], \
                    f"{name} has invalid auth_type"
        
        # Verify requires_api_key is boolean
        assert isinstance(requires_key, bool), f"{name} requires_api_key must be boolean"

def test_dex_network_consistency():
    """Test that DEX networks are properly configured"""
    valid_networks = ['ethereum', 'bsc', 'polygon', 'algorand', 'arbitrum', 'optimism']
    
    for name, entry in config.DEX_ENDPOINTS.items():
        network = entry.get('network')
        assert network in valid_networks, f"{name} has invalid network: {network}"

def test_get_supported_dex_protocols():
    """Test that get_supported_dex_protocols returns the correct list"""
    protocols = config.get_supported_dex_protocols()
    
    assert isinstance(protocols, list), "get_supported_dex_protocols must return a list"
    assert len(protocols) > 0, "get_supported_dex_protocols should not be empty"
    
    # Verify all expected protocols are present
    expected = [
        'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
        'dydx', 'curve', 'balancer', 'oneinch', 'kyber',
        'tinyman', 'pact'
    ]
    for protocol in expected:
        assert protocol in protocols, f"Missing protocol in get_supported_dex_protocols: {protocol}"

def test_dex_key_data_fields():
    """Test that key_data fields are properly specified"""
    for name, entry in config.DEX_ENDPOINTS.items():
        key_data = entry.get('key_data', [])
        assert isinstance(key_data, list), f"{name} key_data must be a list"
        assert len(key_data) > 0, f"{name} key_data should not be empty"
        
        # Verify all key_data entries are strings
        for data in key_data:
            assert isinstance(data, str), f"{name} key_data must contain strings"
