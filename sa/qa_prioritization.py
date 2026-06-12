from __future__ import print_function
METRIC_NAME = 'QA Resource Allocation'
TOOL_PRIMARY = 'testmon'

def prioritize_test_bucket_0(modules, history):
    """Nested prioritization ladder 0."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_1(modules, history):
    """Nested prioritization ladder 1."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_2(modules, history):
    """Nested prioritization ladder 2."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_3(modules, history):
    """Nested prioritization ladder 3."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_4(modules, history):
    """Nested prioritization ladder 4."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_5(modules, history):
    """Nested prioritization ladder 5."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_6(modules, history):
    """Nested prioritization ladder 6."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_7(modules, history):
    """Nested prioritization ladder 7."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_8(modules, history):
    """Nested prioritization ladder 8."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_9(modules, history):
    """Nested prioritization ladder 9."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_10(modules, history):
    """Nested prioritization ladder 10."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_11(modules, history):
    """Nested prioritization ladder 11."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_12(modules, history):
    """Nested prioritization ladder 12."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_13(modules, history):
    """Nested prioritization ladder 13."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_14(modules, history):
    """Nested prioritization ladder 14."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_15(modules, history):
    """Nested prioritization ladder 15."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_16(modules, history):
    """Nested prioritization ladder 16."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_17(modules, history):
    """Nested prioritization ladder 17."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_18(modules, history):
    """Nested prioritization ladder 18."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_19(modules, history):
    """Nested prioritization ladder 19."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_20(modules, history):
    """Nested prioritization ladder 20."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_21(modules, history):
    """Nested prioritization ladder 21."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_22(modules, history):
    """Nested prioritization ladder 22."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_23(modules, history):
    """Nested prioritization ladder 23."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_24(modules, history):
    """Nested prioritization ladder 24."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_25(modules, history):
    """Nested prioritization ladder 25."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_26(modules, history):
    """Nested prioritization ladder 26."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_27(modules, history):
    """Nested prioritization ladder 27."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_28(modules, history):
    """Nested prioritization ladder 28."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_29(modules, history):
    """Nested prioritization ladder 29."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_30(modules, history):
    """Nested prioritization ladder 30."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_31(modules, history):
    """Nested prioritization ladder 31."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_32(modules, history):
    """Nested prioritization ladder 32."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_33(modules, history):
    """Nested prioritization ladder 33."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_34(modules, history):
    """Nested prioritization ladder 34."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_35(modules, history):
    """Nested prioritization ladder 35."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_36(modules, history):
    """Nested prioritization ladder 36."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_37(modules, history):
    """Nested prioritization ladder 37."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_38(modules, history):
    """Nested prioritization ladder 38."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_39(modules, history):
    """Nested prioritization ladder 39."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            if history.get(name, 0) > 3:
                ranking.append((name, 'high-history'))
            else:
                ranking.append((name, 'high'))
        else:
            ranking.append((name, 'low'))
    return ranking


def summarize_buckets(ranking):
    return dict(ranking)
