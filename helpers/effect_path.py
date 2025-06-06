"""
helpers/effect_path.py

Core BFS logic for “unmixing” (finding which additives produce desired effects),
plus helper functions for applying additive rules and picking the best product.
"""

from collections import deque
from typing import List, Tuple, Dict, Set, FrozenSet, Optional, Any

# ----- Data classes -----
class Additive:
    def __init__(self, Name: str, Effect: Any, Price: float):
        self.Name = Name
        self.Effect = Effect
        self.Price = Price

# ----- Core BFS and logic -----

State = Tuple[FrozenSet[str], Tuple[str, ...]]

def apply_additive(
    current_effects: Set[str],
    additive_name: str,
    additive_obj: Additive,
    nested_rules: Dict[str, Dict[str, str]],
    max_effects: int
) -> Set[str]:
    """
    Given a set of current effects, an additive name/object, nested replacement rules,
    and a max number of allowable effects, return the new set of effects after applying that additive.
    """
    print(f"\n[apply_additive] Applying additive: {additive_name}")
    print(f"[apply_additive] Current effects: {current_effects}")

    # Get any replacement rules for this additive
    rules = nested_rules.get(additive_name, {})
    additive_effects = set(
        additive_obj.Effect if isinstance(additive_obj.Effect, list) else [additive_obj.Effect]
    )
    print(f"[apply_additive] Additive effects: {additive_effects}")
    print(f"[apply_additive] Nested rules: {rules}")

    planned_removals = set()
    planned_additions = set()
    skipped = []

    # First, handle any explicit replacement rules
    for old in list(current_effects):
        if old in rules:
            new = rules[old]
            if new not in current_effects and new not in planned_additions:
                planned_removals.add(old)
                planned_additions.add(new)
                print(f"[apply_additive] Replacing effect '{old}' with '{new}'")
            else:
                skipped.append((old, new))
                print(f"[apply_additive] Skipping replacement '{old}' -> '{new}' (already present)")

    # Remove old effects, add new ones
    new_effects_list = [e for e in current_effects if e not in planned_removals] + list(planned_additions)

    # Re‐apply any “skipped” rules in reverse order if appropriate
    for old, new in reversed(skipped):
        if old in new_effects_list and new not in new_effects_list:
            new_effects_list.remove(old)
            new_effects_list.append(new)
            print(f"[apply_additive] Applied skipped replacement '{old}' -> '{new}'")

    # Finally, add any direct effects the additive grants (so long as we haven’t exceeded max_effects)
    for ae in additive_effects:
        if ae not in new_effects_list and len(new_effects_list) < max_effects:
            new_effects_list.append(ae)
            print(f"[apply_additive] Adding new additive effect '{ae}'")

    new_effects = set(new_effects_list)
    print(f"[apply_additive] New effects after additive: {new_effects}")
    return new_effects


def forward_effect_search(
    product_effects: Set[str],
    desired_effects: Set[str],
    additives: Dict[str, Additive],
    nested_rules: Dict[str, Dict[str, str]],
    max_effects: int = 8,
    max_depth: int = 20,
    cancel_flag: Optional[callable] = None
) -> Optional[List[Tuple[str, Set[str]]]]:
    """
    Perform a breadth‐first search from the product’s base effects to reach all desired_effects.
    Each step “applies” one additive. Stops when desired_effects ⊆ current_effects or max_depth reached.

    Returns:
      - List of (additive_name, resulting_effects_set) if successful
      - None if no path is found or cancel_flag() returns True
    """
    print(f"\n[forward_effect_search] Starting BFS from effects: {product_effects}")
    print(f"[forward_effect_search] Desired effects: {desired_effects}")

    start_state: State = (frozenset(product_effects), ())
    queue = deque([start_state])
    visited = {start_state[0]: 0}  # maps frozen set of effects → depth

    while queue:
        current_effects_frozen, additive_seq = queue.popleft()
        current_effects = set(current_effects_frozen)
        print(f"\n[forward_effect_search] Visiting state: effects={current_effects}, Path={additive_seq}")

        # Check for cancellation
        if cancel_flag and cancel_flag():
            print("[forward_effect_search] Cancelled by flag.")
            return None

        # If we've already satisfied desired_effects, reconstruct steps
        if desired_effects.issubset(current_effects):
            print("[forward_effect_search] Desired effects achieved!")
            steps: List[Tuple[str, Set[str]]] = []
            effects = set(product_effects)
            for addy in additive_seq:
                additive_obj = additives.get(addy)
                effects = apply_additive(effects, addy, additive_obj, nested_rules, max_effects)
                steps.append((addy, set(effects)))
            return steps

        # If depth limit reached, skip expanding this node
        if len(additive_seq) >= max_depth:
            print(f"[forward_effect_search] Max depth {max_depth} reached, skipping state.")
            continue

        # Try applying each additive to expand the BFS frontier
        for addy_name, additive_obj in additives.items():
            new_effects = apply_additive(current_effects, addy_name, additive_obj, nested_rules, max_effects)
            effects_frozen = frozenset(new_effects)
            if effects_frozen not in visited or len(additive_seq) + 1 < visited[effects_frozen]:
                visited[effects_frozen] = len(additive_seq) + 1
                new_path = additive_seq + (addy_name,)
                print(f"[forward_effect_search] Enqueueing: effects={new_effects}, Path={new_path}")
                queue.append((effects_frozen, new_path))

    print("[forward_effect_search] No path found to achieve desired effects.")
    return None


