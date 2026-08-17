from src.preprocessing.normalization import (  # noqa: I001
    dates_in_order,
    normalize_coverage_status_text,
    normalize_currency,
    normalize_date,
    normalize_days,
    normalize_percentage,
)


# --- Currency ---

def test_normalize_currency_rs_with_commas():
    assert normalize_currency("Rs. 200,000") == 200000.0


def test_normalize_currency_backtick_glyph_artifact():
    assert normalize_currency("` 461,699") == 461699.0


def test_normalize_currency_inr_prefix():
    assert normalize_currency("INR 500000") == 500000.0


def test_normalize_currency_lakh():
    assert normalize_currency("5 Lakh") == 500000.0
    assert normalize_currency("5 Lacs") == 500000.0
    assert normalize_currency("2.5 lakh") == 250000.0


def test_normalize_currency_crore():
    assert normalize_currency("1.72 Crore") == 17200000.0


def test_normalize_currency_unparseable_returns_none():
    assert normalize_currency("No Limit") is None
    assert normalize_currency("") is None


# --- Percentage ---

def test_normalize_percentage_symbol():
    assert normalize_percentage("2%") == 2.0
    assert normalize_percentage("2 % of Sum Insured per day") == 2.0


def test_normalize_percentage_word():
    assert normalize_percentage("1 percent") == 1.0


def test_normalize_percentage_unparseable_returns_none():
    assert normalize_percentage("No Limit") is None


# --- Days ---

def test_normalize_days_numeric():
    assert normalize_days("30 days") == 30
    assert normalize_days("30-day") == 30


def test_normalize_days_word():
    assert normalize_days("thirty days waiting period") == 30
    assert normalize_days("initial waiting period of ninety days") == 90


def test_normalize_days_unparseable_returns_none():
    assert normalize_days("waived off") is None


# --- Dates ---

def test_normalize_date_dd_mon_yyyy():
    assert normalize_date("17-Mar-2022") == "2022-03-17"


def test_normalize_date_dd_slash_mm_slash_yyyy():
    assert normalize_date("02/06/2022") == "2022-06-02"


def test_normalize_date_dd_month_yyyy_full():
    assert normalize_date("26 April 2024") == "2024-04-26"


def test_normalize_date_strips_time_prefix():
    assert normalize_date("00:00 hrs 17-Mar-2022") == "2022-03-17"
    assert normalize_date("Midnight 16-Mar-2023") == "2023-03-16"


def test_normalize_date_unparseable_returns_none():
    assert normalize_date("") is None
    assert normalize_date("not a date at all !!!") is None


def test_dates_in_order_true_when_end_after_start():
    assert dates_in_order("2022-03-17", "2023-03-16") is True


def test_dates_in_order_false_when_end_before_start():
    assert dates_in_order("2023-03-16", "2022-03-17") is False


def test_dates_in_order_none_when_missing():
    assert dates_in_order(None, "2023-03-16") is None
    assert dates_in_order("2022-03-17", None) is None


# --- Coverage status text ---

def test_normalize_coverage_status_waived():
    assert normalize_coverage_status_text("waived off for all members") == "waived_off"
    assert normalize_coverage_status_text("condition is waived") == "waived_off"


def test_normalize_coverage_status_covered():
    assert normalize_coverage_status_text("pre-existing diseases are covered") == "covered"


def test_normalize_coverage_status_not_covered():
    assert normalize_coverage_status_text("domiciliary hospitalization is excluded") == "not_covered"


def test_normalize_coverage_status_defaults_to_not_specified():
    assert normalize_coverage_status_text("") == "not_specified"
    assert normalize_coverage_status_text("some unrelated text") == "not_specified"
