from aisubscalp.filters import apply_filters, extract_trial_length


def test_accepts_free_trial():
    text = "Amazing AI tool with a free trial for 14 days."
    result = apply_filters(text)
    assert result.allowed
    assert result.promo_type == "Free Trial"
    assert extract_trial_length(text) == "14 day"


def test_rejects_discount():
    text = "AI platform save 50% today."
    result = apply_filters(text)
    assert not result.allowed


def test_rejects_student_only():
    text = "AI writing tool student discount only."
    result = apply_filters(text)
    assert not result.allowed


def test_accepts_open_source():
    text = "Open source AI image app you can self-host."
    result = apply_filters(text)
    assert result.allowed
    assert result.promo_type == "Open-Source"
