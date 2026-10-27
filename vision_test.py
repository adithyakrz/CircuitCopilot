import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.meta.ai/v1",
    api_key=os.environ.get("MODEL_API_KEY"),
)

IMAGE_PATH = Path("test.png")

if not IMAGE_PATH.exists():
    raise FileNotFoundError("Please save the image before running!")

with open(IMAGE_PATH, "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")
print("Sending circuit to Muse Spark 1.3 for automated hardware diagnostics...")

response = client.responses.create(
    model="muse-spark-1.3",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "You are an expert embedded systems diagnostic engineer. "
                        "Examine this circuit diagram image in detail:\n"
                        "1. Identify the microcontroller board and the connected components.\n"
                        "2. Trace each digital pin and ground connection (which Arduino pins go where).\n"
                        "3. Evaluate the safety of the circuit (are current-limiting resistors present? Are polarities correct?)\n"
                        "4. Provide a structured diagnostic summary: Status (PASS / WARN / FAIL), detected wiring table, and any recommendations."
                    ),
                },
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{base64_image}",
                },
            ],
        }
    ],
)

print("\n------Response-----------\n")
print(response.output_text)