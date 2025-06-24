import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup
import re

def fetch_twitter_info(project_handle):
    """
    Fetch project information from Twitter
    Note: Twitter API requires authentication, this is a simplified version
    In a real implementation, you would use the Twitter API with proper authentication
    """
    try:
        # This is a mock implementation
        # In a real scenario, you would use Twitter API with proper authentication
        url = f"https://nitter.net/{project_handle}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract follower count (simplified)
            follower_text = soup.select_one('.profile-stat-num')
            follower_count = follower_text.text.strip() if follower_text else "N/A"
            
            # Extract recent tweets
            tweets = []
            tweet_elements = soup.select('.timeline-item')
            for tweet_elem in tweet_elements[:5]:  # Get 5 most recent tweets
                tweet_text_elem = tweet_elem.select_one('.tweet-content')
                if tweet_text_elem:
                    tweets.append(tweet_text_elem.text.strip())
            
            return {
                "handle": project_handle,
                "follower_count": follower_count,
                "recent_tweets": tweets
            }
        else:
            print(f"Failed to fetch Twitter info for {project_handle}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching Twitter info for {project_handle}: {e}")
        return None

def fetch_zealy_quests(project_slug):
    """
    Fetch quest information from Zealy
    """
    try:
        url = f"https://zealy.io/c/{project_slug}/questboard"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract quests (simplified)
            quests = []
            quest_elements = soup.select('.quest-card')
            
            for quest_elem in quest_elements:
                title_elem = quest_elem.select_one('.quest-title')
                points_elem = quest_elem.select_one('.quest-points')
                
                title = title_elem.text.strip() if title_elem else "Unknown Quest"
                points = points_elem.text.strip() if points_elem else "0"
                
                quests.append({
                    "title": title,
                    "points": points
                })
            
            return {
                "project": project_slug,
                "quests": quests
            }
        else:
            print(f"Failed to fetch Zealy quests for {project_slug}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching Zealy quests for {project_slug}: {e}")
        return None

def fetch_galxe_campaigns(project_name):
    """
    Fetch campaign information from Galxe
    """
    try:
        # Search for the project
        search_url = f"https://galxe.com/api/v1/search?keyword={project_name}"
        response = requests.get(search_url)
        
        if response.status_code == 200:
            search_data = response.json()
            
            # Find the project in search results
            project_id = None
            for result in search_data.get('data', {}).get('spaces', []):
                if result.get('name', '').lower() == project_name.lower():
                    project_id = result.get('id')
                    break
            
            if not project_id:
                print(f"Project {project_name} not found on Galxe")
                return None
            
            # Fetch campaigns for the project
            campaigns_url = f"https://galxe.com/api/v1/spaces/{project_id}/campaigns"
            campaigns_response = requests.get(campaigns_url)
            
            if campaigns_response.status_code == 200:
                campaigns_data = campaigns_response.json()
                
                campaigns = []
                for campaign in campaigns_data.get('data', {}).get('campaigns', []):
                    campaigns.append({
                        "id": campaign.get('id'),
                        "name": campaign.get('name'),
                        "type": campaign.get('type'),
                        "start_time": campaign.get('startTime'),
                        "end_time": campaign.get('endTime'),
                        "participants": campaign.get('participantsCount')
                    })
                
                return {
                    "project": project_name,
                    "campaigns": campaigns
                }
            else:
                print(f"Failed to fetch Galxe campaigns for {project_name}: {campaigns_response.status_code}")
                return None
        else:
            print(f"Failed to search for {project_name} on Galxe: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching Galxe campaigns for {project_name}: {e}")
        return None

