from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PROFILE_FIELDS = {
    "school_id", "program_type", "enrollment_status", "year", "semester",
    "department_id", "international_student", "gpa_value", "gpa_scale",
    "gpa_period", "current_dorm_resident", "language_qualification",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Localized(StrictModel):
    ko: str
    zh: str


class Profile(StrictModel):
    school_id: str
    program_type: Literal["language", "undergraduate", "master", "doctor"]
    enrollment_status: Literal["enrolled", "leave", "graduated"]
    year: int | None = Field(default=None, ge=1, le=12)
    semester: int | None = Field(default=None, ge=1, le=30)
    department_id: Literal["engineering", "business", "humanities"]
    international_student: bool | None = None
    gpa_value: float | None = Field(default=None, ge=0, le=10)
    gpa_scale: float | None = Field(default=None, gt=0, le=10)
    gpa_period: str | None = None
    current_dorm_resident: bool | None = None
    language_qualification: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def check_gpa(self):
        if self.gpa_value is not None and self.gpa_scale is not None and self.gpa_value > self.gpa_scale:
            raise ValueError("GPA cannot exceed its scale")
        return self


class RegisterRequest(StrictModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=15, max_length=128, repr=False)
    display_name: str = Field(min_length=1, max_length=50)
    program_type: Literal["language", "undergraduate", "master", "doctor"]
    enrollment_status: Literal["enrolled", "leave", "graduated"]
    department_id: Literal["engineering", "business", "humanities"]

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value):
        return value.lower()

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("display_name cannot be whitespace only")
        return value


class LoginRequest(StrictModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=128, repr=False)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value):
        return value.lower()


class Rule(StrictModel):
    op: Literal["all", "any", "eq", "in", "gte", "lte", "is_true", "is_false", "needs_staff_review"]
    field: str | None = None
    value: str | int | float | bool | list[str | int | float | bool] | None = None
    children: list[Rule] = Field(default_factory=list)
    evidence: str = Field(min_length=1)

    @model_validator(mode="after")
    def controlled(self):
        if self.op in {"all", "any"}:
            if not self.children or self.field is not None or self.value is not None:
                raise ValueError("all/any require children only")
        else:
            if self.children:
                raise ValueError("leaf rules cannot contain children")
            if self.field not in PROFILE_FIELDS and not (self.op == "needs_staff_review" and self.field is None):
                raise ValueError("unsupported rule field")
            if self.op in {"gte", "lte"}:
                if self.field not in {"year", "semester", "gpa_value", "gpa_scale"} or type(self.value) not in {int, float}:
                    raise ValueError("numeric comparison requires whitelisted numeric field/value")
            if self.op == "in" and (not isinstance(self.value, list) or not self.value):
                raise ValueError("in requires nonempty list")
            if self.op in {"is_true", "is_false"} and self.field not in {"international_student", "current_dorm_resident"}:
                raise ValueError("boolean operator requires boolean field")
            if self.op in {"is_true", "is_false", "needs_staff_review"} and self.value is not None:
                raise ValueError("this operator has no comparison value")
            if self.op == "eq" and (self.value is None or isinstance(self.value, (dict, list))):
                raise ValueError("eq requires scalar non-null value")
            if self.op in {"eq", "in"}:
                values = self.value if self.op == "in" else [self.value]
                numeric = {"year", "semester", "gpa_value", "gpa_scale"}
                booleans = {"international_student", "current_dorm_resident"}
                enums = {"program_type": {"language", "undergraduate", "master", "doctor"}, "enrollment_status": {"enrolled", "leave", "graduated"}}
                for value in values:
                    if self.field in numeric and type(value) not in {int, float}:
                        raise ValueError("numeric rule requires number, not boolean or text")
                    if self.field in booleans and type(value) is not bool:
                        raise ValueError("boolean rule requires boolean value")
                    if self.field not in numeric | booleans and type(value) is not str:
                        raise ValueError("text field requires text rule value")
                    if self.field in enums and value not in enums[self.field]:
                        raise ValueError("unsupported enum rule value")
        return self


class Document(StrictModel):
    id: str
    title: Localized
    evidence: str = Field(min_length=1)


class TaskTemplate(StrictModel):
    id: str
    title: Localized
    description: Localized
    task_type: Literal["document", "prepare", "apply", "confirm"]
    required_or_suggested: Literal["required", "suggested"]
    source_evidence: str
    depends_on: list[str] = Field(default_factory=list)
    uses_deadline: bool = True
    suggested_lead_days: int | None = Field(default=None, ge=0, le=90)


class Window(StrictModel):
    opens_at: str | None = None
    closes_at: str | None = None


class Contact(StrictModel):
    name: Localized
    email: str | None = None
    phone: str | None = None
    evidence: str
    is_demo: bool = True


