import json
from openai import OpenAI

class OpenAIUtil:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_summary(self, content: str) -> dict:
        messages = [
            {"role": "system", "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})"},
            {"role": "user", "content": content}
        ]
        response = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        result_text = response.choices[0].message.content.strip()
        try:
            result = json.loads(result_text)
            return {"summary": result.get("影響", ""), "reason": result.get("原因", "")}
        except json.JSONDecodeError:
            return {"summary": "", "reason": ""}

    def evaluate_relevance(self, title: str) -> str:
        messages = [
            {"role": "system", "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。"},
            {"role": "user", "content": title}
        ]
        response = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        return response.choices[0].message.content.strip()

    def extract_keywords(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": "你是一個關鍵字提取機器人，請提取出用戶希望看見的關鍵字，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。"},
            {"role": "user", "content": prompt}
        ]
        response = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        return response.choices[0].message.content
