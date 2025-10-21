from math import sqrt

def compare_cost(a, b, metric="euclidean", penalty=0.0):
    if len(a) != len(b):
        raise ValueError("Points must have the same dimensionality.")

    if metric == "euclidean":
        base = sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))
    elif metric == "manhattan":
        base = sum(abs(ai - bi) for ai, bi in zip(a, b))
    elif metric == "chebyshev":
        base = max(abs(ai - bi) for ai, bi in zip(a, b))
    else:
        raise ValueError(f"Unknown metric: {metric}")

    return base + penalty


if __name__ == "__main__":
    A = (0, 0)
    B = (3, 4)
    C = (5, 1)

    print(compare_cost(A, B, metric="euclidean"))
    print(compare_cost(A, B, metric="manhattan"))
    print(compare_cost(A, B, metric="chebyshev"))
    print(compare_cost(A, C, metric="euclidean", penalty=2))
