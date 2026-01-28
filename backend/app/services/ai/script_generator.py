import anthropic
from app.core.config import settings

class ScriptGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def generate(self, topic: str):
        prompt = f"Create a viral vertical video script for about '{topic}'. Use high-retention hooks and short sentences. Return only the script."
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
