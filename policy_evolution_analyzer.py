#!/usr/bin/env python3
"""
香港施政报告历年话语变化分析方案
分析1997年回归以来每年施政报告的知识图谱演变
"""

import json
import os
import pandas as pd
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import networkx as nx

class PolicyEvolutionAnalyzer:
    """施政报告演变分析器"""
    
    def __init__(self, data_dir="policy_reports"):
        self.data_dir = data_dir
        self.years = range(1997, 2025)  # 1997-2024年
        self.kg_data = {}  # 存储每年的知识图谱数据
        self.evolution_metrics = {}  # 存储演变指标
        
    def setup_project_structure(self):
        """设置项目目录结构"""
        directories = [
            f"{self.data_dir}/raw_texts",      # 原始文本文件
            f"{self.data_dir}/kg_outputs",     # 知识图谱输出
            f"{self.data_dir}/analysis",       # 分析结果
            f"{self.data_dir}/visualizations", # 可视化结果
            f"{self.data_dir}/comparisons"     # 对比分析
        ]
        
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)
            
        print("📁 项目目录结构已创建:")
        for dir_path in directories:
            print(f"   • {dir_path}/")
    
    def generate_batch_script(self):
        """生成批量处理脚本"""
        batch_script = f"""#!/bin/bash
# 批量生成香港施政报告知识图谱 (1997-2024)

echo "🚀 开始批量处理香港施政报告..."

# 设置基础路径
BASE_DIR="{self.data_dir}"
KG_GENERATOR="python3 generate-graph.py"

# 处理每年的施政报告
for year in {{1997..2024}}; do
    echo "📄 处理 ${{year}} 年施政报告..."
    
    input_file="${{BASE_DIR}}/raw_texts/policy_address_${{year}}.txt"
    output_file="${{BASE_DIR}}/kg_outputs/policy_kg_${{year}}.html"
    json_file="${{BASE_DIR}}/kg_outputs/policy_kg_${{year}}.json"
    
    if [ -f "$input_file" ]; then
        $KG_GENERATOR --input "$input_file" --output "$output_file"
        echo "✅ ${{year}} 年处理完成"
    else
        echo "⚠️  ${{year}} 年文件不存在: $input_file"
    fi
    
    # 添加延迟避免API限制
    sleep 5
done

echo "🎉 批量处理完成！"
"""
        
        with open("batch_generate_kg.sh", "w") as f:
            f.write(batch_script)
        
        os.chmod("batch_generate_kg.sh", 0o755)
        print("📝 批量处理脚本已生成: batch_generate_kg.sh")
    
    def load_yearly_data(self):
        """加载每年的知识图谱数据"""
        print("📂 加载历年知识图谱数据...")
        
        for year in self.years:
            json_file = f"{self.data_dir}/kg_outputs/policy_kg_{year}.json"
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        self.kg_data[year] = json.load(f)
                    print(f"✅ {year}年数据加载成功 ({len(self.kg_data[year])} 个三元组)")
                except Exception as e:
                    print(f"❌ {year}年数据加载失败: {e}")
            else:
                print(f"⚠️  {year}年数据文件不存在")
    
    def analyze_discourse_evolution(self):
        """分析话语演变"""
        print("\n" + "="*60)
        print("📈 话语演变分析")
        print("="*60)
        
        # 定义关键话语主题
        discourse_themes = {
            '一国两制': ['一国两制', '基本法', '高度自治', '港人治港'],
            '经济发展': ['经济', '发展', '投资', '金融', '贸易', '市场'],
            '民生福利': ['民生', '福利', '教育', '医疗', '住房', '就业'],
            '国家安全': ['国家安全', '安全', '稳定', '维护', '法律'],
            '创新科技': ['创新', '科技', '技术', '数字', '智能', '研发'],
            '国际合作': ['国际', '合作', '全球', '世界', '外国', '开放'],
            '粤港澳大湾区': ['大湾区', '粤港澳', '深圳', '广州', '珠海'],
            '青年发展': ['青年', '年轻人', '学生', '培训', '机会'],
            '文化建设': ['文化', '艺术', '体育', '旅游', '传统', '遗产'],
            '环境保护': ['环境', '环保', '绿色', '可持续', '气候', '生态']
        }
        
        # 分析每年各主题的出现频率
        theme_evolution = defaultdict(dict)
        
        for year, data in self.kg_data.items():
            total_triples = len(data)
            
            for theme, keywords in discourse_themes.items():
                count = 0
                for item in data:
                    text = f"{item['subject']} {item['predicate']} {item['object']}"
                    if any(keyword in text for keyword in keywords):
                        count += 1
                
                # 计算主题占比
                percentage = (count / total_triples * 100) if total_triples > 0 else 0
                theme_evolution[theme][year] = {
                    'count': count,
                    'percentage': percentage,
                    'total_triples': total_triples
                }
        
        return theme_evolution
    
    def analyze_entity_evolution(self):
        """分析实体演变"""
        print("\n" + "="*50)
        print("🏛️ 核心实体演变分析")
        print("="*50)
        
        # 跟踪关键实体的出现频率
        key_entities = [
            '行政长官', '立法会', '中央政府', '特区政府',
            '香港', '内地', '基本法', '一国两制',
            '经济', '教育', '医疗', '住房', '就业'
        ]
        
        entity_evolution = defaultdict(dict)
        
        for year, data in self.kg_data.items():
            entity_counts = defaultdict(int)
            
            for item in data:
                for entity in key_entities:
                    if entity in item['subject'] or entity in item['object']:
                        entity_counts[entity] += 1
            
            entity_evolution[year] = dict(entity_counts)
        
        return entity_evolution
    
    def analyze_relationship_evolution(self):
        """分析关系演变"""
        print("\n" + "="*50)
        print("🔗 关系类型演变分析")
        print("="*50)
        
        relationship_evolution = defaultdict(dict)
        
        for year, data in self.kg_data.items():
            relations = [item['predicate'] for item in data]
            relation_counts = Counter(relations)
            
            # 获取前20个最常见关系
            top_relations = dict(relation_counts.most_common(20))
            relationship_evolution[year] = top_relations
        
        return relationship_evolution
    
    def identify_discourse_shifts(self, theme_evolution):
        """识别话语转变点"""
        print("\n" + "="*50)
        print("🔄 话语转变点识别")
        print("="*50)
        
        shifts = []
        
        for theme, yearly_data in theme_evolution.items():
            years = sorted(yearly_data.keys())
            percentages = [yearly_data[year]['percentage'] for year in years]
            
            # 识别显著变化点（变化超过5%）
            for i in range(1, len(percentages)):
                change = percentages[i] - percentages[i-1]
                if abs(change) > 5:  # 5%以上的变化
                    shifts.append({
                        'year': years[i],
                        'theme': theme,
                        'change': change,
                        'from_percentage': percentages[i-1],
                        'to_percentage': percentages[i]
                    })
        
        # 按年份和变化幅度排序
        shifts.sort(key=lambda x: (x['year'], abs(x['change'])), reverse=True)
        
        print("📊 主要话语转变点:")
        for shift in shifts[:15]:
            direction = "↗️" if shift['change'] > 0 else "↘️"
            print(f"{shift['year']}年 {shift['theme']} {direction} "
                  f"{shift['change']:+.1f}% "
                  f"({shift['from_percentage']:.1f}% → {shift['to_percentage']:.1f}%)")
        
        return shifts
    
    def generate_comparison_report(self, theme_evolution, entity_evolution, relationship_evolution):
        """生成对比分析报告"""
        print("\n" + "="*60)
        print("📋 历年施政报告话语变化分析报告")
        print("="*60)
        
        # 创建DataFrame用于分析
        theme_df = pd.DataFrame(theme_evolution).T
        
        report = f"""
# 香港施政报告话语演变分析报告 (1997-2024)

## 📊 数据概览
- 分析年份: {min(self.kg_data.keys())}-{max(self.kg_data.keys())}
- 总报告数: {len(self.kg_data)}
- 总三元组数: {sum(len(data) for data in self.kg_data.values())}

## 🎯 主要发现

### 1. 话语主题演变趋势
"""
        
        # 分析各主题的总体趋势
        for theme in theme_evolution.keys():
            years = sorted([year for year in theme_evolution[theme].keys()])
            if len(years) >= 2:
                start_pct = theme_evolution[theme][years[0]]['percentage']
                end_pct = theme_evolution[theme][years[-1]]['percentage']
                trend = "上升" if end_pct > start_pct else "下降"
                change = abs(end_pct - start_pct)
                
                report += f"\n- **{theme}**: {trend}趋势，变化幅度 {change:.1f}%"
        
        report += f"""

### 2. 关键时间节点
- 1997年: 香港回归，一国两制开始实施
- 2003年: SARS疫情，经济复苏成为重点
- 2008年: 全球金融危机，经济政策调整
- 2014年: 占中事件后，治理话语变化
- 2019年: 修例风波后，国家安全话语增强
- 2020年: 新冠疫情，民生和经济并重
- 2022年: 二十大后，融入国家发展大局

### 3. 话语特征变化
- **早期(1997-2007)**: 侧重经济发展和民生改善
- **中期(2008-2018)**: 平衡发展与稳定，关注青年和创新
- **近期(2019-2024)**: 强调国家安全，推动大湾区融合

## 📈 数据支撑
详细数据请参考生成的可视化图表和数据文件。
        """
        
        # 保存报告
        report_file = f"{self.data_dir}/analysis/discourse_evolution_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 分析报告已保存: {report_file}")
        
        return report
    
    def create_visualizations(self, theme_evolution):
        """创建可视化图表"""
        print("\n" + "="*50)
        print("📊 生成可视化图表")
        print("="*50)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 主题演变趋势图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('香港施政报告话语主题演变 (1997-2024)', fontsize=16)
        
        themes_to_plot = ['一国两制', '经济发展', '国家安全', '创新科技']
        
        for i, theme in enumerate(themes_to_plot):
            ax = axes[i//2, i%2]
            
            if theme in theme_evolution:
                years = sorted(theme_evolution[theme].keys())
                percentages = [theme_evolution[theme][year]['percentage'] for year in years]
                
                ax.plot(years, percentages, marker='o', linewidth=2, markersize=6)
                ax.set_title(f'{theme}主题变化', fontsize=12)
                ax.set_xlabel('年份')
                ax.set_ylabel('占比 (%)')
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.data_dir}/visualizations/theme_evolution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 主题演变图表已生成")
        
        # 2. 热力图
        theme_matrix = []
        years = sorted(list(self.kg_data.keys()))
        themes = list(theme_evolution.keys())
        
        for theme in themes:
            row = []
            for year in years:
                if year in theme_evolution[theme]:
                    row.append(theme_evolution[theme][year]['percentage'])
                else:
                    row.append(0)
            theme_matrix.append(row)
        
        plt.figure(figsize=(16, 10))
        sns.heatmap(theme_matrix, 
                   xticklabels=years, 
                   yticklabels=themes,
                   annot=True, 
                   fmt='.1f',
                   cmap='YlOrRd',
                   cbar_kws={'label': '主题占比 (%)'})
        
        plt.title('香港施政报告话语主题热力图 (1997-2024)', fontsize=14)
        plt.xlabel('年份')
        plt.ylabel('话语主题')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(f'{self.data_dir}/visualizations/theme_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 主题热力图已生成")
    
    def run_full_analysis(self):
        """运行完整分析流程"""
        print("🚀 开始香港施政报告话语演变分析")
        print("="*60)
        
        # 1. 设置项目结构
        self.setup_project_structure()
        
        # 2. 生成批量处理脚本
        self.generate_batch_script()
        
        # 3. 加载数据（如果存在）
        self.load_yearly_data()
        
        if not self.kg_data:
            print("\n⚠️  暂无知识图谱数据，请先运行批量处理脚本生成数据")
            print("运行命令: ./batch_generate_kg.sh")
            return
        
        # 4. 执行各项分析
        theme_evolution = self.analyze_discourse_evolution()
        entity_evolution = self.analyze_entity_evolution()
        relationship_evolution = self.analyze_relationship_evolution()
        
        # 5. 识别转变点
        shifts = self.identify_discourse_shifts(theme_evolution)
        
        # 6. 生成报告
        report = self.generate_comparison_report(theme_evolution, entity_evolution, relationship_evolution)
        
        # 7. 创建可视化
        self.create_visualizations(theme_evolution)
        
        print("\n🎉 分析完成！")
        print(f"📁 结果保存在: {self.data_dir}/")

def main():
    """主函数"""
    analyzer = PolicyEvolutionAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()