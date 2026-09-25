"""Layer 3 composes validated inputs and existing Layer 2 results."""

from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import (
    FourPillarsAnalysis, KnowledgeBase, VisibleStemAnalysis, analyze_four_pillars,
)

CHART = dict(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
POSITIONS = ("year", "month", "day", "hour")
HIDDEN = (
    [("甲", "食神"), ("丙", "偏財"), ("戊", "七殺")],
    [("乙", "傷官")],
    [("戊", "七殺"), ("辛", "正印"), ("丁", "正財")],
    [("丙", "偏財"), ("戊", "七殺"), ("庚", "偏印")],
)


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase()


@pytest.fixture(scope="module")
def analysis(kb):
    return kb.analyze_four_pillars(**CHART)


def test_canonical_parsing_roles_and_visible_stems(kb, analysis):
    assert analysis.day_master is kb.get_heavenly_stem("壬")
    assert analysis.day_master is analysis.chart.day.stem
    assert tuple(item.position for item in analysis.pillars) == POSITIONS
    for item, position, name in zip(analysis.pillars, POSITIONS, ("偏財", "正印", None, "傷官"), strict=True):
        pillar = getattr(analysis.chart, position)
        assert item.pillar is pillar
        assert pillar.stem is kb.get_heavenly_stem(CHART[position][0])
        assert pillar.branch is kb.get_earthly_branch(CHART[position][1])
        visible = item.visible_stem_analysis
        assert visible.stem is pillar.stem
        if position == "day":
            assert visible.role == "day_master"
            assert visible.ten_god_result is None
        else:
            assert visible.role == "target"
            assert visible.ten_god_result.ten_god.name_zh == name
            assert visible.ten_god_result == kb.get_ten_god("壬", pillar.stem.char)


def test_all_four_hidden_stem_lists_and_traces(kb, analysis):
    for item, expected in zip(analysis.pillars, HIDDEN, strict=True):
        branch = item.branch_analysis
        assert branch.branch is item.pillar.branch
        assert branch.day_master is analysis.day_master
        assert branch == kb.get_branch_ten_gods("壬", item.pillar.branch.id)
        assert [(i.hidden_stem.char, i.ten_god_result.ten_god.name_zh)
                for i in branch.hidden_stem_results] == expected
        assert [i.hidden_stem for i in branch.hidden_stem_results] == kb.get_hidden_stems(item.pillar.branch.id)
        for hidden in branch.hidden_stem_results:
            nested = hidden.ten_god_result
            assert nested.target is hidden.hidden_stem
            assert nested.trace == kb.get_ten_god("壬", hidden.hidden_stem.id).trace
            assert nested.ten_god.source_status.value == "requires_validation"


@pytest.mark.parametrize("position", POSITIONS)
@pytest.mark.parametrize("invalid", ["丙", "寅", "ABC", "甲甲", "子甲", "", "renxu", " 壬戌", "壬戌 ", "壬 戌", "壬戌\n", "1986-03-19 10:22"])
def test_invalid_pillar_input(kb, position, invalid):
    with pytest.raises(ValueError, match=position):
        kb.analyze_four_pillars(**{**CHART, position: invalid})


@pytest.mark.parametrize("position", POSITIONS)
@pytest.mark.parametrize("invalid", [None, 12, True, ["壬", "戌"], {"stem": "壬", "branch": "戌"}])
def test_non_string_pillars(kb, position, invalid):
    with pytest.raises(TypeError, match=position):
        kb.analyze_four_pillars(**{**CHART, position: invalid})


@pytest.mark.parametrize("position", POSITIONS)
def test_all_four_positions_are_required(kb, position):
    with pytest.raises(TypeError):
        kb.analyze_four_pillars(**{key: value for key, value in CHART.items() if key != position})


def test_api_requires_named_pillars_and_no_day_master_override(kb):
    with pytest.raises(TypeError):
        kb.analyze_four_pillars(*CHART.values())
    with pytest.raises(TypeError):
        kb.analyze_four_pillars(**CHART, day_master="甲")


@pytest.mark.parametrize("stem", "甲乙丙丁戊己庚辛壬癸")
def test_day_master_follows_day_stem_for_every_master(kb, stem):
    day_pillar = next(p for p in kb.generate_sexagenary_cycle() if p.stem.char == stem)
    result = kb.analyze_four_pillars(**{**CHART, "day": stem + day_pillar.branch.char})
    assert result.day_master.char == stem
    assert result.pillars[2].visible_stem_analysis.role == "day_master"
    for pillar in result.pillars:
        visible = pillar.visible_stem_analysis.ten_god_result
        if visible is not None:
            assert visible == kb.get_ten_god(stem, pillar.pillar.stem.char)
        assert pillar.branch_analysis == kb.get_branch_ten_gods(stem, pillar.pillar.branch.char)


def test_repeated_pillars_keep_positions_and_only_day_has_special_role(kb):
    result = kb.analyze_four_pillars(**dict.fromkeys(POSITIONS, "壬戌"))
    assert tuple(p.position for p in result.pillars) == POSITIONS
    for item in result.pillars:
        if item.position != "day":
            assert item.visible_stem_analysis.role == "target"
            assert item.visible_stem_analysis.ten_god_result.ten_god.name_zh == "比肩"
        assert item.branch_analysis == kb.get_branch_ten_gods("壬", "戌")


def test_all_pillars_are_validated_before_layer2_calls(monkeypatch):
    kb = KnowledgeBase()

    def unexpected(*args):
        pytest.fail("Layer 2 was called before validating the hour pillar")

    monkeypatch.setattr(kb, "get_ten_god", unexpected)
    monkeypatch.setattr(kb, "get_branch_ten_gods", unexpected)
    with pytest.raises(ValueError, match="hour"):
        kb.analyze_four_pillars(**{**CHART, "hour": "甲甲"})


def test_existing_api_results_are_reused_without_copying(monkeypatch):
    kb = KnowledgeBase()
    compute, expand = kb.get_ten_god, kb.get_branch_ten_gods
    visible_calls, branch_calls = [], []
    inside_branch = False

    def tracked_compute(master, target):
        result = compute(master, target)
        if not inside_branch:
            visible_calls.append((master, target, result))
        return result

    def tracked_expand(master, branch):
        nonlocal inside_branch
        inside_branch = True
        result = expand(master, branch)
        inside_branch = False
        branch_calls.append((master, branch, result))
        return result

    monkeypatch.setattr(kb, "get_ten_god", tracked_compute)
    monkeypatch.setattr(kb, "get_branch_ten_gods", tracked_expand)
    result = kb.analyze_four_pillars(**CHART)
    assert [(master, target) for master, target, _ in visible_calls] == [
        ("ren", "bing"), ("ren", "xin"), ("ren", "yi"),
    ]
    assert [(master, branch) for master, branch, _ in branch_calls] == [
        ("ren", "yin"), ("ren", "mao"), ("ren", "xu"), ("ren", "si"),
    ]
    for item, (_, _, original) in zip(result.pillars, branch_calls, strict=True):
        assert item.branch_analysis is original
    for item, (_, _, original) in zip((p for p in result.pillars if p.position != "day"), visible_calls, strict=True):
        assert item.visible_stem_analysis.ten_god_result is original


def test_chart_trace_and_nested_source_records_are_resolvable(kb, analysis):
    references = {"chart:input": analysis.chart, "day_master:ren": analysis.day_master}
    references.update({f"sexagenary_cycle:{index}": pillar
                       for index, pillar in enumerate(kb.generate_sexagenary_cycle(), start=1)})
    for item in analysis.pillars:
        references[f"pillars:{item.position}"] = item.pillar
        references[f"heavenly_stems:{item.pillar.stem.id}"] = item.pillar.stem
        references[f"earthly_branches:{item.pillar.branch.id}"] = item.pillar.branch
    assert analysis.trace[0].output_refs == tuple(f"pillars:{position}" for position in POSITIONS)
    assert analysis.trace[-1].input_refs == ("pillars:day", "heavenly_stems:ren")
    assert analysis.trace[-1].output_refs == ("day_master:ren",)
    for step in analysis.trace:
        assert step.source_ids == ()  # Caller input + documented implementation convention, not literature evidence.
        assert all(ref in references for ref in (*step.input_refs, *step.output_refs))
    sources = {source.id: source for source in analysis.sources}
    assert len(sources) == len(analysis.sources)
    for item in analysis.pillars:
        results = [item.branch_analysis, item.visible_stem_analysis.ten_god_result]
        results.extend(hidden.ten_god_result for hidden in item.branch_analysis.hidden_stem_results)
        for nested in results:
            if nested is not None:
                assert all(sources[source.id] == source for source in nested.sources)
                assert all(set(step.source_ids) <= sources.keys() for step in nested.trace)


def test_custom_yaml_changes_flow_through_layer3(tmp_path):
    root = Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))
    path = root / "hidden_stems.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    next(r for r in raw["hidden_stems"] if r["branch_id"] == "xu")["stem_ids"] = ["ding", "xin"]
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    path = root / "天干/heavenly_stems.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    next(r for r in raw["heavenly_stems"] if r["id"] == "xin")["element"] = "wood"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    kb = KnowledgeBase(root)
    result = kb.analyze_four_pillars(**CHART)
    assert result.chart.month.stem.element == "wood"
    assert result.pillars[1].visible_stem_analysis.ten_god_result.ten_god.name_zh == "傷官"
    assert [(item.hidden_stem.char, item.ten_god_result.ten_god.name_zh)
            for item in result.pillars[2].branch_analysis.hidden_stem_results] == [("丁", "正財"), ("辛", "傷官")]