class Notice(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    school_id: str
    title: Localized
    category: Literal["scholarship", "dormitory", "activity"]
    source_url: str
    source_text: str = Field(min_length=1, max_length=100000)
    source_hash: str
    version: int = Field(ge=1)
    publication_status: Literal["draft", "under_review", "approved", "archived"]
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    eligibility_rules: Rule
    required_documents: list[Document]
    official_deadline: str | None
    application_window: Window
    application_url: str | None
    application_link_type: Literal["official", "demo", "unknown"]
    office_contact: Contact | None
    task_templates: list[TaskTemplate]
    evidence: dict[str, str]
    ambiguities: list[Localized]
    change_summary: Localized
    extraction_mode: Literal["fixed_demo", "real_ai", "manual"] = "manual"

    @field_validator("official_deadline")
    @classmethod
    def date_precision(cls, value):
        if value is not None:
            parse_temporal(value)
        return value

    @model_validator(mode="after")
    def semantic_validation(self):
        if self.source_hash != sha256(self.source_text.encode("utf-8")).hexdigest():
            raise ValueError("source_hash does not match preserved original")
        quotes = list(self.evidence.values())
        node_count = 0

        def walk(rule, depth=0):
            nonlocal node_count
            node_count += 1
            if depth > 12 or node_count > 100:
                raise ValueError("rule exceeds safe complexity")
            quotes.append(rule.evidence)
            for child in rule.children:
                walk(child, depth + 1)

        walk(self.eligibility_rules)
        quotes.extend(doc.evidence for doc in self.required_documents)
        quotes.extend(task.source_evidence for task in self.task_templates if task.required_or_suggested == "required")
        if self.office_contact:
            quotes.append(self.office_contact.evidence)
        for quote in quotes:
            if not quote or quote not in self.source_text:
                raise ValueError("evidence must be an exact quote of preserved source")
        for field in {"official_deadline", "application_url"}:
            if getattr(self, field) is not None and not self.evidence.get(field):
                raise ValueError(f"{field} requires source evidence")
        if self.official_deadline:
            # Dates/times must appear in evidence, never invented by extraction.
            temporal = parse_temporal(self.official_deadline)
            quote = self.evidence["official_deadline"]
            if temporal.isoformat()[:10] not in quote:
                raise ValueError("deadline date not found in its evidence")
            if isinstance(temporal, datetime) and temporal.strftime("%H:%M") not in quote:
                raise ValueError("deadline time not found in its evidence")
        if self.application_url and self.application_url not in self.evidence["application_url"]:
            raise ValueError("application URL not found in its evidence")
        if self.application_url:
            parsed_url = urlparse(self.application_url)
            if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname:
                raise ValueError("application links must be http(s), never executable URLs")
            if parsed_url.hostname.endswith(".invalid") and self.application_link_type != "demo":
                raise ValueError("reserved .invalid URLs must be marked demo placeholders")
        if self.office_contact:
            if self.office_contact.email and self.office_contact.email not in self.office_contact.evidence:
                raise ValueError("contact email must appear in its evidence")
            if self.office_contact.phone and self.office_contact.phone not in self.office_contact.evidence:
                raise ValueError("contact phone must appear in its evidence")
        for value in [self.application_window.opens_at, self.application_window.closes_at]:
            if value:
                parse_temporal(value)
                if value[:10] not in self.evidence.get("application_window", ""):
                    raise ValueError("application window requires matching date evidence")
        if len({d.id for d in self.required_documents}) != len(self.required_documents):
            raise ValueError("duplicate document IDs")
        for document in self.required_documents:
            if document.title.ko not in document.evidence:
                raise ValueError("required document Korean title must appear in source evidence")
            if not any(t.id == document.id and t.task_type == "document" and t.required_or_suggested == "required" for t in self.task_templates):
                raise ValueError("each required document needs a corresponding required task")
        validate_dependencies(self.task_templates)
        return self


def parse_temporal(value: str) -> date | datetime:
    if len(value) == 10:
        return date.fromisoformat(value)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 9 * 3600:
        raise ValueError("timestamps must include Korea +09:00 timezone; date-only stays date-only")
    return parsed


def validate_dependencies(templates: list[TaskTemplate]):
    by_id = {task.id: task for task in templates}
    if len(by_id) != len(templates):
        raise ValueError("duplicate task template IDs")
    visited, visiting = set(), set()

    def visit(key):
        if key not in by_id:
            raise ValueError("unknown task dependency")
        if key in visiting:
            raise ValueError("cyclic task dependencies")
        if key in visited:
            return
        visiting.add(key)
        for dep in by_id[key].depends_on:
            visit(dep)
        visiting.remove(key)
        visited.add(key)

    for key in by_id:
        visit(key)


TaskStatus = Literal["todo", "in_progress", "done", "needs_help", "requires_reconfirmation"]
SharingScope = Literal["none", "case_only", "tasks_and_cases"]


class TaskUpdate(StrictModel):
    status: TaskStatus


class SharingUpdate(StrictModel):
    sharing_scope: SharingScope


class CaseCreate(StrictModel):
    notice_id: str
    message: str = Field(min_length=1, max_length=2000)
    sharing_scope: SharingScope


class CaseUpdate(StrictModel):
    status: Literal["open", "in_progress", "resolved"]
    response: str = Field(max_length=2000)


class ImportRequest(StrictModel):
    source_text: str = Field(min_length=1, max_length=100000)
    source_url: str = Field(default="https://demo.invalid/source", max_length=1000)
    mode: Literal["demo", "real"] = "demo"
    notice_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,64}$")
