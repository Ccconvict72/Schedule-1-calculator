from helpers.logger import log_debug, log_warning

DEFAULT_COLOR = "#FFFFFF"

class ColorManager:
    def __init__(self, products: dict, effects: dict):
        self.product_colors = {}
        self.effect_colors = {}

        for name, product_data in products.items():
            color = product_data.Color
            if name and color:
                self.product_colors[name.strip()] = color

        for name, effect_data in effects.items():
            color = effect_data.Color
            if name and color:
                self.effect_colors[name.strip()] = color

        log_debug(f"Loaded product colors: {self.product_colors}", tag="ColorManager")
        log_debug(f"Loaded effect colors: {self.effect_colors}", tag="ColorManager")

    def get_product_color(self, name: str) -> str:
        return self.product_colors.get(name, DEFAULT_COLOR)
    
    def get_effect_color(self, name: str) -> str:
        return self.effect_colors.get(name, DEFAULT_COLOR)
