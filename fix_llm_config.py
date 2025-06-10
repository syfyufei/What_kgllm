#!/usr/bin/env python3
"""帮助配置LLM设置的脚本"""

def show_llm_config_options():
    """显示可用的LLM配置选项"""
    
    print("=== LLM配置选项 ===\n")
    
    print("1. 使用OpenAI API:")
    print("""
[llm]
model = "gpt-3.5-turbo"
api_key = "sk-your-openai-api-key"
base_url = "https://api.openai.com/v1/chat/completions"
max_tokens = 4096
temperature = 0.2
""")
    
    print("2. 使用本地Ollama:")
    print("""
[llm]
model = "qwen2:7b"
api_key = "ollama"
base_url = "http://localhost:11434/v1/chat/completions"
max_tokens = 4096
temperature = 0.2
""")
    
    print("3. 使用Azure OpenAI:")
    print("""
[llm]
model = "gpt-35-turbo"
api_key = "your-azure-api-key"
base_url = "https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15"
max_tokens = 4096
temperature = 0.2
""")
    
    print("4. 使用智谱AI (GLM):")
    print("""
[llm]
model = "glm-4"
api_key = "your-zhipu-api-key"
base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
max_tokens = 4096
temperature = 0.2
""")
    
    print("5. 使用阿里云通义千问:")
    print("""
[llm]
model = "qwen-turbo"
api_key = "your-dashscope-api-key"
base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
max_tokens = 4096
temperature = 0.2
""")

def test_llm_connection_guide():
    """LLM连接测试指南"""
    
    print("\n=== LLM连接测试指南 ===\n")
    
    print("1. 检查API密钥是否有效")
    print("2. 确认API端点URL正确")
    print("3. 检查网络连接")
    print("4. 验证模型名称")
    print("5. 确认请求格式符合API要求")
    
    print("\n常见问题解决:")
    print("- 404错误: API端点URL不正确")
    print("- 401错误: API密钥无效或过期")
    print("- 403错误: 没有访问权限")
    print("- 429错误: 请求频率过高")
    print("- 500错误: 服务器内部错误")

def create_test_config():
    """创建测试配置文件"""
    
    test_config = """# 测试配置文件 - 请根据你的实际情况修改

[llm]
# 选择你要使用的模型和API
model = "gpt-3.5-turbo"  # 或者 "qwen2:7b", "glm-4" 等
api_key = "your-api-key-here"  # 替换为你的真实API密钥
base_url = "https://api.openai.com/v1/chat/completions"  # 对应的API端点
max_tokens = 4096
temperature = 0.2

[chunking]
chunk_size = 100
overlap = 20

[standardization]
enabled = true
use_llm_for_entities = true

[inference]
enabled = true
use_llm_for_inference = true
apply_transitive = true

[visualization]
edge_smooth = "continuous"
dark_mode = false
node_size = 25
font_size = 14
edge_length = 200
physics_enabled = true
community_detection = true
"""
    
    with open("config_template.toml", "w", encoding="utf-8") as f:
        f.write(test_config)
    
    print("已创建配置模板文件: config_template.toml")
    print("请编辑此文件，填入你的真实API信息，然后重命名为 config.toml")

if __name__ == "__main__":
    show_llm_config_options()
    test_llm_connection_guide()
    create_test_config()