def test_json_roundtrip_and_top_level_wrapper(analysis):
    assert analyze_four_pillars(**CHART) == analysis
    assert FourPillarsAnalysis.model_validate_json(analysis.model_dump_json()) == analysis


@pytest.mark.parametrize("mutation", ["wrong_master", "wrong_order", "wrong_pillar", "wrong_role", "wrong_branch"])
def test_inconsistent_structured_results_are_rejected(analysis, mutation):
    raw = analysis.model_dump()
    if mutation == "wrong_master":
        raw["day_master"] = raw["chart"]["year"]["stem"]
    elif mutation == "wrong_order":
        raw["pillars"] = tuple(reversed(raw["pillars"]))
    elif mutation == "wrong_pillar":
        raw["pillars"][0]["pillar"] = raw["chart"]["hour"]
    elif mutation == "wrong_role":
        raw["pillars"][0]["visible_stem_analysis"].update(role="day_master", ten_god_result=None)
    else:
        raw["pillars"][0]["branch_analysis"] = raw["pillars"][1]["branch_analysis"]
    with pytest.raises(ValidationError):
        FourPillarsAnalysis.model_validate(raw)


def test_day_master_role_cannot_be_replaced_by_peer_relationship(kb, analysis):
    raw = analysis.pillars[2].visible_stem_analysis.model_dump()
    raw["ten_god_result"] = kb.get_ten_god("壬", "壬")
    with pytest.raises(ValidationError):
        VisibleStemAnalysis.model_validate(raw)


