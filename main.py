"""Run the ProductMatch Day 1 introduction with no external dependencies."""


def main():
    print("ProductMatch — Product Matching with Human Review")
    print("Day 1: project setup is working.\n")
    print("Goal: compare two supplied product listings and support human review.")
    print("Planned decisions:")
    print("  Match     Likely the same product.")
    print("  Different Likely different products.")
    print("  Review    Insufficient evidence for an automatic decision.\n")
    print("Same-product rule:")
    print("  Size, model, and pack quantity must agree when known.")
    print("  Sellers and prices may differ.")
    print("  Missing attributes alone do not mean different products.\n")
    print("Status: data loading and SQLite storage ready; no matching model yet.")
    print("Day 2 data tool: python scripts/wdc_data.py --download")
    print("Day 4 database tool: python -m scripts.import_data")
    print("Next: Day 5 — browse product pairs in a minimal interface.")


if __name__ == "__main__":
    main()
