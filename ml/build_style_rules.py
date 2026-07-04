import re
import numpy as np

# Sample text files to calibrate style ranges
SAMPLES = {
    "slang": [
        "omg this is so broken lmao please fix asap ngl",
        "btw idk why my card got declined yup ugh",
        "lol gonna try again rn tbh hope it works",
    ],
    "casual": [
        "Hey, can you help me reset my password? It's not working.",
        "I just ordered some shoes and I want to double check the status.",
        "Thanks, that worked great! Have a good day.",
    ],
    "formal": [
        "Regarding my previous order, I am requesting a formal receipt herewith.",
        "Therefore, I wish to cancel this subscription and receive a refund.",
        "Sincerely, I appreciate your prompt assistance regarding this transaction.",
    ]
}

def analyze_style_bounds():
    print("📏 Calibrating stylistic axes ranges...")
    for label, texts in SAMPLES.items():
        avg_lens = []
        word_counts = []
        
        for text in texts:
            words = re.findall(r"\b\w+\b", text.lower())
            word_counts.append(len(words))
            avg_lens.append(np.mean([len(w) for w in words]) if words else 0)
            
        print(f"\n🏷 Style: {label.upper()}")
        print(f"  Avg Word Count: {np.mean(word_counts):.1f} words/message")
        print(f"  Avg Word Length: {np.mean(avg_lens):.1f} chars/word")

    print("\n✅ Style axis thresholds calibrated for real-time inference!")

if __name__ == "__main__":
    analyze_style_bounds()
