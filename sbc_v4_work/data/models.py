"""
Data models for SBC Academic Portal.
All structured academic data lives here.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Assignment:
    title: str
    due_date: Optional[str] = None
    grade: Optional[str] = None
    max_grade: Optional[str] = None
    grade_raw: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Subject:
    name: str
    code: Optional[str] = None
    teacher: Optional[str] = None
    grade: Optional[str] = None           # e.g. "85%" or "A"
    grade_raw: Optional[float] = None     # numeric 0-100
    class_average: Optional[float] = None
    year: Optional[int] = None
    period: Optional[str] = None          # e.g. "Semester 1"
    assignments: list = field(default_factory=list)
    topics: list = field(default_factory=list)


@dataclass
class UserProfile:
    username: str = ""
    display_name: str = ""
    email: str = ""
    student_id: str = ""
    year_level: str = ""
    avatar_url: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class AcademicData:
    profile: Optional[UserProfile] = None
    subjects_by_year: dict = field(default_factory=dict)  # {year: [Subject]}
    raw_html: dict = field(default_factory=dict)          # for debugging
    groups: list = field(default_factory=list)            # [{name, url, id}]
    calendar_events: dict = field(default_factory=dict)   # {date: [events]}

    def overall_average(self, year: Optional[int] = None) -> Optional[float]:
        subjects = self._get_subjects(year)
        grades = [s.grade_raw for s in subjects if s.grade_raw is not None]
        if not grades:
            return None
        return round(sum(grades) / len(grades), 1)

    def _get_subjects(self, year: Optional[int] = None):
        if year is not None:
            return self.subjects_by_year.get(year, [])
        all_subjects = []
        for subj_list in self.subjects_by_year.values():
            all_subjects.extend(subj_list)
        return all_subjects

    def all_years(self):
        return sorted(self.subjects_by_year.keys(), reverse=True)
