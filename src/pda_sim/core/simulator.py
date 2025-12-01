class DummyConfig:
    def __init__(self):
        self.state = "q0"
        self.remaining_input = ["a", "b"]
        self.stack = type("DummyStack", (), {"items": ["Z"]})

def stepwise_run(automaton, input_string, mode="step"):
    print(f"[DEBUG] Simulator STUB chamado. Entrada recebida: {input_string}")
    for i in range(3):
        yield [DummyConfig()]
