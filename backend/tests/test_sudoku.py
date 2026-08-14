"""Tests du défi Sudoku (mini-jeu « free XP », 3 niveaux).

Le serveur génère la grille et valide la solution (règles + indices) ; l'XP
(10/20/30 selon le niveau) n'est crédité qu'au premier envoi correct.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from tests.helpers import child_headers, make_child

_BOX = {4: (2, 2), 6: (2, 3), 8: (2, 4)}
_XP = {"easy": 10, "medium": 20, "hard": 30}
_SIZE = {"easy": 4, "medium": 6, "hard": 8}


def _solve(puzzle: list[list[int]], size: int) -> list[list[int]]:
    """Résout une grille par backtracking (grilles petites → rapide)."""
    br, bc = _BOX[size]
    g = [row[:] for row in puzzle]

    def ok(r: int, c: int, v: int) -> bool:
        if any(g[r][x] == v for x in range(size)) or any(g[y][c] == v for y in range(size)):
            return False
        r0, c0 = (r // br) * br, (c // bc) * bc
        return all(g[y][x] != v for y in range(r0, r0 + br) for x in range(c0, c0 + bc))

    def bt(pos: int) -> bool:
        if pos == size * size:
            return True
        r, c = divmod(pos, size)
        if g[r][c] != 0:
            return bt(pos + 1)
        for v in range(1, size + 1):
            if ok(r, c, v):
                g[r][c] = v
                if bt(pos + 1):
                    return True
                g[r][c] = 0
        return False

    bt(0)
    return g


def _new(client: TestClient, h: dict[str, str], difficulty: str) -> dict:
    r = client.post("/api/v1/sudoku/new", json={"difficulty": difficulty}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_new_puzzle_shape_and_metadata(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CE1, name="s1")
    h = child_headers(client, child)
    for diff in ("easy", "medium", "hard"):
        p = _new(client, h, diff)
        size = _SIZE[diff]
        assert p["size"] == size
        assert (p["box_rows"], p["box_cols"]) == _BOX[size]
        assert p["xp_reward"] == _XP[diff]
        assert len(p["puzzle"]) == size and all(len(row) == size for row in p["puzzle"])
        assert any(v == 0 for row in p["puzzle"] for v in row)  # il y a bien des cases à remplir


def test_correct_solution_awards_xp_once(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CE1, name="s2")
    h = child_headers(client, child)
    p = _new(client, h, "medium")
    solution = _solve(p["puzzle"], p["size"])

    r1 = client.post(f"/api/v1/sudoku/{p['session_id']}/solve", json={"grid": solution}, headers=h).json()
    assert r1["correct"] is True
    assert r1["xp_earned"] == 20
    assert r1["balance"] == 20

    # Rejouer la même grille ne recrédite pas.
    r2 = client.post(f"/api/v1/sudoku/{p['session_id']}/solve", json={"grid": solution}, headers=h).json()
    assert r2["correct"] is True
    assert r2["already_solved"] is True
    assert r2["xp_earned"] == 0
    assert r2["balance"] == 20


def test_wrong_solution_is_rejected(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CE1, name="s3")
    h = child_headers(client, child)
    p = _new(client, h, "easy")
    wrong = [[1] * p["size"] for _ in range(p["size"])]  # tout à 1 : viole les règles
    r = client.post(f"/api/v1/sudoku/{p['session_id']}/solve", json={"grid": wrong}, headers=h).json()
    assert r["correct"] is False
    assert r["xp_earned"] == 0
    assert r["balance"] == 0


def test_incomplete_grid_is_rejected(client: TestClient, db_session: Session):
    child = make_child(db_session, level=LevelEnum.CE1, name="s4")
    h = child_headers(client, child)
    p = _new(client, h, "easy")
    solution = _solve(p["puzzle"], p["size"])
    solution[0][0] = 0  # une case laissée vide → refusée
    r = client.post(f"/api/v1/sudoku/{p['session_id']}/solve", json={"grid": solution}, headers=h).json()
    assert r["correct"] is False
    assert r["xp_earned"] == 0
