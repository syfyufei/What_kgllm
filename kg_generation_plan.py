#!/usr/bin/env python3
"""
知识图谱生成分阶段计划
根据文件大小和复杂度分批处理
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from policy_kg_batch_generator import PolicyKGBatchGenerator

def create_generation_plan():
    """创建分阶段生成计划"""

    # 根据文件大小分组
    small_files = [2004, 2017, 2018, 2019, 2003, 2006]  # < 50K
    medium_files = [2009, 2001, 2005, 2008, 2000, 2010, 2007]  # 50K-80K
    large_files = [2014, 1997, 2015, 2011, 1999, 2016, 2013]  # 80K-100K
    xlarge_files = [2024, 1998, 2021, 2020, 2023, 2022]  # > 100K

    plan = {
        "阶段1 - 小文件测试": {
            "files": small_files,
            "description": "处理较小的文件，验证系统稳定性",
            "estimated_time": "30-60分钟"
        },
        "阶段2 - 中等文件": {
            "files": medium_files,
            "description": "处理中等大小的文件",
            "estimated_time": "60-90分钟"
        },
        "阶段3 - 大文件": {
            "files": large_files,
            "description": "处理较大的文件",
            "estimated_time": "90-120分钟"
        },
        "阶段4 - 超大文件": {
            "files": xlarge_files,
            "description": "处理最大的文件",
            "estimated_time": "120-180分钟"
        }
    }

    return plan

def execute_stage(stage_name, years, generator):
    """执行单个阶段"""
    print(f"\n🚀 开始执行: {stage_name}")
    print("=" * 60)

    if not years:
        print("❌ 该阶段没有文件需要处理")
        return

    print(f"📋 处理年份: {years}")

    # 执行批量生成
    results = generator.batch_generate(
        start_year=min(years),
        end_year=max(years),
        force_regenerate=False
    )

    print(f"✅ {stage_name} 完成")
    print(f"📊 成功处理: {len(results)} 个文件")

    return results

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分阶段知识图谱生成计划')
    parser.add_argument('--stage', type=int, choices=[1,2,3,4], help='执行指定阶段 (1-4)')
    parser.add_argument('--plan', action='store_true', help='显示生成计划')
    parser.add_argument('--all', action='store_true', help='执行所有阶段')
    parser.add_argument('--data-dir', default='policy_data', help='数据目录路径')

    args = parser.parse_args()

    plan = create_generation_plan()
    generator = PolicyKGBatchGenerator(args.data_dir)

    if args.plan:
        print("📋 知识图谱生成分阶段计划")
        print("=" * 50)
        for stage_name, stage_info in plan.items():
            print(f"\n{stage_name}:")
            print(f"  文件数量: {len(stage_info['files'])}")
            print(f"  年份: {stage_info['files']}")
            print(f"  说明: {stage_info['description']}")
            print(f"  预计时间: {stage_info['estimated_time']}")

        # 检查当前状态
        print(f"\n🔍 当前状态:")
        generator.check_data_status()

    elif args.stage:
        stage_names = list(plan.keys())
        if 1 <= args.stage <= len(stage_names):
            stage_name = stage_names[args.stage - 1]
            stage_info = plan[stage_name]

            # 过滤掉已完成的文件
            completed_years = generator.get_completed_files()
            pending_years = [year for year in stage_info['files'] if year not in completed_years]

            if pending_years:
                execute_stage(stage_name, pending_years, generator)
            else:
                print(f"✅ {stage_name} 的所有文件都已完成")
        else:
            print("❌ 无效的阶段编号")

    elif args.all:
        print("🚀 执行所有阶段的知识图谱生成")
        print("=" * 60)

        completed_years = generator.get_completed_files()

        for i, (stage_name, stage_info) in enumerate(plan.items(), 1):
            pending_years = [year for year in stage_info['files'] if year not in completed_years]

            if pending_years:
                print(f"\n📍 当前阶段: {i}/4")
                execute_stage(stage_name, pending_years, generator)

                # 更新已完成列表
                completed_years = generator.get_completed_files()
            else:
                print(f"✅ {stage_name} 已全部完成，跳过")

        print(f"\n🎉 所有阶段执行完成！")
        generator.check_data_status()

    else:
        print("请指定操作:")
        print("  --plan       显示生成计划")
        print("  --stage N    执行指定阶段 (1-4)")
        print("  --all        执行所有阶段")

if __name__ == "__main__":
    main()