def fetch_airdrop_projects():
    """
    Fetch a list of potential airdrop projects
    This is a simplified version with a predefined list
    In a real implementation, you might scrape this from airdrop tracking websites
    """
    # Predefined list of projects with potential airdrops
    projects = [
        {
            "name": "LayerZero",
            "twitter": "LayerZero_Labs",
            "zealy": "layerzero",
            "galxe": "LayerZero",
            "category": "Cross-chain",
            "description": "Omnichain interoperability protocol",
            "expected_airdrop": "Q1 2024",
            "tasks": ["Bridge assets", "Use supported dApps", "Participate in Zealy quests"]
        },
        {
            "name": "ZKSync",
            "twitter": "zksync",
            "zealy": "zksync",
            "galxe": "ZKSync",
            "category": "Layer 2",
            "description": "Zero-knowledge rollup scaling solution",
            "expected_airdrop": "TBA",
            "tasks": ["Bridge to ZKSync", "Use ZKSync dApps", "Complete Galxe campaigns"]
        },
        {
            "name": "Starknet",
            "twitter": "StarkNetEco",
            "zealy": "starknet",
            "galxe": "Starknet",
            "category": "Layer 2",
            "description": "Permissionless validity-rollup",
            "expected_airdrop": "TBA",
            "tasks": ["Deploy contracts", "Use Starknet dApps", "Participate in community"]
        },
        {
            "name": "Scroll",
            "twitter": "Scroll_ZKP",
            "zealy": "scroll",
            "galxe": "Scroll",
            "category": "Layer 2",
            "description": "zkEVM-based Layer 2 solution",
            "expected_airdrop": "2024",
            "tasks": ["Bridge to Scroll", "Use Scroll dApps", "Complete testnet tasks"]
        },
        {
            "name": "Linea",
            "twitter": "LineaBuild",
            "zealy": "linea",
            "galxe": "Linea",
            "category": "Layer 2",
            "description": "Consensys zkEVM rollup",
            "expected_airdrop": "TBA",
            "tasks": ["Bridge to Linea", "Use Linea dApps", "Complete Galxe campaigns"]
        }
    ]
    
    return projects

def enrich_project_data(projects):
    """
    Enrich project data with information from Twitter, Zealy, and Galxe
    """
    enriched_projects = []
    
    for project in projects:
        print(f"Enriching data for {project['name']}...")
        
        # Fetch Twitter info
        twitter_info = fetch_twitter_info(project['twitter'])
        
        # Fetch Zealy quests
        zealy_info = fetch_zealy_quests(project['zealy'])
        
        # Fetch Galxe campaigns
        galxe_info = fetch_galxe_campaigns(project['galxe'])
        
        # Combine all data
        enriched_project = project.copy()
        enriched_project['twitter_info'] = twitter_info
        enriched_project['zealy_info'] = zealy_info
        enriched_project['galxe_info'] = galxe_info
        
        enriched_projects.append(enriched_project)
        
        # Avoid rate limiting
        time.sleep(2)
    
    return enriched_projects

def generate_airdrop_calendar(projects):
    """
    Generate a calendar of upcoming airdrop tasks and deadlines
    """
    # Create a calendar for the next 30 days
    today = datetime.now().date()
    calendar = {}
    
    for i in range(30):
        date = today + timedelta(days=i)
        calendar[date.strftime('%Y-%m-%d')] = []
    
    # Add project tasks to the calendar
    # This is a simplified version - in reality, you would extract actual deadlines
    # from the project data
    
    # Distribute projects across the calendar for demonstration
    project_dates = {}
    for i, project in enumerate(projects):
        # Assign each project to a date in the next 30 days
        date = today + timedelta(days=i % 30)
        date_str = date.strftime('%Y-%m-%d')
        
        # Add task to calendar
        calendar[date_str].append({
            "project": project['name'],
            "task": f"Complete {project['name']} tasks",
            "link": f"https://zealy.io/c/{project['zealy']}/questboard"
        })
        
        project_dates[project['name']] = date_str
    
    return calendar, project_dates

def generate_markdown_report(projects, calendar, project_dates):
    """
    Generate markdown report with airdrop projects and calendar
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create projects table
    markdown = f"""# Airdrop Projects Tracker

*Generated on: {now}*

## Upcoming Airdrop Projects

