"""特色工具 API"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.tools import (
    CareerQuestion, CareerAssessmentRequest, CareerAssessmentResponse,
    ResumeOptimizeRequest, ResumeOptimizeResponse,
    JobMatchRequest, JobMatchResponse,
    InterviewStartRequest, InterviewStartResponse,
    InterviewAnswerRequest, InterviewAnswerResponse,
    InterviewReportRequest, InterviewReportResponse,
)
from app.core.dependencies import get_current_user
from app.service.tools_service import (
    HOLLAND_QUESTIONS, process_career_assessment,
    process_resume_optimize, process_job_match,
    start_interview, process_interview_answer, generate_interview_report,
)

router = APIRouter(prefix="/api/tools", tags=["特色工具"])


def get_llm():
    from app.core.config import settings
    if settings.default_llm_model == "deepseek":
        from app.llm.deepseek import DeepSeekAdapter
        return DeepSeekAdapter()
    else:
        from app.llm.zhipu import ZhipuAdapter
        return ZhipuAdapter()


# ===== 职业测评 =====
@router.get("/career-assessment/questions")
async def get_questions():
    return {"questions": HOLLAND_QUESTIONS, "total": len(HOLLAND_QUESTIONS)}


@router.post("/career-assessment")
async def assess_career(req: CareerAssessmentRequest, user: dict = Depends(get_current_user)):
    if len(req.answers) != len(HOLLAND_QUESTIONS):
        raise HTTPException(status_code=400, detail=f"需要回答全部 {len(HOLLAND_QUESTIONS)} 题")
    result = await process_career_assessment(req.answers)
    return result


# ===== 简历优化 =====
@router.post("/resume-optimize")
async def optimize_resume(req: ResumeOptimizeRequest, user: dict = Depends(get_current_user)):
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="简历内容不能为空")
    result = await process_resume_optimize(req.content, get_llm())
    return result


# ===== 岗位匹配 =====
@router.post("/job-match")
async def match_job(req: JobMatchRequest, user: dict = Depends(get_current_user)):
    result = await process_job_match(req.target_job, req.skills, get_llm())
    return result


# ===== 面试模拟 =====
@router.post("/interview-simulator")
async def start_interview_session(req: InterviewStartRequest, user: dict = Depends(get_current_user)):
    result = await start_interview(req.job_title, user["user_id"])
    return result


@router.post("/interview-simulator/answer")
async def answer_interview(req: InterviewAnswerRequest, user: dict = Depends(get_current_user)):
    # 获取当前会话信息
    from app.core.database import get_db
    db = await get_db()
    cursor = await db.execute(
        "SELECT title, session_type FROM sessions WHERE id = ? AND user_id = ?",
        (req.session_id, user["user_id"]),
    )
    session = await cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")

    job_title = session["title"].replace("面试模拟-", "")
    cursor = await db.execute(
        "SELECT COUNT(*) as count FROM messages WHERE session_id = ? AND role = 'user'",
        (req.session_id,),
    )
    count = (await cursor.fetchone())["count"]

    result = await process_interview_answer(req.session_id, req.answer, count, job_title, user["user_id"], get_llm())
    return result


@router.post("/interview-simulator/report")
async def get_interview_report(req: InterviewReportRequest, user: dict = Depends(get_current_user)):
    from app.core.database import get_db
    db = await get_db()
    cursor = await db.execute(
        "SELECT title FROM sessions WHERE id = ? AND user_id = ?",
        (req.session_id, user["user_id"]),
    )
    session = await cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")

    job_title = session["title"].replace("面试模拟-", "")
    result = await generate_interview_report(req.session_id, job_title, get_llm())
    return result
