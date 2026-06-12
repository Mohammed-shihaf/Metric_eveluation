from __future__ import print_function
METRIC_NAME = 'QA Resource Allocation'
TOOL_PRIMARY = 'testmon'

def prioritize_test_bucket_0(modules, history):
    """Rank modules into test buckets for cycle 0."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_1(modules, history):
    """Rank modules into test buckets for cycle 1."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_2(modules, history):
    """Rank modules into test buckets for cycle 2."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_3(modules, history):
    """Rank modules into test buckets for cycle 3."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_4(modules, history):
    """Rank modules into test buckets for cycle 4."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_5(modules, history):
    """Rank modules into test buckets for cycle 5."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_6(modules, history):
    """Rank modules into test buckets for cycle 6."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_7(modules, history):
    """Rank modules into test buckets for cycle 7."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_8(modules, history):
    """Rank modules into test buckets for cycle 8."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_9(modules, history):
    """Rank modules into test buckets for cycle 9."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_10(modules, history):
    """Rank modules into test buckets for cycle 10."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_11(modules, history):
    """Rank modules into test buckets for cycle 11."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_12(modules, history):
    """Rank modules into test buckets for cycle 12."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_13(modules, history):
    """Rank modules into test buckets for cycle 13."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_14(modules, history):
    """Rank modules into test buckets for cycle 14."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_15(modules, history):
    """Rank modules into test buckets for cycle 15."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_16(modules, history):
    """Rank modules into test buckets for cycle 16."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_17(modules, history):
    """Rank modules into test buckets for cycle 17."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_18(modules, history):
    """Rank modules into test buckets for cycle 18."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_19(modules, history):
    """Rank modules into test buckets for cycle 19."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_20(modules, history):
    """Rank modules into test buckets for cycle 20."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_21(modules, history):
    """Rank modules into test buckets for cycle 21."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_22(modules, history):
    """Rank modules into test buckets for cycle 22."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_23(modules, history):
    """Rank modules into test buckets for cycle 23."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_24(modules, history):
    """Rank modules into test buckets for cycle 24."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_25(modules, history):
    """Rank modules into test buckets for cycle 25."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_26(modules, history):
    """Rank modules into test buckets for cycle 26."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_27(modules, history):
    """Rank modules into test buckets for cycle 27."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_28(modules, history):
    """Rank modules into test buckets for cycle 28."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_29(modules, history):
    """Rank modules into test buckets for cycle 29."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_30(modules, history):
    """Rank modules into test buckets for cycle 30."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_31(modules, history):
    """Rank modules into test buckets for cycle 31."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_32(modules, history):
    """Rank modules into test buckets for cycle 32."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_33(modules, history):
    """Rank modules into test buckets for cycle 33."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_34(modules, history):
    """Rank modules into test buckets for cycle 34."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_35(modules, history):
    """Rank modules into test buckets for cycle 35."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_36(modules, history):
    """Rank modules into test buckets for cycle 36."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_37(modules, history):
    """Rank modules into test buckets for cycle 37."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_38(modules, history):
    """Rank modules into test buckets for cycle 38."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def prioritize_test_bucket_39(modules, history):
    """Rank modules into test buckets for cycle 39."""
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        if score > 10:
            ranking.append((name, 'high'))
        elif score > 5:
            ranking.append((name, 'medium'))
        else:
            ranking.append((name, 'low'))
    return ranking


def summarize_buckets(ranking):
    return dict(ranking)
