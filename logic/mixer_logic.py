"""
logic/mixer_logic.py

Defines MixerLogic, the class responsible for computing:
1) Effects resulting from mixing a base product with a sequence of additives.
2) Appropriate color assignments and pricing via PricingManager and ColorManager.
"""

from typing import List, Dict, Tuple, Set, Any
from traceback import format_exc

# Helpers
from helpers.logger import log_debug, log_error, log_info
from helpers.pricing_manager import PricingManager
from helpers.color_manager import ColorManager
from helpers.utils import resource_path
from helpers.rank import RankManager


class MixerLogic:
    """
    MixerLogic encapsulates the core “mixing” algorithm:
    - Tracks transformation rules for each additive.
    - Filters available products/additives by rank.
    - Calculates resulting effects, colors, and pricing.
    """

    def __init__(
        self,
        products: Dict[str, Any],
        additives: Dict[str, Any],
        effects: Dict[str, Any],
        transformations: Dict[str, Any],
        rank_manager: RankManager,
        pricing_manager: PricingManager,
        color_manager: ColorManager = None,
    ):
        """
        Initialize MixerLogic.

        Args:
            products (Dict[str, Any]): All product data loaded from models.loader.
            additives (Dict[str, Any]): All additive data loaded from models.loader.
            effects (Dict[str, Any]): All effect data loaded from models.loader.
            transformations (Dict[str, Any]): Transformation rules keyed by ID.
            rank_manager (RankManager): Manages which products/additives are accessible by rank.
            pricing_manager (PricingManager): Calculates cost data for products/additives.
            color_manager (ColorManager, optional): Provides color assignments for products/effects.
        """
        self.products = products
        self.additives = additives
        self.effects = effects
        self.transformations = transformations
        self.rank_manager = rank_manager
        self.pricing_manager = pricing_manager
        self.color_manager = color_manager

        # Build a mapping of additive → {from_effect: to_effect} rules
        self.effect_rules_by_additive = self._build_additive_rules(transformations)
        log_debug("MixerLogic: Built additive-effect transformation rules", tag="MixerLogic")

        # Filter out products/additives not accessible by the current rank
        self._filter_accessible_items()
        log_debug("MixerLogic: Filtered products/additives by accessible rank", tag="MixerLogic")

    def _build_additive_rules(self, transformations: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Construct a nested dict mapping each additive name to its transformation rules:
            { additive_name: { from_effect: to_effect, ... }, ... }

        Args:
            transformations (Dict[str, Any]): All transformation rule objects.

        Returns:
            Dict[str, Dict[str, Any]]: Mapping additive → its from→to rules.
        """
        rules: Dict[str, Dict[str, Any]] = {}
        for t in transformations.values():
            # Each transformation object has attributes: Additive, From, To
            rules.setdefault(t.Additive, {})[t.From] = t.To
        return rules

    def _filter_accessible_items(self):
        """
        Filter the products and additives dicts to include only those
        accessible by the current rank (via rank_manager).
        Stores filtered results in:
          - self.filtered_products
          - self.filtered_additives
        """
        self.filtered_products = {
            name: self.products[name]
            for name in self.rank_manager.get_accessible_product_names()
            if name in self.products
        }
        self.filtered_additives = {
            name: self.additives[name]
            for name in self.rank_manager.get_accessible_additive_names()
            if name in self.additives
        }

    def get_filtered_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Return filtered products/additives for UI dropdowns.

        Returns:
            Dict[str, Dict[str, Any]]: {"products": filtered_products, "additives": filtered_additives}
        """
        return {
            "products": self.filtered_products,
            "additives": self.filtered_additives,
        }

    def calculate_mix(
        self,
        base_product_name: str,
        additives_selected: List[str],
        max_effects: int = 8
    ) -> Tuple[
        List[str],           # effects list
        Dict[str, str],      # effect_colors mapping
        str,                 # base_color hex string
        float,               # base_product      (rounded)
        float,               # additive_total    (rounded)
        float,               # total_cost        (rounded)
        float                # final_price       (rounded)
    ]:
        """
        Compute the resulting effects and pricing of mixing a base product with additives.

        Steps:
        1) Validate base product exists; raise ValueError if unknown.
        2) Start with the base product’s existing effects.
        3) For each additive in sequence:
            a) Apply transformation rules: replace “from” effects with “to” effects.
            b) Append additive-specific effects if room remains (up to max_effects).
        4) Calculate pricing via PricingManager.
        5) Assign colors via ColorManager for base and each effect.

        Args:
            base_product_name (str): Name of the base product to mix.
            additives_selected (List[str]): List of additive names in chosen sequence.
            max_effects (int, optional): Maximum number of effects to include. Defaults to 8.

        Returns:
            Tuple[List[str], Dict[str, str], str, float, float, float, float]:
                - effects: Final list of effect names.
                - effect_colors: Mapping effect_name → color hex string.
                - base_color: Color hex string for the base product.
                - base_product: Rounded cost of the base product.
                - additive_total: Rounded cumulative cost of all additives.
                - total_cost: Rounded sum of base + additive costs.
                - final_price: Rounded sell price computed by PricingManager.
        """
        try:
            # Retrieve base product object; strip whitespace
            base_product = self.products.get(base_product_name.strip())
            if not base_product:
                raise ValueError(f"Unknown base product '{base_product_name}'")

            # Clean up additive list (remove blank or whitespace-only strings)
            additives_selected = [a.strip() for a in additives_selected if a.strip()]

            # Get base product’s initial effects (string→list if necessary)
            base_effect = getattr(base_product, "Effect", []) or []
            if isinstance(base_effect, str):
                base_effect = [base_effect]
            effects: List[str] = [e for e in base_effect if isinstance(e, str)]

            # Collect additive data (name, effects, transformation rules)
            all_additives: List[Dict[str, Any]] = []
            if effects:
                all_additives.append({
                    "Name": getattr(base_product, "Name", base_product_name),
                    "Effect": effects,
                    "EffectRules": getattr(base_product, "EffectRules", {}) or {}
                })

            for additive_name in additives_selected:
                additive = self.additives.get(additive_name)
                if not additive:
                    continue
                ae = getattr(additive, "Effect", []) or []
                if isinstance(ae, str):
                    ae = [ae]
                all_additives.append({
                    "Name": additive_name,
                    "Effect": [e for e in ae if isinstance(e, str)],
                    "EffectRules": self.effect_rules_by_additive.get(additive_name, {})
                })

            # Process each additive in sequence, applying transformation rules first
            for additive in all_additives:
                name = additive["Name"]
                rules = additive["EffectRules"]
                additive_effects = additive["Effect"]

                planned_removals: Set[str] = set()
                planned_additions: Set[str] = set()
                skipped: List[Tuple[str, str]] = []

                # 1) Apply transformation rules: old→new
                for old in list(effects):
                    if old in rules:
                        new = rules[old]
                        if new not in effects and new not in planned_additions:
                            planned_removals.add(old)
                            planned_additions.add(new)
                        else:
                            skipped.append((old, new))

                effects = [e for e in effects if e not in planned_removals] + list(planned_additions)

                # Handle skipped rules (old still present, new not yet added)
                for old, new in reversed(skipped):
                    if old in effects and new not in effects:
                        effects.remove(old)
                        effects.append(new)

                # 2) Append additive-specific effects up to max_effects
                for ae in additive_effects:
                    if ae not in effects and len(effects) < max_effects:
                        effects.append(ae)

            # Calculate pricing details
            price_data = self.pricing_manager.calculate_price(
                base_product=base_product_name,
                additive_names=additives_selected,
                chosen_effects=effects
            )

            # Round each cost field and the final_price to nearest dollar
            cost = price_data.get("cost", {})
            rounded_base   = round(cost.get("base_cost", 0))
            rounded_add    = round(cost.get("additives", 0))
            rounded_total  = round(cost.get("total", 0))
            rounded_price  = round(price_data.get("final_price", 0))

            # Determine colors for base product and each effect
            base_color = (
                self.color_manager.get_product_color(base_product_name)
                if self.color_manager else "#FFFFFF"
            )
            effect_colors = {
                effect: (self.color_manager.get_effect_color(effect) or "#FFFFFF")
                for effect in effects
            }

            log_info(f"MixerLogic: calculate_mix success for base '{base_product_name}'", tag="MixerLogic")
            return (
                effects,
                effect_colors,
                base_color,
                rounded_base,
                rounded_add,
                rounded_total,
                rounded_price
            )

        except Exception as e:
            log_error(f"MixerLogic: Mixing failed: {e}\n{format_exc()}", tag="MixerLogic")
            # Fallback: return empty effects and zero costs, with default color
            fallback_color = (
                self.color_manager.get_product_color("default")
                if self.color_manager else "#FFFFFF"
            )
            return [], {}, fallback_color, 0.0, 0.0, 0.0, 0.0

    def apply_additives(self, product_name: str, additive_sequence: List[str]) -> Set[str]:
        """
        Convenience method to compute resulting effects (as a set) given a product and additive list.
        Ignores pricing; returns only the final effects set.

        Args:
            product_name (str): Product to start with.
            additive_sequence (List[str]): Sequence of additive names.

        Returns:
            Set[str]: Set of resulting effect names.
        """
        try:
            effects, *_ = self.calculate_mix(product_name, additive_sequence)
            return set(effects)
        except Exception as e:
            log_error(f"MixerLogic: apply_additives failed: {e}", tag="MixerLogic")
            return set()
