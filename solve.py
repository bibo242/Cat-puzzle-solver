import sys
import argparse
import os

print("[DEBUG] Loading dotenv...", flush=True)
from dotenv import load_dotenv
load_dotenv()

print("[DEBUG] Importing vision module...", flush=True)
from vision import parse_image

print("[DEBUG] Importing solver module...", flush=True)
from solver import solve

def main():
    print("[DEBUG] Parsing arguments...", flush=True)
    parser = argparse.ArgumentParser(description="AI-Assisted Cat Sort Solver")
    parser.add_argument("image_path", help="Path to the screenshot of the puzzle")
    parser.add_argument("--capacity", type=int, default=None, help="Override tube capacity. Auto-detected from image if not set.")
    args = parser.parse_args()

    print(f"[*] Analyzing image at {args.image_path} using Gemini API...")
    try:
        initial_state, ai_capacity = parse_image(args.image_path)
    except Exception as e:
        print(f"[!] Error during vision extraction: {e}")
        sys.exit(1)

    capacity = args.capacity if args.capacity is not None else ai_capacity
    if args.capacity is not None:
        print(f"[*] Overriding AI-detected capacity ({ai_capacity}) with user-specified: {capacity}")
    else:
        print(f"[*] Using AI-detected tube capacity: {capacity}")

    print("\n[*] Extracted Initial State:")
    color_counts = {}
    for i, col in enumerate(initial_state):
        print(f"    Tube {i}: {col}")
        for color in col:
            color_counts[color] = color_counts.get(color, 0) + 1
            
    print("\n[*] Color Distribution Tally:")
    for color, count in color_counts.items():
        print(f"    - {color}: {count}")
    
    counts = list(color_counts.values())
    if len(set(counts)) > 1:
        print("\n[!] WARNING: The AI count is mathematically unbalanced! A valid puzzle must have identical counts for each color.")
        print("    The BFS will likely fail. Please verify the AI didn't hallucinate a ghost cat.")

    print(f"\n[*] Running Breadth-First Search to find optimal solution...")
    solution_moves = solve(initial_state, capacity=capacity)

    if solution_moves is None:
        print("\n[!] No solution could be found. The puzzle might be in an unsolvable state, "
              "or the parsed colors were inaccurate. Please verify the extracted state.")
        sys.exit(1)
        
    print(f"\n[*] Puzzle solved in {len(solution_moves)} moves!")
    print("-" * 30)
    
    for step, (src, dst, count, color) in enumerate(solution_moves, 1):
        print(f"Step {step:02d}: Move {count} {color} cat(s) from Tube {src} to Tube {dst}")
        
if __name__ == "__main__":
    main()
