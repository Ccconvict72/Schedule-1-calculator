"""
helpers/pricing_manager.py

This module defines:
1) Utility functions to calculate soil cost, enhancer cost, and specialized prices for weed, cocaine, and meth.
2) A PricingManager class that wraps these utilities and provides a `calculate_price` method used by MixerLogic and ReverseLogic.
"""

import math
from typing import List, Dict
from models.schemas import Product, Additive  # Pydantic schemas

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
      - Base product cost
      - Additive cost
      - Total cost (base + additives)
      - Final sell price
    """
    def __init__(
        self,
        products: Dict[str, Product],
        additives: Dict[str, Additive],
        effects: Dict[str, object] = None,
    ):
        self.products = products      # dict[str, Product]
        self.additives = additives    # dict[str, Additive]
        self.effects = effects or {}

    def calculate_price(
        self,
        base_product: str,
        additive_names: List[str],
        effects: List[str],
    ) -> Dict[str, object]:
        """
        Compute pricing data for a mix or unmix operation.

        Args:
          base_product (str): Name of the base product.
          additive_names (List[str]): List of additive names applied.
          effects (List[str]): Resulting effects (unused for cost, but included).

        Returns:
          {
            "cost": {
              "base_product": float,
              "additives": float,
              "total": float
            },
            "final_price": float
          }
        """
        # 1) Base product cost: read the product’s Price
        base_obj = self.products.get(base_product)
        base_cost = float(base_obj.Price) if base_obj else 0.0

        # 2) Additive cost: sum each additive’s Price
        additive_cost = 0.0
        for name in additive_names:
            additive = self.additives.get(name)
            if additive and hasattr(additive, 'Price'):
                additive_cost += float(additive.Price)

        # 3) Total cost
        total_cost = base_cost + additive_cost

        # 4) Final sell price: same as the product’s Price
        final_price = float(base_obj.Price) if base_obj else 0.0

        return {
            "cost": {
                "base_product": base_cost,
                "additives": additive_cost,
                "total": total_cost,
            },
            "final_price": final_price,
        }
