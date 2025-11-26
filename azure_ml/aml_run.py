from transformers import pipeline

def main():
    print("Loading sentiment model...")
    model = pipeline("sentiment-analysis")
    out = model("Azure ML test run")
    print("Model Output:", out)

if __name__ == "__main__":
    main()
