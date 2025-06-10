#!/usr/bin/env python3
"""
香港施政报告知识图谱对比分析器
第二阶段：基于已生成的知识图谱数据进行多维度对比分析
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class PolicyComparativeAnalyzer:
    """施政报告对比分析器"""

    def __init__(self, data_dir="policy_data"):
        self.data_dir = Path(data_dir)
        self.kg_data = {}  # 存储加载的知识图谱数据
        self.analysis_results = {}  # 存储分析结果

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def load_kg_data(self):
        """加载所有年份的知识图谱数据"""
        print("📂 加载知识图谱数据...")

        kg_dir = self.data_dir / "kg_json"
        if not kg_dir.exists():
            print(f"❌ 数据目录不存在: {kg_dir}")
            return False

        json_files = list(kg_dir.glob("policy_kg_*.json"))
        if not json_files:
            print(f"❌ 未找到知识图谱数据文件")
            return False

        for file_path in sorted(json_files):
            try:
                year = int(file_path.stem.split('_')[-1])
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.kg_data[year] = {
                    'metadata': data.get('metadata', {}),
                    'triples': data.get('knowledge_graph', [])
                }

                print(f"✅ {year}年: {len(self.kg_data[year]['triples'])} 个三元组")

            except Exception as e:
                print(f"❌ 加载失败 {file_path}: {str(e)}")

        print(f"📊 总计加载: {len(self.kg_data)} 个年份的数据")
        return len(self.kg_data) > 0

    def analyze_theme_evolution(self):
        """分析话语主题演变"""
        print("\n" + "="*60)
        print("📈 话语主题演变分析")
        print("="*60)

        # 定义话语主题关键词
        theme_keywords = {
            '一国两制': ['一国两制', '基本法', '高度自治', '港人治港', '中央政府'],
            '经济发展': ['经济', '发展', '投资', '金融', '贸易', '市场', '产业'],
            '民生福利': ['民生', '福利', '教育', '医疗', '住房', '就业', '社会保障'],
            '国家安全': ['国家安全', '安全', '稳定', '维护', '法律', '秩序'],
            '创新科技': ['创新', '科技', '技术', '数字', '智能', '研发', '人工智能'],
            '国际合作': ['国际', '合作', '全球', '世界', '外国', '开放', '交流'],
            '粤港澳大湾区': ['大湾区', '粤港澳', '深圳', '广州', '珠海', '融合'],
            '青年发展': ['青年', '年轻人', '学生', '培训', '机会', '就业'],
            '文化建设': ['文化', '艺术', '体育', '旅游', '传统', '遗产', '创意'],
            '环境保护': ['环境', '环保', '绿色', '可持续', '气候', '生态', '节能']
        }

        theme_evolution = defaultdict(dict)

        for year, data in self.kg_data.items():
            triples = data['triples']
            total_triples = len(triples)

            for theme, keywords in theme_keywords.items():
                count = 0
                for triple in triples:
                    # 检查三元组中是否包含主题关键词
                    text = f"{triple['subject']} {triple['predicate']} {triple['object']}"
                    if any(keyword in text for keyword in keywords):
                        count += 1

                percentage = (count / total_triples * 100) if total_triples > 0 else 0
                theme_evolution[theme][year] = {
                    'count': count,
                    'percentage': percentage,
                    'total_triples': total_triples
                }

        self.analysis_results['theme_evolution'] = theme_evolution
        return theme_evolution

    def analyze_entity_networks(self):
        """分析实体网络结构"""
        print("\n" + "="*50)
        print("🕸️ 实体网络结构分析")
        print("="*50)

        network_metrics = {}

        for year, data in self.kg_data.items():
            triples = data['triples']

            # 构建网络图
            G = nx.Graph()
            for triple in triples:
                G.add_edge(triple['subject'], triple['object'],
                          relation=triple['predicate'])

            # 计算网络指标
            if len(G.nodes()) > 0:
                metrics = {
                    'nodes': len(G.nodes()),
                    'edges': len(G.edges()),
                    'density': nx.density(G),
                    'avg_clustering': nx.average_clustering(G),
                    'components': nx.number_connected_components(G)
                }

                # 中心性分析
                if len(G.nodes()) > 1:
                    degree_centrality = nx.degree_centrality(G)
                    betweenness_centrality = nx.betweenness_centrality(G)

                    metrics['top_degree_entities'] = sorted(
                        degree_centrality.items(),
                        key=lambda x: x[1], reverse=True
                    )[:10]

                    metrics['top_betweenness_entities'] = sorted(
                        betweenness_centrality.items(),
                        key=lambda x: x[1], reverse=True
                    )[:10]

                network_metrics[year] = metrics

                print(f"{year}年: {metrics['nodes']}节点, {metrics['edges']}边, "
                      f"密度{metrics['density']:.3f}, 聚类{metrics['avg_clustering']:.3f}")

        self.analysis_results['network_metrics'] = network_metrics
        return network_metrics

    def analyze_relationship_patterns(self):
        """分析关系模式变化"""
        print("\n" + "="*50)
        print("🔗 关系模式变化分析")
        print("="*50)

        relation_evolution = {}

        for year, data in self.kg_data.items():
            triples = data['triples']

            # 统计关系类型
            relations = [triple['predicate'] for triple in triples]
            relation_counts = Counter(relations)

            # 获取前20个最常见关系
            top_relations = dict(relation_counts.most_common(20))

            relation_evolution[year] = {
                'total_relations': len(relations),
                'unique_relations': len(relation_counts),
                'top_relations': top_relations,
                'relation_diversity': len(relation_counts) / len(relations) if relations else 0
            }

            print(f"{year}年: {len(relations)}个关系, {len(relation_counts)}种类型, "
                  f"多样性{relation_evolution[year]['relation_diversity']:.3f}")

        self.analysis_results['relation_evolution'] = relation_evolution
        return relation_evolution

    def identify_discourse_shifts(self, theme_evolution):
        """识别话语转变点"""
        print("\n" + "="*50)
        print("🔄 话语转变点识别")
        print("="*50)

        shifts = []

        for theme, yearly_data in theme_evolution.items():
            years = sorted(yearly_data.keys())
            if len(years) < 2:
                continue

            percentages = [yearly_data[year]['percentage'] for year in years]

            # 识别显著变化点（变化超过阈值）
            for i in range(1, len(percentages)):
                change = percentages[i] - percentages[i-1]
                if abs(change) > 3:  # 3%以上的变化
                    shifts.append({
                        'year': years[i],
                        'theme': theme,
                        'change': change,
                        'from_percentage': percentages[i-1],
                        'to_percentage': percentages[i],
                        'significance': 'major' if abs(change) > 8 else 'moderate'
                    })

        # 按年份和变化幅度排序
        shifts.sort(key=lambda x: (x['year'], abs(x['change'])), reverse=True)

        print("📊 主要话语转变点:")
        for shift in shifts[:20]:
            direction = "↗️" if shift['change'] > 0 else "↘️"
            significance = "🔥" if shift['significance'] == 'major' else "📈"
            print(f"{shift['year']}年 {shift['theme']} {direction} {significance} "
                  f"{shift['change']:+.1f}% "
                  f"({shift['from_percentage']:.1f}% → {shift['to_percentage']:.1f}%)")

        self.analysis_results['discourse_shifts'] = shifts
        return shifts

    def create_visualizations(self):
        """创建可视化图表"""
        print("\n" + "="*50)
        print("📊 生成可视化图表")
        print("="*50)

        # 确保输出目录存在
        viz_dir = self.data_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)

        # 1. 主题演变趋势图
        self._create_theme_evolution_plot(viz_dir)

        # 2. 主题热力图
        self._create_theme_heatmap(viz_dir)

        # 3. 网络指标变化图
        self._create_network_metrics_plot(viz_dir)

        # 4. 关系多样性变化图
        self._create_relation_diversity_plot(viz_dir)

        print("✅ 所有可视化图表已生成")

    def _create_theme_evolution_plot(self, viz_dir):
        """创建主题演变趋势图"""
        if 'theme_evolution' not in self.analysis_results:
            return

        theme_evolution = self.analysis_results['theme_evolution']

        # 选择重点主题
        key_themes = ['一国两制', '经济发展', '国家安全', '粤港澳大湾区', '创新科技', '民生福利']

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('香港施政报告话语主题演变趋势 (1997-2024)', fontsize=16, fontweight='bold')

        for i, theme in enumerate(key_themes):
            if theme not in theme_evolution:
                continue

            ax = axes[i//3, i%3]

            years = sorted(theme_evolution[theme].keys())
            percentages = [theme_evolution[theme][year]['percentage'] for year in years]

            ax.plot(years, percentages, marker='o', linewidth=2.5, markersize=6,
                   color=plt.cm.Set3(i), alpha=0.8)
            ax.fill_between(years, percentages, alpha=0.3, color=plt.cm.Set3(i))

            ax.set_title(f'{theme}', fontsize=12, fontweight='bold')
            ax.set_xlabel('年份', fontsize=10)
            ax.set_ylabel('占比 (%)', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, max(percentages) * 1.1 if percentages else 1)

        plt.tight_layout()
        plt.savefig(viz_dir / 'theme_evolution_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ 主题演变趋势图已生成")

    def _create_theme_heatmap(self, viz_dir):
        """创建主题热力图"""
        if 'theme_evolution' not in self.analysis_results:
            return

        theme_evolution = self.analysis_results['theme_evolution']

        # 构建数据矩阵
        years = sorted(list(self.kg_data.keys()))
        themes = list(theme_evolution.keys())

        data_matrix = []
        for theme in themes:
            row = []
            for year in years:
                if year in theme_evolution[theme]:
                    row.append(theme_evolution[theme][year]['percentage'])
                else:
                    row.append(0)
            data_matrix.append(row)

        # 创建热力图
        plt.figure(figsize=(16, 10))
        sns.heatmap(data_matrix,
                   xticklabels=years,
                   yticklabels=themes,
                   annot=True,
                   fmt='.1f',
                   cmap='YlOrRd',
                   cbar_kws={'label': '主题占比 (%)'})

        plt.title('香港施政报告话语主题热力图 (1997-2024)', fontsize=14, fontweight='bold')
        plt.xlabel('年份', fontsize=12)
        plt.ylabel('话语主题', fontsize=12)
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(viz_dir / 'theme_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ 主题热力图已生成")

    def _create_network_metrics_plot(self, viz_dir):
        """创建网络指标变化图"""
        if 'network_metrics' not in self.analysis_results:
            return

        network_metrics = self.analysis_results['network_metrics']

        years = sorted(network_metrics.keys())
        nodes = [network_metrics[year]['nodes'] for year in years]
        edges = [network_metrics[year]['edges'] for year in years]
        density = [network_metrics[year]['density'] for year in years]
        clustering = [network_metrics[year]['avg_clustering'] for year in years]

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('知识图谱网络结构指标变化', fontsize=16, fontweight='bold')

        # 节点数量
        axes[0,0].plot(years, nodes, marker='o', color='blue', linewidth=2)
        axes[0,0].set_title('实体数量变化')
        axes[0,0].set_ylabel('节点数')
        axes[0,0].grid(True, alpha=0.3)

        # 边数量
        axes[0,1].plot(years, edges, marker='s', color='red', linewidth=2)
        axes[0,1].set_title('关系数量变化')
        axes[0,1].set_ylabel('边数')
        axes[0,1].grid(True, alpha=0.3)

        # 网络密度
        axes[1,0].plot(years, density, marker='^', color='green', linewidth=2)
        axes[1,0].set_title('网络密度变化')
        axes[1,0].set_ylabel('密度')
        axes[1,0].set_xlabel('年份')
        axes[1,0].grid(True, alpha=0.3)

        # 聚类系数
        axes[1,1].plot(years, clustering, marker='d', color='orange', linewidth=2)
        axes[1,1].set_title('平均聚类系数变化')
        axes[1,1].set_ylabel('聚类系数')
        axes[1,1].set_xlabel('年份')
        axes[1,1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(viz_dir / 'network_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ 网络指标图已生成")

    def _create_relation_diversity_plot(self, viz_dir):
        """创建关系多样性变化图"""
        if 'relation_evolution' not in self.analysis_results:
            return

        relation_evolution = self.analysis_results['relation_evolution']

        years = sorted(relation_evolution.keys())
        diversity = [relation_evolution[year]['relation_diversity'] for year in years]
        unique_relations = [relation_evolution[year]['unique_relations'] for year in years]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('关系模式多样性分析', fontsize=16, fontweight='bold')

        # 关系多样性
        ax1.plot(years, diversity, marker='o', color='purple', linewidth=2.5)
        ax1.set_title('关系多样性变化')
        ax1.set_xlabel('年份')
        ax1.set_ylabel('多样性指数')
        ax1.grid(True, alpha=0.3)

        # 唯一关系类型数量
        ax2.bar(years, unique_relations, color='skyblue', alpha=0.7)
        ax2.set_title('唯一关系类型数量')
        ax2.set_xlabel('年份')
        ax2.set_ylabel('关系类型数')
        ax2.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(viz_dir / 'relation_diversity.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✅ 关系多样性图已生成")

    def generate_analysis_report(self):
        """生成综合分析报告"""
        print("\n" + "="*60)
        print("📋 生成综合分析报告")
        print("="*60)

        report_content = self._create_report_content()

        # 保存报告
        report_dir = self.data_dir / "analysis"
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / f"comparative_analysis_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📄 分析报告已保存: {report_file}")
        return report_file

    def _create_report_content(self):
        """创建报告内容"""
        years_range = f"{min(self.kg_data.keys())}-{max(self.kg_data.keys())}"
        total_years = len(self.kg_data)

        report = f"""# 香港施政报告知识图谱对比分析报告

