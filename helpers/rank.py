from typing import Dict, List

class RankManager:
    def __init__(self, ranks, products, additives):
        self.rank_order = list(ranks)
        self.products = products
        self.additives = additives
        self.current_rank = None
        self.current_rank_index = None

        self._product_map = products
        self._additive_map = additives

    def set_current_rank(self, rank_name):
        if rank_name not in self.rank_order:
            raise ValueError(f"Invalid rank: {rank_name}")
        self.current_rank = rank_name
        self.current_rank_index = self.rank_order.index(rank_name)

    def _is_rank_allowed(self, required_rank):
        if required_rank is None:
            return True
        try:
            return self.rank_order.index(required_rank) <= self.current_rank_index
        except ValueError:
            return False

    def get_accessible_product_names(self):
        return {
            name for name, data in self._product_map.items()
            if self._is_rank_allowed(data.Rank)
        }

    def get_accessible_additive_names(self):
        return {
            name for name, data in self._additive_map.items()
            if self._is_rank_allowed(data.Rank)
        }

    def get_product_metadata(self, name):
        return self._product_map.get(name)

    def get_additive_metadata(self, name):
        return self._additive_map.get(name)
    
    def get_unlock_order_map(self) -> Dict[str, int]:
        """
        Returns a dict mapping product/additive names to their unlock rank index for sorting.
        Lower index means earlier unlock.
        """
        unlock_map = {}

        def get_rank_index(rank_name):
            try:
                return self.rank_order.index(rank_name)
            except ValueError:
                return 9999  # Unknown or missing ranks get the last index

        # Map products
        for name, data in self._product_map.items():
            unlock_map[name] = get_rank_index(data.rank)

        # Map additives
        for name, data in self._additive_map.items():
            unlock_map[name] = get_rank_index(data.rank)

        return unlock_map

def sorted_accessible_items(items: Dict[str, dict], ranks_order: List[str]) -> List[str]:
    # items is dict like {"Donut": {"rank": "Streetrat I", ...}, ...}
    # ranks_order is list like ["Streetrat I", "Streetrat II", ...]
    
    def sort_key(name):
        rank = items[name].get("rank", "")
        try:
            rank_index = ranks_order.index(rank)
        except ValueError:
            rank_index = 9999  # Put unknown ranks last
        return (rank_index, name.lower())
    
    return sorted(items.keys(), key=sort_key)
