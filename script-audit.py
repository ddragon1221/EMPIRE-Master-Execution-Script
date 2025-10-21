# tools/script-audit.py
import re, os

def audit_repo(root="src"):
    for path, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(path, f)) as fh:
                    text = fh.read()
                    if "TODO" in text:
                        print(f"TODO in {f}")
                    if "cost" not in text and "instrument" in text:
                        print(f"issing cost reference in {f}")

if __name__ == "__main__":
    audit_repo()
