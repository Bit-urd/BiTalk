import requests
import pandas as pd
import json
import time
from datetime import datetime

def fetch_debank_wallet_data(address):
    """
    Fetch wallet data from Debank API
    """
    # Fetch token list
    token_url = f"https://openapi.debank.com/v1/user/token_list?id={address}&is_all=true"
    token_response = requests.get(token_url)
    tokens = token_response.json()
    
    # Fetch protocol list (DeFi positions)
    protocol_url = f"https://openapi.debank.com/v1/user/complex_protocol_list?id={address}"
    protocol_response = requests.get(protocol_url)
    protocols = protocol_response.json()
    
    return {
        "tokens": tokens,
        "protocols": protocols
    }

def fetch_covalent_transactions(address, chain_id=1):
    """
    Fetch recent transactions from Covalent API
    Requires API key from https://www.covalenthq.com/
    """
    # Replace with your actual API key
    api_key = "YOUR_COVALENT_API_KEY"
    
    url = f"https://api.covalenthq.com/v1/{chain_id}/address/{address}/transactions_v2/"
    headers = {"Authorization": f"Basic {api_key}"}
    
    response = requests.get(url, headers=headers)
    return response.json()

def calculate_wallet_stats(wallet_data):
    """
    Calculate statistics from wallet data
    """
    tokens = wallet_data["tokens"]
    protocols = wallet_data["protocols"]
    
    # Calculate total value
    total_token_value = sum(token.get("price", 0) * token.get("amount", 0) for token in tokens)
    total_protocol_value = sum(protocol.get("portfolio_item_list", [{}])[0].get("stats", {}).get("net_usd_value", 0) 
                              for protocol in protocols)
    
    total_value = total_token_value + total_protocol_value
    
    # Get token distribution
    token_distribution = []
    for token in tokens:
        if token.get("price", 0) * token.get("amount", 0) > 0:
            token_distribution.append({
                "symbol": token.get("symbol", "Unknown"),
                "value_usd": token.get("price", 0) * token.get("amount", 0),
                "percentage": (token.get("price", 0) * token.get("amount", 0) / total_value * 100) if total_value > 0 else 0
            })
    
    # Sort by value
    token_distribution = sorted(token_distribution, key=lambda x: x["value_usd"], reverse=True)
    
    return {
        "total_value_usd": total_value,
        "token_value_usd": total_token_value,
        "defi_value_usd": total_protocol_value,
        "token_distribution": token_distribution
    }

def generate_markdown_report(address, wallet_data, stats):
    """
    Generate a markdown report from wallet data
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown = f"""# Whale Wallet Analysis: {address}

*Generated on: {now}*

## Portfolio Summary

- **Total Portfolio Value:** ${stats['total_value_usd']:,.2f}
- **Token Holdings Value:** ${stats['token_value_usd']:,.2f}
- **DeFi Positions Value:** ${stats['defi_value_usd']:,.2f}

## Top Token Holdings

| Token | Value (USD) | % of Portfolio |
|-------|-------------|----------------|
"""
    
    # Add top 10 tokens
    for token in stats['token_distribution'][:10]:
        markdown += f"| {token['symbol']} | ${token['value_usd']:,.2f} | {token['percentage']:.2f}% |\n"
    
    markdown += """
## DeFi Positions

| Protocol | Value (USD) |
|----------|-------------|
"""
    
    # Add DeFi positions
    for protocol in wallet_data['protocols']:
        if len(protocol.get("portfolio_item_list", [])) > 0:
            value = protocol["portfolio_item_list"][0]["stats"].get("net_usd_value", 0)
            if value > 0:
                markdown += f"| {protocol.get('name', 'Unknown')} | ${value:,.2f} |\n"
    
    return markdown

def save_data(address, wallet_data, stats, markdown):
    """
    Save data to files
    """
    # Save raw data as JSON
    with open(f"data/wallets/{address}_data.json", "w") as f:
        json.dump(wallet_data, f, indent=2)
    
    # Save stats as JSON
    with open(f"data/wallets/{address}_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    # Save markdown report
    with open(f"content/wallets/{address}.md", "w") as f:
        f.write(markdown)

def main():
    # List of whale addresses to track
    whale_addresses = [
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Example whale address
        "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance 14
        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8"   # Binance 7
    ]
    
    for address in whale_addresses:
        print(f"Fetching data for {address}...")
        
        # Fetch data
        wallet_data = fetch_debank_wallet_data(address)
        
        # Calculate stats
        stats = calculate_wallet_stats(wallet_data)
        
        # Generate markdown
        markdown = generate_markdown_report(address, wallet_data, stats)
        
        # Save data
        try:
            save_data(address, wallet_data, stats, markdown)
            print(f"Data for {address} saved successfully")
        except Exception as e:
            print(f"Error saving data for {address}: {e}")
        
        # Avoid rate limiting
        time.sleep(2)
    
    # Generate summary report of all whales
    generate_whale_summary(whale_addresses)

def generate_whale_summary(addresses):
    """
    Generate a summary report of all tracked whale wallets
    """
    summary_data = []
    
    for address in addresses:
        try:
            with open(f"data/wallets/{address}_stats.json", "r") as f:
                stats = json.load(f)
                
            summary_data.append({
                "address": address,
                "total_value_usd": stats["total_value_usd"],
                "token_value_usd": stats["token_value_usd"],
                "defi_value_usd": stats["defi_value_usd"]
            })
        except Exception as e:
            print(f"Error loading data for {address}: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(summary_data)
    
    # Generate markdown table
    markdown = """# Whale Wallet Tracking Summary

*Generated on: {}*

| Address | Total Value (USD) | Token Value (USD) | DeFi Value (USD) |
|---------|------------------|-------------------|------------------|
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    for _, row in df.iterrows():
        markdown += f"| [{row['address']}](./wallets/{row['address']}.md) | ${row['total_value_usd']:,.2f} | ${row['token_value_usd']:,.2f} | ${row['defi_value_usd']:,.2f} |\n"
    
    # Save summary markdown
    with open("content/wallets/index.md", "w") as f:
        f.write(markdown)
    
    print("Whale summary report generated successfully")

if __name__ == "__main__":
    main()