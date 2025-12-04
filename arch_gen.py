
import random
import copy
from Inputs import *


default_seed = 718
random.seed(default_seed)

class SystemElement:
    """Holds information for System Elements
    Double linked list
    Contains interfaces its associted with
    Holds all elements functions and capabilities
    """
    element_id = 0
    function_id = 0
    capability_id = 0

    def __init__(self):
        self.element_id = self.get_element_id()
        self.parent = None
        self.children = []
        self.interfaces = []
        self.functions = []
        self.capabilities = []
        self.foundational = None

    def set_parent(self, parent):
        self.parent = parent

    def assign_foundational(self, found_cost: FoundationalCosts):
        self.foundational = found_cost

    def get_element_id(self):
        SystemElement.element_id += 1
        return SystemElement.element_id

    def add_function(self):
        SystemElement.function_id += 1
        self.functions.append(f"F{SystemElement.function_id}")

    def add_capability(self):
        SystemElement.capability_id += 1
        self.capabilities.append(f"F{SystemElement.capability_id}")

    def add_interface(self, interface):
        self.interfaces.append(interface)

class Interface:
    """Holds information on an interface:
        p_element    : System Element providing function
        r_element    : System Element depending on function
        p_function   : Function that is provided
        r_function   : Function that depends on provided function
        r_capability : Capability achieved through interface
        ver_type     : Verification type for interface
    """
    def __init__(self, p_element: SystemElement, r_element: SystemElement):
        self.p_element = p_element
        self.r_element = r_element
        self.p_function = p_element.functions[-1]
        self.r_function = r_element.functions[-1]
        self.r_capability = r_element.capabilities[-1]
        self.ver_type = self.set_ver_type()

    def set_ver_type(self):
        # Randomly choose a verification class and initilize it
        return random.choices(
            ver_types,
            ver_weights
        )[0]()

def assign_interface(provider: SystemElement,
                    reciever: SystemElement):
    """Creates an Interface Class and associates it between two system elements

    Args:
        provider (SystemElement): System Element providing a funciton
        reciever (SystemElement): System Element depending on a function
    """
    # Adds needed functions and capabilities to system elements
    provider.add_function()
    reciever.add_function()
    reciever.add_capability()
    # Generate interface and associate them to the system elements
    interface = Interface(provider, reciever)
    provider.add_interface(interface)
    reciever.add_interface(interface)

def generate_architecture(layers: int, max_children: int):
    """Generates a double linked list of System Elements

    Args:
        layers (int): Depth of tree structure generated
        max_children (int): Maximum number of child nodes created for a parent

    Returns:
        _type_: _description_
    """
    past_layer = []
    current_layer = []
    all_elements = []
    for i in range(layers):
        # First layer is just head node
        if(i == 0):
            head = SystemElement()
            past_layer = [head]
            all_elements.append(head)
            continue

        for element in past_layer:
            # Randomly generate a number of children
            num_children = random.randint(0, max_children)
            # System elements can not have only 1 child
            if num_children < 2:
                continue
            for _ in range(num_children):
                child = SystemElement()
                element.children.append(child)
                child.set_parent(element)
                current_layer.append(child)
        all_elements += current_layer
        past_layer = copy.copy(current_layer)
    return all_elements

def generate_interfaces(all_elements: list[SystemElement], prob_interface = 0.4):
    """
    Given a list of system elements,
    generates interfaces between children of system elements
    randomly assigns an additional interface to any node in the system
    """
    for element in all_elements:
        children  = element.children
        for child in children:
            # get all children that arent itself
            valid_interfaces = [
                e
                for e in children
                if e != child
                ]
            # assign interface
            interface_element = random.choices(valid_interfaces)[0]
            assign_interface(child, interface_element)
            # 15% chance to randomly assign an additional interface
            if (random.random() < prob_interface):
                # While loop to find an element that isnt itself of head node
                interface_element = child
                while interface_element in (child, all_elements[0]):
                    interface_element = random.choices(all_elements)[0]
                assign_interface(child, interface_element)

def assign_foundational_costs(all_elements: list[SystemElement]):
    """Generates a object that holds costs and assigns it to all foundational system elements
    """
    for element in all_elements:
        if not element.children:
            # 50% chance to add a manufactured cost
            manufactured_flag = bool(random.randint(0,1))
            element.assign_foundational(FoundationalCosts(manufactured_flag))

def set_seed(seed: int):
    random.seed(seed)