import base64
import json
from json_repair import repair_json
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
        "Intended Design: Digital pins D8 (Red wire), D7 (Yellow wire), and D4 (Green wire) drive Red, Yellow, Green LEDs. "
        "Each branch requires a current-limiting resistor (220 ohm to 1k ohm). "
        "Cathodes (long horizontal black wires) must return to the breadboard common '-' ground rail connected to Arduino GND."
    ),
    "General Circuit Inspection (Auto-Detect / Custom)": (
        "Project: Unknown / Custom breadboard circuit. "
        "Goal: Perform a general electrical and safety diagnostic. Detect the microcontroller and all sensors/modules, trace visible connections, "
        "verify power/ground rail continuity, identify active loads or pull-up/load resistors, and check for missing current limiters or direct shorts."
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
    2. Power/Ground Connections & Cross-Span Tracing: Thoroughly trace return leads from their component terminals across the breadboard blocks to their destination rails. Check both left and right-side power/ground rails before declaring a net "floating" or ungrounded.
    3. Grid Alignment Tolerance: Account for 2D perspective and pixel rendering limits. If a wire terminal or resistor leg appears to be within 1 row of a matching net node, treat it as connected unless there is a clear visual gap.
    4. Strict Hallucination Prevention & Wire Arcs: Verify that any reported fault or extra wire is physically present and terminating into a valid hole. NEVER assume a wire terminates into a power/ground rail or creates a short simply because its visual arc, loop, or routing path passes near, dips toward, or crosses over the rails. Always trace the actual endpoint insertion coordinate.
    5. Cathode Return Terminations: For LED cathode return black wires, terminal strip rows (columns a-e or f-j) are completely valid electrical connections to shared rows. Do NOT require black return wires to stretch all the way to the outer blue '-' rails as long as they are seated within a valid numbered terminal row.
    
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

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        repaired = repair_json(raw_output)
        parsed = json.loads(repaired)

    parsed["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    parsed["blueprint_used"] = preset_name
    parsed["model_version"] = "muse-spark-1.3"
    return parsed