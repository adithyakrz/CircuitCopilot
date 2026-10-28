import base64
import json
import os
from datetime import datetime, timezone
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
    expected_spec = CIRCUIT_PRESETS.get(
        preset_name, 
        CIRCUIT_PRESETS["General Circuit Inspection (Auto-Detect / Custom)"]
    )

    prompt = f"""
    You are an expert embedded systems diagnostic engineer.
    Target Specification / Mode: {expected_spec}

    2D VISUAL INTERPRETATION RULES (Tinkercad / Diagram Context):
    1. Insulated Wire Overlaps: In 2D breadboard views, lines visually crossing over headers, power rails, or other wires are insulated jumpers. Do NOT mark an intersection as a short circuit unless a wire clearly terminates into that hole.
    2. Power/Ground Connections: Long horizontal black wires originating from LED cathodes stretch across the breadboard and plug directly into the left '-' Ground rail holes. Verify whether return leads terminate into the ground rail and connect back to Arduino GND.
    3. Wire Colors: Red wire connects D8, Yellow wire connects D7, Green wire connects D4.

    Evaluate the circuit against the target specification.
    For spatial annotations, estimate bounding boxes as [x_min, y_min, x_max, y_max] in percentages (0 to 100) relative to image width and height.

    Return ONLY a valid, raw JSON object (no markdown formatting, no backticks, no text outside JSON).

    Schema:
    {{
      "circuit_name": "string",
      "status": "PASS" | "WARN" | "FAIL",
      "summary": "1-2 sentence technical diagnosis",
      "resistor_check": {{
        "detected_value": "string",
        "acceptable": true | false,
        "notes": "string"
      }},
      "pin_checks": [
        {{
          "id": "string (e.g., PIN-D8)",
          "pin": "string (e.g., D8)",
          "target_led": "string (e.g., Red LED)",
          "status": "OK" | "WARN" | "ISSUE",
          "severity": "HEALTHY" | "WARNING" | "FAULT",
          "expected_connection": "string (e.g., D8 -> 1k Resistor -> Red LED Anode -> Cathode -> GND Rail -> Arduino GND)",
          "detected_connection": "string (actual traced path)",
          "detail": "string (supporting evidence and concise technical explanation)",
          "remediation": "string (specific repair instruction, or 'None required' if OK)",
          "bbox": [number, number, number, number]
        }}
      ],
      "annotations": [
        {{
          "label": "string (e.g., Arduino Uno R3, D8 Red Branch, GND Rail)",
          "type": "MCU" | "COMPONENT" | "TRACE" | "FAULT",
          "status": "OK" | "WARN" | "ISSUE",
          "bbox": [number, number, number, number]
        }}
      ],
      "safety": {{
        "short_circuit_risk": "NONE" | "LOW" | "HIGH",
        "power_rail_grounded": true | false,
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

    parsed = json.loads(raw_output)
    parsed["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    parsed["blueprint_used"] = preset_name
    parsed["model_version"] = "muse-spark-1.3"
    return parsed