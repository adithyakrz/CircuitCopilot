import base64
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.meta.ai/v1",
    api_key=os.environ.get("MODEL_API_KEY"),
)

CIRCUIT_PRESETS = {
    "Arduino Uno 3-LED Traffic Light": (
        "Project: Arduino Uno Traffic Light Circuit (Tinkercad Simulation). "
        "Intended Design: Digital pins D8, D7, and D4 drive Red, Yellow, Green LEDs. "
        "Each branch requires a current-limiting resistor (220 ohm to 1k ohm). "
        "Cathodes must return to the breadboard common ground rail connected to Arduino GND."
    ),
    "General Circuit Inspection (Auto-Detect / Custom)": (
        "Project: Unknown / Custom breadboard circuit. "
        "Goal: Perform a general electrical and safety diagnostic. Detect the microcontroller, trace visible connections, "
        "verify power/ground integrity, identify active loads, and check for missing current-limiting resistors or direct shorts."
    )
}

def analyze_circuit(image_bytes: bytes, preset_name: str) -> dict:
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    expected_spec = CIRCUIT_PRESETS.get(preset_name, CIRCUIT_PRESETS["General Circuit Inspection (Auto-Detect / Custom)"])

    prompt = f"""
    You are an expert embedded systems diagnostic engineer.
    Target Specification / Mode: {expected_spec}

    2D VISUAL INTERPRETATION RULES (Tinkercad / Diagram Context):
    1. Insulated Wire Overlaps: In 2D breadboard views, lines visually crossing over headers, power rails, or other wires are insulated jumpers. Do NOT mark an intersection as a short circuit unless a wire clearly terminates into that pinhole.
    2. Power/Ground Connections: Verify whether the return leads actually terminate into the power or ground rails and connect back to the microcontroller supply.

    Evaluate the circuit against the provided target or general electronics design rules.
    Return ONLY a valid, raw JSON object (no markdown formatting, no backticks, no text outside JSON).

    Schema:
    {{
      "circuit_name": "string",
      "status": "PASS" | "WARN" | "FAIL",
      "summary": "1-2 sentence overall diagnosis",
      "resistor_check": {{
        "detected_value": "string",
        "acceptable": true,
        "notes": "string"
      }},
      "pin_checks": [
        {{"pin": "string", "target_led": "string", "status": "OK" | "ISSUE", "detail": "string"}}
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

    return json.loads(raw_output)