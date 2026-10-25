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
    print("Status: introduction only; no matching model or database yet.")
    print("Day 2 data tool: python scripts/wdc_data.py --download")
    print("Next: Day 3 — inspect 30 training pairs manually.")


if __name__ == "__main__":
    main()
