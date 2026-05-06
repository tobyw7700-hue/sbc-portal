"""
Grade calculation logic:
  - Skip Formative tasks entirely
  - Part A and Part B are NEVER included in the grade average —
    they are sub-components. Only the final/overall assessment counts.
  - All grades shown to 1 decimal place
"""
import re
from typing import List, Optional, Tuple
from data.models import Assignment


def is_formative(assignment: Assignment) -> bool:
    title = (assignment.title or "").lower()
    desc  = (assignment.description or "").lower()
    if "formative" in title:
        return True
    if "formative" in desc:
        return True
    if "unweighted" in title:
        return True
    return False


def _is_part_ab(title: str) -> bool:
    """Return True if this is a sub-part (Part A, Part B, Part C etc.)."""
    return bool(re.search(r'\bpart\s+[A-Ca-c]\b', title, re.I))


def fmt_grade(grade_raw: Optional[float]) -> str:
    if grade_raw is None:
        return "N/A"
    return f"{grade_raw:.1f}%"


def grade_label(grade_raw: Optional[float]) -> str:
    """SBC: A+=90+, A=80-89, B=70-79, C=60-69, D=40-59, UG=<40"""
    if grade_raw is None: return ""
    if grade_raw >= 90:   return "A+"
    if grade_raw >= 80:   return "A"
    if grade_raw >= 70:   return "B"
    if grade_raw >= 60:   return "C"
    if grade_raw >= 40:   return "D"
    return "UG"


def compute_subject_grade(assignments: List[Assignment]) -> Tuple[Optional[float], List[Assignment]]:
    """
    Returns (grade_1dp, tasks_included).

    Rules applied in order:
      1. Remove formative tasks
      2. Remove Part A / Part B tasks — they are never averaged;
         only the final assessment result counts
      3. Average remaining graded tasks
    """
    if not assignments:
        return None, []

    # Step 1: remove formatives
    non_formative = [a for a in assignments if not is_formative(a)]

    # Step 2: remove Part A / Part B sub-components
    final = [a for a in non_formative if not _is_part_ab(a.title)]

    # Step 3: only tasks with a grade
    graded = [a for a in final if a.grade_raw is not None]

    if not graded:
        return None, []

    avg = sum(a.grade_raw for a in graded) / len(graded)
    return round(avg, 1), graded
