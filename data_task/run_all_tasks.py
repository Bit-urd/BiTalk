#!/usr/bin/env python3
"""
BiTalk Data Tasks Runner
执行所有数据收集和内容生成任务
"""

import sys
import os
import argparse
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config, logger
from utils import ensure_directory, save_json

def run_task(task_name, task_function):
    """运行单个任务并捕获错误"""
    try:
        logger.info(f"开始执行任务: {task_name}")
        start_time = datetime.now()
        
        task_function()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"任务 {task_name} 执行成功，耗时 {duration:.1f} 秒")
        
        return {
            "task": task_name,
            "status": "success",
            "duration": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"任务 {task_name} 执行失败: {e}", exc_info=True)
        return {
            "task": task_name,
            "status": "failed",
            "error": str(e),
            "start_time": start_time.isoformat() if 'start_time' in locals() else None,
            "end_time": datetime.now().isoformat()
        }

def run_airdrop_tasks():
    """运行空投相关任务"""
    from fetch_airdrop_tasks import main as fetch_airdrops
    fetch_airdrops()

def run_wallet_tasks():
    """运行钱包追踪任务"""
    from fetch_wallet_data import main as fetch_wallets
    fetch_wallets()

def run_tool_ranking_tasks():
    """运行工具排名任务"""
    from update_tool_rankings import main as update_rankings
    update_rankings()

def run_daily_headlines_tasks():
    """运行每日资讯任务"""
    from gen_daily_headlines import main as gen_headlines
    gen_headlines()

def run_strategy_tasks():
    """运行策略分析任务"""
    from generate_strategy_md import main as gen_strategies
    gen_strategies()

def run_sdk_update_tasks():
    """运行SDK更新任务"""
    from fetch_sdk_update import main as fetch_sdk_updates
    fetch_sdk_updates()

def run_tutorial_tasks():
    """运行教程索引任务"""
    from build_tutorial_index import main as build_tutorials
    build_tutorials()

def get_available_tasks():
    """获取所有可用任务"""
    return {
        "airdrops": {
            "function": run_airdrop_tasks,
            "description": "获取空投项目数据和任务日历"
        },
        "wallets": {
            "function": run_wallet_tasks,
            "description": "追踪巨鲸钱包数据"
        },
        "rankings": {
            "function": run_tool_ranking_tasks,
            "description": "更新工具和协议排名"
        },
        "headlines": {
            "function": run_daily_headlines_tasks,
            "description": "生成每日资讯和内容脚本"
        },
        "strategies": {
            "function": run_strategy_tasks,
            "description": "生成策略分析报告"
        },
        "sdk": {
            "function": run_sdk_update_tasks,
            "description": "获取SDK和开发工具更新"
        },
        "tutorials": {
            "function": run_tutorial_tasks,
            "description": "构建教程索引"
        }
    }

def run_tasks_sequential(task_names):
    """顺序执行任务"""
    available_tasks = get_available_tasks()
    results = []
    
    for task_name in task_names:
        if task_name not in available_tasks:
            logger.error(f"未知任务: {task_name}")
            results.append({
                "task": task_name,
                "status": "failed",
                "error": "Unknown task"
            })
            continue
        
        result = run_task(task_name, available_tasks[task_name]["function"])
        results.append(result)
    
    return results

def run_tasks_parallel(task_names, max_workers=3):
    """并行执行任务"""
    available_tasks = get_available_tasks()
    results = []
    
    # 验证任务名称
    valid_tasks = []
    for task_name in task_names:
        if task_name not in available_tasks:
            logger.error(f"未知任务: {task_name}")
            results.append({
                "task": task_name,
                "status": "failed",
                "error": "Unknown task"
            })
        else:
            valid_tasks.append(task_name)
    
    # 并行执行有效任务
    if valid_tasks:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_task, task_name, available_tasks[task_name]["function"]): task_name
                for task_name in valid_tasks
            }
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    task_name = futures[future]
                    logger.error(f"任务 {task_name} 执行异常: {e}")
                    results.append({
                        "task": task_name,
                        "status": "failed",
                        "error": str(e)
                    })
    
    return results

def save_execution_report(results, output_dir):
    """保存执行报告"""
    report = {
        "execution_time": datetime.now().isoformat(),
        "total_tasks": len(results),
        "successful_tasks": len([r for r in results if r["status"] == "success"]),
        "failed_tasks": len([r for r in results if r["status"] == "failed"]),
        "results": results
    }
    
    report_path = os.path.join(output_dir, "execution_report.json")
    save_json(report, report_path)
    
    # 打印摘要
    logger.info(f"执行报告已保存到: {report_path}")
    logger.info(f"任务摘要: 总计 {report['total_tasks']}, 成功 {report['successful_tasks']}, 失败 {report['failed_tasks']}")
    
    if report["failed_tasks"] > 0:
        logger.warning("失败的任务:")
        for result in results:
            if result["status"] == "failed":
                logger.warning(f"  - {result['task']}: {result.get('error', 'Unknown error')}")

def main():
    parser = argparse.ArgumentParser(description="BiTalk数据任务执行器")
    parser.add_argument(
        "tasks", 
        nargs="*", 
        help="要执行的任务列表。不指定则执行所有任务。可用任务: airdrops, wallets, rankings, headlines, strategies, sdk, tutorials"
    )
    parser.add_argument(
        "--parallel", 
        action="store_true", 
        help="并行执行任务（默认为顺序执行）"
    )
    parser.add_argument(
        "--max-workers", 
        type=int, 
        default=3, 
        help="并行执行时的最大工作线程数（默认3）"
    )
    parser.add_argument(
        "--list-tasks", 
        action="store_true", 
        help="列出所有可用任务"
    )
    parser.add_argument(
        "--output-dir",
        default="logs",
        help="执行报告输出目录（默认：logs）"
    )
    
    args = parser.parse_args()
    
    # 列出可用任务
    if args.list_tasks:
        available_tasks = get_available_tasks()
        print("可用任务:")
        for task_name, task_info in available_tasks.items():
            print(f"  {task_name}: {task_info['description']}")
        return
    
    # 确定要执行的任务
    available_tasks = get_available_tasks()
    if args.tasks:
        task_names = args.tasks
    else:
        task_names = list(available_tasks.keys())
        logger.info("未指定任务，将执行所有可用任务")
    
    logger.info(f"准备执行任务: {', '.join(task_names)}")
    
    # 确保输出目录存在
    ensure_directory(args.output_dir)
    
    # 执行任务
    if args.parallel:
        logger.info(f"并行执行任务（最大工作线程数: {args.max_workers}）")
        results = run_tasks_parallel(task_names, args.max_workers)
    else:
        logger.info("顺序执行任务")
        results = run_tasks_sequential(task_names)
    
    # 保存执行报告
    save_execution_report(results, args.output_dir)

if __name__ == "__main__":
    main()