class ChatMemory:
    def __init__(self, max_turns=4):
        self.max_turns = max_turns
        self.memory = []

    def add_turn(self, user_input, bot_response):
        self.memory.append((user_input, bot_response))
        if len(self.memory) > self.max_turns:
            self.memory.pop(0)

    def get_context(self):
        if not self.memory:
            return ""
        return " ".join([f"User: {u} Bot: {b}" for u, b in self.memory])
