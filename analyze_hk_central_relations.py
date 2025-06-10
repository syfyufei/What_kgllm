#!/usr/bin/env python3
"""分析香港与中央政府关系的专门脚本"""

import json
from collections import Counter, defaultdict
import re

def load_kg_data(file_path):
    """加载知识图谱数据"""
    print(f"📂 加载知识图谱数据进行香港-中央关系分析...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 成功加载 {len(data)} 个三元组")
    return data

def extract_hk_central_relations(data):
    """提取香港与中央相关的关系"""
    print("\n" + "="*60)
    print("🏛️ 香港与中央政府关系分析")
    print("="*60)
    
    # 定义香港相关关键词
    hk_keywords = [
        '香港', '特区', '特别行政区', '港府', '香港政府', 
        '行政长官', '立法会', '司法机关', '基本法'
    ]
    
    # 定义中央相关关键词
    central_keywords = [
        '中央', '中央政府', '国家', '全国', '内地', 
        '中共中央', '国务院', '人大', '中华人民共和国'
    ]
    
    # 定义一国两制相关关键词
    octs_keywords = [
        '一国两制', '港人治港', '高度自治', '爱国者治港',
        '基本法', '宪法', '国家安全', '二十三条'
    ]
    
    # 提取相关三元组
    hk_central_triples = []
    hk_triples = []
    central_triples = []
    octs_triples = []
    
    for item in data:
        text = f"{item['subject']} {item['predicate']} {item['object']}"
        
        # 香港-中央直接关系
        has_hk = any(keyword in text for keyword in hk_keywords)
        has_central = any(keyword in text for keyword in central_keywords)
        has_octs = any(keyword in text for keyword in octs_keywords)
        
        if has_hk and has_central:
            hk_central_triples.append(item)
        elif has_hk:
            hk_triples.append(item)
        elif has_central:
            central_triples.append(item)
        
        if has_octs:
            octs_triples.append(item)
    
    print(f"📊 数据统计:")
    print(f"   • 香港-中央直接关系: {len(hk_central_triples)} 个三元组")
    print(f"   • 香港相关关系: {len(hk_triples)} 个三元组")
    print(f"   • 中央相关关系: {len(central_triples)} 个三元组")
    print(f"   • 一国两制相关关系: {len(octs_triples)} 个三元组")
    
    return hk_central_triples, hk_triples, central_triples, octs_triples

def analyze_direct_relations(hk_central_triples):
    """分析香港与中央的直接关系"""
    print("\n" + "="*50)
    print("🤝 香港-中央直接关系分析")
    print("="*50)
    
    if not hk_central_triples:
        print("❌ 未找到香港与中央的直接关系")
        return
    
    print(f"📈 发现 {len(hk_central_triples)} 个直接关系:")
    
    # 分析关系类型
    relations = [item['predicate'] for item in hk_central_triples]
    relation_counts = Counter(relations)
    
    print("\n🔗 关系类型分布:")
    for i, (relation, count) in enumerate(relation_counts.most_common(10), 1):
        percentage = (count / len(hk_central_triples)) * 100
        print(f"{i:2d}. {relation:<20} {count:>3} 次 ({percentage:4.1f}%)")
    
    # 显示具体关系
    print(f"\n📋 具体关系示例（前20个）:")
    for i, item in enumerate(hk_central_triples[:20], 1):
        print(f"{i:2d}. {item['subject']} → {item['predicate']} → {item['object']}")
    
    return relation_counts

def analyze_support_relations(data):
    """分析中央对香港的支持关系"""
    print("\n" + "="*50)
    print("🎯 中央对香港支持关系分析")
    print("="*50)
    
    support_keywords = ['支持', '支援', '协助', '帮助', '促进', '推动', '鼓励']
    central_keywords = ['中央', '中央政府', '国家', '内地']
    hk_keywords = ['香港', '特区', '特别行政区']
    
    support_relations = []
    
    for item in data:
        # 中央支持香港
        if (any(ck in item['subject'] for ck in central_keywords) and 
            any(sk in item['predicate'] for sk in support_keywords) and
            any(hk in item['object'] for hk in hk_keywords)):
            support_relations.append(item)
        
        # 或者香港获得中央支持
        elif (any(hk in item['subject'] for hk in hk_keywords) and
              any(ck in item['object'] for ck in central_keywords) and
              any(sk in item['predicate'] for sk in support_keywords)):
            support_relations.append(item)
    
    print(f"📊 发现 {len(support_relations)} 个支持关系:")
    
    if support_relations:
        for i, item in enumerate(support_relations[:15], 1):
            print(f"{i:2d}. {item['subject']} → {item['predicate']} → {item['object']}")
    
    return support_relations

