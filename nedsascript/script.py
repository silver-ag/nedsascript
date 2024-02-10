from lark import Lark, Transformer, Visitor, Tree, Token, Discard
from .stackautomaton import NonErasingStackAutomaton, Transition
import itertools

with open('nedsascript/nedsascript_grammar.lark', 'r') as grammar:
    nedsascript_parser = Lark(grammar, start = 'program')

def parse(code):
    initial_tree = nedsascript_parser.parse(code)
    processed_tree = EndReplacer().transform(initial_tree)
    return processed_tree

def construct_nedsa(code):
    new_tree, variables, states, alphabet = Preprocessor().transform(parse(code))
    variable_possibilities = list(itertools.product(*[list(range(v[1])) for v in variables.values()]))
    variable_names = list(variables.keys()) # tells us what order variable_possibilities is in
    variable_initialisations = [v[0] for v in variables.values()]
    return Script(parse_program(new_tree, alphabet, variable_possibilities, variable_names, variable_initialisations))

class Script:
    def __init__(self, nedsa):
        self.nedsa = nedsa
    def run(self):
        return self.clean(self.nedsa.run('+START+'))
    def decide(self):
        # same as run, but instead of running forever it'll return '+DOESNOTHALT+'
        return self.clean(self.nedsa.run_with_transition_tables('+START+'))
    def clean(self, string):
        # '-' is a character that can't appear in user-specified labels that's used to seperate out variable data
        return string.partition('-')[0]

def state_endings(variable_possibilities):
    # make a list of all possible states in the form <statename>_<val1>_<val2> ... for values given as possible
    r = []
    for possibility in variable_possibilities:
        r.append('')
        for variable in possibility:
            r[-1] += '-' + str(variable)
    return r

class EndReplacer(Transformer):
    # replace any initial codeblock with a labelledcodeblock with the label +FIRSTLABEL (note the + makes it not a valid user-declared label)
    # and replace any final label with a labelledcodeblock with an empty codeblock
    def program(self, items):
        if isinstance(items[0], Tree) and items[0].data == 'codeblock':
            items[0] = Tree(Token('RULE', 'labelledcodeblock'), [Tree(Token('RULE', 'label'), [Token('NAME', '+FIRSTLABEL')])] + items[0].children)
        if isinstance(items[-1], Tree) and items[-1].data == 'label':
            items[-1] = Tree(Token('RULE', 'labelledcodeblock'), [items[-1]])
        return Tree(Token('RULE', 'program'), items)

class Preprocessor(Transformer):
    # remove all var declarations and record them, state names and alphabet seperately
    def __init__(self):
        super().__init__()
        self.vars = {}
        self.states = []
        self.alphabet = set(['BLANK'])
    def transform(self, tree):
        new_tree = super().transform(tree)
        return (new_tree, self.vars, self.states, self.alphabet)
    def labelledcodeblock(self, items):
        label = items[0].children[0].value
        if label in self.states:
            raise(ParseException(f"parse error: label '{label}' declared twice"))
        else:
            self.states.append(label)
        return Tree(Token('RULE', 'labelledcodeblock'), items)
    def vardeclaration(self, items):
        name = items[0].value
        value = items[1]
        maximum = items[2]
        if name in self.vars:
            raise(ParseException(f"parse error: variable '{name}' declared twice"))
        elif value > maximum:
            raise(ParseException(f"parse error: variable '{name}' initialised to a larger value than its declared maximum ({value} > {maximum})"))
        else:
            self.vars[name] = (value, maximum)
            return Discard
    def push(self, items):
        self.alphabet.add(items[0].value)
        return Tree(Token('RULE', 'push'), items)
    def ifread(self, items):
        self.alphabet.add(items[0].value)
        return Tree(Token('RULE', 'ifread'), items)
    def number(self, items):
        return int(items[0].value)

def parse_program(program, alphabet, variable_possibilities, variable_names, variable_initialisations):
    transitions = []
    initial_ending = ''
    for init in variable_initialisations:
        initial_ending += '-' + str(init)
    transitions.append(Transition('+START+', 'BLANK', program.children[0].children[0].children[0].value + initial_ending, {}))
    for i in range(len(program.children)):
        new_transitions, final_n = parse_labelled_block(program.children[i], alphabet, variable_possibilities, variable_names)
        transitions += new_transitions
        if i + 1 < len(program.children):
            for ending in state_endings(variable_possibilities):
                for symbol in alphabet:
                    transitions.append(Transition(program.children[i].children[0].children[0].value + ending + '-block' + str(final_n), symbol,
                                                  program.children[i+1].children[0].children[0].value + ending, {}))
    return NonErasingStackAutomaton(transitions)
        

