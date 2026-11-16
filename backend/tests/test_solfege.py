"""Solfège contracts, grading and the downloadable CE1 / 1C1 agent workflow."""

import pytest

from app.api.exercises import check_answer_correctness
from app.models.content import Exercise, ExerciseType
from app.schemas.exercise import staff_step, validate_exercise_payload
from app.services.pack_format import PackRejected, validate_pack
from tests.helpers import dev_login
from tests.test_contributions import AUTHOR, first_upload
from tests.test_pack_format import lesson, pack


def validate(kind, content, answer):
    validate_exercise_payload(ExerciseType(kind), content, answer)


def grade(kind, content, correct, given):
    return check_answer_correctness(Exercise(type=kind, content=content, correct_answer=correct), given)


def rhythm(mode="count", events=None, **kwargs):
    return {"mode": mode, "events": events or ["noire", "soupir", "blanche"], **kwargs}


def listening():
    return rhythm(
        "listen",
        ["croche", "croche", "noire"],
        beats_per_bar=2,
        choices=[
            {"id": "a", "events": ["noire", "croche", "croche"]},
            {"id": "b", "events": ["croche", "croche", "noire"]},
        ],
    )


def test_bass_clef_contract_and_positions():
    assert staff_step("fa", "G2") == 0
    assert staff_step("fa", "F3") == 6
    assert staff_step("fa", "C2") == -4
    assert staff_step("fa", "E4") == 12
    validate("music_note", {"clef": "fa", "pitch": "F3"}, {"name": "fa"})
    with pytest.raises(ValueError):
        validate("music_note", {"clef": "fa", "pitch": "F4"}, {"name": "fa"})


@pytest.mark.parametrize(
    "events,total",
    [
        (["ronde"], 4),
        (["blanche"], 2),
        (["noire"], 1),
        (["croche"], 0.5),
        (["noire", "soupir", "blanche"], 4),
        (["blanche", "demi_pause"], 4),
        (["croche", "demi_soupir", "noire"], 2),
    ],
)
def test_rhythm_counts_include_silences(events, total):
    content = rhythm(events=events)
    validate("music_rhythm", content, {"beats": total})
    assert grade("music_rhythm", content, {"beats": total}, {"beats": total})
    assert not grade("music_rhythm", content, {"beats": total}, {"beats": total + 1})
    assert not grade("music_rhythm", content, {"beats": total}, {"beats": True})


@pytest.mark.parametrize(
    "overrides",
    [
        {"events": []},
        {"events": ["triolet"]},
        {"bpm": 0},
        {"bpm": 121},
        {"bpm": True},
        {"events": ["soupir"]},
        {"events": ["ronde"] * 5},
        {"beats_per_bar": 6},
        {"events": ["noire", "ronde"]},
        {"mode": "tap", "events": ["blanche"]},
        {"mode": "tap", "events": ["soupir", "noire", "noire"]},
        {"choices": [{"id": "a", "events": ["noire"]}, {"id": "b", "events": ["blanche"]}]},
    ],
)
def test_rhythm_rejects_unsupported_or_unplayable_patterns(overrides):
    content = rhythm()
    content.update(overrides)
    with pytest.raises(ValueError):
        validate("music_rhythm", content, {"beats": 4})


def test_rhythm_count_answer_must_match_content():
    with pytest.raises(ValueError, match="durée"):
        validate("music_rhythm", rhythm(), {"beats": 3})


def test_rhythm_listen_contract_and_grading():
    content = listening()
    validate("music_rhythm", content, {"option_id": "b"})
    assert grade("music_rhythm", content, {"option_id": "b"}, {"option_id": "b"})
    assert not grade("music_rhythm", content, {"option_id": "b"}, {"option_id": "a"})
    assert not grade("music_rhythm", content, {"option_id": "b"}, {})


@pytest.mark.parametrize(
    "fault", ["missing_choices", "duplicate_id", "duplicate_pattern", "unequal_duration", "no_match", "wrong_answer"]
)
def test_rhythm_listen_rejects_ambiguous_answers(fault):
    content = listening()
    answer = {"option_id": "b"}
    if fault == "missing_choices":
        del content["choices"]
    elif fault == "duplicate_id":
        content["choices"][0]["id"] = "b"
    elif fault == "duplicate_pattern":
        content["choices"][0]["events"] = content["events"]
    elif fault == "unequal_duration":
        content["choices"][0]["events"] = ["noire"]
    elif fault == "no_match":
        content["events"] = ["blanche"]
    else:
        answer["option_id"] = "a"
    with pytest.raises(ValueError):
        validate("music_rhythm", content, answer)


def test_taps_use_tempo_relative_to_first_attack_and_include_rest():
    content = rhythm("tap", ["noire", "soupir", "croche", "croche"], bpm=60)
    validate("music_rhythm", content, {})
    assert grade("music_rhythm", content, {}, {"taps": [10, 12.1, 12.6]})
    assert not grade("music_rhythm", content, {}, {"taps": [10, 11, 11.5]})
    assert not grade("music_rhythm", content, {}, {"taps": [10, 12]})
    assert not grade("music_rhythm", content, {}, {"taps": [10, 12, 12.5, 13]})
    with pytest.raises(ValueError, match="correct_answer"):
        validate("music_rhythm", content, {"taps": [0, 2, 2.5]})


