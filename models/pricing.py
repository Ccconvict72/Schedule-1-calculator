import math
from models.product import Product

def calculate_soil_cost(soil_type: str) -> float:
    soil_data = {
        "Soil": (10, 1),
        "Long-Life Soil": (30, 2),
        "Extra Long-Life Soil": (60, 3)
    }
    cost, uses = soil_data.get(soil_type, (0, 1))
    return cost / uses

def calculate_enhancer_cost(enhancers: list[str]) -> float:
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

def update_product_prices(products: dict[str, Product],
                          container: str, soil: str,
                          enhancers: list[str], meth_quality: str,
                          disable_prices: bool = False) -> dict[str, Product]:
    soil_cost = calculate_soil_cost(soil)
    enhancer_cost = calculate_enhancer_cost(enhancers)
    pgr = "PGR" in enhancers

    updated_products = {}
    for name, product in products.items():
        price = product.Price  # default
        if disable_prices:
            price = 0
        elif name in ["OGKush", "Sour Diesel", "Green Crack", "Granddaddy Purple"]:
            seed_costs = {"OGKush": 30, "Sour Diesel": 35, "Green Crack": 40, "Granddaddy Purple": 45}
            seed_cost = seed_costs.get(name, 0)
            price = calculate_weed_price(seed_cost, soil_cost, enhancer_cost, container, pgr)
        elif name == "Cocaine":
            price = calculate_cocaine_price(soil_cost, enhancer_cost, container, pgr)
        elif name == "Meth":
            price = calculate_meth_price(meth_quality)
        else:
            # leave price untouched for other products
            pass

        # Update Product (immutably if needed)
        updated_product = Product(
            Name=product.Name,
            Effect=product.Effect,
            Color=product.Color,
            Price=price,
            Value=product.Value,
            Rank=product.Rank,
            Order=product.Order
        )
        updated_products[name] = updated_product

    return updated_products
