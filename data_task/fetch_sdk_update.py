import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import os
import re
from bs4 import BeautifulSoup
import markdown

def fetch_github_releases(repo_owner, repo_name, token=None):
    """
    Fetch releases from GitHub API
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch releases for {repo_owner}/{repo_name}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching releases for {repo_owner}/{repo_name}: {e}")
        return []

def fetch_github_repo_info(repo_owner, repo_name, token=None):
    """
    Fetch repository information from GitHub API
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch repo info for {repo_owner}/{repo_name}: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching repo info for {repo_owner}/{repo_name}: {e}")
        return {}

def fetch_npm_package_info(package_name):
    """
    Fetch package information from NPM registry
    """
    url = f"https://registry.npmjs.org/{package_name}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch NPM info for {package_name}: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching NPM info for {package_name}: {e}")
        return {}

def fetch_pypi_package_info(package_name):
    """
    Fetch package information from PyPI
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch PyPI info for {package_name}: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching PyPI info for {package_name}: {e}")
        return {}

def fetch_documentation_updates(doc_url):
    """
    Fetch documentation updates from a URL
    """
    try:
        response = requests.get(doc_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # This is a simplified implementation
            # In a real scenario, you would need to parse the specific documentation site structure
            
            # Try to find last updated date
            last_updated = None
            date_elements = soup.select(".last-updated, .modified-date, time")
            
            if date_elements:
                last_updated = date_elements[0].text.strip()
            
            # Try to find main content
            content = ""
            content_elements = soup.select("main, .content, article")
            
            if content_elements:
                content = content_elements[0].text.strip()
            
            return {
                "url": doc_url,
                "last_updated": last_updated,
                "content_sample": content[:500] + "..." if len(content) > 500 else content
            }
        else:
            print(f"Failed to fetch documentation from {doc_url}: {response.status_code}")
            return {
                "url": doc_url,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        print(f"Error fetching documentation from {doc_url}: {e}")
        return {
            "url": doc_url,
            "error": str(e)
        }

def extract_code_examples(release_notes):
    """
    Extract code examples from release notes
    """
    # Look for code blocks in markdown
    code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)\s*```', release_notes, re.DOTALL)
    
    # If no code blocks found, try to find inline code
    if not code_blocks:
        inline_code = re.findall(r'`(.*?)`', release_notes)
        if inline_code:
            code_blocks = inline_code
    
    return code_blocks

def generate_sdk_update_report(sdk_data):
    """
    Generate a markdown report for SDK updates
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown_content = f"""# SDK Updates Report

*Generated on: {now}*

This report tracks updates to popular Web3 SDKs and developer tools.

## Latest SDK Releases

| SDK | Latest Version | Release Date | Changes |
|-----|----------------|--------------|---------|
"""
    
    # Add SDK releases
    for sdk in sdk_data:
        latest_release = sdk.get("latest_release", {})
        version = latest_release.get("tag_name", "N/A")
        date = latest_release.get("published_at", "N/A")
        if date != "N/A":
            date = date.split("T")[0]  # Format date
        
        # Truncate changes
        changes = latest_release.get("body", "")
        changes_summary = changes[:100] + "..." if len(changes) > 100 else changes
        changes_summary = changes_summary.replace("\n", " ")
        
        markdown_content += f"| [{sdk['name']}]({sdk['repo_url']}) | {version} | {date} | {changes_summary} |\n"
    
    # Add detailed sections for each SDK
    markdown_content += "\n## SDK Details\n\n"
    
    for sdk in sdk_data:
        markdown_content += f"### {sdk['name']}\n\n"
        
        # Add repository info
        repo_info = sdk.get("repo_info", {})
        markdown_content += f"**Repository:** [{sdk['repo_owner']}/{sdk['repo_name']}]({sdk['repo_url']})\n\n"
        markdown_content += f"**Description:** {repo_info.get('description', 'N/A')}\n\n"
        markdown_content += f"**Stars:** {repo_info.get('stargazers_count', 'N/A')} | "
        markdown_content += f"**Forks:** {repo_info.get('forks_count', 'N/A')} | "
        markdown_content += f"**Open Issues:** {repo_info.get('open_issues_count', 'N/A')}\n\n"
        
        # Add latest release info
        latest_release = sdk.get("latest_release", {})
        if latest_release:
            markdown_content += f"**Latest Release:** [{latest_release.get('tag_name', 'N/A')}]({latest_release.get('html_url', '#')})\n\n"
            markdown_content += f"**Released on:** {latest_release.get('published_at', 'N/A').split('T')[0] if latest_release.get('published_at') else 'N/A'}\n\n"
            
            # Add release notes
            if latest_release.get("body"):
                markdown_content += "**Release Notes:**\n\n"
                markdown_content += f"```\n{latest_release['body']}\n```\n\n"
        
        # Add code examples
        code_examples = sdk.get("code_examples", [])
        if code_examples:
            markdown_content += "**Code Examples:**\n\n"
            
            for i, example in enumerate(code_examples[:3]):  # Show up to 3 examples
                markdown_content += f"Example {i+1}:\n\n```\n{example}\n```\n\n"
        
        # Add documentation info
        doc_info = sdk.get("documentation", {})
        if doc_info:
            markdown_content += f"**Documentation:** [{doc_info.get('url', '#')}]({doc_info.get('url', '#')})\n\n"
            
            if doc_info.get("last_updated"):
                markdown_content += f"**Last Updated:** {doc_info['last_updated']}\n\n"
        
        # Add package info
        package_info = sdk.get("package_info", {})
        if package_info:
            if "npm" in package_info:
                npm_info = package_info["npm"]
                markdown_content += f"**NPM Package:** [{npm_info.get('name', 'N/A')}](https://www.npmjs.com/package/{npm_info.get('name', '')})\n\n"
                markdown_content += f"**Weekly Downloads:** {npm_info.get('weekly_downloads', 'N/A')}\n\n"
            
            if "pypi" in package_info:
                pypi_info = package_info["pypi"]
                markdown_content += f"**PyPI Package:** [{pypi_info.get('name', 'N/A')}](https://pypi.org/project/{pypi_info.get('name', '')})\n\n"
        
        markdown_content += "---\n\n"
    
    return markdown_content

