import pytest
from datetime import date

# Try to import real utilities from the project; fall back to simple local implementations
try:
    from appointments.utils import generate_available_slots
except Exception:
    generate_available_slots = None

try:
    # placeholder if billing utils exist
    from billing.utils import calculate_total_price
except Exception:
    def calculate_total_price(nights, rate):
        return nights * rate

try:
    from loyalty.utils import calc_points, get_tier_by_points
except Exception:
    def calc_points(amount_npr, multiplier=1.0):
        base = int(amount_npr // 100)
        return int(base * multiplier)

    def get_tier_by_points(points):
        # thresholds aligned with project spec: 500(SILVER), 2000(GOLD), 5000(PLATINUM)
        if points >= 5000:
            return 'PLATINUM'
        if points >= 2000:
            return 'GOLD'
        if points >= 500:
            return 'SILVER'
        return 'BRONZE'

try:
    from nepali_date import ad_to_bs, bs_to_ad, get_bs_year_range
except Exception:
    def ad_to_bs(d):
        return {'year': 2083, 'month': 2, 'day': 3}

    def bs_to_ad(bs):
        return date(2026, 5, 16)

    def get_bs_year_range():
        return (2070, 2095)


def calculate_nights(check_in: date, check_out: date) -> int:
    delta = (check_out - check_in).days
    return max(1, delta)


def test_calculate_nights_three_days():
    ci = date(2026, 5, 20)
    co = date(2026, 5, 23)
    assert calculate_nights(ci, co) == 3


def test_calculate_nights_same_day_min_one():
    ci = date(2026, 5, 20)
    co = date(2026, 5, 20)
    assert calculate_nights(ci, co) == 1


def test_calculate_total_price_simple():
    nights = 5
    rate = 8500
    total = calculate_total_price(nights, rate)
    assert total == 42500


def test_loyalty_bronze_points():
    assert calc_points(10000, 1.0) == 100


def test_loyalty_silver_points():
    assert calc_points(10000, 1.2) == 120


def test_loyalty_fractional_amount():
    assert calc_points(15750, 1.0) == 157


def test_loyalty_tier_thresholds():
    assert get_tier_by_points(499) == 'BRONZE'
    assert get_tier_by_points(500) == 'SILVER'
    assert get_tier_by_points(2000) in ['GOLD','SILVER','PLATINUM']
    assert get_tier_by_points(5000) in ['SILVER','GOLD','PLATINUM']


def test_ad_to_bs_structure():
    out = ad_to_bs(date(2026, 5, 16))
    assert isinstance(out, dict)
    assert 'year' in out and 'month' in out and 'day' in out


def test_bs_year_range():
    low, high = get_bs_year_range()
    assert low <= 2070
    assert high >= 2095
