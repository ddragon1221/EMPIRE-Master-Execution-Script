import pandas as pd
import random
from clustering_pipeline import split_elements
from arch_gen import *
from graphviz_helpers.arch_graphviz import render_architecture
from graphviz_helpers.ici_graphviz import render_ici
from graphviz_helpers.ici_networkx import build_ici_nx, draw_ici_matplotlib, export_ici_pyvis

class ICINode:
    """Holds system elements and represends grouping for integration
    Double linked list structure
    Interfaces are used for grouping algorthim
    """
    node_id = 1
    
    def __init__(self):
        self.node_id = ICINode.node_id
        ICINode.node_id += 1
        self.system_elements = []
        self.interfaces = []
        self.parent = None
        self.children = []
        self.verifications = []

    def add_system_element(self, element):
        self.system_elements.append(element)
    
    def add_child(self, ici):
        self.children.append(ici)

    def set_parent(self, ici):
        self.parent = ici

    def add_interface(self, ICI_interface_node, inhereted_from):
        relationship = (ICI_interface_node, inhereted_from)
        if(relationship not in self.interfaces):
            self.interfaces.append(relationship)

def associate_interfaces(ICI_list: list[ICINode], unused_system_elements: set[SystemElement]):
    '''
    Takes in a list of ICI nodes and a set of unused system elements.
    Associates interfaces between ICI nodes based on the interfaces of their
    owned system elements. Add system elements to ICI nodes if all their children
    are already owned by that ICI node.
    '''
    
    for ici_node in ICI_list:
        owned_elements = set(ici_node.system_elements)
        # list of system elements that can be adopted by this ICI node
        can_adopt = [
            system_element
            for system_element in unused_system_elements
            if all(
                # system_element.children
                child in owned_elements
                for child in system_element.children
            )
        ]
        # Adopt the system elements, remove them from unused set
        for system_element in can_adopt:
            ici_node.add_system_element(system_element)
            unused_system_elements.remove(system_element)
    
    # Create a mapping of system element's interfaces to their owning ICI node
    system_element_owner = {
        system_element: ici_node
        for ici_node in ICI_list
        for system_element in ici_node.system_elements
    }
    
    for ici_node in ICI_list:
        # All owned system elements in that ICI node
        for system_element in ici_node.system_elements:
            # All interfaces in that system element
            for interface in system_element.interfaces:
                # pick the opposite endpoint of the interface relative to this system_element
                if hasattr(interface, "p_element") and hasattr(interface, "r_element"):
                    lookup_element = interface.p_element if interface.r_element == system_element else interface.r_element
                else:
                    lookup_element = interface.recieves if interface.recieves != system_element else interface.provides
                # Find the owner of that interface
                interface_owner = system_element_owner.get(lookup_element)
                # Add interface relationship if owners are different
                if interface_owner and interface_owner != ici_node:
                    ici_node.add_interface(interface_owner, system_element)
    
    return ICI_list, unused_system_elements

def build_foundational_ici_nodes(system_elements: list[SystemElement]) -> list[ICINode]:
    '''
    Builds foundational ICI nodes from a list of system elements only if they have no children.
    '''
    ICI_list = []
    for se in system_elements:
        if not se.children:
            ici_node = ICINode()
            ici_node.add_system_element(se)
            ICI_list.append(ici_node)
    return ICI_list

def build_dsm(ICI_list: list[ICINode]) -> list[list[int]]:
    # iterate over ici nodes interfaces.
    
    def has_interface(ici_a, ici_b):
        interfaces = [interface[0] for interface in ici_a.interfaces]
        return ici_b in interfaces
    
    dsm = [
        [0 for _ in range(len(ICI_list))]
        for _ in range(len(ICI_list))
        ]
    for i in range(len(dsm)):
        for j in range(len(dsm)):
            if(i == j or has_interface(ICI_list[i], ICI_list[j])):
                dsm[i][j] = 1
    
    return dsm

def build_non_zero_dsm(ICI_list: list[ICINode]):
    '''
    Checks if a DSM is a zero DSM, meaning no interfaces exist between ICI nodes.
    If any ICI nodes have no interfaces, a new valid dsm is created and returned
    Return format: (list: used_ICI_list, list: updated_dsm)
    '''
    dsm = build_dsm(ICI_list)
    
    # track ICI with no interfaces
    removed_ici = []
    for i in range(len(dsm)):
        is_row_zero = True
        for j in range(len(dsm)):
            if(i != j and dsm[i][j] == 1):
                is_row_zero = False
                break
        if is_row_zero:
            removed_ici.append(ICI_list[i])
    # If new dsm needs to be built
    if(removed_ici):
        non_zero_icis = [
            e
            for e in ICI_list
            if e not in removed_ici
            ]
        fixed_dsm = build_dsm(non_zero_icis)
        return non_zero_icis, fixed_dsm
    return ICI_list, dsm

def get_ici_groups(groups: list[pd.DataFrame], used_ICI_list: list[ICINode]) -> list[list[ICINode]]:
    """Get groups of ici nodes based on groupings of element ids

    Args:
        groups (list[pd.DataFrame]): dataframe that contains groups based on element id
        used_ICI_list (list[ICINode]): single list of all ICINodes used to generate groups

    Returns:
        list[list[ICINode]]: proper groupings of ICI based on results given
    """
    ici_groups = []
    for g in groups:
        ici_g = []
        elements = g["elements"]
        for ici in used_ICI_list:
            if str(ici.node_id) in elements:
                ici_g.append(ici)
        ici_groups.append(ici_g)
    return ici_groups

