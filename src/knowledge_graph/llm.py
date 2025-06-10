"""LLM interaction utilities for knowledge graph generation."""
import requests
import json
import re

def call_llm(model, user_prompt, api_key, system_prompt=None, max_tokens=1000, temperature=1.0, base_url=None) -> str:
    """
    调用语言模型 API。
    
    Args:
        model: 要使用的模型名称
        user_prompt: 用户提示
        api_key: API 认证密钥
        system_prompt: 可选的系统提示
        max_tokens: 最大生成令牌数
        temperature: 采样温度
        base_url: API 端点的基础 URL
        
    Returns:
        模型的响应字符串
    """
    # 根据API类型设置Authorization头格式
    if base_url and 'sankuai.com' in base_url:
        # 美团API使用Bearer格式
        auth_header = f'Bearer {api_key}'
    elif api_key.startswith('sk-'):
        # OpenAI格式使用Bearer
        auth_header = f'Bearer {api_key}'
    else:
        # 其他格式
        auth_header = api_key

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth_header
    }
    
    # 构建消息
    messages = []
    if system_prompt:
        messages.append({
            'role': 'system',
            'content': system_prompt
        })
    
    messages.append({
        'role': 'user',
        'content': user_prompt
    })
    
    # 构建请求负载
    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stream': False  # 关闭流式输出以简化处理
    }
    
    try:
        print(f"正在调用LLM API: {base_url}")
        print(f"使用模型: {model}")
        print(f"Authorization: Bearer {api_key[:10]}...")  # 显示Bearer格式

        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"API响应状态码: {response.status_code}")

        if response.status_code == 200:
            resp_json = response.json()
            print(f"API响应结构: {list(resp_json.keys())}")

            # 标准OpenAI格式（包括美团API）
            if 'choices' in resp_json and len(resp_json['choices']) > 0:
                content = resp_json['choices'][0]['message']['content']
                print(f"✅ 成功获取LLM响应，长度: {len(content)} 字符")
                return content
            # MiniMax格式
            elif 'reply' in resp_json:
                print(f"✅ 成功获取LLM响应 (MiniMax格式)，长度: {len(resp_json['reply'])} 字符")
                return resp_json['reply']
            # 其他格式
            else:
                print(f"❌ 无法从API响应中提取内容，响应格式: {resp_json}")
                return None
        elif response.status_code == 429:
            print("❌ API请求频率超限，请稍后重试")
            return None
        else:
            print(f"❌ LLM API调用失败，状态码: {response.status_code}")
            print(f"错误响应: {response.text[:500]}...")
            return None

    except requests.exceptions.Timeout:
        print("❌ LLM API调用超时")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到LLM API服务器")
        return None
    except Exception as e:
        print(f"❌ 调用API时出错: {str(e)}")
        return None

def extract_json_from_text(text):
    """
    Extract JSON array from text that might contain additional content.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        The parsed JSON if found, None otherwise
    """
    # First, check if the text is wrapped in code blocks with triple backticks
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    code_match = re.search(code_block_pattern, text)
    if code_match:
        text = code_match.group(1).strip()
        print("Found JSON in code block, extracting content...")
    
    try:
        # Try direct parsing in case the response is already clean JSON
        return json.loads(text)
    except json.JSONDecodeError:
        # Look for opening and closing brackets of a JSON array
        start_idx = text.find('[')
        if start_idx == -1:
            print("No JSON array start found in text")
            return None
            
        # Simple bracket counting to find matching closing bracket
        bracket_count = 0
        complete_json = False
        for i in range(start_idx, len(text)):
            if text[i] == '[':
                bracket_count += 1
            elif text[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    # Found the matching closing bracket
                    json_str = text[start_idx:i+1]
                    complete_json = True
                    break
        
        # Handle complete JSON array
        if complete_json:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print("Found JSON-like structure but couldn't parse it.")
                print("Trying to fix common formatting issues...")
                
                # Try to fix missing quotes around keys
                fixed_json = re.sub(r'(\s*)(\w+)(\s*):(\s*)', r'\1"\2"\3:\4', json_str)
                # Fix trailing commas
                fixed_json = re.sub(r',(\s*[\]}])', r'\1', fixed_json)
                
                try:
                    return json.loads(fixed_json)
                except:
                    print("Could not fix JSON format issues")
        else:
            # Handle incomplete JSON - try to complete it
            print("Found incomplete JSON array, attempting to complete it...")
            
            # Get all complete objects from the array
            objects = []
            obj_start = -1
            obj_end = -1
            brace_count = 0
            
            # First find all complete objects
            for i in range(start_idx + 1, len(text)):
                if text[i] == '{':
                    if brace_count == 0:
                        obj_start = i
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        obj_end = i
                        objects.append(text[obj_start:obj_end+1])
            
            if objects:
                # Reconstruct a valid JSON array with complete objects
                reconstructed_json = "[\n" + ",\n".join(objects) + "\n]"
                try:
                    return json.loads(reconstructed_json)
                except json.JSONDecodeError:
                    print("Couldn't parse reconstructed JSON array.")
                    print("Trying to fix common formatting issues...")
                    
                    # Try to fix missing quotes around keys
                    fixed_json = re.sub(r'(\s*)(\w+)(\s*):(\s*)', r'\1"\2"\3:\4', reconstructed_json)
                    # Fix trailing commas
                    fixed_json = re.sub(r',(\s*[\]}])', r'\1', fixed_json)
                    
                    try:
                        return json.loads(fixed_json)
                    except:
                        print("Could not fix JSON format issues in reconstructed array")
            
        print("No complete JSON array could be extracted")
        return None