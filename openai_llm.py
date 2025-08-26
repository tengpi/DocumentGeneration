import os
from openai import OpenAI

class OpenAILLM:
    def __init__(self, api_key=None, base_url=None, model=None):

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_API_BASE")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def invoke(self, messages, model=None):
        completion = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages
        )
        return completion.choices[0].message.content
    
# openai_llm = OpenAILLM(
#     api_key=cfg.openai_api_key,
#     base_url=cfg.openai_api_base,
#     model="gpt-3.5-turbo"  # 或 "gpt-4", "gpt-3.5-turbo" 等
# )

# result = openai_llm.invoke([
#     {"role": "system", "content": "You are a helpful assistant."},  
#     {"role": "user", "content": "解释 CrewAI 的核心概念"}
# ])

# print(result)