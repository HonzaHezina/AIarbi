#!/usr/bin/env python3
"""
Demo script to showcase DEX endpoint configuration and usage.

This script demonstrates how to:
1. List all supported DEX protocols
2. Get endpoint configurations
3. Check rate limits
4. Display testnet vs production URLs
5. Show authentication requirements

Usage:
    python tools/demo_dex_endpoints.py
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from utils import config
import json


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Print a formatted section header"""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}")


def list_all_protocols():
    """List all supported DEX protocols"""
    print_header("SUPPORTED DEX PROTOCOLS")
    
    protocols = config.get_supported_dex_protocols()
    print(f"\nTotal protocols: {len(protocols)}")
    print("\nProtocols:")
    for i, protocol in enumerate(protocols, 1):
        protocol_config = config.DEX_CONFIG.get(protocol, {})
        name = protocol_config.get('name', 'Unknown')
        network = protocol_config.get('network', 'Unknown')
        reliable = "✓" if protocol_config.get('reliable', False) else "✗"
        print(f"  {i:2d}. {protocol:15s} ({name:20s}) Network: {network:10s} Reliable: {reliable}")


def show_endpoint_details(protocol_name):
    """Show detailed information for a specific protocol"""
    print_section(f"DETAILS FOR: {protocol_name.upper()}")
    
    # Get endpoint configuration
    endpoint = config.get_dex_endpoint(protocol_name, testnet=False)
    if not endpoint:
        print(f"  ⚠️  Protocol '{protocol_name}' not found in DEX_ENDPOINTS")
        return
    
    # Get protocol configuration
    protocol_config = config.DEX_CONFIG.get(protocol_name, {})
    
    print(f"\n📋 Basic Information:")
    print(f"   Name:              {endpoint.get('name', 'N/A')}")
    print(f"   Network:           {endpoint.get('network', 'N/A')}")
    print(f"   API Type:          {endpoint.get('api_type', 'N/A')}")
    
    print(f"\n🔗 Endpoints:")
    print(f"   Production URL:    {endpoint.get('base_url', 'N/A')}")
    print(f"   Testnet URL:       {endpoint.get('testnet_url', 'N/A')}")
    
    if endpoint.get('websocket_url'):
        print(f"   WebSocket (Prod):  {endpoint['websocket_url']}")
    if endpoint.get('testnet_websocket_url'):
        print(f"   WebSocket (Test):  {endpoint['testnet_websocket_url']}")
    
    print(f"\n⚡ Rate Limiting:")
    limit, period = config.get_dex_rate_limit(protocol_name)
    if limit and period:
        print(f"   Limit:             {limit:,} requests per {period}")
    else:
        print(f"   Limit:             Not configured")
    
    print(f"\n🔐 Authentication:")
    requires_key = endpoint.get('requires_api_key', False)
    auth_type = endpoint.get('auth_type', 'None')
    print(f"   Required:          {'Yes ⚠️' if requires_key else 'No ✓'}")
    if requires_key:
        print(f"   Type:              {auth_type}")
    
    print(f"\n💰 Trading Costs:")
    print(f"   Protocol Fee:      {protocol_config.get('fee', 0) * 100:.2f}%")
    print(f"   Avg Gas Cost:      ${protocol_config.get('gas_cost_usd', 0):.2f}")
    
    print(f"\n📊 Key Data Available:")
    key_data = endpoint.get('key_data', [])
    for data in key_data:
        print(f"   • {data}")
    
    print(f"\n📖 Documentation:")
    print(f"   {endpoint.get('docs', 'N/A')}")


def compare_production_vs_testnet():
    """Compare production and testnet endpoints"""
    print_header("PRODUCTION vs TESTNET COMPARISON")
    
    print(f"\n{'Protocol':<15} {'Production URL':<60} {'Testnet URL':<60}")
    print(f"{'-' * 15} {'-' * 60} {'-' * 60}")
    
    for protocol_name in ['uniswap', 'sushiswap', 'pancakeswap', 'dydx']:
        prod = config.get_dex_endpoint(protocol_name, testnet=False)
        test = config.get_dex_endpoint(protocol_name, testnet=True)
        
        if prod and test:
            prod_url = prod.get('base_url', 'N/A')[:57] + "..."
            test_url = test.get('testnet_url', 'N/A')[:57] + "..."
            print(f"{protocol_name:<15} {prod_url:<60} {test_url:<60}")


