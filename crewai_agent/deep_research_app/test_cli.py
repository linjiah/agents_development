import argparse
from controllers.research_controller import run_deep_research


def main():
    parser = argparse.ArgumentParser(
        description="CLI tester for the Deep Research app (no Streamlit UI)."
    )
    parser.add_argument("query", help="Research query/topic")
    parser.add_argument("--breadth", type=int, default=1, help="Search breadth (number of queries)")
    parser.add_argument("--depth", type=int, default=1, help="Search depth (recursion levels)")
    parser.add_argument("--pdf-path", default="test_report.pdf", help="Where to save the generated PDF")
    args = parser.parse_args()

    print(f"Running deep research for: {args.query!r} (breadth={args.breadth}, depth={args.depth})")
    cleaned_output, pdf_data, _ = run_deep_research(args.query, args.breadth, args.depth)

    print("\n=== Cleaned Output (first 800 chars) ===")
    print(cleaned_output[:800] + ("..." if len(cleaned_output) > 800 else ""))

    with open(args.pdf_path, "wb") as f:
        f.write(pdf_data)
    print(f"\nPDF saved to: {args.pdf_path}")


if __name__ == "__main__":
    main()

