import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import json

def load_strategy_data(file_path):
    """
    Load strategy backtest data from CSV or Excel file
    """
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please use CSV or Excel.")
    
    # Ensure date column is in datetime format
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.rename(columns={'Date': 'date'}, inplace=True)
    
    return df

def calculate_performance_metrics(df):
    """
    Calculate key performance metrics from backtest data
    """
    # Ensure we have a returns column
    if 'returns' not in df.columns and 'Returns' in df.columns:
        df.rename(columns={'Returns': 'returns'}, inplace=True)
    
    if 'returns' not in df.columns and 'daily_return' in df.columns:
        df.rename(columns={'daily_return': 'returns'}, inplace=True)
    
    # Calculate metrics
    total_return = (df['returns'] + 1).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(df)) - 1
    daily_returns = df['returns']
    volatility = daily_returns.std() * np.sqrt(252)
    sharpe_ratio = annual_return / volatility if volatility != 0 else 0
    max_drawdown = (df['returns'].cumsum() - df['returns'].cumsum().cummax()).min()
    win_rate = len(daily_returns[daily_returns > 0]) / len(daily_returns)
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate
    }

def generate_performance_chart(df, strategy_name, output_dir):
    """
    Generate performance chart and save as image
    """
    # Create cumulative returns
    if 'cumulative_returns' not in df.columns:
        df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1
    
    # Create figure
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['cumulative_returns'] * 100, linewidth=2)
    plt.title(f'{strategy_name} Performance')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns (%)')
    plt.grid(True, alpha=0.3)
    
    # Add horizontal line at y=0
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    
    # Save figure
    chart_path = os.path.join(output_dir, f"{strategy_name.replace(' ', '_').lower()}_performance.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return chart_path

def generate_monthly_returns_heatmap(df, strategy_name, output_dir):
    """
    Generate monthly returns heatmap and save as image
    """
    # Ensure date is set as index
    if 'date' in df.columns:
        df = df.set_index('date')
    
    # Calculate monthly returns
    monthly_returns = df['returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
    monthly_returns = monthly_returns.to_frame()
    
    # Create a pivot table with years as rows and months as columns
    monthly_returns['year'] = monthly_returns.index.year
    monthly_returns['month'] = monthly_returns.index.month
    heatmap_data = monthly_returns.pivot_table(
        index='year', 
        columns='month', 
        values='returns'
    )
    
    # Create heatmap
    plt.figure(figsize=(12, 8))
    cmap = plt.cm.RdYlGn  # Red for negative, green for positive
    plt.pcolormesh(heatmap_data.columns, heatmap_data.index, heatmap_data.values, cmap=cmap, vmin=-0.1, vmax=0.1)
    plt.colorbar(label='Returns')
    
    # Set labels
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    plt.xticks(np.arange(1, 13) + 0.5, month_labels)
    plt.yticks(heatmap_data.index, heatmap_data.index)
    
    plt.title(f'{strategy_name} Monthly Returns')
    
    # Add text annotations
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            try:
                value = heatmap_data.iloc[i, j]
                if not np.isnan(value):
                    text_color = 'white' if abs(value) > 0.05 else 'black'
                    plt.text(j + 0.5, i + 0.5, f'{value:.1%}', 
                             ha='center', va='center', color=text_color)
            except:
                pass
    
    # Save figure
    heatmap_path = os.path.join(output_dir, f"{strategy_name.replace(' ', '_').lower()}_monthly_heatmap.png")
    plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return heatmap_path

def generate_markdown(strategy_name, df, metrics, chart_path, heatmap_path, output_dir):
    """
    Generate markdown report for strategy
    """
    # Create markdown content
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown = f"""# {strategy_name} Strategy Performance

*Generated on: {now}*

## Performance Summary

| Metric | Value |
|--------|-------|
| Total Return | {metrics['total_return']:.2%} |
| Annual Return | {metrics['annual_return']:.2%} |
| Volatility | {metrics['volatility']:.2%} |
| Sharpe Ratio | {metrics['sharpe_ratio']:.2f} |
| Maximum Drawdown | {metrics['max_drawdown']:.2%} |
| Win Rate | {metrics['win_rate']:.2%} |

## Performance Chart

![Performance Chart]({os.path.basename(chart_path)})

## Monthly Returns

![Monthly Returns Heatmap]({os.path.basename(heatmap_path)})

## Recent Daily Returns

| Date | Return | Cumulative Return |
|------|--------|------------------|
"""
    
    # Add recent daily returns (last 10 days)
    recent_data = df.sort_values('date', ascending=False).head(10)
    for _, row in recent_data.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        daily_return = row['returns']
        cumulative_return = row['cumulative_returns'] if 'cumulative_returns' in df.columns else 0
        markdown += f"| {date_str} | {daily_return:.2%} | {cumulative_return:.2%} |\n"
    
    # Save markdown file
    md_file_path = os.path.join(output_dir, f"{strategy_name.replace(' ', '_').lower()}.md")
    with open(md_file_path, 'w') as f:
        f.write(markdown)
    
    return md_file_path

def generate_strategy_index(strategies, output_dir):
    """
    Generate index page for all strategies
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown = f"""# Trading Strategy Performance Dashboard

*Last updated: {now}*

## Strategy Performance Summary

| Strategy | Total Return | Annual Return | Sharpe Ratio | Win Rate |
|----------|--------------|--------------|--------------|----------|
"""
    
    # Add each strategy to the table
    for strategy in strategies:
        markdown += f"| [{strategy['name']}](./{os.path.basename(strategy['md_path'])}) | {strategy['metrics']['total_return']:.2%} | {strategy['metrics']['annual_return']:.2%} | {strategy['metrics']['sharpe_ratio']:.2f} | {strategy['metrics']['win_rate']:.2%} |\n"
    
    # Save index file
    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, 'w') as f:
        f.write(markdown)
    
    return index_path

def main():
    # Configuration
    data_dir = "data/strategies"  # Directory with strategy data files
    output_dir = "content/strategies"  # Directory for output markdown files
    img_dir = "static/img/strategies"  # Directory for charts
    
    # Ensure directories exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    
    # List of strategies to process
    strategies = []
    
    # Example strategy data (in real use, you would load from files)
    # For demonstration, we'll create a sample dataframe
    dates = pd.date_range(start='2022-01-01', end='2023-01-01')
    np.random.seed(42)  # For reproducibility
    
    # Strategy 1: Momentum
    momentum_returns = np.random.normal(0.001, 0.01, len(dates))
    momentum_df = pd.DataFrame({
        'date': dates,
        'returns': momentum_returns,
        'cumulative_returns': (1 + pd.Series(momentum_returns)).cumprod() - 1
    })
    
    # Strategy 2: Mean Reversion
    mean_rev_returns = np.random.normal(0.0008, 0.008, len(dates))
    mean_rev_df = pd.DataFrame({
        'date': dates,
        'returns': mean_rev_returns,
        'cumulative_returns': (1 + pd.Series(mean_rev_returns)).cumprod() - 1
    })
    
    # Process each strategy
    for strategy_name, df in [("Momentum Strategy", momentum_df), 
                             ("Mean Reversion Strategy", mean_rev_df)]:
        print(f"Processing {strategy_name}...")
        
        # Calculate metrics
        metrics = calculate_performance_metrics(df)
        
        # Generate charts
        chart_path = generate_performance_chart(df, strategy_name, img_dir)
        heatmap_path = generate_monthly_returns_heatmap(df, strategy_name, img_dir)
        
        # Generate markdown
        md_path = generate_markdown(strategy_name, df, metrics, chart_path, heatmap_path, output_dir)
        
        # Add to strategies list
        strategies.append({
            'name': strategy_name,
            'metrics': metrics,
            'md_path': md_path
        })
        
        print(f"Generated report for {strategy_name}")
    
    # Generate index page
    index_path = generate_strategy_index(strategies, output_dir)
    print(f"Generated strategy index at {index_path}")
    
    # Save strategy data as JSON for future reference
    with open(os.path.join(data_dir, "strategy_metrics.json"), 'w') as f:
        json.dump([{
            'name': s['name'],
            'metrics': s['metrics']
        } for s in strategies], f, indent=2, default=str)

if __name__ == "__main__":
    main()