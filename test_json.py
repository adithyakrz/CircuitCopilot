import base64
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.meta.ai/v1",
    api_key=os.environ.get("MODEL_API_KEY"),
)

IMAGE_PATH = Path("./Test_Images/NoResistorTest.png")

with open(IMAGE_PATH, "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")

expected_circuit = (
    "Arduino Uno Traffic Light Circuit (Tinkercad Simulation): "
    "- Microcontroller: Arduino Uno R3. "
    "- Three LEDs (Red, Yellow, Green) driven by 3 Arduino Digital Pins (D8, D7, and D4). "
    "- Each LED branch has a series current-limiting resistor (1k ohm or 220-330 ohm are acceptable). "
    "- Common ground return from the breadboard '-' rail to Arduino POWER GND."
)

prompt = f"""
You are an expert embedded systems diagnostic engineer.
Target Expected Circuit: {expected_circuit}

IMPORTANT 2D VISUAL INTERPRETATION RULES:
1. Insulated Wire Overlaps: In this 2D diagram, wires visually crossing over headers, power rails, or other wires are insulated jumpers. An overlap is NOT a solder bridge or short circuit unless a wire explicitly terminates into that pinhole.
2. Ground Returns: The long horizontal black wires originating from LED cathodes stretch across the breadboard and plug directly into the left '-' Ground rail holes (rows 1, 12, 23/24).
3. Wire Colors: Red wire connects D8, Yellow wire connects D7, Green wire connects D4.

Evaluate whether each LED branch completes a valid series path (Arduino Pin -> Resistor -> LED -> Ground rail -> Arduino GND) without destructive shorts[cite: 5].
Return ONLY a valid, raw JSON object (no markdown, no backticks, no text outside JSON).

Schema:
{{
  "circuit_name": "string",
  "status": "PASS" | "WARN" | "FAIL",
  "summary": "1-2 sentence overall verdict",
  "resistor_check": {{
    "detected_value": "string",
    "acceptable": true,
    "notes": "string"
  }},
  "pin_checks": [
    {{"pin": "string", "target_led": "Red | Yellow | Green", "status": "OK" | "ISSUE", "detail": "string"}}
  ],
  "safety": {{
    "short_circuit_risk": "NONE" | "LOW" | "HIGH",
    "power_rail_grounded": true,
    "notes": "string"
  }},
  "action_items": [
    "string"
  ]
}}
"""

print("Running structured diagnostic check with Muse Spark 1.3...")

response = client.responses.create(
    model="muse-spark-1.3",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/png;base64,{base64_image}"},
            ],
        }
    ],
)

raw_output = response.output_text.strip()

if raw_output.startswith("```"):
    raw_output = raw_output.strip("`")
    if raw_output.startswith("json"):
        raw_output = raw_output[4:].strip()

try:
    parsed_json = json.loads(raw_output)
    print("\nParsed JSON Output Successfully\n")
    print(json.dumps(parsed_json, indent=2))
except Exception as e:
    print("\nRaw Output (Failed to parse JSON):")
    print(raw_output)
    print(f"\nParse Error: {e}")