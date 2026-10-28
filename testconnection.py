import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.environ.get("MODEL_API_KEY")

if not api_key:
    raise ValueError("MODEL_API_KEY is not set! Check your .env file or environment variable.")

client = OpenAI(
    base_url="https://api.meta.ai/v1",
    api_key=api_key,
)

print("Pinging Meta Muse Spark 1.3...")

response = client.responses.create(
    model="muse-spark-1.3",
    input="Respond with 'Connection successful! Ready to build'",
)

# You can access the direct text via response.output_text
print("\n--- Response ---")
print(response.output_text)