import pandas as pd

def validate_rankings_csv(filepath: str) -> bool:
    """
    Validate the dynasty rankings CSV file to ensure it has required columns
    and reasonable data.
    Returns True if valid, False otherwise.
    """
    required_columns = {"name", "overall_rank", "dynasty_value"}
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
        return False

    missing = required_columns - set(df.columns)
    if missing:
        print(f"Validation error: missing columns {missing}")
        return False

    if df.empty:
        print("Validation error: rankings CSV is empty")
        return False

    # Check if 'name' column has any empty or nulls
    if df["name"].isnull().any() or (df["name"].str.strip() == "").any():
        print("Validation error: some player names are empty or null")
        return False

    # Check for reasonable ranges in overall_rank and dynasty_value
    if not df["overall_rank"].between(1, 10000).all():
        print("Validation warning: 'overall_rank' contains unexpected values")
        # This might be warning only, but you can decide to fail

    if not df["dynasty_value"].between(0, 2000).all():
        print("Validation warning: 'dynasty_value' contains unexpected values")

    print("✅ Rankings CSV validation passed")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python validate_rankings_csv.py <path_to_csv>")
        sys.exit(1)
    filepath = sys.argv[1]
    valid = validate_rankings_csv(filepath)
    sys.exit(0 if valid else 1)