@pytest.mark.parametrize("field", ["weight", "qi_classification", "month_priority", "strength", "fortune", "birth_date"])
def test_new_models_reject_out_of_scope_fields(analysis, field):
    for record in (analysis, analysis.chart, analysis.chart.day, analysis.pillars[0],
                   analysis.pillars[0].visible_stem_analysis):
        with pytest.raises(ValidationError, match="Extra inputs"):
            type(record).model_validate({**record.model_dump(), field: "unsupported"})


def test_analysis_is_immutable(analysis):
    with pytest.raises(ValidationError, match="frozen"):
        analysis.pillars = ()


def test_canonical_chart_interactions_preserve_positions_and_trace(kb, analysis):
    stem, = analysis.stem_interactions
    branch, = analysis.branch_interactions
    assert (stem.domain, stem.left_position, stem.right_position) == ("heavenly_stem", "year", "month")
    assert (branch.domain, branch.left_position, branch.right_position) == ("earthly_branch", "month", "day")
    assert (stem.left_member.char, stem.right_member.char, stem.relation_result.rule.relation) == ("丙", "辛", "combine")
    assert (branch.left_member.char, branch.right_member.char, branch.relation_result.rule.relation) == ("卯", "戌", "six_harmony")
    assert stem.relation_result == kb.get_stem_relations("丙", "辛")[0]
    assert branch.relation_result == kb.get_branch_relations("卯", "戌")[0]
    sources = {source.id: source for source in analysis.sources}
    for item in (stem, branch):
        assert item.relation_result.rule.source_status.value == "requires_validation"
        assert all(sources[source.id] == source for source in item.relation_result.sources)


