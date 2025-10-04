import random
from itertools import count
from pprint import PrettyPrinter
class Node: 
    def __init__(self, id:int, parent = None):
        self.parent = parent
        self.id = id
        self.children = []
        self.test_type = None
        self.test_env = None
        self.instruments = None
        self.people = None
        
    def __repr__(self) -> str:
        return f'ID: {self.id} NUMBER OF CHILDREN: {len(self.children)}'

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "children": [c.to_dict() for c in self.children]
        }

    def add_child(self, child):
        self.children.append(child)

        

def build_tree(depth: int, min_child: int, max_child:int) -> Node:

    if depth < 0:
        raise ValueError("depth must be >= 0")
    if min_child > max_child or min_child < 0:
        raise ValueError("invalid child range")

    node_id = count(start=0)
    head = Node(next(node_id))
    level = [head]

    for _ in range(depth):
        next_level: list[Node] = []
        for parent in level:
            num_child = random.randint(min_child, max_child)
            child_list = [Node(next(node_id),parent) for _ in range(num_child)]
            parent.children.extend(child_list)
            next_level.extend(child_list)
        level = next_level

    return head
            
if __name__ == '__main__':
    chain = build_tree(5,1,10)
    pretty_printer = PrettyPrinter(indent=2, sort_dicts=False)
    pretty_printer.pprint(chain.to_dict())