def track_sdk_updates(sdks, output_dir, data_dir):
    """
    Track updates for a list of SDKs
    """
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # GitHub token (optional)
    github_token = os.environ.get("GITHUB_TOKEN")
    
    sdk_data = []
    
    for sdk in sdks:
        print(f"Processing {sdk['name']}...")
        
        repo_owner = sdk["repo_owner"]
        repo_name = sdk["repo_name"]
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        
        # Fetch GitHub releases
        releases = fetch_github_releases(repo_owner, repo_name, github_token)
        latest_release = releases[0] if releases else {}
        
        # Fetch repository info
        repo_info = fetch_github_repo_info(repo_owner, repo_name, github_token)
        
        # Fetch package info if available
        package_info = {}
        
        if "npm_package" in sdk:
            npm_info = fetch_npm_package_info(sdk["npm_package"])
            if npm_info:
                package_info["npm"] = {
                    "name": sdk["npm_package"],
                    "latest_version": npm_info.get("dist-tags", {}).get("latest", "N/A"),
                    "weekly_downloads": "N/A"  # Would require additional API call
                }
        
        if "pypi_package" in sdk:
            pypi_info = fetch_pypi_package_info(sdk["pypi_package"])
            if pypi_info:
                package_info["pypi"] = {
                    "name": sdk["pypi_package"],
                    "latest_version": pypi_info.get("info", {}).get("version", "N/A")
                }
        
        # Fetch documentation updates if URL provided
        doc_info = {}
        if "documentation_url" in sdk:
            doc_info = fetch_documentation_updates(sdk["documentation_url"])
        
        # Extract code examples from release notes
        code_examples = []
        if latest_release and "body" in latest_release:
            code_examples = extract_code_examples(latest_release["body"])
        
        # Compile SDK data
        sdk_data.append({
            "name": sdk["name"],
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "repo_url": repo_url,
            "repo_info": repo_info,
            "latest_release": latest_release,
            "all_releases": releases[:5],  # Store only the 5 most recent releases
            "package_info": package_info,
            "documentation": doc_info,
            "code_examples": code_examples
        })
        
        # Avoid rate limiting
        time.sleep(1)
    
    # Generate markdown report
    markdown_report = generate_sdk_update_report(sdk_data)
    
    # Save markdown report
    with open(os.path.join(output_dir, "index.md"), "w") as f:
        f.write(markdown_report)
    
    # Save raw data as JSON
    with open(os.path.join(data_dir, "sdk_updates.json"), "w") as f:
        # Convert to serializable format (remove complex objects)
        serializable_data = []
        for sdk in sdk_data:
            serializable_sdk = {
                "name": sdk["name"],
                "repo_url": sdk["repo_url"],
                "latest_version": sdk.get("latest_release", {}).get("tag_name", "N/A"),
                "latest_release_date": sdk.get("latest_release", {}).get("published_at", "N/A"),
                "stars": sdk.get("repo_info", {}).get("stargazers_count", "N/A"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            serializable_data.append(serializable_sdk)
        
        json.dump(serializable_data, f, indent=2)
    
    print(f"SDK update report generated with {len(sdk_data)} SDKs")
    return sdk_data

def main():
    # List of SDKs to track
    sdks = [
        {
            "name": "web3.js",
            "repo_owner": "web3",
            "repo_name": "web3.js",
            "npm_package": "web3",
            "documentation_url": "https://web3js.readthedocs.io/"
        },
        {
            "name": "ethers.js",
            "repo_owner": "ethers-io",
            "repo_name": "ethers.js",
            "npm_package": "ethers",
            "documentation_url": "https://docs.ethers.org/"
        },
        {
            "name": "web3.py",
            "repo_owner": "ethereum",
            "repo_name": "web3.py",
            "pypi_package": "web3",
            "documentation_url": "https://web3py.readthedocs.io/"
        },
        {
            "name": "wagmi",
            "repo_owner": "wagmi-dev",
            "repo_name": "wagmi",
            "npm_package": "wagmi",
            "documentation_url": "https://wagmi.sh/"
        },
        {
            "name": "viem",
            "repo_owner": "wagmi-dev",
            "repo_name": "viem",
            "npm_package": "viem",
            "documentation_url": "https://viem.sh/"
        }
    ]
    
    # Output directories
    output_dir = "content/tools"
    data_dir = "data/tools"
    
    # Track SDK updates
    track_sdk_updates(sdks, output_dir, data_dir)

if __name__ == "__main__":
    main()