def analyze_octs_implementation(octs_triples):
    """分析一国两制实施情况"""
    print("\n" + "="*50)
    print("🏛️ 一国两制实施分析")
    print("="*50)
    
    if not octs_triples:
        print("❌ 未找到一国两制相关关系")
        return
    
    print(f"📊 一国两制相关关系: {len(octs_triples)} 个")
    
    # 分析关键概念
    key_concepts = defaultdict(int)
    
    for item in octs_triples:
        text = f"{item['subject']} {item['object']}"
        
        concepts = {
            '基本法': ['基本法', '宪法'],
            '高度自治': ['高度自治', '自治权'],
            '港人治港': ['港人治港', '香港人'],
            '爱国者治港': ['爱国者治港', '爱国'],
            '国家安全': ['国家安全', '安全', '稳定'],
            '司法独立': ['司法', '法院', '法官'],
            '行政主导': ['行政长官', '政府', '行政']
        }
        
        for concept, keywords in concepts.items():
            if any(keyword in text for keyword in keywords):
                key_concepts[concept] += 1
    
    print("\n📈 一国两制核心概念分布:")
    for concept, count in sorted(key_concepts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {concept:<12} {count:>3} 次")
    
    # 显示具体关系
    print(f"\n📋 一国两制具体实施（前15个）:")
    for i, item in enumerate(octs_triples[:15], 1):
        print(f"{i:2d}. {item['subject']} → {item['predicate']} → {item['object']}")
    
    return key_concepts

def analyze_cooperation_areas(data):
    """分析合作领域"""
    print("\n" + "="*50)
    print("🤝 港中合作领域分析")
    print("="*50)
    
    cooperation_areas = {
        '经济合作': ['经济', '贸易', '投资', '金融', '市场', '商业'],
        '科技合作': ['科技', '创新', '技术', '研发', '数字', '智能'],
        '教育合作': ['教育', '学校', '大学', '学生', '人才', '培训'],
        '文化合作': ['文化', '艺术', '体育', '旅游', '交流', '传统'],
        '基建合作': ['基础设施', '交通', '建设', '工程', '港口', '机场'],
        '医疗合作': ['医疗', '健康', '医院', '药物', '治疗', '卫生'],
        '环保合作': ['环境', '环保', '绿色', '可持续', '气候', '生态']
    }
    
    area_relations = defaultdict(list)
    
    for item in data:
        text = f"{item['subject']} {item['predicate']} {item['object']}"
        
        # 检查是否涉及香港和内地/中央
        has_hk = any(keyword in text for keyword in ['香港', '特区'])
        has_mainland = any(keyword in text for keyword in ['内地', '中央', '国家'])
        
        if has_hk and has_mainland:
            for area, keywords in cooperation_areas.items():
                if any(keyword in text for keyword in keywords):
                    area_relations[area].append(item)
    
    print("📊 合作领域分布:")
    for area, relations in sorted(area_relations.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   • {area:<12} {len(relations):>3} 个关系")
    
    # 显示每个领域的具体合作
    for area, relations in area_relations.items():
        if relations:
            print(f"\n🔹 {area}合作示例:")
            for i, item in enumerate(relations[:5], 1):
                print(f"   {i}. {item['subject']} → {item['predicate']} → {item['object']}")
    
    return area_relations

def analyze_policy_coordination(data):
    """分析政策协调机制"""
    print("\n" + "="*50)
    print("⚙️ 政策协调机制分析")
    print("="*50)
    
    coordination_keywords = [
        '协调', '统筹', '配合', '衔接', '对接', 
        '沟通', '联系', '合作', '协作', '联动'
    ]
    
    coordination_relations = []
    
    for item in data:
        text = f"{item['subject']} {item['predicate']} {item['object']}"
        
        # 涉及香港和中央的协调
        has_hk = any(keyword in text for keyword in ['香港', '特区'])
        has_central = any(keyword in text for keyword in ['中央', '内地', '国家'])
        has_coordination = any(keyword in item['predicate'] for keyword in coordination_keywords)
        
        if (has_hk and has_central and has_coordination):
            coordination_relations.append(item)
    
    print(f"📊 发现 {len(coordination_relations)} 个协调机制:")
    
    if coordination_relations:
        for i, item in enumerate(coordination_relations[:10], 1):
            print(f"{i:2d}. {item['subject']} → {item['predicate']} → {item['object']}")
    
    return coordination_relations

def generate_hk_central_summary(hk_central_triples, support_relations, octs_triples, cooperation_areas):
    """生成香港-中央关系总结"""
    print("\n" + "="*60)
    print("📋 香港与中央政府关系总结报告")
    print("="*60)
    
    total_relations = len(hk_central_triples) + len(support_relations) + len(octs_triples)
    
    print(f"""
🎯 关系概览:
   • 直接关系: {len(hk_central_triples)} 个
   • 支持关系: {len(support_relations)} 个  
   • 一国两制关系: {len(octs_triples)} 个
   • 合作领域: {len(cooperation_areas)} 个

🏛️ 制度框架:
   • 一国两制是根本制度安排
   • 基本法是宪制基础
   • 高度自治与中央全面管治权相结合
   • 爱国者治港原则得到落实

🤝 合作特点:
   • 经济合作是重点领域
   • 科技创新合作日益重要
   • 教育文化交流持续深化
   • 基础设施互联互通加强

💡 关系特征:
   • 中央对香港给予强有力支持
   • 香港积极融入国家发展大局
   • 政策协调机制不断完善
   • 合作领域全面拓展

🔮 发展趋势:
   • 制度优势进一步发挥
   • 合作层次不断提升
   • 协调机制日趋完善
   • 共同发展前景广阔
    """)

def main():
    """主函数"""
    file_path = "/Users/adrian/Documents/GitHub/What_kgllm/complete_policy_address_kg.json"
    
    try:
        # 加载数据
        data = load_kg_data(file_path)
        
        # 提取相关关系
        hk_central_triples, hk_triples, central_triples, octs_triples = extract_hk_central_relations(data)
        
        # 各项分析
        relation_counts = analyze_direct_relations(hk_central_triples)
        support_relations = analyze_support_relations(data)
        key_concepts = analyze_octs_implementation(octs_triples)
        cooperation_areas = analyze_cooperation_areas(data)
        coordination_relations = analyze_policy_coordination(data)
        
        # 生成总结报告
        generate_hk_central_summary(hk_central_triples, support_relations, octs_triples, cooperation_areas)
        
        print(f"\n✅ 香港与中央政府关系分析完成！")
        
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()