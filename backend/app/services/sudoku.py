"""Service du défi Sudoku : génération de grille, validation et attribution d'XP.

Le serveur génère une grille pleine valide (backtracking), en retire des cases
selon le niveau, puis mémorise les indices de départ (:class:`SudokuSession`). À
la résolution, il valide la grille soumise (chaque ligne, colonne et bloc
contient bien 1..n, et les indices de départ sont respectés) et crédite l'XP une
seule fois via :func:`app.services.gamification.award_xp` sur la matière « Défis »
(le même porte-monnaie que le défi Pythagore, qui alimente le Pokédex).
"""

import random
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.challenge import SudokuSession
from app.models.content import Subject
from app.schemas.sudoku import SudokuDifficulty
from app.services.collection import get_balance
from app.services.gamification import award_xp

CHALLENGE_SUBJECT_SLUG = "defis"

# Taille de grille et forme des blocs par niveau.
_SIZE: dict[SudokuDifficulty, int] = {
    SudokuDifficulty.EASY: 4,
    SudokuDifficulty.MEDIUM: 6,
    SudokuDifficulty.HARD: 8,
}
# (hauteur, largeur) d'un bloc : 4→2×2, 6→2×3, 8→2×4.
_BOX: dict[int, tuple[int, int]] = {4: (2, 2), 6: (2, 3), 8: (2, 4)}
_XP: dict[SudokuDifficulty, int] = {
    SudokuDifficulty.EASY: 10,
    SudokuDifficulty.MEDIUM: 20,
    SudokuDifficulty.HARD: 30,
}
# Nombre de cases retirées (cases à remplir) par niveau — dosé pour des enfants.
_BLANKS: dict[SudokuDifficulty, int] = {
    SudokuDifficulty.EASY: 6,
    SudokuDifficulty.MEDIUM: 14,
    SudokuDifficulty.HARD: 24,
}


def _challenge_subject_id(db: Session) -> UUID:
    """Récupère (ou crée) la matière « Défis » support de l'XP des mini-jeux."""
    subject = db.query(Subject).filter(Subject.slug == CHALLENGE_SUBJECT_SLUG).first()
    if subject is None:
        subject = Subject(
            name="Défis",
            slug=CHALLENGE_SUBJECT_SLUG,
            description="Mini-jeux pour gagner de l'XP",
            icon="🏆",
            is_active=False,
        )
        db.add(subject)
        db.flush()
    return subject.id


def _shuffled(seq: range) -> list[int]:
    out = list(seq)
    random.shuffle(out)
    return out


def _generate_full(size: int, box_rows: int, box_cols: int) -> list[list[int]]:
    """Génère une grille pleine valide en O(n²), sans backtracking.

    On part du motif canonique d'un Sudoku rectangulaire (blocs ``box_rows`` ×
    ``box_cols``, ``size == box_rows * box_cols``), garanti valide, puis on le
    brouille : permutation des chiffres, des lignes dans chaque bande, des
    colonnes dans chaque pile, et des bandes/piles entre elles. Instantané même
    en 8×8 (contrairement au backtracking, qui peut s'emballer).
    """
    rows_per_box, cols_per_box = box_rows, box_cols

    def pattern(r: int, c: int) -> int:
        return (cols_per_box * (r % rows_per_box) + r // rows_per_box + c) % size

    # Bandes = groupes de ``rows_per_box`` lignes ; piles = groupes de ``cols_per_box`` colonnes.
    row_order = [
        band * rows_per_box + r
        for band in _shuffled(range(size // rows_per_box))
        for r in _shuffled(range(rows_per_box))
    ]
    col_order = [
        stack * cols_per_box + c
        for stack in _shuffled(range(size // cols_per_box))
        for c in _shuffled(range(cols_per_box))
    ]
    nums = list(range(1, size + 1))
    random.shuffle(nums)
    return [[nums[pattern(r, c)] for c in col_order] for r in row_order]


def _carve(full: list[list[int]], size: int, blanks: int) -> list[list[int]]:
    """Retire ``blanks`` cases (mises à 0) d'une grille pleine pour créer le puzzle."""
    puzzle = [row[:] for row in full]
    cells = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(cells)
    for r, c in cells[:blanks]:
        puzzle[r][c] = 0
    return puzzle


def new_puzzle(user_id: UUID, difficulty: SudokuDifficulty, db: Session) -> dict[str, Any]:
    """Génère une grille, la mémorise et renvoie le payload pour ``PuzzleResponse``."""
    size = _SIZE[difficulty]
    box_rows, box_cols = _BOX[size]
    full = _generate_full(size, box_rows, box_cols)
    puzzle = _carve(full, size, _BLANKS[difficulty])
    xp_reward = _XP[difficulty]

    session = SudokuSession(
        user_id=user_id,
        difficulty=difficulty.value,
        size=size,
        puzzle=puzzle,
        xp_reward=xp_reward,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": str(session.id),
        "difficulty": difficulty,
        "size": size,
        "box_rows": box_rows,
        "box_cols": box_cols,
        "puzzle": puzzle,
        "xp_reward": xp_reward,
    }


def _is_valid_solution(puzzle: list[list[int]], grid: list[list[int]], size: int) -> bool:
    """Valide une grille complète : dimensions, indices respectés, lignes/colonnes/blocs."""
    if len(grid) != size or any(len(row) != size for row in grid):
        return False
    for row in grid:
        for v in row:
            # ``bool`` est un sous-type d'``int`` : on l'exclut explicitement.
            if isinstance(v, bool) or not isinstance(v, int) or v < 1 or v > size:
                return False
    # Les indices de départ doivent être conservés.
    for r in range(size):
        for c in range(size):
            if puzzle[r][c] != 0 and grid[r][c] != puzzle[r][c]:
                return False
    full = set(range(1, size + 1))
    for r in range(size):
        if set(grid[r]) != full:
            return False
    for c in range(size):
        if {grid[r][c] for r in range(size)} != full:
            return False
    box_rows, box_cols = _BOX[size]
    for r0 in range(0, size, box_rows):
        for c0 in range(0, size, box_cols):
            box = [grid[y][x] for y in range(r0, r0 + box_rows) for x in range(c0, c0 + box_cols)]
            if set(box) != full:
                return False
    return True


def solve(session: SudokuSession, grid: list[list[int]], db: Session) -> dict[str, Any]:
    """Vérifie la solution soumise et crédite l'XP au premier envoi correct."""
    if session.solved_at is not None:
        return {
            "correct": True,
            "already_solved": True,
            "xp_earned": 0,
            "balance": get_balance(session.user_id, db),
        }

    if not _is_valid_solution(session.puzzle, grid, session.size):
        return {
            "correct": False,
            "already_solved": False,
            "xp_earned": 0,
            "balance": get_balance(session.user_id, db),
        }

    award_xp(session.user_id, session.xp_reward, _challenge_subject_id(db), db)
    session.solved_at = datetime.utcnow()
    session.xp_earned = session.xp_reward
    db.commit()

    return {
        "correct": True,
        "already_solved": False,
        "xp_earned": session.xp_reward,
        "balance": get_balance(session.user_id, db),
    }
