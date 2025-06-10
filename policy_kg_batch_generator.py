#!/usr/bin/env python3
"""
香港施政报告知识图谱批量生成器 - 改进版
支持分批处理、错误恢复和进度监控
"""

import os
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import traceback

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.knowledge_graph.main import process_text_in_chunks
from src.knowledge_graph.config import load_config

class PolicyKGBatchGenerator:
    """施政报告知识图谱批量生成器 - 改进版"""

    def __init__(self, data_dir="policy_data"):
        self.data_dir = Path(data_dir)
        self.setup_directories()
        self.batch_size = 5  # 每批处理5个文件
        self.delay_between_files = 10  # 文件间延迟10秒
        self.delay_between_batches = 30  # 批次间延迟30秒

    def setup_directories(self):
        """设置目录结构"""
        directories = [
            self.data_dir / "raw_texts",      # 原始文本
            self.data_dir / "kg_json",        # 知识图谱JSON数据
            self.data_dir / "kg_html",        # 知识图谱可视化
            self.data_dir / "logs",           # 处理日志
            self.data_dir / "metadata"        # 元数据信息
        ]

        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)

    def create_policy_config(self):
        """创建针对施政报告的专用配置"""
        base_config = load_config()

        # 针对施政报告优化的配置
        policy_config = base_config.copy()
        policy_config.update({
            'chunking': {
                'chunk_size': 120,  # 适中的块大小
                'overlap': 25       # 适当的重叠
            },
            'standardization': {
                'enabled': True,
                'use_llm_for_entities': True,
                'focus_entities': [
                    '行政长官', '特区政府', '中央政府', '立法会', '行政会议',
                    '一国两制', '基本法', '国家安全', '香港国安法',
                    '经济发展', '民生改善', '教育政策', '房屋政策', '医疗政策',
                    '大湾区', '粤港澳大湾区', '创新科技', '青年发展',
                    '国际金融中心', '贸易中心', '航运中心'
                ]
            },
            'inference': {
                'enabled': True,
                'use_llm_for_inference': True,
                'apply_transitive': True
            }
        })

        return policy_config

    def get_available_files(self):
        """获取可用的文本文件列表"""
        available_files = []
        years = range(1997, 2025)

        for year in years:
            text_file = self.data_dir / "raw_texts" / f"policy_address_{year}.txt"
            if text_file.exists():
                available_files.append((year, text_file))

        return sorted(available_files)

    def get_completed_files(self):
        """获取已完成的文件列表"""
        completed_years = set()
        kg_dir = self.data_dir / "kg_json"

        for kg_file in kg_dir.glob("policy_kg_*.json"):
            try:
                year = int(kg_file.stem.split('_')[-1])
                completed_years.add(year)
            except ValueError:
                continue

        return completed_years

    def generate_single_kg(self, year, text_content, config):
        """为单年施政报告生成知识图谱"""
        print(f"\n📄 处理 {year} 年施政报告...")
        print(f"   文本长度: {len(text_content):,} 字符")

        try:
            start_time = time.time()

            # 处理文本生成知识图谱
            kg_data = process_text_in_chunks(config, text_content, debug=False)

            if not kg_data:
                print(f"❌ {year}年知识图谱生成失败 - 无数据返回")
                return None

            processing_time = time.time() - start_time

            # 添加元数据
            metadata = {
                'year': year,
                'generated_at': datetime.now().isoformat(),
                'processing_time_seconds': round(processing_time, 2),
                'total_triples': len(kg_data),
                'unique_entities': len(self._get_unique_entities(kg_data)),
                'unique_relations': len(set(item['predicate'] for item in kg_data)),
                'text_length': len(text_content),
                'chunks_processed': max([item.get('chunk', 1) for item in kg_data]) if kg_data else 0
            }

            # 保存JSON数据
            json_file = self.data_dir / "kg_json" / f"policy_kg_{year}.json"
            output_data = {
                'metadata': metadata,
                'knowledge_graph': kg_data
            }

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"✅ {year}年处理完成 (耗时: {processing_time:.1f}秒):")
            print(f"   • 三元组数量: {metadata['total_triples']}")
            print(f"   • 唯一实体: {metadata['unique_entities']}")
            print(f"   • 关系类型: {metadata['unique_relations']}")
            print(f"   • 处理块数: {metadata['chunks_processed']}")

            return metadata

        except Exception as e:
            print(f"❌ {year}年处理出错: {str(e)}")
            print(f"   错误详情: {traceback.format_exc()}")

            # 保存错误日志
            error_log = {
                'year': year,
                'error_time': datetime.now().isoformat(),
                'error_message': str(e),
                'error_traceback': traceback.format_exc()
            }

            error_file = self.data_dir / "logs" / f"error_{year}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_log, f, ensure_ascii=False, indent=2)

            return None

    def _get_unique_entities(self, kg_data):
        """获取唯一实体集合"""
        entities = set()
        for item in kg_data:
            entities.add(item['subject'])
            entities.add(item['object'])
        return entities

    def batch_generate(self, start_year=None, end_year=None, force_regenerate=False):
        """批量生成知识图谱"""
        print("🚀 开始批量生成香港施政报告知识图谱")
        print("=" * 60)

        # 获取配置
        config = self.create_policy_config()

        # 获取可用文件
        available_files = self.get_available_files()
        if not available_files:
            print("❌ 未找到任何施政报告文本文件")
            return {}

        # 过滤年份范围
        if start_year or end_year:
            available_files = [
                (year, file) for year, file in available_files
                if (not start_year or year >= start_year) and (not end_year or year <= end_year)
            ]

        # 获取已完成的文件
        completed_years = self.get_completed_files()

        # 过滤未完成的文件
        if not force_regenerate:
            pending_files = [(year, file) for year, file in available_files if year not in completed_years]
            if completed_years:
                print(f"📋 已完成: {sorted(completed_years)}")
        else:
            pending_files = available_files
            print("🔄 强制重新生成所有文件")

        if not pending_files:
            print("✅ 所有文件都已处理完成")
            return self.check_data_status()

        print(f"📊 待处理文件: {len(pending_files)} 个")
        print(f"📁 年份列表: {[year for year, _ in pending_files]}")

        # 分批处理
        results = {}
        total_batches = (len(pending_files) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(pending_files))
            batch_files = pending_files[start_idx:end_idx]

            print(f"\n🔄 处理批次 {batch_idx + 1}/{total_batches}")
            print(f"   文件: {[year for year, _ in batch_files]}")

            # 处理批次中的每个文件
            for i, (year, text_file) in enumerate(batch_files):
                try:
                    # 读取文本
                    with open(text_file, 'r', encoding='utf-8') as f:
                        text_content = f.read()

                    # 生成知识图谱
                    metadata = self.generate_single_kg(year, text_content, config)
                    if metadata:
                        results[year] = metadata

                    # 文件间延迟
                    if i < len(batch_files) - 1:
                        print(f"⏳ 等待 {self.delay_between_files} 秒...")
                        time.sleep(self.delay_between_files)

                except Exception as e:
                    print(f"❌ 读取{year}年文件失败: {str(e)}")
                    continue

            # 批次间延迟
            if batch_idx < total_batches - 1:
                print(f"\n⏸️  批次完成，等待 {self.delay_between_batches} 秒后继续...")
                time.sleep(self.delay_between_batches)

        # 保存批量处理结果
        self._save_batch_results(results)

        print(f"\n🎉 批量处理完成!")
        print(f"✅ 本次成功处理: {len(results)} 个年份")
        print(f"📁 数据保存在: {self.data_dir}/kg_json/")

        return results

    def _save_batch_results(self, results):
        """保存批量处理结果摘要"""
        if not results:
            return

        summary = {
            'generated_at': datetime.now().isoformat(),
            'batch_size': len(results),
            'years_processed': sorted(results.keys()),
            'summary_stats': {
                'total_triples': sum(r['total_triples'] for r in results.values()),
                'avg_triples_per_year': sum(r['total_triples'] for r in results.values()) / len(results),
                'total_entities': sum(r['unique_entities'] for r in results.values()),
                'avg_entities_per_year': sum(r['unique_entities'] for r in results.values()) / len(results),
                'total_processing_time': sum(r.get('processing_time_seconds', 0) for r in results.values())
            },
            'yearly_details': results
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.data_dir / "metadata" / f"batch_generation_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"📋 批量处理摘要已保存: {summary_file}")

    def check_data_status(self):
        """检查数据生成状态"""
        print("🔍 检查知识图谱数据状态...")
        print("=" * 50)

        kg_dir = self.data_dir / "kg_json"
        existing_files = list(kg_dir.glob("policy_kg_*.json"))

        if not existing_files:
            print("❌ 未找到任何知识图谱数据文件")
            return {}

        data_status = {}
        total_triples = 0
        total_entities = 0

        for file_path in sorted(existing_files):
            try:
                year = int(file_path.stem.split('_')[-1])
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                metadata = data.get('metadata', {})
                triples = metadata.get('total_triples', 0)
                entities = metadata.get('unique_entities', 0)
                relations = metadata.get('unique_relations', 0)

                data_status[year] = {
                    'file': file_path,
                    'triples': triples,
                    'entities': entities,
                    'relations': relations,
                    'generated_at': metadata.get('generated_at', 'Unknown')
                }

                total_triples += triples
                total_entities += entities

                print(f"✅ {year}年: {triples:,} 三元组, {entities:,} 实体, {relations} 关系")

            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {str(e)}")

        print(f"\n📊 总计: {len(data_status)} 个年份")
        print(f"📈 总三元组: {total_triples:,}")
        print(f"🏷️  总实体: {total_entities:,}")

        return data_status

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='香港施政报告知识图谱批量生成器 - 改进版')
    parser.add_argument('--generate', action='store_true', help='批量生成知识图谱')
    parser.add_argument('--check', action='store_true', help='检查数据状态')
    parser.add_argument('--start-year', type=int, help='开始年份')
    parser.add_argument('--end-year', type=int, help='结束年份')
    parser.add_argument('--force', action='store_true', help='强制重新生成')
    parser.add_argument('--data-dir', default='policy_data', help='数据目录路径')

    args = parser.parse_args()

    generator = PolicyKGBatchGenerator(args.data_dir)

    if args.generate:
        generator.batch_generate(
            start_year=args.start_year,
            end_year=args.end_year,
            force_regenerate=args.force
        )
    elif args.check:
        generator.check_data_status()
    else:
        print("请指定操作:")
        print("  --generate           批量生成知识图谱")
        print("  --check              检查数据状态")
        print("  --start-year YYYY    指定开始年份")
        print("  --end-year YYYY      指定结束年份")
        print("  --force              强制重新生成")

if __name__ == "__main__":
    main()
