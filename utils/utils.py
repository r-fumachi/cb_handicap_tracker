import pandas as pd
import numpy as np
from cloudbet.process import getCleanEvent, get_handicap_market_details, extract_event_summary

def fetch_event_data(event_id, event_name, homeOrAway):
    event_data = getCleanEvent(event_id)
    if not event_data['marketsAmount']:
        return {
        "event_id": event_id,
        "event_name": event_name,
        "event_start_time": event_data["cutoffTime"],
        "status": "Event Over"
    }
    lines = get_handicap_market_details(event_data)
    eventdata = extract_event_summary(
        lines,
        event_name=event_name,
        event_id=event_id,
        homeOrAway=homeOrAway)
    return eventdata


def compute_spread_slope(csv_path, start_time, end_time):
    """
    Compute the slope of spread over a given time interval.

    :param csv_path: Path to CSV
    :param start_time: Start time in minutes from first timestamp
    :param end_time: End time in minutes from first timestamp
    :return: Slope of spread vs time, or None if not enough points
    """
    # Load CSV
    df = pd.read_csv(csv_path)

    # Ensure numeric
    df['time_since_start'] = pd.to_numeric(df['time_since_start'], errors='coerce')
    df['spread'] = pd.to_numeric(df['spread'], errors='coerce')

    # Reference time
    ref_time = df['time_since_start'].iloc[0]

    # Filter rows within interval
    mask = (df['time_since_start'] - ref_time >= start_time) & (df['time_since_start'] - ref_time <= end_time)
    df_interval = df[mask]

    if len(df_interval) < 2:
        return None  # Not enough points to compute slope

    # x-values relative to start_time for slope per minute
    x = df_interval['time_since_start'].values - ref_time
    y = df_interval['spread'].values

    # Linear regression slope
    slope = np.cov(x, y, bias=True)[0, 1] / np.var(x)

    return slope


def compute_slopes_table(csv_path):
    """
    Compute slope of spread between each consecutive point in the CSV.

    :param csv_path: Path to the CSV file
    :return: pandas DataFrame with columns:
             ['time_start', 'time_end', 'spread_start', 'spread_end', 'slope']
    """
    # Load CSV
    df = pd.read_csv(csv_path)

    # Ensure numeric columns
    df['time_since_start'] = pd.to_numeric(df['time_since_start'], errors='coerce')
    df['spread'] = pd.to_numeric(df['spread'], errors='coerce')

    # Compute differences between consecutive rows
    df['time_next'] = df['time_since_start'].shift(-1)
    df['spread_next'] = df['spread'].shift(-1)

    # Drop last row (no next point)
    df = df[:-1]

    # Compute slope = Δspread / Δtime
    df['slope'] = (df['spread_next'] - df['spread']) / (df['time_next'] - df['time_since_start'])

    # Keep relevant columns
    slope_table = df[['time_since_start', 'time_next', 'spread', 'spread_next', 'slope']].rename(
        columns={
            'time_since_start': 'time_start',
            'time_next': 'time_end',
            'spread': 'spread_start',
            'spread_next': 'spread_end'
        }
    )

    return slope_table

def compute_spread_slope_from_df(df, start_idx, end_idx):
    """
    Compute slope from a slice of the already-loaded dataframe.
    """
    df_interval = df.iloc[start_idx:end_idx+1]

    if len(df_interval) < 2:
        return None

    x = df_interval['time_since_start'].values
    y = df_interval['spread'].values

    return np.cov(x, y, bias=True)[0, 1] / np.var(x)


def find_spread_jump_fast(csv_path, base_spread: float, window_minutes, slope_threshold=0.15):
    df = pd.read_csv(csv_path)
    df['time_since_start'] = pd.to_numeric(df['time_since_start'], errors='coerce')
    df['spread'] = pd.to_numeric(df['spread'], errors='coerce')

    target_spread = base_spread + 3.5

    # earliest time when a minute window can exist
    min_window_time = df['time_since_start'].iloc[0] + window_minutes

    # find first index where window is valid
    first_valid_idx = df.index[df['time_since_start'] >= min_window_time][0]

    left = 0  # sliding pointer for window start

    for i in range(first_valid_idx, len(df)):
        row = df.iloc[i]

        # 1. check spread first (cheap)
        if row['spread'] < target_spread:
            continue

        current_time = row['time_since_start']
        window_start_time = current_time - window_minutes

        # 2. advance left pointer until window starts within window min range
        while df['time_since_start'].iloc[left] < window_start_time:
            left += 1

        # right pointer is i → window = df[left:i+1]
        if i - left < 1:  # need 2 points minimum
            continue

        window_df = df.iloc[left:i+1]

        # 3. compute slope
        x = window_df['time_since_start'].values
        y = window_df['spread'].values
        slope = np.cov(x, y, bias=True)[0, 1] / np.var(x)

        if slope < slope_threshold:
            return {
                "time": row['time_since_start'],
                "spread": row['spread'],
                "slope": slope,
                "window_start": x[0],
                "window_end": x[-1]
            }

    return None