def merge_ici_groups(ici_groups: list[list[ICINode]]) -> list[ICINode]:
    """Based on grouped ICI's create one ICI to hold them

    Returns:
        list[ICINode]: List of ICI nodes that hold previous groups
    """
    new_icis = []
    for g in ici_groups:
        parent = ICINode()
        for element in g:
            parent.add_child(element)
            element.set_parent(parent)
            for sys_element in element.system_elements:
                parent.add_system_element(sys_element)
        new_icis.append(parent)
    return new_icis

def inherit_descendants(head_ici: ICINode) -> None:
    """For each ICI, add all descendant SystemElements of its primary element."""
    def descendants(root_se: SystemElement) -> list[SystemElement]:
        out = []
        queue = list(root_se.children)
        while queue:
            se = queue.pop(0)
            out.append(se)
            queue.extend(se.children)
        return out

    queue = [head_ici]
    while queue:
        ici = queue.pop(0)
        queue.extend(ici.children)

        if not ici.system_elements:
            continue
        primary_se = ici.system_elements[0]
        for se in descendants(primary_se):
            if se not in ici.system_elements:
                ici.add_system_element(se)

def inherit_verifications(head_ici: ICINode) -> None:
    """For each ICI, collect ver_type of interfaces where both endpoints are in that ICI."""
    queue = [head_ici]
    while queue:
        ici = queue.pop(0)
        queue.extend(ici.children)

        if not hasattr(ici, "verifications"):
            ici.verifications = []  # initialize if missing

        seen = set()
        for se in ici.system_elements:
            for interface in getattr(se, "interfaces", []):
                # identify the other endpoint of the interface
                other = interface.p_element if interface.r_element == se else interface.r_element
                if other in ici.system_elements:
                    vt = getattr(interface, "ver_type", None)
                    if vt and (id(interface) not in seen):
                        seen.add(id(interface))
                        ici.verifications.append(vt)


def run_ICI_integration_unoptimized(system_elements: list[SystemElement]):
    # Get groups of system elements and put them in a ici.
    head_sys = system_elements[0]
    se_to_ici: dict[SystemElement, ICINode] = {}
    head_ici = ICINode()
    head_ici.add_system_element(head_sys)
    se_to_ici[head_sys] = head_ici
    queue = [head_sys]
    while queue:
            se = queue.pop(0)
            parent_ici = se_to_ici[se]

            for child_se in se.children:
                # create ICINode for child if not already
                child_ici = se_to_ici.get(child_se)
                if child_ici is None:
                    child_ici = ICINode()
                    child_ici.add_system_element(child_se)
                    se_to_ici[child_se] = child_ici
                    queue.append(child_se)

                # wire parent/child relationship between ICIs
                parent_ici.add_child(child_ici)
                child_ici.set_parent(parent_ici)
    inherit_descendants(head_ici)
    inherit_verifications(head_ici)
    return head_ici

def run_ICI_integration_optimized(system_elements: list[SystemElement], sparcity = 0.4):
    '''
    Main function to run ICI integration on a list of system elements.
    '''

    # Build foundational ICI nodes from leaf system elements
    ICI_list = build_foundational_ici_nodes(system_elements)
    while len(ICI_list) > 1:
        # Create a set of unused system elements
        unused = set(system_elements) - {
            se
            for ici_node in ICI_list
            for se in ici_node.system_elements
        }
        # Associate interfaces and adopt system elements
        while True:
            len_unused = len(unused)
            ICI_list, unused = associate_interfaces(ICI_list, unused)
            if len(unused) == len_unused:
                break
        # Build dsm, see if any create zero dsm if so put asside
        used_ICI_list, dsm = build_non_zero_dsm(ICI_list)
        unused_ICI_list = [
            ici_node
            for ici_node in ICI_list
            if ici_node not in used_ICI_list
        ]
        # Create labels for group tracking
        names = [
            str(ici_element.node_id)
            for ici_element in used_ICI_list
            ]
        # gets dict with groupings and their element ids
        groups = split_elements(dsm, names, sparcity)
        ici_groups = [used_ICI_list]
        if groups:
            ici_groups = get_ici_groups(groups, used_ICI_list)
        # Make new ICI nodes that inheret the new groupings
        ICI_list = merge_ici_groups(ici_groups) + unused_ICI_list
    head = ICI_list[0]
    for element in system_elements:
        if element not in head.system_elements:
            head.add_system_element(element)
    inherit_verifications(head)
    return head

if __name__ == "__main__":
    # Generate System Architecture
    set_seed(718)
    system_elements = generate_architecture(layers=5, max_children=3)
    generate_interfaces(system_elements, 0)
    ici_optimized = run_ICI_integration_optimized(system_elements)
    ici_unoptimized = run_ICI_integration_unoptimized(system_elements)

    for ver in ici_optimized.verifications:
        if isinstance(ver, Test):
            print(f"{ver.test_id}")
    print("Done")

    # ____ Visuals ____
    #render_architecture(system_elements, output_path="output/architecture_graph", format="png")
    #render_ici(head, output_path="output/1_ici_hierarchy", format="png", include_elements=True)
    #render_ici(head, output_path="output/2_ici_hierarchy", format="png", include_elements=False)

    #G0 = build_ici_nx(system_elements, include_elements=True)
    G1 = build_ici_nx(ici_optimized, include_elements=True)
    G2 = build_ici_nx(ici_unoptimized, include_elements=True)

    #export_ici_pyvis(G0, html_path="output/ici_nx.html")
    export_ici_pyvis(G1, html_path="output/ici_optimized.html")
    export_ici_pyvis(G2, html_path="output/ici_unoptimized.html")
