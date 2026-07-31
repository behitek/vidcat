from core.grouping import (
    parse_order_suffix,
    group_videos_by_suffix,
    assign_group_indices,
    sanitize_suffix,
    dedupe_suffixes,
)


def test_parse_order_suffix_basic():
    assert parse_order_suffix("01_A.mp4") == (1, "A")

def test_parse_order_suffix_suffix_with_underscores():
    assert parse_order_suffix("01_intro_final.mp4") == (1, "intro_final")

def test_parse_order_suffix_no_match_returns_none_order():
    assert parse_order_suffix("weird.mp4") == (None, "weird")

def test_parse_order_suffix_ignores_directory():
    assert parse_order_suffix("C:/videos/02_B.mov") == (2, "B")


def test_group_videos_by_suffix_groups_matching_suffixes():
    videos = ["01_A.mp4", "02_A.mp4", "01_B.mp4"]
    groups = group_videos_by_suffix(videos)

    assert [g.suffix for g in groups] == ["A", "B"]
    assert groups[0].paths == ["01_A.mp4", "02_A.mp4"]
    assert groups[1].paths == ["01_B.mp4"]

def test_group_videos_by_suffix_orders_by_first_appearance():
    videos = ["01_B.mp4", "01_A.mp4", "02_B.mp4"]
    groups = group_videos_by_suffix(videos)

    assert [g.suffix for g in groups] == ["B", "A"]

def test_group_videos_by_suffix_sorts_within_group_by_order_not_position():
    videos = ["03_A.mp4", "01_A.mp4", "02_A.mp4"]
    groups = group_videos_by_suffix(videos)

    assert groups[0].paths == ["01_A.mp4", "02_A.mp4", "03_A.mp4"]

def test_group_videos_by_suffix_unmatched_filenames_are_singletons():
    videos = ["weird.mp4", "01_A.mp4", "weird.mp4"]
    groups = group_videos_by_suffix(videos)

    # both "weird.mp4" entries are unmatched -> each gets its own group,
    # even though their stems collide
    assert len(groups) == 3
    unmatched_groups = [g for g in groups if g.suffix == "weird"]
    assert len(unmatched_groups) == 2
    assert all(len(g.items) == 1 for g in unmatched_groups)

def test_group_videos_by_suffix_duplicate_order_tiebreaks_by_original_index():
    # Both share suffix "A" and order 1 (parse_order_suffix ignores the
    # extension); original list position ("01_A.mp4" first) must break the tie.
    videos = ["01_A.mp4", "01_A.mov"]
    groups = group_videos_by_suffix(videos)
    assert len(groups) == 1
    assert groups[0].paths == ["01_A.mp4", "01_A.mov"]


def test_assign_group_indices_aligned_with_input_order():
    videos = ["01_B.mp4", "01_A.mp4", "02_B.mp4"]
    assignments = assign_group_indices(videos)

    # group 0 = "B" (first appearance), group 1 = "A"
    assert assignments[0] == (0, "B")
    assert assignments[1] == (1, "A")
    assert assignments[2] == (0, "B")


def test_sanitize_suffix_replaces_unsafe_characters():
    assert sanitize_suffix('a<b>c:d"e/f\\g|h?i*j') == "a_b_c_d_e_f_g_h_i_j"

def test_sanitize_suffix_empty_falls_back_to_video():
    assert sanitize_suffix("...") == "video"

def test_sanitize_suffix_reserved_windows_name():
    assert sanitize_suffix("CON") == "_CON"
    assert sanitize_suffix("con") == "_con"

def test_sanitize_suffix_caps_length():
    assert len(sanitize_suffix("x" * 500)) == 100


def test_dedupe_suffixes_disambiguates_collisions():
    assert dedupe_suffixes(["A", "B", "A", "A"]) == ["A", "B", "A_2", "A_3"]

def test_dedupe_suffixes_no_collision_unchanged():
    assert dedupe_suffixes(["A", "B", "C"]) == ["A", "B", "C"]
