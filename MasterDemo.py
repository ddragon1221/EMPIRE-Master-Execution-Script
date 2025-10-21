# MasterDemo.py
# Temporary integration file to connect team modules.

from src.TreeBuilder import build_tree
from src.distance import generate_instrument_catalog
from src.stone_visuals import generate_visuals

def main():
    # 1. Build fake integration chain (Kyle)
    root = build_tree(depth=2, min_child=1, max_child=3)
    print("Integration tree built with root:", root.id)

    # 2. Generate instrument catalog (Cora)
    instruments = generate_instrument_catalog()
    print("Instrument catalog sample:", list(instruments.items())[:3])

    # 3. Generate visuals (Stone)
    generate_visuals("./out_viz")

if __name__ == "__main__":
    main()
