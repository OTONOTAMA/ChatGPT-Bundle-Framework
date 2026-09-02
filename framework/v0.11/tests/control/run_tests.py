from pathlib import Path
import runpy

root = Path(__file__).resolve().parent
files = sorted(root.glob("test_*.py"))
tests = []
for path in files:
    ns = runpy.run_path(str(path))
    tests.extend((f"{path.name}::{name}", fn) for name, fn in ns.items() if name.startswith("test_") and callable(fn))

failed = []
for name, fn in tests:
    try:
        fn()
        print(f"PASS {name}")
    except Exception as e:
        failed.append((name, e))
        print(f"FAIL {name}: {type(e).__name__}: {e}")

print(f"RESULT pass={len(tests)-len(failed)} fail={len(failed)} total={len(tests)}")
if failed:
    raise SystemExit(1)
