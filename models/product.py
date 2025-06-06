# (This file is no longer required for pricing; you can delete or leave it as-is.)
from dataclasses import dataclass

@dataclass
class Product:
    Name: str
    Effect: str
    Color: str
    Price: float
    Value: int
    Rank: str
    Order: int

    def to_dict(self):
        """
        Convert the Product object back to a dictionary for saving.
        """
        return {
            "Name": self.Name,
            "Effect": self.Effect,
            "Color": self.Color,
            "Price": self.Price,
            "Value": self.Value,
            "Rank": self.Rank,
            "Order": self.Order
        }

    def update_price(self, new_price: float):
        """
        Update the product price.
        """
        self.Price = round(new_price, 2)
