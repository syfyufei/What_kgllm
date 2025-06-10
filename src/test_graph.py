"""测试知识图谱生成"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_graph.main import create_knowledge_graph

def main():
    # 读取测试文本
    with open("data/test.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # 生成知识图谱
    output_path = create_knowledge_graph(text, "概念关系图")
    
    if output_path:
        print(f"知识图谱已生成：{output_path}")
    else:
        print("生成知识图谱失败")

if __name__ == "__main__":
    main()
