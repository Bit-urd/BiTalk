import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import os
import re
import random
from bs4 import BeautifulSoup

from config import config, logger
from utils import (
    retry_on_failure, safe_request, default_cache, default_rate_limiter,
    ensure_directory, save_json, save_markdown, truncate_text, get_time_ago
)

# Try to import OpenAI, but provide fallback if not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI module not available. Using sample data for ChatGPT functions.")

@retry_on_failure(max_retries=config.scraping.max_retries)
def fetch_crypto_news(api_key=None, count=10):
    """
    Fetch latest crypto news from a news API
    """
    if api_key:
        # Use a real news API if key is provided
        url = f"https://newsapi.org/v2/everything"
        params = {
            "q": "cryptocurrency OR blockchain OR bitcoin OR ethereum",
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": count,
            "apiKey": api_key
        }

        try:
            response = safe_request(
                url,
                params=params,
                timeout=config.scraping.timeout,
                rate_limiter=default_rate_limiter
            )

            if response:
                data = response.json()
                return data.get("articles", [])
            else:
                logger.error("Failed to fetch news")
                return get_sample_news()
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return get_sample_news()
    else:
        # Use sample data if no API key
        return get_sample_news()

def fetch_trending_topics(count=10):
    """
    Fetch trending crypto topics from Twitter or other sources
    Note: This is a simplified version
    """
    # In a real implementation, you would use Twitter API or other sources
    # For demonstration, return sample data
    return get_sample_trending_topics()

