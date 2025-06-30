import os
import requests
import pandas as pd
import json
import time
from datetime import datetime
import logging

from config import config, logger
from utils import (
    retry_on_failure, safe_request, default_cache, default_rate_limiter,
    ensure_directory, save_json, save_markdown, format_currency, 
    validate_address
)

@retry_on_failure(max_retries=config.scraping.max_retries)
def fetch_debank_wallet_data(address):
    """
    Fetch wallet data from Debank API
    """
    if not validate_address(address):
        logger.error(f"Invalid address format: {address}")
        return None
    
    cache_key = f"debank_wallet_{address}"
    cached_data = default_cache.get(cache_key)
    if cached_data:
        logger.debug(f"Using cached DeBank data for {address}")
        return cached_data
    
    try:
        headers = {"User-Agent": config.scraping.user_agent}
        
        # Fetch token list
        token_url = f"https://openapi.debank.com/v1/user/token_list"
        token_params = {"id": address, "is_all": "true"}
        
        token_response = safe_request(
            token_url, 
            headers=headers, 
            params=token_params,
            timeout=config.scraping.timeout,
            rate_limiter=default_rate_limiter
        )
        
        if not token_response:
            logger.error(f"Failed to fetch token data for {address}")
            return None
        
        tokens = token_response.json()
        
        # Add delay to respect rate limits
        time.sleep(config.scraping.request_delay)
        
        # Fetch protocol list (DeFi positions)
        protocol_url = f"https://openapi.debank.com/v1/user/complex_protocol_list"
        protocol_params = {"id": address}
        
        protocol_response = safe_request(
            protocol_url,
            headers=headers,
            params=protocol_params,
            timeout=config.scraping.timeout,
            rate_limiter=default_rate_limiter
        )
        
        protocols = protocol_response.json() if protocol_response else []
        
        result = {
            "address": address,
            "tokens": tokens,
            "protocols": protocols,
            "fetched_at": datetime.now().isoformat()
        }
        
        # Cache the result
        default_cache.set(cache_key, result)
        logger.info(f"Successfully fetched DeBank data for {address}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching DeBank data for {address}: {e}")
        return None

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
    """Main function to orchestrate whale wallet tracking"""
    logger.info("Starting whale wallet tracking process")
    
    try:
        # Create directories
        wallets_data_dir = os.path.join(config.paths.data_dir, "wallets")
        wallets_content_dir = os.path.join(config.paths.content_dir, "wallets")
        
        ensure_directory(wallets_data_dir)
        ensure_directory(wallets_content_dir)
        
        # List of whale addresses to track
        whale_addresses = [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Example whale address
            "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance 14
            "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8"   # Binance 7
        ]
        
        successful_addresses = []
        failed_addresses = []
        
        for address in whale_addresses:
            logger.info(f"Processing wallet {address}...")
            
            try:
                # Validate address
                if not validate_address(address):
                    logger.error(f"Invalid address format: {address}")
                    failed_addresses.append(address)
                    continue
                
                # Fetch data
                wallet_data = fetch_debank_wallet_data(address)
                
                if not wallet_data:
                    logger.warning(f"No data fetched for {address}")
                    failed_addresses.append(address)
                    continue
                
                # Calculate stats
                stats = calculate_wallet_stats(wallet_data)
                
                # Generate markdown
                markdown = generate_markdown_report(address, wallet_data, stats)
                
                # Save data
                save_data(address, wallet_data, stats, markdown)
                successful_addresses.append(address)
                logger.info(f"Successfully processed wallet {address}")
                
            except Exception as e:
                logger.error(f"Error processing wallet {address}: {e}", exc_info=True)
                failed_addresses.append(address)
            
            # Rate limiting delay
            time.sleep(config.scraping.request_delay)
        
        # Generate summary report of all successful wallets
        if successful_addresses:
            generate_whale_summary(successful_addresses)
            
        # Log summary
        logger.info(f"Wallet tracking complete. Success: {len(successful_addresses)}, Failed: {len(failed_addresses)}")
        if failed_addresses:
            logger.warning(f"Failed addresses: {failed_addresses}")
            
    except Exception as e:
        logger.error(f"Error in main wallet tracking process: {e}", exc_info=True)
        raise

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