"""Replay the supplied plans and probe mission rules using Python's standard library.

This checker supports the typed, conjunctive STRIPS subset used by these files.
It is independent of Pyperplan's search and relevance pruning; it is not VAL.
Run from any directory: python3 /path/to/validation/check_model.py
"""
from pathlib import Path
import copy
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKS = []


def parse(text):
    tokens = iter(re.findall(r'\(|\)|[^\s()]+', re.sub(r';[^\n]*', '', text).lower()))
    def read(first):
        if first != '(':
            return first
        result = []
        for token in tokens:
            if token == ')':
                return result
            result.append(read(token))
        raise ValueError('Unclosed list')
    result = read(next(tokens))
    assert next(tokens, None) is None
    return result


def typed(tokens):
    result, pending = {}, []
    i = 0
    while i < len(tokens):
        if tokens[i] == '-':
            result.update((x, tokens[i+1]) for x in pending)
            pending = []
            i += 2
        else:
            pending.append(tokens[i])
            i += 1
    result.update((x, 'object') for x in pending)
    return result


def conjunction(expr):
    return expr[1:] if expr[0] == 'and' else [expr]


class Model:
    def __init__(self, mission):
        folder = ROOT/'PDDL'/('PartC' if mission == 3 else 'PartA&B')
        self.domain_text = (folder/('domain-ext.pddl' if mission == 3 else 'domain.pddl')).read_text()
        d = parse(self.domain_text)
        p = parse((folder/f'mission{mission}.pddl').read_text())
        self.sections = {x[0]: x[1:] for x in p[2:]}
        self.objects = typed(self.sections[':objects'])
        self.initial = {tuple(f) for f in self.sections[':init']}
        self.goals = {tuple(f) for f in conjunction(self.sections[':goal'][0])}
        self.actions = {}
        for item in d[2:]:
            if item[0] == ':action':
                fields = dict(zip(item[2::2], item[3::2]))
                self.actions[item[1]] = (typed(fields[':parameters']),
                    conjunction(fields[':precondition']), conjunction(fields[':effect']))

    def step(self, state, text):
        tokens = text.strip('()').split()
        params, pres, effs = self.actions[tokens[0]]
        args = tokens[1:]
        assert len(args) == len(params), text
        assert all(self.objects.get(a) == typ for a, typ in zip(args, params.values())), text
        binding = dict(zip(params, args))
        ground = lambda atom: tuple(binding.get(x, x) for x in atom)
        if not all(ground(p) in state for p in pres):
            raise ValueError('Unsatisfied precondition: '+text)
        deletes = {ground(e[1]) for e in effs if e[0] == 'not'}
        adds = {ground(e) for e in effs if e[0] != 'not'}
        return (state - deletes) | adds

    def trace(self, *steps):
        state = set(self.initial)
        for step in steps:
            state = self.step(state, step)
            self.invariants(state)
        return state

    def invariants(self, state):
        facts = lambda name, obj: [f for f in state if f[0] == name and f[1] == obj]
        for obj, typ in self.objects.items():
            if typ == 'rover':
                assert len(facts('belongs-to', obj)) == 1
                assert len(facts('rover-at', obj)) + len(facts('aboard', obj)) == 1
                assert len(facts('carrying-image', obj)) + len(facts('carrying-scan', obj)) + len(facts('memory-free', obj)) == 1
                assert len(facts('carrying-sample', obj)) + len(facts('sample-slot-free', obj)) == 1
            if typ == 'lander':
                assert len(facts('lander-at', obj)) == 1
                assert len(facts('sample-stored', obj)) + len(facts('lander-storage-free', obj)) == 1
            if typ == 'astronaut':
                assert len(facts('astronaut-belongs-to', obj)) == 1
                assert len(facts('in-control-room', obj)) + len(facts('in-docking-bay', obj)) == 1
                home = facts('astronaut-belongs-to', obj)[0][2]
                assert all(f[2] == home for f in facts('in-control-room', obj)+facts('in-docking-bay', obj))
        for name in ('connected', 'belongs-to', 'lander-at', 'astronaut-belongs-to'):
            assert {f for f in state if f[0] == name} == {f for f in self.initial if f[0] == name}


def check(label, condition):
    assert condition, label
    CHECKS.append(label)


def blocked(model, state, action, label):
    try:
        model.step(state, action)
    except ValueError:
        check(label, True)
    else:
        raise AssertionError('Action unexpectedly allowed: '+label)