## 📊 数据概览
- **分析时期**: {years_range}
- **报告数量**: {total_years} 份
- **生成时间**: {datetime.now().strftime('%Y年%m月%d日')}

## 🎯 主要发现

### 1. 话语主题演变特征
"""

        # 添加主题演变分析
        if 'theme_evolution' in self.analysis_results:
            theme_evolution = self.analysis_results['theme_evolution']

            for theme in ['一国两制', '经济发展', '国家安全', '粤港澳大湾区']:
                if theme in theme_evolution:
                    years = sorted(theme_evolution[theme].keys())
                    if len(years) >= 2:
                        start_pct = theme_evolution[theme][years[0]]['percentage']
                        end_pct = theme_evolution[theme][years[-1]]['percentage']
                        trend = "上升" if end_pct > start_pct else "下降"
                        change = abs(end_pct - start_pct)

                        report += f"\n- **{theme}**: {trend}趋势，变化幅度 {change:.1f}%"

        report += f"""

### 2. 网络结构演变
"""

        # 添加网络分析
        if 'network_metrics' in self.analysis_results:
            network_metrics = self.analysis_results['network_metrics']
            years = sorted(network_metrics.keys())

            if years:
                start_year = years[0]
                end_year = years[-1]

                start_nodes = network_metrics[start_year]['nodes']
                end_nodes = network_metrics[end_year]['nodes']

                start_density = network_metrics[start_year]['density']
                end_density = network_metrics[end_year]['density']

                report += f"""
