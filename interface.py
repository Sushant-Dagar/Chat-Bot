import re
import string
import difflib
from model_loader import load_model
from chat_memory import ChatMemory

CAPITALS = {
    "india": "New Delhi",
    "italy": "Rome",
    "france": "Paris",
    "germany": "Berlin",
    "spain": "Madrid",
    "united kingdom": "London",
    "uk": "London",
    "china": "Beijing",
    "japan": "Tokyo",
    "canada": "Ottawa",
    "australia": "Canberra",
    "russia": "Moscow",
    "usa": "Washington, D.C.",
    "united states": "Washington, D.C.",
    "oman": "Muscat",
}

FACTUALS = {
    "president of india": "Droupadi Murmu",
    "prime minister of india": "Narendra Modi",
    "president of france": "Emmanuel Macron",
    "prime minister of uk": "Rishi Sunak",
    "president of usa": "Joe Biden",
    "prime minister of canada": "Justin Trudeau",
    "president of russia": "Vladimir Putin",
    "prime minister of japan": "Fumio Kishida",
    "prime minister of pakistan": "Shehbaz Sharif",
    "president of china": "Xi Jinping",
    "prime minister of china": "Li Qiang",
}

CURRENCIES = {
    "india": "Indian rupee",
    "usa": "United States dollar",
    "united states": "United States dollar",
    "uk": "British pound sterling",
    "united kingdom": "British pound sterling",
    "japan": "Japanese yen",
    "china": "Chinese yuan",
    "canada": "Canadian dollar",
    "australia": "Australian dollar",
    "pakistan": "Pakistani rupee",
    "france": "Euro",
    "germany": "Euro",
    "italy": "Euro",
    "spain": "Euro",
    "russia": "Russian ruble",
}

def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = s.translate(str.maketrans("", "", string.punctuation))
    return s.strip()

def detect_capital_question(text: str):
    txt = normalize_text(text)
    for p in [r"what is the capital of (.+)", r"what's the capital of (.+)", r"capital of (.+)"]:
        m = re.search(p, txt)
        if m:
            return normalize_text(m.group(1))
    return None

def detect_country_from_capital(text: str):
    txt = normalize_text(text)
    for p in [r"(.+) is the capital of which country", r"(.+) is capital of which country", r"(.+) capital of which country"]:
        m = re.search(p, txt)
        if m:
            return normalize_text(m.group(1))
    return None

def lookup_capital(country: str):
    if not country:
        return None
    if country in CAPITALS:
        return CAPITALS[country]
    match = difflib.get_close_matches(country, CAPITALS.keys(), n=1, cutoff=0.75)
    return CAPITALS[match[0]] if match else None

def lookup_country_by_capital(capital: str):
    capital = capital.lower()
    for c, cap in CAPITALS.items():
        if capital in cap.lower():
            return c.capitalize()
    match = difflib.get_close_matches(capital, [v.lower() for v in CAPITALS.values()], n=1, cutoff=0.75)
    if match:
        for c, cap in CAPITALS.items():
            if cap.lower() == match[0]:
                return c.capitalize()
    return None

def lookup_factual(question: str):
    q = normalize_text(question)
    for key, val in FACTUALS.items():
        if key in q:
            return val
    return None

def detect_question_type(text: str):
    """Detect the type of question being asked (president, prime_minister, etc.)"""
    txt = normalize_text(text)
    if 'prime minister' in txt or 'pm of' in txt:
        return 'prime_minister'
    elif 'president' in txt:
        return 'president'
    elif 'capital' in txt:
        return 'capital'
    elif 'currency' in txt:
        return 'currency'
    return None

def detect_currency_question(text: str):
    """Detect currency questions like 'what is the currency of India'"""
    txt = normalize_text(text)
    for p in [r"what is the currency of (.+)", r"what's the currency of (.+)",
              r"currency of (.+)", r"official currency of (.+)"]:
        m = re.search(p, txt)
        if m:
            return normalize_text(m.group(1))
    return None

def lookup_currency(country: str):
    """Look up currency for a country"""
    if not country:
        return None
    if country in CURRENCIES:
        return CURRENCIES[country]
    match = difflib.get_close_matches(country, CURRENCIES.keys(), n=1, cutoff=0.75)
    return CURRENCIES[match[0]] if match else None

