class DummyAutomaton:
    def __init__(self):
        self.states = {"q0", "q1"}
        self.initial_state = "q0"
        self.final_states = {"q1"}
        self.transitions = []

def load_automaton(path):
    print(f"[DEBUG] Loader STUB chamado. Arquivo recebido: {path}")
    return DummyAutomaton()
