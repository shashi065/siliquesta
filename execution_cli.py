"""
CLI for Execution-Based AI System

Usage:
    python execution_cli.py "optimize for low power under 1GHz"
    python execution_cli.py "maximize frequency with power budget 20mW"
    python execution_cli.py "balance power and efficiency, keep voltage low"
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from execution_engine import ExecutionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def format_solution(solution: dict, title: str) -> str:
    """Format a solution for display"""
    return f"""
  {title}:
    Design Parameters:
      WN (NMOS width):  {solution['wn']:.3f} µm
      WP (PMOS width):  {solution['wp']:.3f} µm
      VDD (Supply):     {solution['vdd']:.3f} V
    Performance:
      Frequency:        {solution['frequency']:.4f} GHz
      Power:            {solution['power']:.2f} mW
      Efficiency:       {solution['efficiency']:.4f} GHz/mW
"""


def main():
    """Execute optimization from command line"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("Examples:")
        print('  python execution_cli.py "optimize for low power under 1GHz"')
        print('  python execution_cli.py "maximize frequency with power budget 20mW"')
        print('  python execution_cli.py "high efficiency design, voltage at 2.8V"')
        return
    
    # Get request from command line
    request = " ".join(sys.argv[1:])
    
    print("\n" + "="*70)
    print("EXECUTION-BASED AI SYSTEM")
    print("="*70)
    print(f"\nRequest: {request}\n")
    
    # Initialize and execute
    try:
        engine = ExecutionEngine()
        result = engine.execute(request)
        
        # Display results
        if result['status'] == 'success':
            print(f"Status: ✓ SUCCESS\n")
            
            print("OBJECTIVES:")
            for obj in result['objectives']:
                print(f"  • {obj}")
            
            print("\nCONSTRAINTS EXTRACTED:")
            constraints = result['constraints']
            if constraints['max_power']:
                print(f"  • Max Power: {constraints['max_power']} mW")
            if constraints['min_frequency']:
                print(f"  • Min Frequency: {constraints['min_frequency']} GHz")
            if constraints['max_frequency']:
                print(f"  • Max Frequency: {constraints['max_frequency']} GHz")
            if constraints['min_efficiency']:
                print(f"  • Min Efficiency: {constraints['min_efficiency']} GHz/mW")
            
            opt = result['optimization']
            print("\nOPTIMIZATION EXECUTION:")
            print(f"  • Population Size: {opt['population_size']}")
            print(f"  • Generations: {opt['generations']}")
            print(f"  • Total Solutions: {opt['total_solutions']}")
            print(f"  • Valid Solutions (meeting constraints): {opt['valid_solutions']}")
            
            # Show solutions if available
            if 'solutions' in result:
                print("\nOPTIMAL SOLUTIONS:")
                sols = result['solutions']
                
                if sols.get('best_power'):
                    print(format_solution(sols['best_power'], "MINIMUM POWER"))
                
                if sols.get('best_frequency'):
                    print(format_solution(sols['best_frequency'], "MAXIMUM FREQUENCY"))
                
                if sols.get('best_efficiency'):
                    print(format_solution(sols['best_efficiency'], "BEST EFFICIENCY"))
            
            print("\n" + "="*70)
            print("Execution completed successfully")
            print("="*70 + "\n")
            
        else:
            print(f"Status: ✗ ERROR\n")
            print(f"Error: {result.get('error', 'Unknown error')}\n")
            return 1
    
    except Exception as e:
        print(f"Status: ✗ FATAL ERROR\n")
        print(f"Error: {e}\n")
        logger.exception("Execution failed")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