def detect_followup_country(text: str):
    """Detect follow-up questions like 'and Japan', 'what about Italy', etc."""
    txt = normalize_text(text)
    # Order matters! More specific patterns first
    patterns = [
        r"^and what about\s+(\w+(?:\s+\w+)?)",  # "and what about Japan"
        r"^and of\s+(\w+(?:\s+\w+)?)",  # "and of Japan"
        r"^what about\s+(\w+(?:\s+\w+)?)",  # "what about Japan"
        r"^how about\s+(\w+(?:\s+\w+)?)",  # "how about Japan"
        r"^and\s+(\w+(?:\s+\w+)?)",  # "and Japan", "and United States"
    ]
    for pattern in patterns:
        m = re.search(pattern, txt)
        if m:
            return normalize_text(m.group(1))
    return None

def main():
    print("🤖 Local CLI Chatbot (Factual + FLAN-T5)")
    print("Type '/exit' to quit.\n")

    generator = load_model()
    memory = ChatMemory(max_turns=4)
    last_question_type = None  # Track question context: 'capital', 'currency', 'president', 'prime_minister'

    while True:
        try:
            user_input = input("User: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nChatbot interrupted. Exiting...")
            break

        if user_input.lower() == "/exit":
            print("Exiting chatbot. Goodbye!")
            break

        # Check for follow-up questions (e.g., "and Japan", "what about Italy")
        followup_country = detect_followup_country(user_input)
        if followup_country and last_question_type:
            # Apply the previous question type to the new country
            if last_question_type == 'capital':
                cap = lookup_capital(followup_country)
                if cap:
                    print(f"Bot: {cap}")
                    memory.add_turn(user_input, cap)
                    continue
                # If not found, reconstruct full question for model
                user_input = f"what is the capital of {followup_country}"
            elif last_question_type == 'currency':
                curr = lookup_currency(followup_country)
                if curr:
                    print(f"Bot: {curr}")
                    memory.add_turn(user_input, curr)
                    continue
                # If not found, reconstruct full question for model
                user_input = f"what is the currency of {followup_country}"
            elif last_question_type in ['president', 'prime_minister']:
                # Try to construct the factual key (replace underscore with space)
                factual_key = f"{last_question_type.replace('_', ' ')} of {followup_country}"
                factual_key_normalized = normalize_text(factual_key)

                # Search for matching factual
                found_fact = None
                for key, val in FACTUALS.items():
                    if key == factual_key_normalized:
                        found_fact = val
                        break

                if found_fact:
                    print(f"Bot: {found_fact}")
                    memory.add_turn(user_input, found_fact)
                    continue
                # If not found, reconstruct full question for model
                user_input = f"who is the {last_question_type.replace('_', ' ')} of {followup_country}"

        country = detect_capital_question(user_input)
        if country:
            cap = lookup_capital(country)
            if cap:
                print(f"Bot: {cap}")
                memory.add_turn(user_input, cap)
                last_question_type = 'capital'
                continue

        capital = detect_country_from_capital(user_input)
        if capital:
            cname = lookup_country_by_capital(capital)
            if cname:
                print(f"Bot: {cname}")
                memory.add_turn(user_input, cname)
                last_question_type = 'capital'
                continue

        # Check for currency questions
        country_curr = detect_currency_question(user_input)
        if country_curr:
            curr = lookup_currency(country_curr)
            if curr:
                print(f"Bot: {curr}")
                memory.add_turn(user_input, curr)
                last_question_type = 'currency'
                continue

        fact = lookup_factual(user_input)
        if fact:
            print(f"Bot: {fact}")
            memory.add_turn(user_input, fact)
            # Determine what type of factual question it was
            q_normalized = normalize_text(user_input)
            if 'president' in q_normalized:
                last_question_type = 'president'
            elif 'prime minister' in q_normalized:
                last_question_type = 'prime_minister'
            continue

        # Detect question type even if we don't have the answer
        # This ensures follow-ups work correctly
        detected_type = detect_question_type(user_input)
        if detected_type:
            last_question_type = detected_type

        # Build context from previous conversation
        context = memory.get_context()

        if context:
            prompt = (
                f"The following is a conversation between a user and a helpful, factual AI assistant.\n"
                f"{context}\nUser: {user_input}\nBot:"
            )
        else:
            prompt = f"User: {user_input}\nBot:"

        # Generate model response with context
        response = generator(
            prompt,
            max_new_tokens=150,
            do_sample=False,
            truncation=True
        )

        bot_reply = response[0]["generated_text"]

        # Extract only new bot reply (ignore context echoes)
        bot_reply = bot_reply.split("Bot:")[-1].strip()
        bot_reply = re.sub(r"User:.*", "", bot_reply).strip()

        if not bot_reply:
            bot_reply = "I'm not sure, but I can try to find out."

        print(f"Bot: {bot_reply}")
        memory.add_turn(user_input, bot_reply)

if __name__ == "__main__":
    main()
