#!/usr/bin/env python3
"""
知识图谱生成进度监控器
"""

import time
import json
from pathlib import Path
from datetime import datetime

def monitor_progress(data_dir="policy_data", check_interval=30):
    """监控知识图谱生成进度"""
    data_path = Path(data_dir)
    kg_dir = data_path / "kg_json"
    logs_dir = data_path / "logs"

    print("🔍 开始监控知识图谱生成进度...")
    print("=" * 50)

    last_count = 0
    start_time = datetime.now()

    try:
        while True:
            # 检查已完成的文件
            kg_files = list(kg_dir.glob("policy_kg_*.json"))
            current_count = len(kg_files)

            # 检查错误日志
            error_files = list(logs_dir.glob("error_*.json"))
            error_count = len(error_files)

            # 显示进度
            current_time = datetime.now()
            elapsed = current_time - start_time

            print(f"\n⏰ {current_time.strftime('%H:%M:%S')} (运行时间: {elapsed})")
            print(f"✅ 已完成: {current_count} 个文件")
            print(f"❌ 错误数: {error_count} 个")

            if current_count > last_count:
                print(f"🎉 新增完成: {current_count - last_count} 个文件")

                # 显示最新完成的文件
                for kg_file in sorted(kg_files)[-3:]:
                    try:
                        with open(kg_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        metadata = data.get('metadata', {})
                        year = metadata.get('year', 'Unknown')
                        triples = metadata.get('total_triples', 0)
                        entities = metadata.get('unique_entities', 0)
                        print(f"   📄 {year}年: {triples} 三元组, {entities} 实体")
                    except:
                        pass

            last_count = current_count

            # 如果有错误，显示最新的错误
            if error_files:
                latest_error = max(error_files, key=lambda x: x.stat().st_mtime)
                try:
                    with open(latest_error, 'r', encoding='utf-8') as f:
                        error_data = json.load(f)
                    print(f"⚠️  最新错误: {error_data.get('year')}年 - {error_data.get('error_message', '')[:100]}")
                except:
                    pass

            print(f"⏳ 等待 {check_interval} 秒后继续检查...")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n🛑 监控已停止")
        print(f"📊 最终统计: {current_count} 个文件已完成, {error_count} 个错误")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='知识图谱生成进度监控器')
    parser.add_argument('--data-dir', default='policy_data', help='数据目录路径')
    parser.add_argument('--interval', type=int, default=30, help='检查间隔(秒)')

    args = parser.parse_args()

    monitor_progress(args.data_dir, args.interval)
