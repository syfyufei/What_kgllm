#!/usr/bin/env python3
"""
香港施政报告数据处理器
功能：
1. 提取PDF和XML格式的施政报告文本
2. 统一格式并转换为简体中文
3. 生成标准化的文本文件供知识图谱分析使用
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# 导入所需的库
try:
    import PyPDF2
    import pdfplumber
    HAS_PDF_LIBS = True
except ImportError:
    print("⚠️  PDF处理库未安装，将跳过PDF文件处理")
    print("   安装命令: pip install PyPDF2 pdfplumber")
    HAS_PDF_LIBS = False

try:
    from opencc import OpenCC
    HAS_OPENCC = True
except ImportError:
    print("⚠️  OpenCC未安装，将跳过繁简转换")
    print("   安装命令: pip install opencc-python-reimplemented")
    HAS_OPENCC = False

class PolicyAddressProcessor:
    """施政报告处理器"""

    def __init__(self, source_dir="data/pa", output_dir="policy_data/raw_texts"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化繁简转换器
        if HAS_OPENCC:
            self.converter = OpenCC('t2s')  # 繁体转简体
        else:
            self.converter = None

        # 存储处理结果
        self.processing_log = []

    def convert_to_simplified(self, text: str) -> str:
        """将繁体中文转换为简体中文"""
        if self.converter and text:
            try:
                return self.converter.convert(text)
            except Exception as e:
                print(f"⚠️  繁简转换失败: {str(e)}")
                return text
        return text

    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除页码和页眉页脚模式
        text = re.sub(r'第\s*\d+\s*页', '', text)
        text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)

        # 移除重复的分隔符
        text = re.sub(r'-{3,}', '---', text)
        text = re.sub(r'={3,}', '===', text)

        # 移除多余的换行符
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 清理首尾空白
        text = text.strip()

        return text

    def extract_from_xml(self, file_path: Path) -> str:
        """从XML文件提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 处理XML格式
            if content.startswith('<?xml'):
                # 标准XML格式
                try:
                    root = ET.fromstring(content)
                    # 提取所有文本内容
                    text_parts = []
                    for elem in root.iter():
                        if elem.text and elem.text.strip():
                            text_parts.append(elem.text.strip())
                        if elem.tail and elem.tail.strip():
                            text_parts.append(elem.tail.strip())

                    text = '\n'.join(text_parts)
                except ET.ParseError:
                    # 如果XML解析失败，直接提取文本
                    text = re.sub(r'<[^>]+>', '', content)
            else:
                # 纯文本格式
                text = content

            return self.clean_text(text)

        except Exception as e:
            print(f"❌ XML提取失败 {file_path}: {str(e)}")
            return ""

    def extract_from_pdf(self, file_path: Path) -> str:
        """从PDF文件提取文本"""
        if not HAS_PDF_LIBS:
            print(f"⚠️  跳过PDF文件 {file_path.name}（缺少PDF处理库）")
            return ""

        text = ""

        # 尝试使用pdfplumber提取
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if text.strip():
                return self.clean_text(text)
        except Exception as e:
            print(f"⚠️  pdfplumber提取失败: {str(e)}")

        # 备用方案：使用PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            return self.clean_text(text)

        except Exception as e:
            print(f"❌ PDF提取失败 {file_path}: {str(e)}")
            return ""

    def extract_year_from_filename(self, filename: str) -> Optional[int]:
        """从文件名提取年份"""
        # 匹配年份模式
        patterns = [
            r'pa(\d{4})\.(?:xml|pdf)',  # pa1997.xml, pa2024.pdf
            r'PA(\d{4})\.pdf',          # PA2013.pdf
            r'pa(\d{4})(\d{2})\.pdf'    # pa200502.pdf (特殊情况)
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                # 处理特殊情况 pa200502.pdf
                if len(match.groups()) > 1 and match.group(2):
                    # 这是2005年的第二份报告，我们标记为2005
                    pass
                return year

        return None

    def process_single_file(self, file_path: Path) -> bool:
        """处理单个文件"""
        print(f"📄 处理文件: {file_path.name}")

        # 提取年份
        year = self.extract_year_from_filename(file_path.name)
        if not year:
            print(f"❌ 无法从文件名提取年份: {file_path.name}")
            return False

        # 提取文本内容
        if file_path.suffix.lower() == '.xml':
            text = self.extract_from_xml(file_path)
        elif file_path.suffix.lower() == '.pdf':
            text = self.extract_from_pdf(file_path)
        else:
            print(f"❌ 不支持的文件格式: {file_path.name}")
            return False

        if not text or len(text.strip()) < 100:
            print(f"❌ 提取的文本内容过少: {file_path.name}")
            return False

        # 转换为简体中文
        simplified_text = self.convert_to_simplified(text)

        # 添加标题和元信息
        header = f"香港特别行政区行政长官{year}年施政报告\n\n"
        final_text = header + simplified_text

        # 保存到输出文件
        output_file = self.output_dir / f"policy_address_{year}.txt"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_text)

            # 记录处理结果
            result = {
                'year': year,
                'source_file': str(file_path),
                'output_file': str(output_file),
                'text_length': len(final_text),
                'status': 'success'
            }
            self.processing_log.append(result)

            print(f"✅ {year}年施政报告处理完成 ({len(final_text):,} 字符)")
            return True

        except Exception as e:
            print(f"❌ 保存文件失败 {output_file}: {str(e)}")
            return False

    def process_all_files(self):
        """处理所有文件"""
        print("🚀 开始处理香港施政报告数据")
        print("="*60)

        if not self.source_dir.exists():
            print(f"❌ 源数据目录不存在: {self.source_dir}")
            return

        # 获取所有文件
        files = list(self.source_dir.glob("*.xml")) + list(self.source_dir.glob("*.pdf"))
        files.sort()

        if not files:
            print(f"❌ 在 {self.source_dir} 中未找到任何XML或PDF文件")
            return

        print(f"📁 找到 {len(files)} 个文件")

        # 处理每个文件
        success_count = 0
        for file_path in files:
            if self.process_single_file(file_path):
                success_count += 1
            print()  # 空行分隔

        # 生成处理报告
        self.generate_processing_report(success_count, len(files))

    def generate_processing_report(self, success_count: int, total_count: int):
        """生成处理报告"""
        print("="*60)
        print("📊 数据处理完成报告")
        print("="*60)

        print(f"总文件数: {total_count}")
        print(f"成功处理: {success_count}")
        print(f"失败数量: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")

        if self.processing_log:
            # 按年份排序
            successful_files = [log for log in self.processing_log if log['status'] == 'success']
            successful_files.sort(key=lambda x: x['year'])

            print(f"\n📋 成功处理的文件:")
            for log in successful_files:
                print(f"  {log['year']}年: {log['text_length']:,} 字符")

            # 保存处理日志
            log_file = self.output_dir.parent / "processing_log.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.processing_log, f, ensure_ascii=False, indent=2)
            print(f"\n📄 处理日志已保存: {log_file}")

        print(f"\n📁 输出目录: {self.output_dir}")
        print("✅ 数据处理完成！")

    def check_output_files(self):
        """检查输出文件"""
        print("🔍 检查输出文件...")

        output_files = list(self.output_dir.glob("policy_address_*.txt"))
        output_files.sort()

        if not output_files:
            print("❌ 未找到任何输出文件")
            return

        print(f"📁 找到 {len(output_files)} 个输出文件:")

        for file_path in output_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取年份
                year_match = re.search(r'policy_address_(\d{4})\.txt', file_path.name)
                year = year_match.group(1) if year_match else "未知"

                print(f"  ✅ {year}年: {len(content):,} 字符")

            except Exception as e:
                print(f"  ❌ {file_path.name}: 读取失败 - {str(e)}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='香港施政报告数据处理器')
    parser.add_argument('--source', default='data/pa', help='源数据目录')
    parser.add_argument('--output', default='policy_data/raw_texts', help='输出目录')
    parser.add_argument('--check', action='store_true', help='检查输出文件')

    args = parser.parse_args()

    processor = PolicyAddressProcessor(args.source, args.output)

    if args.check:
        processor.check_output_files()
    else:
        processor.process_all_files()

if __name__ == "__main__":
    main()
