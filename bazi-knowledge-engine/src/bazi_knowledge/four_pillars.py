"""Chart-level composition of existing pairwise APIs, preserving position context."""

from itertools import combinations
from typing import TYPE_CHECKING, get_args

from .models import ChartInteraction, FourPillars, PillarPosition

if TYPE_CHECKING:
    from .loader import KnowledgeBase


def scan_chart_interactions(kb: "KnowledgeBase", chart: FourPillars):
    stems, branches = [], []
    for left, right in combinations(get_args(PillarPosition), 2):
        left_pillar, right_pillar = getattr(chart, left), getattr(chart, right)
        for output, domain, results in (
            (stems, "heavenly_stem", kb.get_stem_relations(left_pillar.stem.id, right_pillar.stem.id)),
            (branches, "earthly_branch", kb.get_branch_relations(left_pillar.branch.id, right_pillar.branch.id)),
        ):
            output.extend(ChartInteraction(domain=domain, left_position=left, right_position=right,
                                           relation_result=result) for result in results)
    return tuple(stems), tuple(branches)
