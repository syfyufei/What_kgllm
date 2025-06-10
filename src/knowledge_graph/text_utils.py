"""
Text processing utilities for the knowledge graph generator.
"""
import re

def split_into_sentences(text):
    """将文本分割成句子"""
    # 基本句子结束的正则模式
    text = re.sub('([。!?！？])([^"\'"])', '\\1\n\\2', text)
    # 省略号(6个点)结束的句子
    text = re.sub('(\\.{6})([^"\'"])', '\\1\n\\2', text)
    # 省略号(3个点)结束的句子
    text = re.sub('(\\.{3})([^"\'"])', '\\1\n\\2', text)
    # 引号结束的句子
    text = re.sub('([。!?！？]["\'])([^，。！？!?])', '\\1\n\\2', text)
    return [s.strip() for s in text.split('\n') if s.strip()]

def count_words(text):
    """统计词数，支持中英文"""
    # 英文按空格分词
    english_words = len(text.split())
    # 中文字符计数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return english_words + chinese_chars

def chunk_text(text, max_length=200, overlap=20, respect_sentences=True, respect_paragraphs=True):
    """
    智能分块处理文本，支持中英文，保持句子和段落的完整性。
    
    Args:
        text: 要处理的输入文本
        max_length: 每个块的最大词数
        overlap: 块之间的重叠词数
        respect_sentences: 是否在句子边界处分块
        respect_paragraphs: 是否优先在段落边界处分块
        
    Returns:
        文本块列表
    """
    # 处理空文本
    if not text or not text.strip():
        return []

    # 按段落分割
    if respect_paragraphs:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    else:
        paragraphs = [text]

    chunks = []
    current_chunk = []
    current_length = 0
    last_sentences = []  # 用于存储overlap部分的句子

    for paragraph in paragraphs:
        sentences = split_into_sentences(paragraph) if respect_sentences else [paragraph]
        
        for sentence in sentences:
            sentence_length = count_words(sentence)
            
            # 如果单个句子超过最大长度，强制分割
            if sentence_length > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    last_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                chunks.append(sentence)
                current_chunk = []
                current_length = 0
                continue
            
            # 检查是否需要创建新的块
            if current_length + sentence_length > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    last_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                    # 添加重叠部分
                    current_chunk = last_sentences if overlap > 0 else []
                    current_length = sum(count_words(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_length

    # 处理最后一个块
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def normalize_text(text):
    """
    规范化文本，进行基本的清理和标准化处理。
    
    Args:
        text: 输入文本字符串
        
    Returns:
        规范化后的文本
    """
    if not text:
        return ""
        
    # 统一换行符
    text = re.sub(r'[\r\n]+', '\n', text)
    
    # 删除连续的空格
    text = re.sub(r'\s+', ' ', text)
    
    # 修复常见的标点符号问题
    text = re.sub(r'[\u200b\ufeff]', '', text)  # 删除零宽空格
    text = re.sub(r'[""]', '"', text)  # 统一引号
    text = re.sub(r'['']', "'", text)  # 统一单引号
    text = re.sub(r'\.{3,}', '...', text)  # 统一省略号
    
    # 确保句子之间有适当的空格
    text = re.sub(r'([。!?！？])\s*([^"\'\n])', r'\1 \2', text)
    
    return text.strip()