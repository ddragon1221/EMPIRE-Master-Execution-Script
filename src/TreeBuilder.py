import random
from itertools import count
from pprint import PrettyPrinter
from cora_distance import *
from stone_visuals import *
class Node: 
    def __init__(self, id:int, instrument: tuple, test: TestType, enviroment: Environment, parent = None):
        self.parent = parent
        self.id = id
        self.children = []
        self.instrument = instrument
        self.test = test
        self.enviroment = enviroment
        
    def __repr__(self) -> str:
        return f'ID: {self.id}'

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "children": [c.to_dict() for c in self.children],
            "intrument": self.instrument[0],
            "test": self.test.name,
            "enviroment": self.enviroment.name,
        }

    def add_child(self, child):
        self.children.append(child)

class NodeBuilder():
    def __init__(self):
        self.instuments = list(generate_instrument_catalog().items())
        self.tests = list(generate_test_data().values())
        self.enviroment = list(generate_environment_data().values())
    def add_node(self, id:int, parent = None):
        return Node(
            id,
            random.choice(self.instuments),
            random.choice(self.tests),
            random.choice(self.enviroment),
            parent,
            )
        

def build_tree(depth: int, min_child: int, max_child:int) -> tuple:
    node_builder = NodeBuilder()
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if min_child > max_child or min_child < 0:
        raise ValueError("invalid child range")

    node_id = count(start=0)
    head = node_builder.add_node(next(node_id))
    level = [head]
    node_list = [head]

    for _ in range(depth):
        next_level: list[Node] = []
        for parent in level:
            num_child = random.randint(min_child, max_child)
            child_list = [node_builder.add_node(next(node_id),parent) for _ in range(num_child)]
            parent.children.extend(child_list)
            next_level.extend(child_list)
            node_list.extend(child_list)
        level = next_level

    return (head, node_list)
            
if __name__ == '__main__':
    chain, node_list = build_tree(3,2,3)
    pretty_printer = PrettyPrinter(indent=2, sort_dicts=False)
    pretty_printer.pprint(chain.to_dict())
    print(node_list)