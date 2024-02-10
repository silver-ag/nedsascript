
class Transition:
    def __init__(self, state_from, value_from, state_to, side_effects):
        self.state_from = state_from
        self.value_from = value_from
        self.state_to = state_to
        self.push = side_effects['push'] if 'push' in side_effects else None
        self.move = {'left': -1, 'right': 1}[side_effects['move']] if 'move' in side_effects else 0

class TableTransition:
    # elements of the transition table can't push or move, but they do need to be able to halt before reaching the end
    def __init__(self, state_from, state_to, halt = False):
        self.state_from = state_from
        self.state_to = state_to
        self.halt = halt
    def __eq__(self, other):
        # required so that transition tables can be compared for equality
        if isinstance(other, TableTransition):
            return self.state_from == other.state_from and self.state_to == other.state_to and self.halt == other.halt
        else:
            return False
        

class NonErasingStackAutomaton:
    # inputless version, because that's all i need
    def __init__(self, transitions):
        self.transitions = {(transition.state_from, transition.value_from) : transition for transition in transitions}
        self.states = set()
        self.alphabet = set(['BLANK'])
        for transition in transitions:
            self.states.add(transition.state_from)
            self.states.add(transition.state_to)
            self.alphabet.add(transition.value_from)
    def run(self, state):
        pointer = 0
        stack = []
        while True:
            print(f"{stack}:{pointer} in {state}")
            if (state, stack[pointer] if pointer < len(stack) else 'BLANK') in self.transitions:
                t = self.transitions[(state, stack[pointer] if pointer < len(stack) else 'BLANK')]
            else:
                # if there's no transition for this situation, halt and return the current state
                return state
            state = t.state_to
            if t.push is not None:
                if pointer == len(stack):
                    stack += [t.push]
                    pointer += 1
                else:
                    # pushing while not at the top of the stack is rejecting
                    return '+REJECT:INVALIDPUSH+'
            pointer += t.move
            if pointer < 0 or pointer > len(stack):
                # moving the pointer off the stack is rejecting
                return '+REJECT:INVALIDMOVE+'
    def make_transition_table(self, prev_transition_table, new_value):
        return {state: self.get_eventual_transition(state, prev_transition_table, new_value) for state in self.states}
    def get_eventual_transition(self, state, prev_transition_table, new_value):
        original_state = state
        for i in range(len(self.states) + 1):
            if (state, new_value) in self.transitions:
                t = self.transitions[(state, new_value)]
            else:
                # if there's no transition for this situation, halts and returns the reached state
                return TableTransition(original_state, state, halt = True)
            state = t.state_to
            if t.push is not None:
                # pushing while not at the top of the stack is rejecting
                return TableTransition(original_state, '+REJECT:INVALIDPUSH+', halt = True)
            if t.move == 1:
                return TableTransition(original_state, state)
            if t.move == -1:
                if prev_transition_table[state].halt:
                    return TableTransition(original_state, prev_transition_table[state].state_to, halt = True)
                else:
                    state = prev_transition_table[state].state_to
        return TableTransition(original_state, '+DOESNOTHALT+', halt = True)
    @property
    def first_transition_table(self):
        return {state: TableTransition(state, '+REJECT:INVALIDMOVE+', halt = True) for state in self.states}
    def run_with_transition_tables(self, state):
        # guaranteed to halt!! (in exponential time, tbf)
        # see: Nonerasing Stack Automata, J. Hopcroft, J. Ullman, Journal of Computer and Systems Sciences, 1 (1967), pp. 166-186
        # https://www.sciencedirect.com/science/article/pii/S0022000067800138
        # especially section 5 theorem 1
        # we detect infinite runs that don't loop by detecting equivalent transition tables
        # even if the stack is different, if we're in the same state with the same current transition table that's a loop,
        # because stacks with the same transition table are indistinguishable by the automaton.
        # this will always happen eventually because there are finitely many different transition tables for n states

        # estimate worst case runtime:
        print(f"may have to run through {pow(len(self.states), 2) * 2} tables in the worst case")

        current_transition_table = self.first_transition_table
        all_transition_tables = [(current_transition_table, [])] # have to use an assoc-list because dicts aren't valid dict keys
        while True:
            #print(all_transition_tables)
            if (state, 'BLANK') in self.transitions:
                t = self.transitions[(state, 'BLANK')]
            else:
                # if there's no transition for this situation, halt and return the current state
                return state
            state = t.state_to
            if t.push is not None:
                current_transition_table = self.make_transition_table(current_transition_table, t.push)
                table_index = assoc_index(current_transition_table, all_transition_tables)
                if table_index == -1:
                    all_transition_tables.append((current_transition_table, []))
            if t.move == 1:
                return '+REJECT:INVALIDMOVE+'
            if t.move == -1:
                if current_transition_table[state].halt:
                   return current_transition_table[state].state_to
                else:
                    state = current_transition_table[state].state_to
                
            table_index = assoc_index(current_transition_table, all_transition_tables)
            if state in all_transition_tables[table_index][1]:
                # non-halting program detected
                return '+DOESNOTHALT+'
            else:
                all_transition_tables[table_index] = (all_transition_tables[table_index][0], all_transition_tables[table_index][1] + [state])
            

def assoc_index(v, al):
    for i in range(len(al)):
        if al[i][0] == v:
            return i
    return -1

# tests
#test = NonErasingStackAutomaton([Transition('a', 'BLANK', 'b', {'push': 'X'}), Transition('b', 'X', 'a', {'move': 'left'})])
#testxyzforever = NonErasingStackAutomaton([Transition('a', 'BLANK', 'b', {'push': 'X'}), Transition('b', 'BLANK', 'c', {'push': 'Y'}), Transition('c', 'BLANK', 'a', {'push': 'Z'})])
