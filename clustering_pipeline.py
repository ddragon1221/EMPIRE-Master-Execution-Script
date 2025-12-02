import pandas as pd
import numpy as np
from spectral_algorithm import *
from IC import *

def is_sparse_group(adj_sub, S_group=0.40):
    A = np.asarray(adj_sub.values, dtype=float)

    # Make binary if not already 0/1
    A_bin = (A > 0).astype(int)
    # Zero diagonal for safety
    np.fill_diagonal(A_bin, 0)

    n = A_bin.shape[0]
    max_edges = n * (n - 1) // 2
    if max_edges == 0:
        return False

    iu = np.triu_indices(n, k=1)
    edges = int(A_bin[iu].sum())
    density = edges / max_edges

    return (n >= 4) and (density <= S_group)

def spectral_analysis(adj_matrix_list, adj_matrix, elements):
    # Run spectral analysis using the provided adjacency as-is (no mutation)
    k_min = 2
    k_max = len(adj_matrix_list)//2
    # List of all possible groupins with k_min groups to k_max groups
    k_list = {}
    for k in range(k_min, k_max + 1):
        # Functions from spectral analysis
        V_k = spectral_clustering(adj_matrix, k)
        labels = apply_kmeans(V_k, k)
        labels = np.asarray(labels).ravel().astype(int)
        # Create DataFrame to hold Components and their grouping number
        df_k = pd.DataFrame({"Component": list(map(str, elements)), "Module": labels})
        # Sort to maintain grouping order
        df_k = df_k.sort_values("Module", kind="stable", ignore_index=True)
        k_list[f"k_{k}"] = df_k
    return k_list

# Calculates system complexity based on ICdata.py
def calculate_complexity(adj_matrix_list, adj_matrix, int_matrix_list, int_matrix, k_list):
    complexity = [1] * len(adj_matrix_list)
    systemC1 = sum_system_complexities(complexity)
    systemC2 = calculate_C2(adj_matrix_list, int_matrix_list)
    ge = calculate_ge(adj_matrix)
    totalComp = len(adj_matrix)
    systemC3 = calculate_C3(ge, totalComp)
    systemC2C3 = systemC2 * systemC3
    systemC = systemC1 + systemC2C3
    systemComplexity = round(systemC,2)
    lowest_complexity = None

    # Iterates through all k_# groups and calculates their respective complexity
    for i, k_order in k_list.items():
        ordered_components = k_order["Component"].tolist()
        module_assignments = k_order["Module"].tolist()

        x = sum_components_by_module(module_assignments)
        module_bounds = get_module_bounds(x)

        adj_ordered = adj_matrix.loc[ordered_components, ordered_components]
        int_ordered = int_matrix.loc[ordered_components, ordered_components]

        adj_modules = extract_modules(adj_ordered, module_bounds)
        int_modules = extract_modules(int_ordered, module_bounds)

        module_C1_values = calculate_module_complexity(complexity,module_bounds)
        c2, ge = calculate_module_C2_GE(adj_modules, int_modules)
        c3, c2xc3 = calculate_module_C2_C3(c2,ge,x)
        sum_moduleC2C3 = sum(c2xc3)
        intComp = systemC2C3 - sum_moduleC2C3
        normalizedIntComp = 1 - (sum_moduleC2C3/systemC2C3)
        if(lowest_complexity == None):
            lowest_complexity = (i, normalizedIntComp)
        elif(lowest_complexity[1] > normalizedIntComp):
            lowest_complexity = (i, normalizedIntComp)
        #print(f"Normalized Integrative Complexity = {normalizedIntComp:.3f} when k = {i}")
    # prints lowest integrative complexity
    #print(f"lowest complexity is when {lowest_complexity[0]}") # type: ignore
    low_com_df = k_list[lowest_complexity[0]] # type: ignore
    # Seperates k split into touples (element names, adjacency matrix, interaction matrix)
    module_groups = []
    # 0 - number of groups at that k, split k_# text for range
    for i in range(int(lowest_complexity[0][2:])):  # type: ignore
        module_group_i = low_com_df[low_com_df['Module'] == i]['Component'].astype(str).tolist()
        sub_adj_matrix = adj_matrix.loc[module_group_i, module_group_i]
        sub_i_matrix = int_matrix.loc[module_group_i, module_group_i]
        group_dict = {
            "elements"   : module_group_i,
            "adj_matrix" : sub_adj_matrix,
            "int_matrix" : sub_i_matrix
        }
        module_groups.append(group_dict)
    #for i, group in enumerate(module_groups):
        #print(f"Group {i} Contains:\n{group["elements"]}")
        #print(f"SubMatrix is:\n{group["adj_matrix"]}\n")
    return module_groups

def split_elements(
        adj_matrix_list: list[list[int]],
        names: list[str],
        SPARSE_CUTOFF: float = 0.4
        )-> list[pd.DataFrame] | None:
    adj_matrix = pd.DataFrame(adj_matrix_list, names, names)
    head_matrix = adj_matrix
    int_matrix_list = []
    for i in range(len(adj_matrix_list)):
        row = []
        for j in range(len(adj_matrix_list[i])):
            element = adj_matrix_list[i][j]
            if element == 1:
                element = 0.1
            row.append(element)
        int_matrix_list.append(row)
    int_matrix = pd.DataFrame(int_matrix_list, index=names, columns=names)

    if is_sparse_group(adj_matrix, SPARSE_CUTOFF):
        k_list = spectral_analysis(adj_matrix_list, adj_matrix, names)
        return calculate_complexity(adj_matrix_list, adj_matrix, int_matrix_list, int_matrix, k_list)

    return None
