"""
Hovedskript for å kjøre alle tre TSP formuleringer og generere sammenligningstabell
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtz_model import solve_mtz
from svestka_model import solve_svestka
from dantzig_model import solve_dantzig


def print_results_table(results: dict, name: str = "MartinAndreassen"):
    """
    Skriver ut formatert resultattabell som sammenligner alle tre modellene
    """
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    # Header
    header = f"{'Model':<12} | {'Num Vars':<10} | {'Num Constrs':<12} | {'Objective':<12} | {'Runtime (s)':<12} | {'Status':<12}"
    print(header)
    print("-" * 80)
    
    # Data rows
    for model_name in ['MTZ', 'Svestka', 'Dantzig']:
        if model_name in results:
            r = results[model_name]
            num_vars = r.get('num_vars', 'N/A')
            num_constrs = r.get('num_constrs', 'N/A')
            
            # Format objective
            if 'objective' in r:
                objective = f"{r['objective']:.2f}"
            elif 'bound' in r:
                objective = f"{r['objective']:.2f} (bound: {r['bound']:.2f})"
            else:
                objective = 'N/A'
            
            runtime = f"{r.get('runtime', 0):.2f}" if 'runtime' in r else 'N/A'
            status = r.get('status', 'Unknown')
            
            row = f"{model_name:<12} | {str(num_vars):<10} | {str(num_constrs):<12} | {objective:<12} | {runtime:<12} | {status:<12}"
            print(row)
        else:
            print(f"{model_name:<12} | {'N/A':<10} | {'N/A':<12} | {'N/A':<12} | {'N/A':<12} | {'Not run':<12}")
    
    print("="*80)
    
    # Save to file
    os.makedirs('solutions', exist_ok=True)
    summary_file = os.path.join('solutions', 'summary.txt')
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("TSP Model Comparison Results\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"User: {name}\n")
        f.write("="*80 + "\n\n")
        
        f.write(header + "\n")
        f.write("-" * 80 + "\n")
        
        for model_name in ['MTZ', 'Svestka', 'Dantzig']:
            if model_name in results:
                r = results[model_name]
                num_vars = r.get('num_vars', 'N/A')
                num_constrs = r.get('num_constrs', 'N/A')
                
                if 'objective' in r:
                    objective = f"{r['objective']:.2f}"
                elif 'bound' in r:
                    objective = f"{r['objective']:.2f} (bound: {r['bound']:.2f})"
                else:
                    objective = 'N/A'
                
                runtime = f"{r.get('runtime', 0):.2f}" if 'runtime' in r else 'N/A'
                status = r.get('status', 'Unknown')
                
                row = f"{model_name:<12} | {str(num_vars):<10} | {str(num_constrs):<12} | {objective:<12} | {runtime:<12} | {status:<12}"
                f.write(row + "\n")
                
                # Additional details for Dantzig
                if model_name == 'Dantzig' and 'lazy_constrs' in r:
                    f.write(f"  Lazy constraints added: {r['lazy_constrs']}\n")
        
        f.write("="*80 + "\n")
        
        # Best model
        best_obj = float('inf')
        best_model = None
        for model_name, r in results.items():
            if r.get('status') == 'Optimal' and 'objective' in r:
                if r['objective'] < best_obj:
                    best_obj = r['objective']
                    best_model = model_name
        
        if best_model:
            f.write(f"\nBest objective value: {best_obj:.2f} ({best_model} model)\n")
        
        # Runtime comparison
        fastest_time = float('inf')
        fastest_model = None
        for model_name, r in results.items():
            if 'runtime' in r and r['runtime'] < fastest_time:
                fastest_time = r['runtime']
                fastest_model = model_name
        
        if fastest_model:
            f.write(f"Fastest runtime: {fastest_time:.2f} seconds ({fastest_model} model)\n")
    
    print(f"\nSummary saved to: {summary_file}")


def main(name: str = "MartinAndreassen"):
    """
    Hovedfunksjon for å kjøre alle tre TSP modeller
    """
    print("="*80)
    print("TSP Assignment 1 - Comparing Three Formulations")
    print("="*80)
    print(f"User: {name}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = {}
    
    # Solve with MTZ
    try:
        print("\n\n" + "=" * 40 + " MTZ MODEL " + "=" * 40)
        results['MTZ'] = solve_mtz(name)
    except Exception as e:
        print(f"\n[ERROR] Error in MTZ model: {e}")
        results['MTZ'] = {'status': 'Error', 'error': str(e)}
    
    # Solve with Svestka
    try:
        print("\n\n" + "=" * 40 + " SVESTKA MODEL " + "=" * 40)
        results['Svestka'] = solve_svestka(name)
    except Exception as e:
        print(f"\n[ERROR] Error in Svestka model: {e}")
        results['Svestka'] = {'status': 'Error', 'error': str(e)}
    
    # Solve with Dantzig
    try:
        print("\n\n" + "=" * 40 + " DANTZIG MODEL " + "=" * 40)
        results['Dantzig'] = solve_dantzig(name)
    except Exception as e:
        print(f"\n[ERROR] Error in Dantzig model: {e}")
        results['Dantzig'] = {'status': 'Error', 'error': str(e)}
    
    # Print comparison table
    print_results_table(results, name)
    
    return results


if __name__ == "__main__":
    user_name = "MartinAndreassen"
    
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
    
    results = main(user_name)
    
    print("\n[OK] Alle modeller fullført!")
    print(f"Sjekk logs/ mappen for detaljerte logger")
    print(f"Sjekk solutions/ mappen for løsningsfiler og sammenfatning")
