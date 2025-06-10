"""测试知识图谱生成 - 技术文档分析"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_graph.main import create_knowledge_graph

def main():
    # 读取测试文本
    with open("data/tech_article.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # 生成知识图谱
    output_path = create_knowledge_graph(text, "技术概念图谱")
    
    if output_path:
        print(f"技术概念图谱已生成：{output_path}")
    else:
        print("生成图谱失败")

if __name__ == "__main__":
    main()
