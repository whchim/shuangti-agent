from typing import Optional
from pydantic import BaseModel


# === 职业测评 ===
class CareerQuestion(BaseModel):
    id: int
    question: str
    options: list[str]


class CareerAssessmentRequest(BaseModel):
    answers: list[int]  # 每个题目的选项索引


class CareerAssessmentResponse(BaseModel):
    type_code: str      # R/I/A/S/E/C
    type_name: str      # 现实型/研究型...
    description: str
    recommended_careers: list[str]


# === 简历优化 ===
class ResumeOptimizeRequest(BaseModel):
    content: str  # 简历文本


class ResumeSuggestion(BaseModel):
    category: str      # 结构/措辞/排版
    suggestion: str
    example: str


class ResumeOptimizeResponse(BaseModel):
    suggestions: list[ResumeSuggestion]


# === 岗位匹配 ===
class JobMatchRequest(BaseModel):
    target_job: str
    skills: list[str]


class JobMatchResponse(BaseModel):
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    learning_suggestions: list[str]


# === 面试模拟 ===
class InterviewStartRequest(BaseModel):
    job_title: str


class InterviewStartResponse(BaseModel):
    session_id: str
    question: str
    question_number: int
    total_questions: int


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


class InterviewAnswerResponse(BaseModel):
    feedback: str
    next_question: Optional[str] = None  # None 表示所有问题已完成
    question_number: int
    total_questions: int


class InterviewReportRequest(BaseModel):
    session_id: str


class InterviewReportResponse(BaseModel):
    session_id: str
    job_title: str
    strengths: list[str]
    improvements: list[str]
    overall_feedback: str