@pytest.mark.parametrize(
    "taps",
    [
        None,
        [],
        [0],
        [0, 0],
        [1, 0],
        [-1, 0],
        [0, float("nan")],
        [0, float("inf")],
        ["bad", 1],
        [False, True],
        [0, 1] * 9,
    ],
)
def test_malformed_taps_fail_cleanly(taps):
    assert not grade("music_rhythm", rhythm("tap", ["noire", "noire"]), {}, {"taps": taps})


@pytest.mark.parametrize("mode", ["read", "listen"])
def test_sequences_validate_and_grade_all_names_in_order(mode):
    content = {"clef": "sol", "mode": mode, "pitches": ["C4", "D4", "E4"]}
    answer = {"names": ["do", "ré", "mi"]}
    validate("music_sequence", content, answer)
    assert grade("music_sequence", content, answer, {"names": [" DO ", "Re", "mi"]})
    for wrong in [{}, {"names": ["do"]}, {"names": ["mi", "ré", "do"]}, {"names": "do ré mi"}]:
        assert not grade("music_sequence", content, answer, wrong)


@pytest.mark.parametrize(
    "overrides",
    [
        {"pitches": ["C4"]},
        {"pitches": ["C4"] * 9},
        {"pitches": ["C#4", "D4"]},
        {"pitches": ["C1", "D1"]},
        {"clef": "ut4"},
        {"bpm": 49},
        {"mode": "sing"},
    ],
)
def test_bad_sequences_are_rejected(overrides):
    content = {"clef": "sol", "pitches": ["C4", "D4"]}
    content.update(overrides)
    with pytest.raises(ValueError):
        validate("music_sequence", content, {"names": ["do", "ré"]})


def test_sequence_answer_mismatch_is_rejected():
    with pytest.raises(ValueError, match="names"):
        validate("music_sequence", {"pitches": ["C4", "D4"]}, {"names": ["ré", "do"]})


def test_agent_starter_is_valid_ce1_only_and_uploads_through_token(client, db_session):
    from uuid import UUID

    from app.models.content import Lesson
    from app.models.pack import Pack

    response = client.get("/api/v1/agent/solfege-1c1.explorito")
    assert response.status_code == 200
    document = response.json()
    payload, issues, score = validate_pack(document)
    assert score == 100
    assert not [issue for issue in issues if issue.severity in {"error", "warning"}]
    assert len(payload["lessons"]) == 8
    assert {lesson["level"] for lesson in payload["lessons"]} == {"ce1"}
    exercises = [ex for lesson in payload["lessons"] for ex in lesson["exercises"]]
    assert len(exercises) == 40
    assert {"music_note", "music_sequence", "music_rhythm"} <= {ex["type"] for ex in exercises}
    assert {ex["content"]["mode"] for ex in exercises if ex["type"] == "music_rhythm"} == {"count", "listen", "tap"}
    headers = dev_login(client, AUTHOR)
    assert (
        client.post("/api/v1/contributions/terms/accept", headers=headers, json={"handle": "Toto"}).status_code == 200
    )
    secret = client.post("/api/v1/contributions/tokens", headers=headers, json={"label": "solfege"}).json()["token"]
    body = first_upload(client, {"X-Upload-Token": secret}, document)
    pack_id = UUID(body["pack_id"])
    assert db_session.query(Pack).filter(Pack.id == pack_id).one().community_status == "draft"
    lessons = db_session.query(Lesson).filter(Lesson.pack_id == pack_id).all()
    assert len(lessons) == 8
    assert db_session.query(Exercise).filter(Exercise.lesson_id.in_([lesson.id for lesson in lessons])).count() == 40


def test_invalid_agent_music_returns_indexed_pack_errors():
    exercise = {
        "type": "music_rhythm",
        "question": "Combien de temps ?",
        "content": rhythm(),
        "correct_answer": {"beats": 99},
        "difficulty_level": 1,
    }
    with pytest.raises(PackRejected) as exc:
        validate_pack(pack(lessons=[lesson(slug="musique", exercises=[exercise])]))
    issue = next(issue for issue in exc.value.issues if issue.code == "exercise_shape")
    assert (issue.lesson_index, issue.exercise_index) == (0, 0)


def test_agent_manifest_links_the_complete_solfege_workflow(client):
    music = client.get("/api/v1/agent").json()["capabilities"]["music"]
    assert music["curriculum"] == {"level": "ce1", "music_year": "1C1"}
    assert music["clefs"] == ["sol", "fa", "ut3"]
    assert music["exercise_types"]["music_rhythm"] == ["count", "listen", "tap"]
    guide = client.get(music["guide_url"])
    assert guide.status_code == 200
    assert "music_sequence" in guide.text and "music_rhythm" in guide.text
    assert client.get(music["starter_pack_url"]).status_code == 200
    # Every guide JSON exercise is a usable contract, not just illustrative prose.
    import json
    import re

    for block in re.findall(r"~~~json\n(.*?)\n~~~", guide.text, re.S):
        exercise = json.loads(block)
        validate(exercise["type"], exercise["content"], exercise["correct_answer"])