- **实体规模**: 从{start_year}年的{start_nodes}个实体增长到{end_year}年的{end_nodes}个实体
- **网络密度**: 从{start_density:.3f}变化到{end_density:.3f}
"""

        report += f"""

### 3. 关键转变节点
"""

        # 添加转变点分析
        if 'discourse_shifts' in self.analysis_results:
            shifts = self.analysis_results['discourse_shifts']
            major_shifts = [s for s in shifts if s['significance'] == 'major'][:10]

            for shift in major_shifts:
                direction = "显著上升" if shift['change'] > 0 else "显著下降"
                report += f"\n- **{shift['year']}年**: {shift['theme']}话语{direction} ({shift['change']:+.1f}%)"

        report += f"""

## 📈 分析方法
1. **知识图谱构建**: 使用大语言模型从文本中提取实体关系三元组
2. **主题分类**: 基于关键词匹配识别10个主要话语主题
3. **网络分析**: 计算图结构指标（密度、聚类系数、中心性等）
4. **时序对比**: 识别话语重点的显著变化节点

## 📊 数据文件
- 原始数据: `kg_json/policy_kg_YYYY.json`
- 可视化图表: `visualizations/`
- 详细分析: `analysis/`

---
*报告由知识图谱对比分析系统自动生成*
"""

        return report

    def run_full_analysis(self):
        """运行完整的对比分析流程"""
        print("🚀 开始香港施政报告知识图谱对比分析")
        print("="*60)

        # 1. 加载数据
        if not self.load_kg_data():
            print("❌ 数据加载失败，请先生成知识图谱数据")
            return False

        # 2. 执行各项分析
        print("\n🔍 执行多维度分析...")
        theme_evolution = self.analyze_theme_evolution()
        network_metrics = self.analyze_entity_networks()
        relation_patterns = self.analyze_relationship_patterns()

        # 3. 识别转变点
        discourse_shifts = self.identify_discourse_shifts(theme_evolution)

        # 4. 创建可视化
        self.create_visualizations()

        # 5. 生成报告
        report_file = self.generate_analysis_report()

        print(f"\n🎉 对比分析完成!")
        print(f"📁 结果保存在: {self.data_dir}/")
        print(f"📄 分析报告: {report_file}")

        return True

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='香港施政报告知识图谱对比分析器')
    parser.add_argument('--analyze', action='store_true', help='执行完整对比分析')
    parser.add_argument('--data-dir', default='policy_data', help='数据目录路径')

    args = parser.parse_args()

    analyzer = PolicyComparativeAnalyzer(args.data_dir)

    if args.analyze:
        analyzer.run_full_analysis()
    else:
        print("请指定操作:")
        print("  --analyze   执行完整对比分析")

if __name__ == "__main__":
    main()
