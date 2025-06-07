# File: helpers/pricing_manager.py

import math
from typing import List, Dict
from models.schemas import Product, Additive, Effect
from helpers.utils import resource_path

def calculate_soil_cost(soil_type: str) -> float:
    soil_data = {
        "Soil": (10, 1),
        "Long-Life Soil": (30, 2),
        "Extra Long-Life Soil": (60, 3)
    }
    cost, uses = soil_data.get(soil_type, (0, 1))
    return cost / uses

def calculate_enhancer_cost(enhancers: List[str]) -> float:
    return 30 * len(enhancers)

def calculate_weed_price(seed_cost: float, soil_cost: float, enhancer_cost: float,
                         container: str, pgr: bool) -> int:
    if container == "Grow Tent":
        plants = 12 if pgr else 8
    else:
        plants = 16 if pgr else 12
    total_cost = seed_cost + soil_cost + enhancer_cost
    unit_cost = math.ceil(total_cost / plants) + 2
    return unit_cost

def calculate_cocaine_price(soil_cost: float, enhancer_cost: float,
                            container: str, pgr: bool) -> int:
    seed_cost = 80
    if container == "Grow Tent":
        plants = 11 if pgr else 6
    else:
        plants = 16 if pgr else 9
    total_cost = seed_cost + soil_cost + enhancer_cost
    unit_cost = math.ceil(total_cost / plants)
    batch_cost = unit_cost * 20 + 5
    final_unit_price = math.ceil(batch_cost / 10) + 2
    return final_unit_price

def calculate_meth_price(pseudo_quality: str) -> int:
    pseudo_cost = {"Poor": 60, "Standard": 80, "Premium": 110}.get(pseudo_quality, 0)
    batch_cost = pseudo_cost + 80
    final_unit_price = math.ceil(batch_cost / 10) + 2
    return final_unit_price


class PricingManager:
    """
    Wraps pricing utilities and provides a unified interface for calculating:
      – base_cost    : Product.Price   (what it costs you to produce one unit),
      – base_value   : Product.Value   (the raw “sell price” before multipliers),
      – additive_cost: sum of Additive.Price,
      – total_cost   : base_cost + additive_cost,
      – final_price  : base_value × (1 + sum_of_effect_multipliers).
    """

    def __init__(
        self,
        products: Dict[str, Product],
        additives: Dict[str, Additive],
        effects: Dict[str, Effect] = None,
    ):
        self.products = products      # dict[str, Product]
        self.additives = additives    # dict[str, Additive]
        self.effects = effects or {}  # dict[str, Effect]

    def calculate_price(
        self,
        base_product: str,
        additive_names: List[str],
        chosen_effects: List[str],
    ) -> Dict[str, object]:
        """
        1) base_cost = Product.Price
        2) base_value = Product.Value
        3) additive_cost = sum(Additive.Price for each additive in additive_names)
        4) total_cost = base_cost + additive_cost
        5) total_effect_multiplier = sum(Effect.Multiplier for each effect in chosen_effects)
        6) final_sell_price = base_value * (1 + total_effect_multiplier)

        Returns a dict with two keys:
          {
            "cost": {
                "base_cost": float,
                "base_value": float,
                "additives": float,
                "total": float
            },
            "final_price": float
          }
        """
        # ——— 1) Look up the product object ———
        product_obj = self.products.get(base_product)
        if not product_obj:
            base_cost = 0.0
            base_value = 0.0
        else:
            base_cost = float(product_obj.Price)
            base_value = float(product_obj.Value)

        # ——— 2) Additive cost ———
        additive_cost = 0.0
        for name in additive_names:
            add_obj = self.additives.get(name)
            if add_obj and hasattr(add_obj, "Price"):
                additive_cost += float(add_obj.Price)

        # ——— 3) Total cost to produce one unit ———
        total_cost = base_cost + additive_cost

        # ——— 4) Sum of chosen effects’ multipliers ———
        total_effect_multiplier = 0.0
        for eff_name in chosen_effects:
            eff_obj = self.effects.get(eff_name)
            if eff_obj and hasattr(eff_obj, "Multiplier"):
                total_effect_multiplier += float(eff_obj.Multiplier)

        # ——— 5) Final sell price based on base_value ———
        if base_value > 0.0:
            final_price = base_value * (1.0 + total_effect_multiplier)
        else:
            final_price = 0.0

        return {
            "cost": {
                "base_cost": base_cost,
                "base_value": base_value,
                "additives": additive_cost,
                "total": total_cost,
            },
            "final_price": final_price,
        }
