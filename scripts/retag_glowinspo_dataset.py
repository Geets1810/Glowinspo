import pandas as pd
import anthropic
import os
import json
import time

# -----------------------------
# CONFIG
# -----------------------------

INPUT_FILE = "../data/glowinspo_outfits_tone_multi.csv"
OUTPUT_FILE = "../data/glowinspo_outfits_retagged_v2.csv"

client = anthropic.Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"]
)

# -----------------------------
# TAXONOMY
# -----------------------------

ENERGY_BUCKETS = ["Soften", "Stabilize", "Brighten", "Amplify"]

ALLOWED_TONES = [
    "muted", "minimal", "soft", "neutral", "flowy",
    "structured", "balanced", "earth-toned", "steady", "tailored",
    "warm", "playful", "lively", "colorful", "expressive-light",
    "bold", "dramatic", "elevated", "commanding", "statement"
]

# -----------------------------
# LOAD DATA
# -----------------------------

df = pd.read_csv(INPUT_FILE)

# Ensure description column exists
if "image_description" not in df.columns:
    raise ValueError("Your CSV must contain a 'image_description' column.")

# -----------------------------
# RETAG FUNCTION
# -----------------------------

def classify_item(description):

    prompt = f"""
You are classifying fashion items by presentation energy.

Energy buckets (choose EXACTLY ONE):
Soften, Stabilize, Brighten, Amplify

Tone tags (choose 2–3 max from this exact list only):
{", ".join(ALLOWED_TONES)}

Description:
{description}

Return ONLY valid JSON in this format:

{{
  "energy_bucket": "...",
  "tone_tags_v2": ["...", "..."]
}}
"""

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()

    try:
        result = json.loads(text)
        return result["energy_bucket"], result["tone_tags_v2"]
    except Exception as e:
        print("Failed to parse response:", text)
        return None, None


# -----------------------------
# APPLY RETAGGING
# -----------------------------

energy_results = []
tone_results = []

for i, row in df.iterrows():
    description = str(row["image_description"])

    print(f"Processing row {i+1}/{len(df)}")

    energy, tones = classify_item(description)

    energy_results.append(energy)
    tone_results.append(", ".join(tones) if tones else None)

    time.sleep(0.5)  # small delay to avoid rate limit


df["energy_bucket"] = energy_results
df["tone_tags_v2"] = tone_results

# -----------------------------
# SAVE NEW FILE
# -----------------------------

df.to_csv(OUTPUT_FILE, index=False)

print("Retagging complete. Saved to:", OUTPUT_FILE)
