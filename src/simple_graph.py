"""知识图谱生成工具"""
import os
import sys
from knowledge_graph.config import load_config
from knowledge_graph.text_utils import chunk_text
from knowledge_graph.llm import call_llm
from knowledge_graph.visualization import visualize_knowledge_graph

def analyze_text(text, title="知识图谱", debug=False):
    """分析文本并生成知识图谱"""
    # 加载配置
    config = load_config()
    
    # 分块处理文本
    chunks = chunk_text(text, max_length=200)
    all_triples = []
    
    print(f"开始处理{len(chunks)}个文本块...")
    
    # 处理每个文本块
    for i, chunk in enumerate(chunks):
        print(f"处理第{i+1}个文本块...")
        
        # 调用LLM处理
        response = call_llm(
            model=config["llm"]["model"],
            user_prompt=chunk,
            api_key=config["llm"]["api_key"],
            system_prompt="请分析文本中的关键概念和它们之间的关系",
            max_tokens=1000,
            temperature=1.0,
            base_url=config["llm"]["base_url"]
        )
        
        if response:
            # 简单解析响应
            lines = response.split('\n')
            for line in lines:
                if ' - ' in line:
                    parts = line.split(' - ')
                    if len(parts) == 3:
                        triple = {
                            'subject': parts[0].strip(),
                            'predicate': parts[1].strip(),
                            'object': parts[2].strip()
                        }
                        all_triples.append(triple)
    
    if all_triples:
        # 生成可视化
        output_path = visualize_knowledge_graph(all_triples, title=title)
        return output_path
    else:
        print("未能提取任何关系")
        return None

def main():
    # 读取文本文件
    with open("data/tech_article.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # 生成知识图谱
    output_path = analyze_text(text, "技术概念图谱")
    if output_path:
        print(f"知识图谱已生成：{output_path}")
    else:
        print("生成图谱失败")

if __name__ == "__main__":
    main()