def show_rate_limit_summary():
    """Show rate limits for all protocols"""
    print_header("RATE LIMIT SUMMARY")
    
    print(f"\n{'Protocol':<15} {'Rate Limit':<20} {'Time Period':<15} {'Notes'}")
    print(f"{'-' * 15} {'-' * 20} {'-' * 15} {'-' * 30}")
    
    for protocol_name in config.DEX_ENDPOINTS.keys():
        limit, period = config.get_dex_rate_limit(protocol_name)
        endpoint = config.DEX_ENDPOINTS[protocol_name]
        requires_auth = "🔐 Auth Required" if endpoint.get('requires_api_key') else "✓ No Auth"
        
        if limit and period:
            print(f"{protocol_name:<15} {limit:>15,}      per {period:<10} {requires_auth}")
        else:
            print(f"{protocol_name:<15} {'Not configured':<20} {'':<15} {requires_auth}")


def show_network_distribution():
    """Show DEX protocols grouped by network"""
    print_header("NETWORK DISTRIBUTION")
    
    networks = {}
    for protocol_name, endpoint in config.DEX_ENDPOINTS.items():
        network = endpoint.get('network', 'Unknown')
        if network not in networks:
            networks[network] = []
        networks[network].append(protocol_name)
    
    print(f"\nProtocols grouped by blockchain network:\n")
    for network, protocols in sorted(networks.items()):
        print(f"  {network.upper()}:")
        for protocol in sorted(protocols):
            protocol_config = config.DEX_CONFIG.get(protocol, {})
            gas_cost = protocol_config.get('gas_cost_usd', 0)
            print(f"    • {protocol:<15} (Avg gas: ${gas_cost:.2f})")


def show_api_type_distribution():
    """Show DEX protocols grouped by API type"""
    print_header("API TYPE DISTRIBUTION")
    
    api_types = {}
    for protocol_name, endpoint in config.DEX_ENDPOINTS.items():
        api_type = endpoint.get('api_type', 'Unknown')
        if api_type not in api_types:
            api_types[api_type] = []
        api_types[api_type].append(protocol_name)
    
    print(f"\nProtocols grouped by API type:\n")
    for api_type, protocols in sorted(api_types.items()):
        print(f"  {api_type.upper()}:")
        for protocol in sorted(protocols):
            endpoint = config.DEX_ENDPOINTS[protocol]
            has_ws = "✓ WebSocket" if endpoint.get('websocket_url') else "✗ REST only"
            print(f"    • {protocol:<15} ({has_ws})")


def main():
    """Main demo function"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  DEX ENDPOINTS CONFIGURATION DEMO".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Show all protocols
    list_all_protocols()
    
    # Show detailed information for key protocols
    for protocol in ['uniswap', 'pancakeswap', 'dydx', 'curve']:
        show_endpoint_details(protocol)
    
    # Show comparisons and summaries
    compare_production_vs_testnet()
    show_rate_limit_summary()
    show_network_distribution()
    show_api_type_distribution()
    
    # Summary
    print_header("SUMMARY")
    print(f"""
  Total DEX Protocols:     {len(config.DEX_ENDPOINTS)}
  Total Networks:          {len(set(e.get('network') for e in config.DEX_ENDPOINTS.values()))}
  Protocols with Auth:     {sum(1 for e in config.DEX_ENDPOINTS.values() if e.get('requires_api_key'))}
  Protocols with WebSocket: {sum(1 for e in config.DEX_ENDPOINTS.values() if e.get('websocket_url'))}
  GraphQL APIs:            {sum(1 for e in config.DEX_ENDPOINTS.values() if e.get('api_type') == 'graphql')}
  REST APIs:               {sum(1 for e in config.DEX_ENDPOINTS.values() if e.get('api_type') == 'rest')}
    """)
    
    print("\n" + "=" * 80)
    print("  ✓ Demo completed successfully!")
    print("  📖 For more details, see: docs_archive/DEX_ENDPOINTS.md")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
