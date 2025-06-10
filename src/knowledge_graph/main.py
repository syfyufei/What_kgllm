"""
Knowledge Graph Generator and Visualizer main module.
"""
import argparse
import json
import os
import sys

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge_graph.config import load_config
from src.knowledge_graph.llm import call_llm, extract_json_from_text
from src.knowledge_graph.visualization import visualize_knowledge_graph, sample_data_visualization
from src.knowledge_graph.text_utils import chunk_text
from src.knowledge_graph.entity_standardization import standardize_entities, infer_relationships, limit_predicate_length
from src.knowledge_graph.prompts import MAIN_SYSTEM_PROMPT, MAIN_USER_PROMPT

def process_with_llm(config, input_text, debug=False):
    """
    处理输入文本，使用LLM提取三元组。
    
    Args:
        config: 配置字典
        input_text: 要分析的文本
        debug: 如果为True，打印详细调试信息
        
    Returns:
        提取的三元组列表，如果处理失败则返回None
    """
    try:
        # 使用专门的知识图谱提取提示
        system_prompt = "你是一个专业的知识图谱构建助手。请从文本中提取实体和关系，并以JSON格式返回。"

        user_prompt = f"""
        请从以下文本中提取实体和关系，并以JSON格式返回：

        文本：{input_text}

        请返回JSON数组格式，每个元素包含subject（主体）、predicate（关系）、object（客体）：
        [
            {{"subject": "实体1", "predicate": "关系", "object": "实体2"}},
            {{"subject": "实体3", "predicate": "关系", "object": "实体4"}}
        ]

        要求：
        1. 关系词（predicate）最多3个字
        2. 只返回JSON数组，不要其他内容
        3. 确保JSON格式正确
    """

        # LLM配置
        model = config["llm"]["model"]
        api_key = config["llm"]["api_key"]
        max_tokens = config["llm"]["max_tokens"]
        temperature = config["llm"]["temperature"]
        base_url = config["llm"]["base_url"]
        
        if debug:
            print(f"发送给LLM的提示:\n{user_prompt[:200]}...")

        # 处理文本
        response = call_llm(model, user_prompt, api_key, system_prompt, max_tokens, temperature, base_url)
        
        if response is None:
            print("LLM API调用失败")
            return None
        
        if debug:
            print(f"LLM原始响应:\n{response}")
            
        # 从响应中提取JSON
        triples = extract_json_from_text(response)
            
        if triples is None:
            print("无法从LLM响应中提取JSON")
            return None
            
        # 验证提取的三元组格式
        valid_triples = []
        for triple in triples:
            if isinstance(triple, dict) and 'subject' in triple and 'predicate' in triple and 'object' in triple:
                valid_triples.append({
                    'subject': str(triple['subject']).strip(),
                    'predicate': str(triple['predicate']).strip(),
                    'object': str(triple['object']).strip()
                })

        if debug:
            print(f"提取的有效三元组数量: {len(valid_triples)}")
            for i, triple in enumerate(valid_triples[:5]):  # 只显示前5个
                print(f"  {i+1}. {triple}")

        return valid_triples
    except Exception as e:
        print(f"处理文本时出错: {str(e)}")
        return None

