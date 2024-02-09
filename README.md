# NEDSAScript

this is a programming language in which programs describe a non-erasing deterministic stack automaton (NEDSA) - a model of computation
equivalent to an nlogn-bounded turing machine, so about as powerful as you can get while remaining decidable. the language comes with
a decider based on the (gorgeous) transition matrix method from Hopcroft & Ullman (1967) which you can read (here)[https://www.sciencedirect.com/science/article/pii/S0022000067800138].
the decider runs in exponential time in the worst case, but for test programs so far it's entirely usable.
