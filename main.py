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
    print("Status: title baseline and attribute extractor ready; pair explorer still shows benchmark labels only.")
    print("Day 2 data tool: python scripts/wdc_data.py --download")
    print("Day 4 database tool: python -m scripts.import_data")
    print("Day 5 interface: python -m streamlit run app.py")
    print("Day 6 preview: python -m scripts.preview_normalization")
    print("Day 7 baseline: python -m scripts.run_baseline")
    print("Day 8 attributes: python -m scripts.preview_attributes")
    print("Day 9 features: python -m scripts.preview_features")
    print("Next: Day 10 — train a classifier with similarity and attribute features.")


if __name__ == "__main__":
    main()
