import pandas as pd
from transformers import pipeline
from textblob import TextBlob

# Load your cleaned CSV
df = pd.read_csv("../data/glowinspo_outfits_cleaned.csv")

# Load HuggingFace emotion classifier
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=3)

# Define emotion-to-tone mapping
emotion_to_tone = {
    "joy": "uplifting",
    "amusement": "playful",
    "excitement": "uplifting",
    "love": "wholesome",
    "gratitude": "wholesome",
    "relief": "grounding",
    "optimism": "uplifting",
    "contentment": "calm",
    "pride": "empowering",
    "admiration": "gentle",
    "curiosity": "reflective",
    "desire": "dreamy",
    "realization": "reflective",
    "surprise": "playful",
    "caring": "wholesome",
    "approval": "gentle",
    "sadness": "reflective",
    "disappointment": "reflective",
    "nervousness": "grounding",
    "fear": "grounding",
    "remorse": "reflective",
    "embarrassment": "reflective",
    "anger": "grounding",
    "confusion": "reflective",
    "annoyance": "reflective",
    "grief": "reflective"
}

# Fallback tone via TextBlob sentiment polarity
def fallback_tone(text):
    polarity = TextBlob(str(text)).sentiment.polarity
    if polarity > 0.3:
        return "uplifting"
    elif polarity < -0.3:
        return "reflective"
    else:
        return "calm"

# Classify tone based on emotion labels
def classify_tone(text):
    if not isinstance(text, str) or not text.strip():
        return "unclassified"
    try:
        emotions = emotion_classifier(text[:512])
        for emotion in emotions:
            tone = emotion_to_tone.get(emotion['label'])
            if tone:
                return tone
    except Exception:
        pass
    return fallback_tone(text)

# Apply classification
df["tone_tags"] = df["image_description"].apply(classify_tone)

# Save result
df.to_csv("../data/glowinspo_outfits_tone_tagged.csv", index=False)
print("✅ Tone-tagged dataset saved: glowinspo_outfits_tone_tagged.csv")
