from transformers import pipeline

def load_model(model_name="google/flan-t5-large"):
    print(f"Loading model: {model_name} ...")
    generator = pipeline("text2text-generation", model=model_name, tokenizer=model_name)
    print("Model loaded successfully.\n")
    return generator