def get_sample_news():
    """
    Return sample news data for demonstration
    """
    return [
        {
            "title": "Bitcoin Surges Past $60,000 as ETF Approval Rumors Intensify",
            "description": "Bitcoin has surged past $60,000 for the first time in months as rumors of a potential spot ETF approval by the SEC intensify.",
            "url": "https://example.com/bitcoin-etf-rumors",
            "publishedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": {"name": "Crypto News Daily"}
        },
        {
            "title": "Ethereum Completes Major Network Upgrade, Gas Fees Drop 30%",
            "description": "Ethereum has successfully completed its latest network upgrade, resulting in a significant 30% reduction in gas fees for users.",
            "url": "https://example.com/ethereum-upgrade",
            "publishedAt": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": {"name": "Blockchain Insider"}
        },
        {
            "title": "Major Bank Launches Cryptocurrency Custody Service for Institutional Clients",
            "description": "A major global bank has announced the launch of a cryptocurrency custody service aimed at institutional clients, marking another step in mainstream adoption.",
            "url": "https://example.com/bank-crypto-custody",
            "publishedAt": (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": {"name": "Financial Times Crypto"}
        },
        {
            "title": "New Layer 2 Solution Claims to Achieve 100,000 TPS with Full Ethereum Security",
            "description": "A new Layer 2 scaling solution for Ethereum claims to achieve 100,000 transactions per second while maintaining full security guarantees.",
            "url": "https://example.com/layer2-scaling",
            "publishedAt": (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": {"name": "DeFi Pulse"}
        },
        {
            "title": "SEC Commissioner Speaks Out in Favor of Clearer Crypto Regulations",
            "description": "A commissioner from the U.S. Securities and Exchange Commission has spoken out in favor of establishing clearer regulations for the cryptocurrency industry.",
            "url": "https://example.com/sec-crypto-regulations",
            "publishedAt": (datetime.now() - timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": {"name": "Regulatory Watch"}
        }
    ]

def get_sample_trending_topics():
    """
    Return sample trending topics for demonstration
    """
    return [
        {"topic": "Bitcoin ETF", "volume": 45000, "sentiment": "positive"},
        {"topic": "Ethereum Layer 2", "volume": 32000, "sentiment": "positive"},
        {"topic": "DeFi Yield Farming", "volume": 28000, "sentiment": "neutral"},
        {"topic": "NFT Market Recovery", "volume": 25000, "sentiment": "positive"},
        {"topic": "Crypto Regulations", "volume": 22000, "sentiment": "negative"},
        {"topic": "Solana Ecosystem", "volume": 18000, "sentiment": "positive"},
        {"topic": "Meme Coins", "volume": 15000, "sentiment": "mixed"},
        {"topic": "Web3 Gaming", "volume": 12000, "sentiment": "positive"},
        {"topic": "DAO Governance", "volume": 10000, "sentiment": "neutral"},
        {"topic": "Cross-chain Bridges", "volume": 8000, "sentiment": "neutral"}
    ]

def extract_keywords(news_articles, trending_topics):
    """
    Extract keywords from news articles and trending topics
    """
    # Combine titles and descriptions from news
    text_content = " ".join([
        f"{article['title']} {article.get('description', '')}" 
        for article in news_articles
    ])

    # Add trending topics
    text_content += " " + " ".join([topic["topic"] for topic in trending_topics])

    # Simple keyword extraction (in a real implementation, use NLP techniques)
    # Remove common words and punctuation
    text_content = text_content.lower()
    words = re.findall(r'\b[a-z0-9]{3,}\b', text_content)

    # Count word frequency
    word_counts = {}
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1

    # Filter out common words
    common_words = ["the", "and", "for", "has", "with", "its", "from", "that", "this", "have"]
    filtered_counts = {word: count for word, count in word_counts.items() if word not in common_words}

    # Sort by frequency
    sorted_words = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)

    # Return top keywords
    return [{"keyword": word, "count": count} for word, count in sorted_words[:20]]

@retry_on_failure(max_retries=config.scraping.max_retries)
def generate_news_summary(news_articles, api_key=None):
    """
    Generate a summary of news articles using ChatGPT
    """
    if not api_key or not OPENAI_AVAILABLE:
        # Return a sample summary if no API key or OpenAI not available
        return get_sample_summary(news_articles)

    try:
        client = openai.OpenAI(api_key=api_key)

        # Prepare news data for the prompt
        news_text = "\n\n".join([
            f"Title: {article['title']}\nSource: {article['source']['name']}\nDescription: {article.get('description', 'No description available.')}"
            for article in news_articles[:5]  # Limit to 5 articles to avoid token limits
        ])

        prompt = f"""Please provide a concise summary of the following crypto news articles:

{news_text}

Create a 3-paragraph summary that highlights the most important developments and their potential impact on the market.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary with ChatGPT: {e}")
        return get_sample_summary(news_articles)

def get_sample_summary(news_articles):
    """
    Generate a sample summary without using ChatGPT
    """
    return """
The cryptocurrency market is showing significant momentum with Bitcoin surpassing $60,000 amid growing optimism around potential ETF approvals. This price movement represents a critical psychological barrier and could signal renewed institutional interest in the asset class.

Meanwhile, Ethereum's recent network upgrade has successfully reduced gas fees by approximately 30%, addressing one of the main pain points for users and developers. This improvement comes at a crucial time as Layer 2 solutions continue to gain traction, with one new protocol claiming to achieve 100,000 transactions per second while maintaining Ethereum's security guarantees.

On the regulatory front, there are signs of potential progress as an SEC Commissioner has publicly advocated for clearer cryptocurrency regulations. This development coincides with traditional financial institutions expanding their crypto offerings, exemplified by a major global bank launching custody services for institutional clients, further bridging the gap between traditional finance and digital assets.
"""

@retry_on_failure(max_retries=config.scraping.max_retries)
def generate_content_script(topic, keywords, api_key=None):
    """
    Generate a content script for a given topic using ChatGPT
    """
    if not api_key or not OPENAI_AVAILABLE:
        # Return a sample script if no API key or OpenAI not available
        return get_sample_script(topic)

    try:
        openai.api_key = api_key

        # Prepare keywords for the prompt
        keyword_text = ", ".join([k["keyword"] for k in keywords[:10]])

        prompt = f"""Create a short script for a crypto content creator covering the topic: "{topic}".

The script should:
1. Have a catchy introduction that grabs attention
2. Include these trending keywords: {keyword_text}
3. Present 3 main points about the topic
4. End with a call to action

Format the script with clear sections for INTRO, MAIN POINTS, and CONCLUSION.
Keep it under 500 words and make it engaging for a crypto audience.
"""

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.8
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating script with ChatGPT: {e}")
        return get_sample_script(topic)

def get_sample_script(topic):
    """
    Generate a sample content script without using ChatGPT
    """
    return f"""
## SCRIPT: {topic}

### INTRO
Hey crypto fam! Welcome back to the channel. Today we're diving deep into {topic} - one of the hottest trends shaping the future of blockchain technology right now. If you've been following the markets lately, you know this couldn't come at a more critical time.

### MAIN POINTS
First, let's break down what's actually happening with {topic}. The recent developments have caught the attention of both retail investors and institutional players, creating a perfect storm of opportunity and innovation.

Second, we need to look at the broader implications. This isn't just about price action - it's about fundamental changes to how blockchain technology is being adopted and implemented across different sectors.

Third, let's talk strategy. Whether you're a HODLer, trader, or just curious about the technology, there are specific ways you can position yourself to benefit from these developments.

### CONCLUSION
So there you have it - the complete picture on {topic} and why it matters for your crypto journey. If you found this analysis helpful, make sure to smash that like button and subscribe for more insights. Drop your questions in the comments below, and let me know what topics you want me to cover next!

Remember, I'm not a financial advisor, but I am your guide through the exciting world of crypto. Stay informed, stay strategic, and I'll see you in the next video!
"""

def generate_markdown_report(news, topics, keywords, summary, scripts):
    """
    Generate a markdown report with daily headlines and content ideas
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    markdown = f"""# Daily Crypto Headlines & Content Ideas

*Generated on: {now}*

## Today's Hot Topics

| Topic | Volume | Sentiment |
|-------|--------|-----------|
"""

    # Add trending topics
    for topic in topics[:5]:
        markdown += f"| {topic['topic']} | {topic['volume']:,} | {topic['sentiment'].title()} |\n"

    # Add news summary
    markdown += f"""
## News Summary

{summary}

## Latest News Headlines

| Headline | Source | Time |
|----------|--------|------|
"""

    # Add news headlines
    for article in news[:8]:
        published_time = article.get("publishedAt", "")
        if published_time:
            try:
                dt = datetime.strptime(published_time, "%Y-%m-%dT%H:%M:%SZ")
                time_ago = get_time_ago(dt)
            except:
                time_ago = published_time
        else:
            time_ago = "Recent"

        markdown += f"| [{article['title']}]({article.get('url', '#')}) | {article.get('source', {}).get('name', 'Unknown')} | {time_ago} |\n"

    # Add trending keywords
    markdown += """
## Trending Keywords

"""

    # Create keyword cloud (simple markdown version)
    for keyword in keywords[:15]:
        size = min(3, max(1, keyword["count"] // 2))
        markdown += f"{'#' * size} {keyword['keyword']} "

    # Add content scripts
    markdown += """

## Content Script Ideas

The following script templates can be used as starting points for creating content:

"""

    # Add scripts
    for topic, script in scripts.items():
        markdown += f"### {topic}\n\n```\n{script}\n```\n\n"

    return markdown

# get_time_ago function is now imported from utils

def main():
    """Main function to orchestrate daily headlines generation"""
    logger.info("Starting daily headlines generation process")
    
    try:
        # Configuration
        output_dir = os.path.join(config.paths.content_dir, "daily")
        data_dir = os.path.join(config.paths.data_dir, "daily")

        # Ensure directories exist
        ensure_directory(output_dir)
        ensure_directory(data_dir)

        # API keys from config
        news_api_key = config.api.news_api_key
        openai_api_key = config.api.openai_api_key

        # Fetch data
        logger.info("Fetching latest crypto news...")
        news = fetch_crypto_news(news_api_key)

        logger.info("Fetching trending topics...")
        topics = fetch_trending_topics()

        # Extract keywords
        logger.info("Extracting keywords...")
        keywords = extract_keywords(news, topics)

        # Generate news summary
        logger.info("Generating news summary...")
        summary = generate_news_summary(news, openai_api_key)

        # Generate content scripts for top topics
        logger.info("Generating content scripts...")
        scripts = {}
        for topic in topics[:3]:
            logger.info(f"Generating script for {topic['topic']}...")
            scripts[topic['topic']] = generate_content_script(topic['topic'], keywords, openai_api_key)
            time.sleep(config.scraping.request_delay)  # Avoid rate limiting

        # Generate markdown report
        logger.info("Generating markdown report...")
        markdown_report = generate_markdown_report(news, topics, keywords, summary, scripts)

        # Save markdown report
        today = datetime.now().strftime("%Y-%m-%d")
        daily_report_path = os.path.join(output_dir, f"{today}.md")
        index_report_path = os.path.join(output_dir, "index.md")
        
        save_markdown(markdown_report, daily_report_path)
        save_markdown(markdown_report, index_report_path)

        # Save raw data as JSON
        data_path = os.path.join(data_dir, f"{today}_data.json")
        save_json({
            "news": news,
            "topics": topics,
            "keywords": keywords,
            "summary": summary,
            "scripts": scripts,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, data_path)

        logger.info(f"Daily headlines report generated for {today}")
        
    except Exception as e:
        logger.error(f"Error in main daily headlines process: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
