import pandas as pd

# Load your cleaned dataset
df = pd.read_csv("../data/glowinspo_outfits_cleaned.csv")

# Define expanded tone keyword lists
tone_keywords = {
    "calm": ["linen", "cotton", "neutral", "matte", "earthy", "minimal", "slate"],
    "uplifting": ["silk", "bold", "shine", "neon", "puffed", "vibrant", "red"],
    "grounding": ["leather", "denim", "structured", "black", "utility", "rugged"],
    "reflective": ["wool", "gray", "cozy", "knit", "quilted", "oversized"],
    "playful": ["yellow", "ruffle", "print", "cheerful", "fun", "frill", "floral"]
}

def classify_multi_tone(desc):
    desc = str(desc).lower()
    matched = []
    for tone, words in tone_keywords.items():
        if any(word in desc for word in words):
            matched.append(tone)
    return ", ".join(sorted(set(matched))) if matched else "calm"

# Apply the classifier
df["tone_tags_custom"] = df["image_description"].apply(classify_multi_tone)

# Save to a new file
df.to_csv("../data/glowinspo_outfits_tone_multi.csv", index=False)
print("✅ Saved: glowinspo_outfits_tone_multi.csv")
