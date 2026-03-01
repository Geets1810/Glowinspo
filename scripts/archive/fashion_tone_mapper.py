import pandas as pd

# Load your cleaned GlowInspo dataset
df = pd.read_csv("../data/glowinspo_outfits_cleaned.csv")

# Optionally assign a default tone before remapping
df["tone_tags"] = "calm"

# Define custom fashion tone mapping logic
def remap_tone_from_keywords(row):
    desc = str(row['image_description']).lower()

    if any(word in desc for word in ["linen", "cotton", "neutral", "slate", "beige", "minimal", "earthy"]):
        return "calm"
    elif any(word in desc for word in ["silk", "satin", "vibrant", "red", "bold", "shine", "glossy", "statement"]):
        return "uplifting"
    elif any(word in desc for word in ["wool", "cozy", "gray", "monochrome", "knit", "layer", "warm"]):
        return "reflective"
    elif any(word in desc for word in ["denim", "leather", "structured", "black", "edgy", "rugged"]):
        return "grounding"
    elif any(word in desc for word in ["yellow", "pastel", "floral", "ruffle", "playful", "fun", "cheerful"]):
        return "playful"
    else:
        return "calm"  # fallback tone

# Apply the logic to each row
df["tone_tags_custom"] = df.apply(remap_tone_from_keywords, axis=1)

# Save the output
output_path = "../data/glowinspo_outfits_tone_custom.csv"
df.to_csv(output_path, index=False)

print(f"✅ Tone-tagged file saved at: {output_path}")
