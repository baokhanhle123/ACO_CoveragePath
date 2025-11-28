"""Quick benchmark test - Field (a) only with 100 iterations"""

import sys
import time
from benchmark import create_field_a, run_pipeline

print("=" * 80)
print("QUICK BENCHMARK TEST: Field (a), 100 iterations")
print("=" * 80)
print()

# Create field
field, params = create_field_a()

print(f"Field created: {field.name}")
print(f"Field area: {field.boundary_polygon.area / 10000:.2f} ha")
print(f"Parameters: w={params.operating_width}m, θ={params.driving_direction}°")
print()

# Run with 100 iterations
print("Running 3 tests with 100 iterations...")
print()

results = []
for run in range(3):
    print(f"Run {run + 1}/3...", end=" ", flush=True)
    start = time.time()
    stats, proc_time, n_blocks = run_pipeline(field, params, 100, verbose=False)

    if stats is None:
        print("FAILED - no valid solution")
        continue

    results.append((stats, proc_time, n_blocks))
    print(f"✓ {n_blocks} blocks, {stats['block_connection_distance']:.1f}m connection, {proc_time:.1f}s")

if not results:
    print("\n✗ All runs failed!")
    sys.exit(1)

# Calculate averages
avg_connection = sum(r[0]['block_connection_distance'] for r in results) / len(results)
avg_time = sum(r[1] for r in results) / len(results)
num_blocks = results[0][2]

print()
print("=" * 80)
print("RESULTS (averaged over %d successful runs)" % len(results))
print("=" * 80)
print(f"Blocks: {num_blocks}")
print(f"Connection distance: {avg_connection:.1f} m")
print(f"Processing time: {avg_time:.1f} s")
print()
print("PAPER RESULTS (from Table 2):")
print(f"Connection distance: 371.5 m")
print(f"Processing time: 27.5 s")
print()
print(f"DIFFERENCE:")
print(f"Connection: {((avg_connection - 371.5) / 371.5 * 100):+.1f}%")
print(f"Time: {((avg_time - 27.5) / 27.5 * 100):+.1f}%")
print("=" * 80)
