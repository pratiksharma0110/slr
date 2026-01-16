from collections import OrderedDict
import matplotlib

from utils.pdf import generate_pdf

matplotlib.use('Agg')
from utils.diagram_utils import generate_dfa_diagram_image  

class SLRParser:
    def __init__(self):
        self.grammar = {}
        self.augmented_grammar = {}
        self.start_symbol = None
        self.original_start = None
        self.terminals = set(['$'])
        self.non_terminals = set()
        self.first_sets = {}
        self.follow_sets = {}
        self.states = []
        self.dfa_transitions = {}
        self.parsing_table = {'ACTION': {}, 'GOTO': {}}
        self.productions = []
        self.conflicts = []

    def parse_grammar(self, grammar_text):
        self.grammar = OrderedDict()
        self.conflicts = []
        lines = grammar_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            line = line.replace('→', '->').replace('=>', '->')
            if '->' not in line:
                continue
            left, right = line.split('->', 1)
            left = left.strip()
            right = right.strip()
            if left not in self.grammar:
                self.grammar[left] = []
            productions = [p.strip() for p in right.split('|')]
            for prod in productions:
                if prod:
                    self.grammar[left].append(prod)
        if not self.grammar:
            raise ValueError("Invalid grammar format")
        self.original_start = list(self.grammar.keys())[0]
        self.start_symbol = self.original_start
        self.non_terminals = set(self.grammar.keys())
        self._identify_symbols()
        return self.grammar

    def _identify_symbols(self):
        self.terminals = set(['$'])
        all_symbols = set()
        for productions in self.grammar.values():
            for prod in productions:
                if not prod or prod == 'ε':
                    continue
                symbols = self._split_production(prod)
                all_symbols.update(symbols)
        for symbol in all_symbols:
            if symbol in self.non_terminals:
                continue
            if symbol == 'ε':
                self.terminals.add(symbol)
            elif symbol.isupper() and len(symbol) == 1:
                self.non_terminals.add(symbol)
            else:
                self.terminals.add(symbol)
        for term in ['id', 'num', 'a', 'b', 'c', 'd', 'x', 'y', 'z']:
            if term in str(self.grammar):
                self.terminals.add(term)

    def _split_production(self, prod):
        if not prod or prod == 'ε':
            return []
        if ' ' in prod:
            return [token for token in prod.split() if token]
        potential_symbols = sorted(self.terminals.union(self.non_terminals), key=len, reverse=True)
        tokens = []
        i = 0
        while i < len(prod):
            if prod[i].isspace():
                i += 1
                continue
            matched = False
            for symbol in potential_symbols:
                if symbol and prod.startswith(symbol, i):
                    tokens.append(symbol)
                    i += len(symbol)
                    matched = True
                    break
            if not matched:
                tokens.append(prod[i])
                i += 1
        return tokens

    # --------------------- Grammar Augmentation ---------------------
    def augment_grammar(self):
        new_start = self.original_start + "'"
        self.augmented_grammar = OrderedDict()
        self.augmented_grammar[new_start] = [self.original_start]
        self.augmented_grammar.update(self.grammar)
        self.start_symbol = new_start
        self.non_terminals.add(new_start)
        self.productions = [(new_start, self.original_start)]
        for lhs, rhs_list in self.grammar.items():
            for rhs in rhs_list:
                self.productions.append((lhs, rhs))
        return self.augmented_grammar

    # --------------------- FIRST & FOLLOW ---------------------
    def compute_first_sets(self):
        self.first_sets = {t: {t} for t in self.terminals if t != 'ε'}
        for nt in self.non_terminals:
            self.first_sets[nt] = set()
        self.first_sets['ε'] = {'ε'}
        changed = True
        while changed:
            changed = False
            for lhs, rhs_list in self.augmented_grammar.items():
                for rhs in rhs_list:
                    if not rhs or rhs == 'ε':
                        if 'ε' not in self.first_sets[lhs]:
                            self.first_sets[lhs].add('ε')
                            changed = True
                        continue
                    symbols = self._split_production(rhs)
                    all_have_epsilon = True
                    for symbol in symbols:
                        if symbol in self.terminals:
                            if symbol != 'ε' and symbol not in self.first_sets[lhs]:
                                self.first_sets[lhs].add(symbol)
                                changed = True
                            all_have_epsilon = False
                            break
                        else:
                            first_of_symbol = self.first_sets.get(symbol, set())
                            to_add = first_of_symbol - {'ε'}
                            if not to_add.issubset(self.first_sets[lhs]):
                                self.first_sets[lhs].update(to_add)
                                changed = True
                            if 'ε' not in first_of_symbol:
                                all_have_epsilon = False
                                break
                    if all_have_epsilon and 'ε' not in self.first_sets[lhs]:
                        self.first_sets[lhs].add('ε')
                        changed = True
        return self.first_sets

    def compute_follow_sets(self):
        self.follow_sets = {nt: set() for nt in self.non_terminals}
        self.follow_sets[self.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            new_follow = {nt: set(self.follow_sets[nt]) for nt in self.non_terminals}
            for lhs, rhs_list in self.augmented_grammar.items():
                for rhs in rhs_list:
                    if not rhs or rhs == 'ε':
                        continue
                    symbols = self._split_production(rhs)
                    for i in range(len(symbols)):
                        B = symbols[i]
                        if B not in self.non_terminals:
                            continue
                        # Rule 2a
                        if i + 1 < len(symbols):
                            beta = symbols[i+1:]
                            first_beta = self._first_of_sequence(beta)
                            to_add = first_beta - {'ε'}
                            new_follow[B].update(to_add)
                            if 'ε' in first_beta and lhs != B:
                                new_follow[B].update(self.follow_sets[lhs])
                        else:
                            if lhs != B:
                                new_follow[B].update(self.follow_sets[lhs])
            for nt in self.non_terminals:
                if new_follow[nt] != self.follow_sets[nt]:
                    self.follow_sets[nt] = new_follow[nt]
                    changed = True
        return self.follow_sets

    def _first_of_sequence(self, symbols):
        if not symbols:
            return {'ε'}
        result = set()
        for symbol in symbols:
            if symbol in self.terminals:
                result.add(symbol)
                return result
            first_of_symbol = self.first_sets.get(symbol, set())
            if not first_of_symbol:
                return result
            result.update(first_of_symbol - {'ε'})
            if 'ε' not in first_of_symbol:
                return result
        result.add('ε')
        return result

    # --------------------- DFA Construction ---------------------
    def closure(self, items):
        closure_set = set(items)
        changed = True
        while changed:
            changed = False
            current_items = list(closure_set)
            for item in current_items:
                lhs, rhs, dot_pos = item
                symbols = [] if not rhs or rhs == 'ε' else self._split_production(rhs)
                if dot_pos < len(symbols):
                    next_symbol = symbols[dot_pos]
                    if next_symbol in self.non_terminals:
                        for prod in self.augmented_grammar.get(next_symbol, []):
                            new_item = (next_symbol, prod, 0)
                            if new_item not in closure_set:
                                closure_set.add(new_item)
                                changed = True
        return frozenset(closure_set)

    def goto(self, items, symbol):
        goto_items = set()
        for item in items:
            lhs, rhs, dot_pos = item
            symbols = [] if not rhs or rhs == 'ε' else self._split_production(rhs)
            if dot_pos < len(symbols) and symbols[dot_pos] == symbol:
                goto_items.add((lhs, rhs, dot_pos + 1))
        return self.closure(goto_items) if goto_items else frozenset()

    def build_dfa(self):
        initial_item = (self.start_symbol, self.original_start, 0)
        I0 = self.closure([initial_item])
        self.states = [I0]
        self.dfa_transitions = {}
        queue = [I0]
        while queue:
            current_state = queue.pop(0)
            current_idx = self.states.index(current_state)
            symbols_after_dot = set()
            for item in current_state:
                lhs, rhs, dot_pos = item
                symbols = [] if not rhs or rhs == 'ε' else self._split_production(rhs)
                if dot_pos < len(symbols):
                    symbols_after_dot.add(symbols[dot_pos])
            for symbol in symbols_after_dot:
                goto_state = self.goto(current_state, symbol)
                if goto_state and len(goto_state) > 0:
                    if goto_state not in self.states:
                        self.states.append(goto_state)
                        queue.append(goto_state)
                    goto_idx = self.states.index(goto_state)
                    self.dfa_transitions[(current_idx, symbol)] = goto_idx
        return self.states, self.dfa_transitions

    # --------------------- Parsing Table ---------------------
    def build_parsing_table(self):
        self.parsing_table = {'ACTION': {}, 'GOTO': {}}
        self.conflicts = []
        for i in range(len(self.states)):
            self.parsing_table['ACTION'][i] = {}
            self.parsing_table['GOTO'][i] = {}
        # SHIFT
        for (state_idx, symbol), next_state_idx in self.dfa_transitions.items():
            if symbol in self.terminals and symbol != '$':
                action = f's{next_state_idx}'
                if symbol in self.parsing_table['ACTION'][state_idx]:
                    existing = self.parsing_table['ACTION'][state_idx][symbol]
                    if existing.startswith('r'):
                        self.conflicts.append(f"Shift-Reduce conflict in State I{state_idx}, symbol '{symbol}'")
                self.parsing_table['ACTION'][state_idx][symbol] = action
        # REDUCE
        for state_idx, state in enumerate(self.states):
            for item in state:
                lhs, rhs, dot_pos = item
                symbols = [] if not rhs else self._split_production(rhs)
                if dot_pos == len(symbols):
                    prod_num = next((i for i, (l, r) in enumerate(self.productions) if l == lhs and r == rhs), None)
                    if prod_num is None:
                        continue
                    if lhs == self.start_symbol and rhs == self.original_start:
                        self.parsing_table['ACTION'][state_idx]['$'] = 'acc'
                    else:
                        for terminal in self.follow_sets.get(lhs, set()):
                            if terminal == 'ε':
                                continue
                            action = f'r{prod_num}'
                            existing = self.parsing_table['ACTION'][state_idx].get(terminal)
                            if existing:
                                self.conflicts.append(f"Conflict in State I{state_idx}, symbol '{terminal}'")
                                continue
                            self.parsing_table['ACTION'][state_idx][terminal] = action
        # GOTO
        for (state_idx, symbol), next_state_idx in self.dfa_transitions.items():
            if symbol in self.non_terminals and symbol != self.start_symbol:
                self.parsing_table['GOTO'][state_idx][symbol] = next_state_idx
        return self.parsing_table, self.conflicts

    def parse_string(self, input_string):
        """Parse input string using SLR parsing table"""
        # If there are conflicts, we cannot parse with SLR(1)
        if self.conflicts:
            return {
                'success': False, 
                'steps': [], 
                'message': f'Cannot parse: Grammar has conflicts (not SLR(1)). Conflicts: {len(self.conflicts)} found.'
            }
        
        stack = [0]
        tokens = input_string.split() + ['$']
        input_ptr = 0
        
        steps = []
        step_num = 1
        
        while True:
            current_state = stack[-1]
            current_token = tokens[input_ptr]
            
            action = self.parsing_table['ACTION'].get(current_state, {}).get(current_token, 'error')
            
            stack_str = ' '.join([str(x) for x in stack])
            input_str = ' '.join(tokens[input_ptr:])
            
            if action == 'error':
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': 'ERROR'
                })
                return {'success': False, 'steps': steps, 'message': 'String not accepted'}
            
            if action == 'acc':
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': 'ACCEPT'
                })
                return {'success': True, 'steps': steps, 'message': 'String accepted'}
            
            if action.startswith('s'):
                next_state = int(action[1:])
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': f'Shift to I{next_state}'
                })
                
                stack.append(current_token)
                stack.append(next_state)
                input_ptr += 1
            
            elif action.startswith('r'):
                prod_num = int(action[1:])
                lhs, rhs = self.productions[prod_num]
                
                steps.append({
                    'step': step_num,
                    'stack': stack_str,
                    'input': input_str,
                    'action': f'Reduce by {lhs} -> {rhs if rhs else "ε"}'
                })
                
                if not rhs:
                    rhs_symbols = []
                else:
                    rhs_symbols = self._split_production(rhs)
                
                for _ in range(len(rhs_symbols) * 2):
                    stack.pop()
                
                state_after_pop = stack[-1]
                goto_state = self.parsing_table['GOTO'].get(state_after_pop, {}).get(lhs)
                
                if goto_state is None:
                    return {'success': False, 'steps': steps, 'message': 'GOTO error'}
                
                stack.append(lhs)
                stack.append(goto_state)
            
            step_num += 1
            
            if step_num > 1000:
                return {'success': False, 'steps': steps, 'message': 'Max steps exceeded'}


    def generate_dfa_diagram(self):
        return generate_dfa_diagram_image(self.states, self.dfa_transitions, self._split_production)

    def gen_pdf(self): 
        return generate_pdf(self.grammar,self.start_symbol,self.first_sets, self.follow_sets) 
