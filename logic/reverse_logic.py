"""
logic/reverse_logic.py

Defines ReverseLogic, responsible for computing:
1) The additive sequence (“unmix”) that achieves desired effects from a product.
2) Selecting the best product given a set of desired effects.
Handles rank-based filtering, nested effect rules, and integrates PricingManager.
"""

from typing import Dict, List, Any, Set, Union
from traceback import format_exc

# Helpers
from helpers.logger import log_debug, log_info, log_error
from helpers.effect_utils import extract_effects
from helpers.rank import RankManager
from helpers.pricing_manager import PricingManager
from helpers.effect_path import forward_effect_search
from helpers.utils import resource_path
from models.loader import load_additives


class ReverseLogic:
    """
    ReverseLogic encapsulates the “unmixing” algorithm:
    - Filters products/additives by rank.
    - Uses nested effect rules to find a sequence of additives.
    - Computes pricing via PricingManager.
    """

    def __init__(
        self,
        products: Dict[str, Any],
        effect_rules: Dict[str, Dict[str, str]],
        rank_manager: RankManager,
        pricing_manager: PricingManager = None,
    ):
        """
        Initialize ReverseLogic.

        Args:
            products (Dict[str, Any]): All product data loaded from models.loader.
            effect_rules (Dict[str, Dict[str, str]]): Nested effect transformation rules.
            rank_manager (RankManager): Manages accessibility of products/additives.
            pricing_manager (PricingManager, optional): Calculates cost data.
        """
        # Filter products by accessible rank
        allowed_products = rank_manager.get_accessible_product_names()
        self.products = {
            name: data
            for name, data in products.items()
            if name in allowed_products
        }
        self.nested_rules = effect_rules

        # Load and filter additives by rank
        all_additives = load_additives()
        allowed_additives = rank_manager.get_accessible_additive_names()
        self.additives = {
            name: obj
            for name, obj in all_additives.items()
            if name in allowed_additives
        }

        self.cancel_requested = False
        self.pricing_manager = pricing_manager
        self.rank_manager = rank_manager

        log_debug(
            f"ReverseLogic initialized with {len(self.products)} products "
            f"and {len(self.nested_rules)} nested effect rules.",
            tag="ReverseLogic"
        )

    def cancel(self) -> None:
        """
        Signal to cancel any ongoing search. Background worker checks cancel_flag().
        """
        self.cancel_requested = True
        log_debug("ReverseLogic: Cancel requested (flag set to True)", tag="ReverseLogic")

    def reset_cancel_flag(self) -> None:
        """
        Reset cancel flag to False before starting a new operation.
        """
        self.cancel_requested = False
        log_debug("ReverseLogic: Cancel flag reset to False", tag="ReverseLogic")

    def unmix(
        self,
        product_name: str,
        desired_effects: List[str]
    ) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Compute the sequence of additives needed to achieve desired_effects from product_name.

        Steps:
        1) Validate product exists (return error if unknown).
        2) Extract base product’s effects.
        3) Call forward_effect_search to find additive sequence (returns list of (additive, effects_set)).
        4) If no path or cancelled, return appropriate error.
        5) Compute pricing via PricingManager.
        6) Return dict with product, steps, final_effects, cost, and sell_value.

        Args:
            product_name (str): Starting product name.
            desired_effects (List[str]): List of desired effect names.

        Returns:
            Dict[str, Any] on success, or {"error": str} on failure.
        """
        self.reset_cancel_flag()
        log_debug(
            f"ReverseLogic: Starting unmix for product='{product_name}' "
            f"with desired_effects={desired_effects}",
            tag="ReverseLogic"
        )

        product = self.products.get(product_name)
        if not product:
            log_error(f"ReverseLogic: Unknown product '{product_name}'", tag="ReverseLogic")
            return {"error": f"Unknown product: '{product_name}'"}

        base_effects = extract_effects(product)
        log_debug(f"ReverseLogic: Extracted base effects: {base_effects}", tag="ReverseLogic")

        path = forward_effect_search(
            product_effects=base_effects,
            desired_effects=set(desired_effects),
            additives=self.additives,
            nested_rules=self.nested_rules,
            cancel_flag=lambda: self.cancel_requested,
        )

        if self.cancel_requested:
            log_info("ReverseLogic: Unmix operation cancelled by user", tag="ReverseLogic")
            return {"error": "❌ Operation cancelled by user."}

        if not path:
            log_info(
                f"ReverseLogic: No additive sequence found to achieve desired_effects={desired_effects}",
                tag="ReverseLogic"
            )
            return {
                "error": (
                    "❌ No additive sequence can produce all of: "
                    f"{', '.join(desired_effects)} from '{product_name}'"
                )
            }

        additive_names = [addy for addy, _ in path]
        final_eff = path[-1][1] if path else set()
        log_debug(f"ReverseLogic: Path found: {path}", tag="ReverseLogic")

        # Compute pricing (use correct keyword chosen_effects)
        price_data = self.pricing_manager.calculate_price(
            base_product=product_name,
            additive_names=additive_names,
            chosen_effects=final_eff,
        )
        # Round each cost field and final_price to nearest dollar
        cost = price_data.get("cost", {})
        rounded_base   = round(cost.get("base_cost", 0))
        rounded_add    = round(cost.get("additives", 0))
        rounded_total  = round(cost.get("total", 0))
        rounded_price  = round(price_data.get("final_price", 0))

        # Rename keys so the UI can read cost["base_product"], cost["additives"], cost["total"]
        price_data["cost"] = {
            "base_product": rounded_base,
            "additives": rounded_add,
            "total": rounded_total
        }
        price_data["final_price"] = rounded_price

        log_debug(f"ReverseLogic: Price calculation completed: {price_data}", tag="ReverseLogic")

        return {
            "product": product_name,
            "steps": path,
            "final_effects": list(final_eff),
            "cost": price_data["cost"],
            "sell_value": price_data["final_price"],
        }

    def pick_best_product(
        self,
        desired_effects: List[str]
    ) -> Union[Dict[str, Any], Dict[str, str]]:
        """
        Choose the best product that either:
        a) Directly contains all desired_effects in its base effects, or
        b) Has the shortest additive sequence to reach desired_effects.

        Steps:
        1) Look for direct matches among products.
        2) If found, compute pricing and return.
        3) Otherwise, for each product with base_effects, run forward_effect_search.
        4) Track the product with the shortest valid path.
        5) If none found, return error.
        6) Otherwise compute pricing and return result dict.

        Args:
            desired_effects (List[str]): List of desired effect names.

        Returns:
            Dict[str, Any] on success, or {"error": str} on failure.
        """
        log_debug(
            f"ReverseLogic: Starting pick_best_product for desired_effects={desired_effects}",
            tag="ReverseLogic"
        )

        # 1) Check direct matches
        direct_matches: List[(str, int)] = []
        for prod_name, prod_data in self.products.items():
            base_effects = extract_effects(prod_data)
            if set(desired_effects).issubset(base_effects):
                direct_matches.append((prod_name, len(base_effects)))
                log_debug(f"ReverseLogic: Direct match found: {prod_name} with effects {base_effects}", tag="ReverseLogic")

        if direct_matches:
            direct_matches.sort(key=lambda x: x[1])
            best_prod_name = direct_matches[0][0]
            base_eff = extract_effects(self.products[best_prod_name])
            log_debug(f"ReverseLogic: Best direct match selected: {best_prod_name}", tag="ReverseLogic")

            price_data = self.pricing_manager.calculate_price(
                base_product=best_prod_name,
                additive_names=[],
                chosen_effects=base_eff,
            )
            # Round costs
            cost = price_data.get("cost", {})
            rounded_base   = round(cost.get("base_cost", 0))
            rounded_add    = round(cost.get("additives", 0))
            rounded_total  = round(cost.get("total", 0))
            rounded_price  = round(price_data.get("final_price", 0))

            price_data["cost"] = {
                "base_product": rounded_base,
                "additives": rounded_add,
                "total": rounded_total
            }
            price_data["final_price"] = rounded_price

            log_debug(f"ReverseLogic: Price calculation for direct match {best_prod_name}: {price_data}", tag="ReverseLogic")

            return {
                "product": best_prod_name,
                "steps": [],
                "final_effects": list(base_eff),
                "cost": price_data["cost"],
                "sell_value": price_data["final_price"],
            }

        # 2) Search mixing paths for each product
        best_product = None
        best_path = None
        best_path_len = None

        for prod_name, prod_data in self.products.items():
            base_eff = extract_effects(prod_data)
            if not base_eff:
                log_debug(f"ReverseLogic: Skipping product {prod_name} – no base effects", tag="ReverseLogic")
                continue

            log_debug(f"ReverseLogic: Attempting forward_effect_search for product {prod_name}", tag="ReverseLogic")
            path = forward_effect_search(
                product_effects=base_eff,
                desired_effects=set(desired_effects),
                additives=self.additives,
                nested_rules=self.nested_rules,
                cancel_flag=lambda: self.cancel_requested,
            )

            if self.cancel_requested:
                log_info("ReverseLogic: pick_best_product operation cancelled by user", tag="ReverseLogic")
                return {"error": "❌ Operation cancelled by user."}

            if path:
                log_debug(f"ReverseLogic: Path found for product {prod_name}: {path}", tag="ReverseLogic")
                if best_path_len is None or len(path) < best_path_len:
                    best_product = prod_name
                    best_path_len = len(path)
                    best_path = path
                    log_debug(f"ReverseLogic: New best path selected: product={best_product}, length={best_path_len}", tag="ReverseLogic")

        if not best_product:
            log_info(
                f"ReverseLogic: No product found that can achieve desired_effects={desired_effects}",
                tag="ReverseLogic"
            )
            return {
                "error": f"❌ No product can achieve all of: {', '.join(desired_effects)}"
            }

        additive_names = [addy for addy, _ in best_path]
        final_eff = best_path[-1][1] if best_path else set()
        log_debug(f"ReverseLogic: Best product {best_product}, final effects: {final_eff}", tag="ReverseLogic")

        price_data = self.pricing_manager.calculate_price(
            base_product=best_product,
            additive_names=additive_names,
            chosen_effects=final_eff,
        )
        # Round costs
        cost = price_data.get("cost", {})
        rounded_base   = round(cost.get("base_cost", 0))
        rounded_add    = round(cost.get("additives", 0))
        rounded_total  = round(cost.get("total", 0))
        rounded_price  = round(price_data.get("final_price", 0))

        price_data["cost"] = {
            "base_product": rounded_base,
            "additives": rounded_add,
            "total": rounded_total
        }
        price_data["final_price"] = rounded_price

        log_debug(f"ReverseLogic: Price calculation for best product {best_product}: {price_data}", tag="ReverseLogic")

        return {
            "product": best_product,
            "steps": best_path,
            "final_effects": list(final_eff),
            "cost": price_data["cost"],
            "sell_value": price_data["final_price"],
        }
