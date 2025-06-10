import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import sys
sys.path.append('/Users/adrian/Documents/GitHub/sailor_algorithm_intelligence/What_kgllm/src')
from knowledge_graph.main import create_knowledge_graph

def fetch_policy_data(url):
    """获取施政报告XML数据"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def parse_xml_to_text(xml_content):
    """解析XML内容并提取文本"""
    try:
        soup = BeautifulSoup(xml_content, 'lxml-xml')
        
        # 提取所有段落文本
        paragraphs = []
        
        # 获取标题
        title = soup.find('title')
        if title and title.text.strip():
            paragraphs.append(f"标题：{title.text.strip()}")
        
        # 获取所有段落
        for para in soup.find_all(['para', 'bullet']):
            if para.text and para.text.strip():
                paragraphs.append(para.text.strip())
        
        return "\n\n".join(paragraphs)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

def main():
    url = "https://www.ceo.gov.hk/public/open-data/sc/policy_address/pa2024.xml"
    xml_content = fetch_policy_data(url)
    
    if xml_content:
        text_content = parse_xml_to_text(xml_content)
        if text_content:
            # 保存处理后的文本
            with open("data/policy_address_2024.txt", "w", encoding="utf-8") as f:
                f.write(text_content)
            
            # 使用项目的知识图谱生成功能
            create_knowledge_graph(text_content, "政策分析")
            print("知识图谱生成完成！")
        else:
            print("无法解析XML内容")
    else:
        print("无法获取数据")

if __name__ == "__main__":
    main()
