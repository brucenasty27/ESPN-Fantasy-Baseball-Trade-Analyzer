import subprocess

def run_script(script_name):
    print(f"Running {script_name} ...")
    result = subprocess.run(['python', script_name], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}:\n{result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    scraper_scripts = [
        "scrape_razzball_pitching.py",
        "scrape_razzball_hitting.py",
        "scrape_fantasypros_pitchers.py",
        "scrape_fantasypros_hitters.py",
        "scrape_hashtagbaseball.py",
        "scrape_fangraphs_pitchers.py"
    ]

    for script in scraper_scripts:
        if not run_script(script):
            print(f"Aborting due to error in {script}")
            return

    # After all scrapers succeed, combine rankings
    if run_script("combine_rankings.py"):
        print("All scrapers and combine finished successfully.")
    else:
        print("Error combining rankings.")

if __name__ == "__main__":
    main()
