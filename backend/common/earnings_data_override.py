"""
Override module for earnings data API functions.
This allows us to modify the behavior without changing the original finance_llm_data module.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential


def get_api_key_from_config(key_name: str) -> str:
    """Get API key from config file using absolute path"""
    # First try environment variable
    api_key = os.getenv(key_name)
    if api_key:
        return api_key

    # Try multiple possible locations for config file
    current_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()

    possible_paths = [
        current_dir / "config_api_keys",  # Same directory as this file (backend/)
        current_dir.parent / "config_api_keys",  # Parent directory
        cwd / "config_api_keys",  # Current working directory
        cwd / "backend" / "config_api_keys",  # If running from project root
        cwd / ".." / "config_api_keys",  # If CWD is finance_llm_data, go up to backend
        cwd.parent / "config_api_keys",  # If CWD is finance_llm_data, go up to backend
        Path(__file__).resolve().parent
        / "config_api_keys",  # Absolute path to backend/config_api_keys
    ]

    for config_path in possible_paths:
        try:
            if config_path.exists():
                print(f"Found config file at: {config_path}")
                with open(config_path, "r") as f:
                    config = json.load(f)
                    api_key = config.get(key_name)
                    if api_key:
                        return api_key
        except Exception as e:
            print(f"Failed to read config file at {config_path}: {e}")
            continue

    raise ValueError(
        f"{key_name} not found in environment variables or any config file locations: {[str(p) for p in possible_paths]}"
    )


def get_finnhub_client():
    """Get Finnhub client with API key from config"""
    import finnhub

    api_key = get_api_key_from_config("FINNHUB_API_KEY")
    return finnhub.Client(api_key=api_key)


@retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(2))
def get_earnings_transcript_alpha_vantage(
    quarter: str, ticker: str, year: int
) -> Dict[str, Any]:
    """Get the earnings transcripts using Alpha Vantage API"""
    api_key = get_api_key_from_config("ALPHA_VANTAGE_API_KEY")

    # Convert quarter format (Q1 -> 2023Q1)
    quarter_num = quarter[1]  # Extract number from Q1, Q2, etc.
    av_quarter = f"{year}Q{quarter_num}"

    # Make API request
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALL_TRANSCRIPT&symbol={ticker}&quarter={av_quarter}&apikey={api_key}"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    # Check for API errors
    if "Error Message" in data:
        raise Exception(f"Alpha Vantage API error: {data['Error Message']}")

    if "Note" in data:
        raise Exception(f"Alpha Vantage API limit: {data['Note']}")

    # Extract transcript content
    if "transcript" not in data:
        raise Exception(f"No transcript data found for {ticker} {quarter} {year}")

    transcript_data = data["transcript"]

    # Convert structured transcript to text format
    if isinstance(transcript_data, list):
        # Alpha Vantage returns structured data with speaker, title, content
        content = ""
        for entry in transcript_data:
            speaker = entry.get("speaker", "Unknown")
            text = entry.get("content", "")
            content += f"\n{speaker}:\n{text}\n"
        transcript_content = content.strip()
    elif isinstance(transcript_data, str):
        # If it's already a string, use it directly
        transcript_content = transcript_data
    else:
        # Convert to string as fallback
        transcript_content = str(transcript_data)

    # Create date string (approximate)
    date_str = f"{year}-{int(quarter_num)*3:02d}-01 00:00:00"

    return {
        "content": transcript_content,
        "date": date_str,
        "year": year,
        "quarter": quarter,
    }


@retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(2))
def get_earnings_transcript_finnhub(
    quarter: str, ticker: str, year: int
) -> Dict[str, Any]:
    """Get the earnings transcripts using Finnhub API"""
    client = get_finnhub_client()

    # Get list of available transcripts for the ticker
    transcripts_list = client.transcripts_list(ticker)

    if not transcripts_list:
        raise Exception(f"No transcripts found for {ticker}")

    # Find transcript for the specific quarter and year
    target_transcript = None
    for transcript in transcripts_list:
        transcript_year = transcript.get("year", 0)
        transcript_quarter = transcript.get("quarter", 0)

        # Convert quarter number to Q format (1 -> Q1, 2 -> Q2, etc.)
        quarter_map = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
        target_quarter_num = quarter_map.get(quarter, 0)

        if transcript_year == year and transcript_quarter == target_quarter_num:
            target_transcript = transcript
            break

    if not target_transcript:
        raise Exception(f"No transcript found for {ticker} {quarter} {year}")

    # Get the actual transcript content
    transcript_id = target_transcript["id"]
    transcript_data = client.transcripts(transcript_id)

    if not transcript_data:
        raise Exception(f"Failed to get transcript content for {transcript_id}")

    # Format the response to match the original API structure
    content = ""
    if isinstance(transcript_data, list) and len(transcript_data) > 0:
        # Combine all transcript sections
        for section in transcript_data:
            speaker = section.get("speaker", "Unknown")
            text = section.get("speech", "")
            content += f"\n{speaker}:\n{text}\n"
    else:
        # Handle case where transcript_data is a single object
        content = transcript_data.get("content", str(transcript_data))

    # Create date string (Finnhub might not provide exact date format)
    date_str = f"{year}-{target_quarter_num*3:02d}-01 00:00:00"  # Approximate date

    return {
        "content": content.strip(),
        "date": date_str,
        "year": year,
        "quarter": quarter,
    }


@retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(2))
def get_earnings_transcript_legacy(quarter: str, ticker: str, year: int):
    """Get the earnings transcripts using the original API (kept as fallback)"""
    response = requests.get(
        f"https://discountingcashflows.com/api/transcript/{ticker}/{quarter}/{year}/",
        auth=("user", "pass"),
    )

    resp_text = json.loads(response.text)
    # Import the correction function from original module
    from finance_llm_data.earnings_calls_src.earningsData import correct_date

    corrected_date = correct_date(resp_text[0]["year"], resp_text[0]["date"])
    resp_text[0]["date"] = corrected_date
    return resp_text[0]


def get_earnings_transcript_override(quarter: str, ticker: str, year: int):
    """Override function for get_earnings_transcript with multiple fallback APIs"""
    try:
        # Try Alpha Vantage API first
        return get_earnings_transcript_alpha_vantage(quarter, ticker, year)
    except Exception as e:
        print(f"Alpha Vantage API failed for {ticker} {quarter} {year}: {e}")
        try:
            # Try Finnhub API second
            return get_earnings_transcript_finnhub(quarter, ticker, year)
        except Exception as e2:
            print(f"Finnhub API failed for {ticker} {quarter} {year}: {e2}")
            try:
                # Fallback to original API
                print(f"Trying legacy API for {ticker} {quarter} {year}")
                return get_earnings_transcript_legacy(quarter, ticker, year)
            except Exception as e3:
                print(f"Legacy API also failed for {ticker} {quarter} {year}: {e3}")
                raise e3
