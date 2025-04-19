from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Tuple
import math

app = FastAPI()

# Root route to avoid 404 error

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h2> FastAPI Delivery Cost Estimator is Running </h2>
    <p>Use <code>POST /calculate-cost</code> with product quantities in the request body to calculate delivery cost.</p>
    """

class Order(BaseModel):
    A: int = 0
    B: int = 0
    C: int = 0
    D: int = 0
    E: int = 0
    F: int = 0
    G: int = 0
    H: int = 0
    I: int = 0


class DeliveryNetwork:
    def __init__(self):
        self.product_weight = {
            "A": 3,   # C1
            "B": 2,   # C1
            "C": 8,   # C1
            "D": 12,  # C2
            "E": 25,  # C2
            "F": 15,  # C2
            "G": 0.5,  # C3
            "H": 1,   # C3
            "I": 2    # C3
        }
        self.warehouse_stock = {
            "C1": ["A", "B", "C"],
            "C2": ["D", "E", "F"],
            "C3": ["G", "H", "I"]
        }

        # Distance graph (bidirectional)
        self.distances = {
            ("C1", "C2"): 4,
            ("C1", "L1"): 3,
            ("C2", "L1"): 2.5,
            ("C2", "C3"): 3,
            ("C3", "L1"): 2
        }

    def get_distance(self, from_loc: str, to_loc: str) -> float:
        if (from_loc, to_loc) in self.distances:
            return self.distances[(from_loc, to_loc)]
        elif (to_loc, from_loc) in self.distances:
            return self.distances[(to_loc, from_loc)]
        else:
            return float("inf")  # invalid route

    def get_product_location(self, product: str) -> str:
        for center, items in self.warehouse_stock.items():
            if product in items:
                return center
        return None

    def delivery_cost_per_km(self, weight: float) -> float:
        if weight <= 5:
            return 10
        else:
            extra = math.ceil((weight - 5) / 5)
            return 10 + (extra * 8)

    def build_trip_plan(self, order: Dict[str, int]) -> List[Tuple[str, List[str]]]:
        center_to_products = {"C1": [], "C2": [], "C3": []}
        for product, qty in order.items():
            if qty > 0:
                center = self.get_product_location(product)
                if center:
                    center_to_products[center].extend([product] * qty)
        return [(center, products) for center, products in center_to_products.items() if products]


class DeliveryPlanner:
    def __init__(self, network: DeliveryNetwork):
        self.network = network

    def calculate_min_cost(self, order: Dict[str, int]) -> float:
        trip_plan = self.network.build_trip_plan(order)
        starting_centers = [center for center, _ in trip_plan]
        min_cost = float("inf")
        for start in starting_centers:
            cost = self.simulate_delivery(start, trip_plan)
            min_cost = min(min_cost, cost)
        return round(min_cost, 2)

    def simulate_delivery(self, start: str, trip_plan: List[Tuple[str, List[str]]]) -> float:
        current_location = start
        visited = set()
        total_cost = 0
        trip_sequence = trip_plan.copy()
        while trip_sequence:
            for idx, (center, products) in enumerate(trip_sequence):
                if center in visited:
                    continue
                if current_location != center:
                    dist = self.network.get_distance(current_location, center)
                    total_cost += dist * self.network.delivery_cost_per_km(0)
                    current_location = center
                weight = sum(
                    self.network.product_weight[product] for product in products)
                to_l1_dist = self.network.get_distance(current_location, "L1")
                rate = self.network.delivery_cost_per_km(weight)
                total_cost += to_l1_dist * rate
                current_location = "L1"
                visited.add(center)
                break
            else:
                break
        return total_cost

@app.post("/calculate-cost")
def calculate_cost(order: Order):
    order_dict = order.dict()
    network = DeliveryNetwork()
    planner = DeliveryPlanner(network)
    cost = planner.calculate_min_cost(order_dict)
    return {"minimum_cost": cost}