def calculate_path_cost(
    product_name: str,
    path: List[Tuple[str, Set[str]]],
    products: Dict[str, Dict],
    additives: Dict[str, Additive]
) -> float:
    """
    Sum up the base product’s price plus the price of each additive in the path.
    Expects products: { product_name: {"Price": float, ...}, ... }
            additives: { additive_name: Additive(Name, Effect, Price), ... }
    """
    total_cost = products[product_name]["Price"]
    print(f"\n[calculate_path_cost] Starting cost with product '{product_name}': {total_cost}")
    for additive_name, _ in path:
        additive_obj = additives.get(additive_name)
        if additive_obj and hasattr(additive_obj, "Price"):
            total_cost += additive_obj.Price
            print(f"[calculate_path_cost] Adding cost of additive '{additive_name}': {additive_obj.Price} -> Total: {total_cost}")
    return total_cost


def pick_best_product(
    products: Dict[str, Dict],
    additives: Dict[str, Additive],
    desired_effects: Set[str],
    nested_rules: Dict[str, Dict[str, str]],
    max_effects: int = 8,
    max_depth: int = 40,
) -> Tuple[Optional[str], Optional[List[Tuple[str, Set[str]]]], Optional[float]]:
    """
    Evaluate each product’s base effects. If a product’s base already includes desired_effects,
    return it immediately (with no add-ons). Otherwise, run forward_effect_search for each product
    and pick the one with the shortest path (breaking ties by lower total additive cost).

    Returns:
      (best_product_name, best_path, best_cost) or (None, None, None) if no solution.
    """
    best_product = None
    best_path = None
    best_cost = float("inf")
    best_length = float("inf")

    print(f"\n[pick_best_product] Picking best product from: {list(products.keys())}")
    for product_name, product_data in products.items():
        # Extract base effects from the product_data
        product_effects: Set[str] = set()
        if "Effect" in product_data:
            if isinstance(product_data["Effect"], list):
                product_effects = set(product_data["Effect"])
            else:
                product_effects = {product_data["Effect"]}

        print(f"\n[pick_best_product] Evaluating product '{product_name}' with effects: {product_effects}")

        path = forward_effect_search(
            product_effects=product_effects,
            desired_effects=desired_effects,
            additives=additives,
            nested_rules=nested_rules,
            max_effects=max_effects,
            max_depth=max_depth,
        )

        if path is None:
            print(f"[pick_best_product] No path found for product '{product_name}'")
            continue

        path_length = len(path)
        total_cost = calculate_path_cost(product_name, path, products, additives)

        print(f"[pick_best_product] Path length: {path_length}, Cost: {total_cost}")

        # Choose the shortest path, or if equal length, the cheaper cost
        if path_length < best_length or (path_length == best_length and total_cost < best_cost):
            print(f"[pick_best_product] New best product found: {product_name}")
            best_product = product_name
            best_path = path
            best_cost = total_cost
            best_length = path_length

    if best_product:
        print(f"\n[pick_best_product] Best product: {best_product}, Cost: {best_cost}, Path length: {best_length}")
    else:
        print("\n[pick_best_product] No product can achieve the desired effects.")

    return best_product, best_path, best_cost


# ----- Example usage for testing -----
if __name__ == "__main__":
    products = {
        "Addy": {"Name": "Addy", "Effect": "Thought-Provoking", "Price": 2},
        "OGKush": {"Name": "OGKush", "Effect": "Calming", "Price": 3.75},
    }

    additives = {
        "Addy": Additive("Addy", "Thought-Provoking", 2),
        "OGKush": Additive("OGKush", "Calming", 3.75),
    }

    nested_rules = {
        # e.g. "Addy": {"OldEffect": "NewEffect", ...},
    }

    desired_effects = {"Calming"}

    best_product, best_path, best_cost = pick_best_product(
        products, additives, desired_effects, nested_rules
    )

    if best_product:
        print(f"\nBest product: {best_product}")
        print(f"Total cost: {best_cost}")
        print("Effect chain path:")
        for additive_name, effects in best_path:
            print(f"Additive: {additive_name} -> effects: {effects}")
    else:
        print("No product can achieve the desired effects.")