| Project | Category | Expected Airdrop | Twitter | Tasks |
|---------|----------|------------------|---------|-------|
"""
    
    for project in projects:
        twitter_link = f"[@{project['twitter']}](https://twitter.com/{project['twitter']})"
        tasks = ", ".join(project['tasks'][:2]) + (", ..." if len(project['tasks']) > 2 else "")
        
        markdown += f"| [{project['name']}](#{project['name'].lower().replace(' ', '-')}) | {project['category']} | {project['expected_airdrop']} | {twitter_link} | {tasks} |\n"
    
    # Create calendar section
    markdown += """
## Airdrop Task Calendar

| Date | Project | Task | Link |
|------|---------|------|------|
"""
    
    # Sort calendar by date
    sorted_dates = sorted(calendar.keys())
    for date in sorted_dates:
        tasks = calendar[date]
        if tasks:
            for task in tasks:
                markdown += f"| {date} | {task['project']} | {task['task']} | [Complete Tasks]({task['link']}) |\n"
    
    # Create detailed project sections
    markdown += "\n## Project Details\n\n"
    
    for project in projects:
        markdown += f"### {project['name']}\n\n"
        markdown += f"**Category:** {project['category']}\n\n"
        markdown += f"**Description:** {project['description']}\n\n"
        markdown += f"**Expected Airdrop:** {project['expected_airdrop']}\n\n"
        
        # Add Twitter info if available
        if project.get('twitter_info'):
            twitter_info = project['twitter_info']
            markdown += f"**Twitter:** [@{project['twitter']}](https://twitter.com/{project['twitter']})"
            if twitter_info.get('follower_count'):
                markdown += f" ({twitter_info['follower_count']} followers)\n\n"
            else:
                markdown += "\n\n"
        
        # Add tasks
        markdown += "**Required Tasks:**\n\n"
        for task in project['tasks']:
            markdown += f"- {task}\n"
        
        # Add Zealy quests if available
        if project.get('zealy_info') and project['zealy_info'].get('quests'):
            markdown += "\n**Zealy Quests:**\n\n"
            for quest in project['zealy_info']['quests'][:5]:  # Show top 5 quests
                markdown += f"- {quest.get('title')} ({quest.get('points')})\n"
            
            markdown += f"\n[View All Quests on Zealy](https://zealy.io/c/{project['zealy']}/questboard)\n"
        
        # Add calendar date if available
        if project['name'] in project_dates:
            markdown += f"\n**Next Task Deadline:** {project_dates[project['name']]}\n"
        
        markdown += "\n---\n\n"
    
    return markdown

def main():
    # Create directories
    os.makedirs("data/airdrops", exist_ok=True)
    os.makedirs("content/airdrops", exist_ok=True)
    
    # Fetch airdrop projects
    print("Fetching airdrop projects...")
    projects = fetch_airdrop_projects()
    
    # Enrich project data
    print("Enriching project data...")
    enriched_projects = enrich_project_data(projects)
    
    # Generate airdrop calendar
    print("Generating airdrop calendar...")
    calendar, project_dates = generate_airdrop_calendar(enriched_projects)
    
    # Generate markdown report
    print("Generating markdown report...")
    markdown = generate_markdown_report(enriched_projects, calendar, project_dates)
    
    # Save markdown report
    with open("content/airdrops/index.md", "w") as f:
        f.write(markdown)
    
    # Save raw data as JSON
    with open("data/airdrops/projects.json", "w") as f:
        # Convert to serializable format
        serializable_projects = []
        for project in enriched_projects:
            serializable_project = {k: v for k, v in project.items() if k not in ['twitter_info', 'zealy_info', 'galxe_info']}
            serializable_projects.append(serializable_project)
        
        json.dump(serializable_projects, f, indent=2)
    
    # Save calendar as JSON
    with open("data/airdrops/calendar.json", "w") as f:
        json.dump(calendar, f, indent=2)
    
    print("Airdrop data processing complete!")

if __name__ == "__main__":
    main()