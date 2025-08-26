import requests, os

class DoubaoLLM:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.environ.get("DOUBAO_API_KEY")
        self.api_endpoint = base_url or os.environ.get("DOUBAO_API_ENDPOINT")
        self.model = "volcengine/" + (model or os.environ.get("DOUBAO_MODEL", "doubao-seed-1-6-250615")) # add prefix "volcengine/" to model name to be inline with litellm usage

    def invoke(self, messages, model=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or self.model,
            "messages": messages
        }
        try:
            response = requests.post(
                url=self.api_endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Fail to invoke DOUBAO api: {str(e)}"

# llm = DoubaoLLM()
# messages = [
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "解释 CrewAI 的核心概念"}
# ]
# llm.invoke(messages=messages, model="doubao-seed-1-6-250615")