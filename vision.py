import os
import json
from google import genai
from google.genai import types

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")

PROMPT = """Look at this screenshot of a "cat sort" puzzle game. There are several tubes arranged horizontally, each containing stacked colored cats.

IMPORTANT ORDERING RULES:
- Report tubes LEFT-TO-RIGHT as they appear on screen. Tube index 0 = the leftmost tube.
- List colors BOTTOM-TO-TOP within each tube. The first element in the array = the cat at the bottom. The last element = the cat at the top (most recently placed).

Some tubes may be LOCKED (indicated by a lock icon, padlock symbol, or other visual indicator). LOCKED tubes cannot be interacted with — ignore them completely. Do NOT include locked tubes in the output. Only analyze and report the UNLOCKED/interactive tubes.

Analyze the image and return the puzzle state as a JSON object with these fields:
- "capacity": the maximum number of cats each tube can hold (count the total slots in any tube, they are all the same)
- "state": an array of arrays, one per UNLOCKED tube in LEFT-TO-RIGHT order, listing cat colors from BOTTOM to TOP

Use only these color names: red, orange, yellow, green, blue, purple, pink, brown, white, black, gray, cyan, magenta.

Return ONLY the JSON object, nothing else. Example format:
{
  "capacity": 8,
  "state": [
    ["red", "blue", "red", "red"],
    ["blue", "red", "blue"],
    [],
    ["green", "green", "green", "green"]
  ]
}

Empty unlocked tubes should be represented as empty arrays []. Make sure to count every cat accurately, correctly determine the tube capacity, and skip any locked tubes entirely."""

def parse_image(image_path: str = None):
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    with open(image_path, "rb") as f:
        image_data = f.read()

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
            PROMPT
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )

    result = json.loads(response.text)

    if "state" not in result or "capacity" not in result:
        raise ValueError("AI response missing 'state' or 'capacity' fields")

    with open(STATE_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[*] Detected tube capacity: {result['capacity']}")
    print(f"[*] Saved puzzle state to {STATE_FILE}")
    return result["state"], result["capacity"]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python vision.py <image_path>")
        sys.exit(1)
    state, capacity = parse_image(sys.argv[1])
    print(json.dumps({"capacity": capacity, "state": state}, indent=2))