def parse_labelled_block(block, alphabet, variable_possibilities, variable_names):
    transitions = []
    label = block.children[0].children[0].value
    for ending in state_endings(variable_possibilities):
        for symbol in alphabet:
            transitions.append(Transition(label + ending, symbol, label + ending + '-block0', {}))
    new_transitions, new_n = parse_codeblock(block.children[1:], label, alphabet, variable_possibilities, variable_names, 0)
    transitions += new_transitions
    return transitions, new_n

def parse_codeblock(block, label, alphabet, variable_possibilities, var_names, n):
    transitions = []
    for statement in block:
        if statement.data == 'pass':
            pass
        elif statement.data == 'push':
            for ending in state_endings(variable_possibilities):
                for symbol in alphabet:
                    transitions.append(Transition(label + ending + '-block' + str(n), symbol, label + ending + '-block' + str(n+1), {'push': statement.children[0].value}))
            n += 1
        elif statement.data == 'move':
            for ending in state_endings(variable_possibilities):
                for symbol in alphabet:
                    transitions.append(Transition(label + ending + '-block' + str(n), symbol, label + ending + '-block' + str(n+1),
                                               {'move': {'DOWN':'left', 'UP':'right'}[statement.children[0].value]}))
            n += 1
        elif statement.data == 'halt':
            for ending in state_endings(variable_possibilities):
                for symbol in alphabet:
                    transitions.append(Transition(label + ending + '-block' + str(n), symbol, label + ending + '-block' + str(n), {'halt': True}))
        elif statement.data == 'goto':
            for ending in state_endings(variable_possibilities):
                for symbol in alphabet:
                    transitions.append(Transition(label + ending + '-block' + str(n), symbol, statement.children[0].value + ending, {}))
        elif statement.data == 'ifread':
            read_symbol = statement.children[0].value
            for ending in state_endings(variable_possibilities):
                transitions.append(Transition(label + ending + '-block' + str(n), read_symbol, label + ending + '-block' + str(n+1), {}))
            new_transitions, new_n = parse_codeblock(statement.children[1].children, label, alphabet, variable_possibilities, var_names, n + 1)
            transitions += new_transitions
            for ending in state_endings(variable_possibilities):
                for symbol in alphabet:
                    if symbol != read_symbol:
                        transitions.append(Transition(label + ending + '-block' + str(n), symbol, label + ending + '-block' + str(new_n), {}))
            n = new_n
        elif statement.data == 'ifcomparison':
            constrained_possibilities = constrain_possibilities(variable_possibilities, var_names, statement.children[0], statement.children[1], statement.children[2])
            for ending in state_endings(constrained_possibilities):
                for symbol in alphabet:
                    transitions.append(Transition(label + ending + '-block' + str(n), symbol, label + ending + '-block' + str(n+1), {}))
            new_transitions, new_n = parse_codeblock(statement.children[3].children, label, alphabet, constrained_possibilities, var_names, n + 1)
            transitions += new_transitions
            for ending in state_endings(set(variable_possibilities) - set(constrained_possibilities)):
                for symbol in alphabet:
                    transitions.append(Transition(label + ending + '-block' + str(n), symbol, label + ending + '-block' + str(new_n), {}))
    return transitions, n


def constrain_possibilities(var_possibilities, var_names, a, comparator, b):
    evaluator = ExpressionEvaluator(var_names)
    fa = evaluator.transform(a)
    fb = evaluator.transform(b)
    comp = {'=': lambda a,b: a == b, '>': lambda a,b: a > b, '<': lambda a,b: a < b, '>=': lambda a,b: a >= b, '<=': lambda a,b: a <= b, '!=': lambda a,b: a != b}[comparator]
    r = []
    for possibility in var_possibilities:
        if comp(fa(possibility), fb(possibility)):
            r.append(possibility)
    return r


class ExpressionEvaluator(Transformer):
    # constructs a function that takes a list of variable values and produces an expression value
    def __init__(self, variable_names):
        super().__init__()
        self.variable_names = variable_names
    def expression(self, items):
        if isinstance(items[0], Token) and items[0].type == 'NAME': # variable name
            return lambda variables: variables[self.variable_names.index(items[0])]
        elif len(items) == 3: # operation
            operation = {'+': lambda a,b: a+b, '-': lambda a,b: a-b, '*': lambda a,b: a*b, '/': lambda a,b: a//b}[items[1].value]
            return lambda variables: operation(items[0](variables), items[2](variables))
        else: # in all other cases it's already been processed into a list of numbers
            return lambda variables: items[0]
    

class ParseException(Exception):
    pass