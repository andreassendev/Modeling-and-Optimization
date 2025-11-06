"""
Valgfri plotting utility for TSP turer
"""

import os
from typing import List, Dict, Tuple


def plot_tour(tour: List[int], coords: Dict[str, Tuple[float, float]], 
              cities: List[str], title: str = "TSP Tour", 
              save_path: str = None) -> None:
    """
    Plotter TSP tur ved hjelp av matplotlib
    """
    try:
        import matplotlib.pyplot as plt
        
        if not tour:
            print("Tom tur - kan ikke plotte")
            return
        
        # Extract coordinates for tour
        x_coords = [coords[cities[i]][0] for i in tour]
        y_coords = [coords[cities[i]][1] for i in tour]
        
        # Close the tour
        x_coords.append(x_coords[0])
        y_coords.append(y_coords[0])
        
        plt.figure(figsize=(12, 10))
        plt.plot(x_coords, y_coords, 'b-o', linewidth=2, markersize=10, 
                markerfacecolor='red', markeredgecolor='darkblue')
        
        # Annotate cities
        for i, city_idx in enumerate(tour):
            x, y = coords[cities[city_idx]]
            plt.annotate(f"{i+1}. {cities[city_idx]}", (x, y), 
                        xytext=(8, 8), textcoords='offset points', 
                        fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
        
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('X Coordinate', fontsize=12)
        plt.ylabel('Y Coordinate', fontsize=12)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot lagret til {save_path}")
        else:
            plt.show()
        
        plt.close()
        
    except ImportError:
        print("matplotlib ikke tilgjengelig - installer med: pip install matplotlib")



