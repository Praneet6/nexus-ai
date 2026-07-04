import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os

# Heuristic simulation to generate keystroke datasets
# Features: [backspace_ratio, avg_delay_ms, long_idle_count, max_idle_ms]
def generate_synthetic_keystrokes(n_samples=500):
    np.random.seed(42)
    X = []
    y = []

    for _ in range(n_samples):
        state = np.random.choice(["confident", "confused", "distressed"])
        
        if state == "confident":
            # Fast, smooth typing, minimal backspacing
            backspace_ratio = np.random.uniform(0.0, 0.15)
            avg_delay = np.random.uniform(80.0, 180.0)
            long_idles = np.random.poisson(0.2)
            max_idle = np.random.uniform(0.0, 1500.0)
        elif state == "confused":
            # Moderate speed, some backspacing, occasional pauses
            backspace_ratio = np.random.uniform(0.15, 0.35)
            avg_delay = np.random.uniform(180.0, 300.0)
            long_idles = np.random.poisson(1.5)
            max_idle = np.random.uniform(1500.0, 4500.0)
        else: # distressed
            # Slow speed, high deletions, long hesitation pauses
            backspace_ratio = np.random.uniform(0.35, 0.70)
            avg_delay = np.random.uniform(300.0, 600.0)
            long_idles = np.random.poisson(3.5)
            max_idle = np.random.uniform(4500.0, 12000.0)

        X.append([backspace_ratio, avg_delay, long_idles, max_idle])
        y.append(state)

    return np.array(X), np.array(y)

def train_classifier():
    print("🛠 Generating synthetic keystroke cadence training data...")
    X, y = generate_synthetic_keystrokes(1000)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("🏋 Training Decision Tree classifier...")
    clf = DecisionTreeClassifier(max_depth=4, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print("\n📊 Model Evaluation:")
    print(classification_report(y_test, y_pred))

    model_path = os.path.join(os.path.dirname(__file__), "silence_classifier.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    print(f"💾 Model successfully exported to {model_path}!")

if __name__ == "__main__":
    train_classifier()
