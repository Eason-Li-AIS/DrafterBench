import re
import litellm
from litellm import completion
from typing import List, Dict, Any
from openai import OpenAI

# litellm._turn_on_debug()

class Drafter_agent:
    def __init__(
        self,
        model: str,
        provider: str,
        temperature: float = 0.0,
        vllm_url: str = None,
    ):
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.vllm_url = vllm_url

    def get_response(self, messages: List[Dict[str, Any]]):
        generated_code = None
        trail = 0
        while not generated_code and trail < 10:
            if not self.vllm_url:
                res = completion(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )
            else:
                client = OpenAI( 
                    base_url=self.vllm_url  # litellm-proxy-base url
                )

                res = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=2500,
                    temperature=self.temperature
                )
            response = res.choices[0].message.content
            code_search = re.search(r"`python\s*([^`]+)`", response)
            generated_code = code_search.group(1) if code_search else None
            trail += 1
        return generated_code if generated_code else "Fail to generate code"
