#!/usr/bin/env python3
"""
香港施政报告知识图谱批量生成器
第一阶段：为每年施政报告生成独立的知识图谱数据
"""

import os
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.knowledge_graph.main import process_text_in_chunks
from src.knowledge_graph.config import load_config

class PolicyKGGenerator:
    """施政报告知识图谱生成器"""

    def __init__(self, data_dir="policy_data"):
        self.data_dir = Path(data_dir)
        self.years = range(1997, 2025)  # 1997-2024年
        self.setup_directories()

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

        print("📁 目录结构已创建:")
        for dir_path in directories:
            print(f"   • {dir_path}/")

    def create_policy_config(self):
        """创建针对施政报告的专用配置"""
        base_config = load_config()

        # 针对施政报告优化的配置
        policy_config = base_config.copy()
        policy_config.update({
            'chunking': {
                'chunk_size': 150,  # 施政报告段落较长
                'overlap': 30       # 增加重叠确保政策连贯性
            },
            'standardization': {
                'enabled': True,
                'use_llm_for_entities': True,
                'focus_entities': [
                    '行政长官', '特区政府', '中央政府', '立法会',
                    '一国两制', '基本法', '国家安全',
                    '经济发展', '民生改善', '教育政策', '房屋政策',
                    '大湾区', '创新科技', '青年发展'
                ]
            },
            'inference': {
                'enabled': True,
                'use_llm_for_inference': True,
                'apply_transitive': True
            }
        })

        return policy_config

    def generate_single_kg(self, year, text_content, config):
        """为单年施政报告生成知识图谱"""
        print(f"\n📄 处理 {year} 年施政报告...")

        try:
            # 处理文本生成知识图谱
            kg_data = process_text_in_chunks(config, text_content, debug=False)

            if not kg_data:
                print(f"❌ {year}年知识图谱生成失败")
                return None

            # 添加元数据
            metadata = {
                'year': year,
                'generated_at': datetime.now().isoformat(),
                'total_triples': len(kg_data),
                'unique_entities': len(self._get_unique_entities(kg_data)),
                'unique_relations': len(set(item['predicate'] for item in kg_data)),
                'text_length': len(text_content),
                'chunks_processed': max([item.get('chunk', 1) for item in kg_data])
            }

            # 保存JSON数据
            json_file = self.data_dir / "kg_json" / f"policy_kg_{year}.json"
            output_data = {
                'metadata': metadata,
                'knowledge_graph': kg_data
            }

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"✅ {year}年处理完成:")
            print(f"   • 三元组数量: {metadata['total_triples']}")
            print(f"   • 唯一实体: {metadata['unique_entities']}")
            print(f"   • 关系类型: {metadata['unique_relations']}")
            print(f"   • 数据保存: {json_file}")

            return metadata

        except Exception as e:
            print(f"❌ {year}年处理出错: {str(e)}")
            return None

    def _get_unique_entities(self, kg_data):
        """获取唯一实体集合"""
        entities = set()
        for item in kg_data:
            entities.add(item['subject'])
            entities.add(item['object'])
        return entities

    def batch_generate(self):
        """批量生成所有年份的知识图谱"""
        print("🚀 开始批量生成香港施政报告知识图谱")
        print("=" * 60)

        config = self.create_policy_config()
        results = {}

        # 检查可用的文本文件
        available_files = []
        for year in self.years:
            text_file = self.data_dir / "raw_texts" / f"policy_address_{year}.txt"
            if text_file.exists():
                available_files.append((year, text_file))
            else:
                print(f"⚠️  {year}年文件不存在: {text_file}")

        if not available_files:
            print("❌ 未找到任何施政报告文本文件")
            print("请将文本文件放置在: policy_data/raw_texts/")
            print("文件命名格式: policy_address_YYYY.txt")
            return

        print(f"\n📊 找到 {len(available_files)} 个文件，开始处理...")

        # 处理每个文件
        for i, (year, text_file) in enumerate(available_files, 1):
            print(f"\n[{i}/{len(available_files)}] 处理 {year} 年...")

            try:
                # 读取文本
                with open(text_file, 'r', encoding='utf-8') as f:
                    text_content = f.read()

                # 生成知识图谱
                metadata = self.generate_single_kg(year, text_content, config)
                if metadata:
                    results[year] = metadata

                # 添加延迟避免API限制
                if i < len(available_files):
                    print("⏳ 等待5秒避免API限制...")
                    time.sleep(5)

            except Exception as e:
                print(f"❌ 读取{year}年文件失败: {str(e)}")
                continue

        # 保存批量处理结果
        self._save_batch_results(results)

        print(f"\n🎉 批量处理完成!")
        print(f"✅ 成功处理: {len(results)} 个年份")
        print(f"📁 数据保存在: {self.data_dir}/kg_json/")

        return results

    def _save_batch_results(self, results):
        """保存批量处理结果摘要"""
        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_years': len(results),
            'years_processed': sorted(results.keys()),
            'summary_stats': {
                'total_triples': sum(r['total_triples'] for r in results.values()),
                'avg_triples_per_year': sum(r['total_triples'] for r in results.values()) / len(results) if results else 0,
                'total_entities': sum(r['unique_entities'] for r in results.values()),
                'avg_entities_per_year': sum(r['unique_entities'] for r in results.values()) / len(results) if results else 0
            },
            'yearly_details': results
        }

        summary_file = self.data_dir / "metadata" / "batch_generation_summary.json"
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
        for file_path in sorted(existing_files):
            try:
                year = int(file_path.stem.split('_')[-1])
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                metadata = data.get('metadata', {})
                data_status[year] = {
                    'file': file_path,
                    'triples': metadata.get('total_triples', 0),
                    'entities': metadata.get('unique_entities', 0),
                    'relations': metadata.get('unique_relations', 0),
                    'generated_at': metadata.get('generated_at', 'Unknown')
                }

                print(f"✅ {year}年: {metadata.get('total_triples', 0)} 三元组, "
                      f"{metadata.get('unique_entities', 0)} 实体, "
                      f"{metadata.get('unique_relations', 0)} 关系")

            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {str(e)}")

        print(f"\n📊 总计: {len(data_status)} 个年份的数据已生成")
        return data_status

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='香港施政报告知识图谱批量生成器')
    parser.add_argument('--generate', action='store_true', help='批量生成知识图谱')
    parser.add_argument('--check', action='store_true', help='检查数据状态')
    parser.add_argument('--data-dir', default='policy_data', help='数据目录路径')

    args = parser.parse_args()

    generator = PolicyKGGenerator(args.data_dir)

    if args.generate:
        generator.batch_generate()
    elif args.check:
        generator.check_data_status()
    else:
        print("请指定操作:")
        print("  --generate  批量生成知识图谱")
        print("  --check     检查数据状态")

if __name__ == "__main__":
    main()
