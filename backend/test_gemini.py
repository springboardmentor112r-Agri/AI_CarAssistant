from dotenv import load_dotenv
load_dotenv()
import os
from google import genai

c = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
r = c.models.generate_content(model='gemini-2.0-flash-lite', contents='Say hello')
print(r.text)