def main():
    models = {n: Model(n) for n in (1, 2, 3)}
    edges = {
        1: {(1,2),(1,4),(2,3),(4,3),(3,5),(5,1)},
        2: {(1,2),(2,1),(2,3),(2,4),(4,2),(3,5),(5,3),(5,6),(6,4)}
    }
    for n, model in models.items():
        plan = (ROOT/'validation'/f'mission{n}.plan').read_text().splitlines()
        state = model.trace(*[line for line in plan if line.strip() and not line.startswith(';')])
        check(f'Mission {n}: plan replay, invariants at every step, all delivery goals', model.goals <= state)
        expected = {('connected', f'wp{a}', f'wp{b}') for a,b in edges[1 if n == 1 else 2]}
        check(f'Mission {n}: exact directed map', {f for f in model.initial if f[0] == 'connected'} == expected)
        # No mission-specific object names may occur in a reusable domain.
        clean = re.sub(r';[^\n]*', '', model.domain_text)
        check(f'Mission {n}: no hard-coded mission objects in domain', not(set(re.findall(r'[^\s()]+', clean)) & set(model.objects)))
        print(f'Mission {n}: {len(plan)} actions, replay PASS')

    m = models[1]
    for action in ['move r1 wp1 wp2', 'capture-image r1 wp1', 'perform-scan r1 wp1', 'collect-sample r1 wp1']:
        blocked(m, m.initial, action, 'Undeployed rover cannot '+action.split()[0])
    state = m.trace('deploy r1 l1 wp1')
    blocked(m, m.initial, 'deploy r1 l1 wp2', 'Deployment requires landing site')
    blocked(m, state, 'deploy r1 l1 wp1', 'No repeated deployment')
    blocked(m, state, 'move r1 wp1 wp5', 'No implicit reverse edge WP1 to WP5')
    blocked(m, state, 'transmit-image r1 l1 wp1', 'Cannot transmit an unacquired image')
    blocked(m, state, 'transmit-scan r1 l1 wp1', 'Cannot transmit an unacquired scan')
    state = m.trace('deploy r1 l1 wp1', 'capture-image r1 wp1')
    check('Acquisition does not save data', ('image-saved','l1','wp1') not in state)
    for action in ['capture-image r1 wp1', 'perform-scan r1 wp1']:
        blocked(m, state, action, 'Image occupies shared memory: '+action.split()[0])
    blocked(m, state, 'transmit-scan r1 l1 wp1', 'Wrong data kind cannot be transmitted')
    state = m.trace('deploy r1 l1 wp1', 'perform-scan r1 wp1')
    blocked(m, state, 'capture-image r1 wp1', 'Scan blocks image acquisition')
    blocked(m, state, 'perform-scan r1 wp1', 'Scan blocks second scan')
    state = m.trace('deploy r1 l1 wp1', 'capture-image r1 wp1', 'collect-sample r1 wp1')
    check('Data and sample slots are independent', ('carrying-sample','r1','wp1') in state)
    blocked(m, state, 'collect-sample r1 wp1', 'Cannot carry a second sample')
    check('Pickup does not store sample', ('sample-stored','l1','wp1') not in state)
    state = m.trace('deploy r1 l1 wp1', 'collect-sample r1 wp1', 'store-sample r1 l1 wp1 wp1', 'collect-sample r1 wp1')
    blocked(m, state, 'store-sample r1 l1 wp1 wp1', 'Filled lander rejects another sample')
    state = m.trace('deploy r1 l1 wp1', 'move r1 wp1 wp2', 'collect-sample r1 wp2')
    blocked(m, state, 'store-sample r1 l1 wp2 wp1', 'Sample cannot be delivered remotely')
    blocked(m, state, 'store-sample r1 l1 wp2 wp2', 'Cannot invent a lander landing site')
    state = m.trace('deploy r1 l1 wp1', 'capture-image r1 wp1', 'transmit-image r1 l1 wp1', 'perform-scan r1 wp1')
    check('Transmission frees memory for new data', ('carrying-scan','r1','wp1') in state)

    m = models[2]
    state = m.trace('deploy r2 l2 wp1', 'move r2 wp1 wp2', 'capture-image r2 wp2')
    blocked(m, state, 'transmit-image r2 l1 wp2', 'Cannot transmit to another rover\'s lander')
    blocked(m, m.initial, 'deploy r2 l1 wp2', 'Cannot deploy from another lander')
    state = m.trace('move r1 wp2 wp1', 'collect-sample r1 wp1')
    blocked(m, state, 'store-sample r1 l2 wp1 wp1', 'Cannot store in another lander even when co-located')
    # r1 has not visited its lander: start at WP3 and transmit to L1 at WP2.
    remote = copy.deepcopy(m)
    remote.initial.remove(('rover-at','r1','wp2'))
    remote.initial.add(('rover-at','r1','wp3'))
    state = remote.trace('capture-image r1 wp3', 'transmit-image r1 l1 wp3')
    check('Wireless transfer needs no current or historical lander visit', ('image-saved','l1','wp3') in state)

    m = models[3]
    blocked(m, m.initial, 'deploy r2 l2 wp1 bob', 'Bob in control room cannot enable deployment')
    blocked(m, m.initial, 'deploy r2 l2 wp1 alice', 'Alice cannot assist another lander')
    state = m.trace('capture-image r1 wp2')
    blocked(m, state, 'transmit-image r1 l1 wp2 alice', 'Alice in docking bay cannot enable transmission')
    state = m.trace('capture-image r1 wp2', 'go-to-control-room alice l1', 'transmit-image r1 l1 wp2 alice')
    check('Control-room presence enables transmission', ('image-saved','l1','wp2') in state)
    state = m.trace('go-to-docking-bay bob l2', 'deploy r2 l2 wp1 bob', 'collect-sample r2 wp1', 'go-to-control-room bob l2')
    blocked(m, state, 'store-sample r2 l2 wp1 wp1 bob', 'Control-room presence cannot enable sample storage')
    state = m.step(state, 'go-to-docking-bay bob l2')
    state = m.step(state, 'store-sample r2 l2 wp1 wp1 bob')
    check('Docking-bay presence enables sample storage', ('sample-stored','l2','wp1') in state)
    blocked(m, m.initial, 'go-to-control-room alice l2', 'Astronaut cannot move between landers')
    base3 = {f for f in m.initial if f[0] not in ('astronaut-belongs-to','in-docking-bay','in-control-room')}
    check('Mission 3 preserves Mission 2 map, rover setup and goals', base3 == models[2].initial and m.goals == models[2].goals)
    print('\n'+ '\n'.join('PASS '+label for label in CHECKS))
    print(f'\n{len(CHECKS)} checks passed. This is a focused semantic check, not a formal proof or VAL run.')


if __name__ == '__main__':
    main()