def process_text_in_chunks(config, full_text, debug=False):
    """
    Process a large text by breaking it into chunks with overlap,
    and then processing each chunk separately.
    
    Args:
        config: Configuration dictionary
        full_text: The complete text to process
        debug: If True, print detailed debug information
    
    Returns:
        List of all extracted triples from all chunks
    """
    # Get chunking parameters from config
    chunk_size = config.get("chunking", {}).get("chunk_size", 500)
    overlap = config.get("chunking", {}).get("overlap", 50)
    
    # Split text into chunks
    text_chunks = chunk_text(full_text, chunk_size, overlap)
    
    print("=" * 50)
    print("PHASE 1: INITIAL TRIPLE EXTRACTION")
    print("=" * 50)
    print(f"Processing text in {len(text_chunks)} chunks (size: {chunk_size} words, overlap: {overlap} words)")
    
    # Process each chunk
    all_results = []
    for i, chunk in enumerate(text_chunks):
        print(f"Processing chunk {i+1}/{len(text_chunks)} ({len(chunk.split())} words)")
        
        # Process the chunk with LLM
        chunk_results = process_with_llm(config, chunk, debug)
        if chunk_results:
            # Add chunk information to each triple
            for item in chunk_results:
                item["chunk"] = i + 1
            
            # Add to overall results
            all_results.extend(chunk_results)
        else:
            print(f"Warning: Failed to extract triples from chunk {i+1}")
    
    print(f"\nExtracted a total of {len(all_results)} triples from all chunks")
    
    # Apply entity standardization if enabled
    if config.get("standardization", {}).get("enabled", False):
        print("\n" + "="*50)
        print("PHASE 2: ENTITY STANDARDIZATION")
        print("="*50)
        print(f"Starting with {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")
        
        all_results = standardize_entities(all_results, config)
        
        print(f"After standardization: {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")
    
    # Apply relationship inference if enabled
    if config.get("inference", {}).get("enabled", False):
        print("\n" + "="*50)
        print("PHASE 3: RELATIONSHIP INFERENCE")
        print("="*50)
        print(f"Starting with {len(all_results)} triples")
        
        # Count existing relationships
        relationship_counts = {}
        for triple in all_results:
            relationship_counts[triple["predicate"]] = relationship_counts.get(triple["predicate"], 0) + 1
        
        print("Top 5 relationship types before inference:")
        for pred, count in sorted(relationship_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")
        
        all_results = infer_relationships(all_results, config)
        
        # Count relationships after inference
        relationship_counts_after = {}
        for triple in all_results:
            relationship_counts_after[triple["predicate"]] = relationship_counts_after.get(triple["predicate"], 0) + 1
        
        print("\nTop 5 relationship types after inference:")
        for pred, count in sorted(relationship_counts_after.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")
        
        # Count inferred relationships
        inferred_count = sum(1 for triple in all_results if triple.get("inferred", False))
        print(f"\nAdded {inferred_count} inferred relationships")
        print(f"Final knowledge graph: {len(all_results)} triples")
    
    return all_results

def get_unique_entities(triples):
    """
    Get the set of unique entities from the triples.
    
    Args:
        triples: List of triple dictionaries
        
    Returns:
        Set of unique entity names
    """
    entities = set()
    for triple in triples:
        if not isinstance(triple, dict):
            continue
        if "subject" in triple:
            entities.add(triple["subject"])
        if "object" in triple:
            entities.add(triple["object"])
    return entities

def create_knowledge_graph(text, title="Knowledge Graph", debug=False):
    """
    Create a knowledge graph from input text.
    
    Args:
        text: Input text to analyze
        title: Title for the visualization
        debug: If True, print debug information
        
    Returns:
        Path to the generated HTML file
    """
    # Load configuration
    config = load_config()
    
    # Process text chunks
    chunks = chunk_text(text, max_length=2000)
    all_triples = []
    
    for chunk in chunks:
        # Process each chunk with LLM
        chunk_triples = process_with_llm(config, chunk, debug=debug)
        if chunk_triples:
            all_triples.extend(chunk_triples)
    
    if not all_triples:
        print("No triples extracted from text")
        return None
    
    # Standardize and process triples
    standardized_triples = standardize_entities(all_triples)
    enhanced_triples = infer_relationships(standardized_triples)
    final_triples = limit_predicate_length(enhanced_triples)
    
    # Generate visualization
    output_path = visualize_knowledge_graph(final_triples, title=title)
    
    return output_path

def main():
    """Main entry point for the knowledge graph generator."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Knowledge Graph Generator and Visualizer')
    parser.add_argument('--test', action='store_true', help='Generate a test visualization with sample data')
    parser.add_argument('--config', type=str, default='config.toml', help='Path to configuration file')
    parser.add_argument('--output', type=str, default='knowledge_graph.html', help='Output HTML file path')
    parser.add_argument('--input', type=str, required=False, help='Path to input text file (required unless --test is used)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output (raw LLM responses and extracted JSON)')
    parser.add_argument('--no-standardize', action='store_true', help='Disable entity standardization')
    parser.add_argument('--no-inference', action='store_true', help='Disable relationship inference')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        print(f"Failed to load configuration from {args.config}. Exiting.")
        return
    
    # If test flag is provided, generate a sample visualization
    if args.test:
        print("Generating sample data visualization...")
        sample_data_visualization(args.output, config=config)
        print(f"\nSample visualization saved to {args.output}")
        print(f"To view the visualization, open the following file in your browser:")
        print(f"file://{os.path.abspath(args.output)}")
        return
    
    # For normal processing, input file is required
    if not args.input:
        print("Error: --input is required unless --test is used")
        parser.print_help()
        return
    
    # Override configuration settings with command line arguments
    if args.no_standardize:
        config.setdefault("standardization", {})["enabled"] = False
    if args.no_inference:
        config.setdefault("inference", {})["enabled"] = False
    
    # Load input text from file
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_text = f.read()
        print(f"Using input text from file: {args.input}")
    except Exception as e:
        print(f"Error reading input file {args.input}: {e}")
        return
    
    # Process text in chunks
    result = process_text_in_chunks(config, input_text, args.debug)
    
    if result:
        # Save the raw data as JSON for potential reuse
        json_output = args.output.replace('.html', '.json')
        try:
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Saved raw knowledge graph data to {json_output}")
        except Exception as e:
            print(f"Warning: Could not save raw data to {json_output}: {e}")
        
        # Visualize the knowledge graph
        stats = visualize_knowledge_graph(result, args.output, config=config)
        print("\nKnowledge Graph Statistics:")
        print(f"Nodes: {stats['nodes']}")
        print(f"Edges: {stats['edges']}")
        print(f"Communities: {stats['communities']}")
        
        # Provide command to open the visualization in a browser
        print("\nTo view the visualization, open the following file in your browser:")
        print(f"file://{os.path.abspath(args.output)}")
    else:
        print("Knowledge graph generation failed due to errors in LLM processing.")

if __name__ == "__main__":
    main()