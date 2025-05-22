import math
from datetime import datetime, timedelta, timezone

from config import DEFAULT_DAYS


def require_utc_aware(dt: datetime) -> None:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Datetime must be timezone‑aware (UTC).")


def dt_or_default(dt: datetime | None) -> datetime:
    require_utc_aware(dt)
    return dt if dt \
        else datetime.now(timezone.utc) - timedelta(days=DEFAULT_DAYS)


def days_since_dt(dt: datetime | None) -> int:
    """ Returns the number of days (ceiling) since `dt`.
        If `dt` is None, returns DEFAULT_DAYS."""
    if dt is None:
        return DEFAULT_DAYS
    require_utc_aware(dt)
    return math.ceil((datetime.now(timezone.utc) - dt).total_seconds() / 86400)


def days_for_free_api(days: int) -> int:
    """Adjust days to supported by CoinGecko free tier limits."""
    limits = (1, 7, 14, 30, 90, 180)
    return next((limit for limit in limits if days <= limit), 365)


def utc_n_min_ago(n: int) -> datetime:
    """Returns the UTC datetime of the moment that was n minutes ago."""
    return datetime.now(timezone.utc) - timedelta(minutes=n)


def utc_from_cached_ts(ts: int) -> datetime:
    """Returns the UTC datetime from the given timestamp."""
    return datetime.fromtimestamp(ts/1000, tz=timezone.utc)


def days_to_call(starting_dt: datetime | None,
                 last_cached_dt: datetime | None,
                 is_ohlc: bool) -> int:
    """Decide how many days of data to request:
            1. If we've ever cached data, measure days since last_cached_dt.
            2. Else if the caller provided a starting_dt, measure days since starting_dt.
            3. Otherwise, fall back to DEFAULT_DAYS.

        Then, if this is OHLC data, snap into CoinGecko’s allowed buckets."""
    ref_dt = last_cached_dt or starting_dt
    if ref_dt:
        days = days_since_dt(ref_dt)
    else:
        days = DEFAULT_DAYS

    return days_for_free_api(days) if is_ohlc else days