def test_six_pairs_per_domain_are_called_once_and_results_reused(monkeypatch):
    from itertools import combinations
    kb = KnowledgeBase()
    calls = {"stem": [], "branch": []}
    originals = {"stem": kb.get_stem_relations, "branch": kb.get_branch_relations}

    def tracked(domain):
        def query(left, right):
            results = originals[domain](left, right)
            calls[domain].append((left, right, results))
            return results
        return query

    monkeypatch.setattr(kb, "get_stem_relations", tracked("stem"))
    monkeypatch.setattr(kb, "get_branch_relations", tracked("branch"))
    result = kb.analyze_four_pillars(**CHART)
    for domain, ids, interactions in (
        ("stem", ("bing", "xin", "ren", "yi"), result.stem_interactions),
        ("branch", ("yin", "mao", "xu", "si"), result.branch_interactions),
    ):
        assert [(a, b) for a, b, _ in calls[domain]] == list(combinations(ids, 2))
        matched = [match for _, _, matches in calls[domain] for match in matches]
        assert len(interactions) == len(matched)
        assert all(item.relation_result is original for item, original in zip(interactions, matched, strict=True))


def test_repeated_members_keep_distinct_position_pairs_without_reversed_duplicates(kb):
    result = kb.analyze_four_pillars(year="丙寅", month="辛卯", day="丙寅", hour="辛卯")
    assert [(item.left_position, item.right_position) for item in result.stem_interactions] == [
        ("year", "month"), ("year", "hour"), ("month", "day"), ("day", "hour"),
    ]
    assert result.branch_interactions == ()
    assert result.stem_interactions[2].relation_result.members[0].char == "辛"


def test_clashes_and_no_matches(kb):
    result = kb.analyze_four_pillars(year="甲子", month="甲午", day="甲子", hour="甲午")
    assert result.stem_interactions == ()
    assert len(result.branch_interactions) == 4
    assert {item.relation_result.rule.relation for item in result.branch_interactions} == {"clash"}
    empty = kb.analyze_four_pillars(**dict.fromkeys(POSITIONS, "甲子"))
    assert empty.stem_interactions == empty.branch_interactions == ()


@pytest.mark.parametrize("mutation", ["reverse", "domain", "position", "duplicate"])
def test_bad_chart_interaction_context_rejected(analysis, mutation):
    raw = analysis.model_dump()
    item = raw["stem_interactions"][0]
    if mutation == "reverse":
        item["left_position"], item["right_position"] = item["right_position"], item["left_position"]
    elif mutation == "domain":
        item["domain"] = "earthly_branch"
    elif mutation == "position":
        item["right_position"] = "hour"
    else:
        raw["stem_interactions"] = (item, item)
    with pytest.raises(ValidationError):
        FourPillarsAnalysis.model_validate(raw)
