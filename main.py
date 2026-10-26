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
    print("Status: data loading, SQLite storage and pair explorer ready; no model yet.")
    print("Day 2 data tool: python scripts/wdc_data.py --download")
    print("Day 4 database tool: python -m scripts.import_data")
    print("Day 5 interface: python -m streamlit run app.py")
    print("Next: Day 6 — normalize titles while preserving model codes and numbers.")


if __name__ == "__main__":
    main()
