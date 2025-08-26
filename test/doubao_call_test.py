from crewai.tools import BaseTool
from pydantic import BaseModel, Field  # 用于定义 Tool 的输入参数
import requests
import os
from config_parser import get_config

config = get_config()
cfg = config.get_config()

api_key = cfg.doubao_api_key
api_endpoint = cfg.doubao_api_endpoint

def test_run(query: str) -> str:  # 从参数接收query，而不是类属性
        """Tool 的核心执行逻辑：调用豆包 API 并返回结果"""
        try:
            # 获取API密钥和端点
            api_key = cfg.doubao_api_key
            api_endpoint = cfg.doubao_api_endpoint

            if not api_key or not api_endpoint:
                return "错误：未配置 DOUBAO_API_KEY 或 DOUBAO_API_ENDPOINT（请检查 .env 文件）"

            # 构造请求头
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 构造请求体
            payload = {
                "model": "doubao-seed-1-6-250615",
                "messages": [
                    {"role": "user", "content": query}  # 使用传入的query参数
                ]
            }

            # 发送请求
            response = requests.post(
                url=api_endpoint,
                headers=headers,
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            # 提取回答
            answer = result["choices"][0]["message"]["content"]
            return f"豆包的回答：\n{answer}"

        except requests.exceptions.RequestException as e:
            return f"调用豆包 API 失败：{str(e)}"
        except KeyError as e:
            return f"豆包 API 响应格式异常，缺少字段：{str(e)}"
        except Exception as e:
            return f"调用工具时发生未知错误：{str(e)}"
        

result = test_run("解释 CrewAI 的核心概念")
print(result)