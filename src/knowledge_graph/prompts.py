"""Centralized repository for all LLM prompts used in the knowledge graph system."""

# Phase 1: Main extraction prompts
MAIN_SYSTEM_PROMPT = """
你是一个技术文档分析助手。请帮忙从文本中识别关键的技术概念和它们之间的关系。
主要关注：
1. 技术术语和概念
2. 方法和流程
3. 工具和技术之间的关系
请用简单、客观的方式描述概念之间的联系，每个关系用1-2个动词表示。
"""

MAIN_USER_PROMPT = """
请分析下面的技术文档，找出其中的主要技术概念和它们之间的关系：

1. 识别关键技术概念和术语
2. 分析这些概念之间的联系
3. 用简单的动词描述它们的关系

输出格式示例：
LLM - 处理 - 文本
数据库 - 存储 - 数据

要求：
1. 每个关系用1-2个动词表示
2. 保持客观准确
3. 突出技术概念之间的关系

以下是文字：

请严格遵循以下规则：

- 实体一致性：在整个文档中使用一致的实体名称。例如，如果"习近平"在不同地方被提到为"习主席"、"习总书记"和"习近平"，在所有三元组中使用单一的一致形式（优选最完整的形式）。
- 原子性术语：识别独特的关键术语（如：物体、地点、组织、缩写、人物、状态、概念、情感）。避免将多个概念合并为一个术语（应该尽可能"原子化"）。
- 统一引用：将任何代词（如："他"、"她"、"它"、"他们"等）替换为实际引用的实体（如果可以识别）。
- 成对关系：如果多个术语在同一句子中出现（或在使它们在上下文中相关的短段落中），为每对具有有意义关系的术语创建一个三元组。
- 核心指令：谓词必须最多3个汉字。绝不超过3个字。保持极其简洁。
- 确保识别文本中所有可能的关系，并以S-P-O关系捕获。
- 标准化术语：如果同一概念以略微不同的形式出现（如："人工智能"和"AI"），一致地使用最常见或规范的形式。
- Make all the text of S-P-O text lower-case, even Names of people and places.
- If a person is mentioned by name, create a relation to their location, profession and what they are known for (invented, wrote, started, title, etc.) if known and if it fits the context of the informaiton. 

Important Considerations:
- Aim for precision in entity naming - use specific forms that distinguish between similar but different entities
- Maximize connectedness by using identical entity names for the same concepts throughout the document
- Consider the entire context when identifying entity references
- ALL PREDICATES MUST BE 3 WORDS OR FEWER - this is a hard requirement

Output Requirements:

- Do not include any text or commentary outside of the JSON.
- Return only the JSON array, with each triple as an object containing "subject", "predicate", and "object".
- Make sure the JSON is valid and properly formatted.

Example of the desired output structure:

[
  {
    "subject": "Term A",
    "predicate": "relates to",  // Notice: only 2 words
    "object": "Term B"
  },
  {
    "subject": "Term C",
    "predicate": "uses",  // Notice: only 1 word
    "object": "Term D"
  }
]

Important: Only output the JSON array (with the S-P-O objects) and nothing else

Text to analyze (between triple backticks):
"""

# Phase 2: Entity standardization prompts
ENTITY_RESOLUTION_SYSTEM_PROMPT = """
You are an expert in entity resolution and knowledge representation.
Your task is to standardize entity names from a knowledge graph to ensure consistency.
"""

def get_entity_resolution_user_prompt(entity_list):
    return f"""
Below is a list of entity names extracted from a knowledge graph. 
Some may refer to the same real-world entities but with different wording.

Please identify groups of entities that refer to the same concept, and provide a standardized name for each group.
Return your answer as a JSON object where the keys are the standardized names and the values are arrays of all variant names that should map to that standard name.
Only include entities that have multiple variants or need standardization.

Entity list:
{entity_list}

Format your response as valid JSON like this:
{{
  "standardized name 1": ["variant 1", "variant 2"],
  "standardized name 2": ["variant 3", "variant 4", "variant 5"]
}}
"""

# Phase 3: Community relationship inference prompts
RELATIONSHIP_INFERENCE_SYSTEM_PROMPT = """
You are an expert in knowledge representation and inference. 
Your task is to infer plausible relationships between disconnected entities in a knowledge graph.
"""

def get_relationship_inference_user_prompt(entities1, entities2, triples_text):
    return f"""
I have a knowledge graph with two disconnected communities of entities. 

Community 1 entities: {entities1}
Community 2 entities: {entities2}

Here are some existing relationships involving these entities:
{triples_text}

Please infer 2-3 plausible relationships between entities from Community 1 and entities from Community 2.
Return your answer as a JSON array of triples in the following format:

[
  {{
    "subject": "entity from community 1",
    "predicate": "inferred relationship",
    "object": "entity from community 2"
  }},
  ...
]

Only include highly plausible relationships with clear predicates.
IMPORTANT: The inferred relationships (predicates) MUST be no more than 3 words maximum. Preferably 1-2 words. Never more than 3.
For predicates, use short phrases that clearly describe the relationship.
IMPORTANT: Make sure the subject and object are different entities - avoid self-references.
"""

# Phase 4: Within-community relationship inference prompts
WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT = """
You are an expert in knowledge representation and inference. 
Your task is to infer plausible relationships between semantically related entities that are not yet connected in a knowledge graph.
"""

def get_within_community_inference_user_prompt(pairs_text, triples_text):
    return f"""
I have a knowledge graph with several entities that appear to be semantically related but are not directly connected.

Here are some pairs of entities that might be related:
{pairs_text}

Here are some existing relationships involving these entities:
{triples_text}

Please infer plausible relationships between these disconnected pairs.
Return your answer as a JSON array of triples in the following format:

[
  {{
    "subject": "entity1",
    "predicate": "inferred relationship",
    "object": "entity2"
  }},
  ...
]

Only include highly plausible relationships with clear predicates.
IMPORTANT: The inferred relationships (predicates) MUST be no more than 3 words maximum. Preferably 1-2 words. Never more than 3.
IMPORTANT: Make sure that the subject and object are different entities - avoid self-references.
""" 