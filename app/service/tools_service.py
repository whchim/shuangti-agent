"""特色工具服务"""
import json
from uuid import uuid4
from loguru import logger
from app.core.database import get_db
from app.llm.base import BaseLLM

# ===== 霍兰德职业兴趣测试 (24 题精简版) =====
HOLLAND_QUESTIONS = [
    {"id": 1, "question": "我喜欢修理或组装物品", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "R"},
    {"id": 2, "question": "我喜欢动手制作东西", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "R"},
    {"id": 3, "question": "我喜欢户外活动或体力劳动", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "R"},
    {"id": 4, "question": "我喜欢操作机器或工具", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "R"},
    {"id": 5, "question": "我喜欢解决数学或逻辑难题", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "I"},
    {"id": 6, "question": "我喜欢阅读科学类文章", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "I"},
    {"id": 7, "question": "我喜欢分析和研究问题", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "I"},
    {"id": 8, "question": "我对抽象概念和理论感兴趣", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "I"},
    {"id": 9, "question": "我喜欢绘画、音乐或写作", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "A"},
    {"id": 10, "question": "我享受发挥创意和想象力", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "A"},
    {"id": 11, "question": "我喜欢参观博物馆或艺术展", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "A"},
    {"id": 12, "question": "我重视自我表达和美感", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "A"},
    {"id": 13, "question": "我喜欢帮助他人解决问题", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "S"},
    {"id": 14, "question": "我乐于教导或培训别人", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "S"},
    {"id": 15, "question": "我享受团队合作", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "S"},
    {"id": 16, "question": "我关心他人的感受和需求", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "S"},
    {"id": 17, "question": "我喜欢领导和组织活动", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "E"},
    {"id": 18, "question": "我享受说服和影响他人", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "E"},
    {"id": 19, "question": "我对商业和管理感兴趣", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "E"},
    {"id": 20, "question": "我敢于冒险并追求目标", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "E"},
    {"id": 21, "question": "我喜欢按规则和流程办事", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "C"},
    {"id": 22, "question": "我注重细节和准确性", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "C"},
    {"id": 23, "question": "我善于整理和归档信息", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "C"},
    {"id": 24, "question": "我喜欢有明确规则的工作", "options": ["非常不同意", "不同意", "中立", "同意", "非常同意"], "type": "C"},
]

HOLLAND_TYPES = {
    "R": {"name": "现实型 (Realistic)", "description": "喜欢动手操作、具体明确的任务", "careers": ["工程师", "机械师", "建筑师", "电工"]},
    "I": {"name": "研究型 (Investigative)", "description": "喜欢分析、研究和解决复杂问题", "careers": ["科学家", "数据分析师", "研究员", "程序员"]},
    "A": {"name": "艺术型 (Artistic)", "description": "喜欢创造、表达和自我展现", "careers": ["设计师", "作家", "音乐家", "摄影师"]},
    "S": {"name": "社会型 (Social)", "description": "喜欢帮助、教导和服务他人", "careers": ["教师", "心理咨询师", "社工", "护士"]},
    "E": {"name": "企业型 (Enterprising)", "description": "喜欢领导、说服和管理", "careers": ["管理者", "销售经理", "创业者", "律师"]},
    "C": {"name": "常规型 (Conventional)", "description": "喜欢有序、规范和系统化工作", "careers": ["会计", "行政人员", "数据录入员", "档案管理员"]},
}


def calculate_holland_scores(answers: list[int]) -> str:
    """计算霍兰德测试得分，返回最高分类型"""
    scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}

    for i, answer in enumerate(answers):
        if i < len(HOLLAND_QUESTIONS):
            qtype = HOLLAND_QUESTIONS[i]["type"]
            scores[qtype] += answer  # 0-4 分

    best_type = max(scores, key=scores.get)
    return best_type


async def process_career_assessment(answers: list[int]) -> dict:
    best_type = calculate_holland_scores(answers)
    type_info = HOLLAND_TYPES[best_type]
    return {
        "type_code": best_type,
        "type_name": type_info["name"],
        "description": type_info["description"],
        "recommended_careers": type_info["careers"],
    }


async def process_resume_optimize(content: str, llm: BaseLLM) -> dict:
    prompt = [
        {"role": "system", "content": "你是一位专业的简历优化顾问，擅长帮助求职者改进简历。"},
        {"role": "user", "content": f"""请优化以下简历，从结构、措辞、排版三个方面给出建议（共6-8条），每条附上改进示例：

{content}"""},
    ]

    try:
        response = await llm.chat(prompt)
        # 简化解析
        lines = response.content.split("\n")
        suggestions = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("*") or line.startswith("1")):
                suggestions.append({"category": "优化建议", "suggestion": line, "example": ""})
        return {"suggestions": suggestions or [{"category": "整体评价", "suggestion": response.content[:200], "example": ""}]}
    except Exception as e:
        logger.error(f"简历优化失败: {e}")
        return {"suggestions": []}


async def process_job_match(target_job: str, skills: list[str], llm: BaseLLM) -> dict:
    prompt = [
        {"role": "system", "content": "你是一位职业规划顾问。"},
        {"role": "user", "content": f"""目标岗位：{target_job}
用户技能：{', '.join(skills)}

请分析匹配度，给出：匹配度百分比、匹配技能、缺失技能、学习建议。"""},
    ]
    try:
        response = await llm.chat(prompt)
        return {
            "match_percentage": 50.0,
            "matched_skills": skills[:3],
            "missing_skills": ["根据 LLM 分析结果"],
            "learning_suggestions": [response.content[:200]],
        }
    except Exception as e:
        logger.error(f"岗位匹配失败: {e}")
        return {"match_percentage": 0, "matched_skills": [], "missing_skills": [], "learning_suggestions": []}


async def start_interview(job_title: str, user_id: str) -> dict:
    session_id = uuid4().hex
    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (id, user_id, title, session_type) VALUES (?, ?, ?, 'interview')",
        (session_id, user_id, f"面试模拟-{job_title}"),
    )
    await db.commit()
    return {
        "session_id": session_id,
        "question": f"你好！欢迎参加{job_title}岗位的面试。请先做一个简单的自我介绍。",
        "question_number": 1,
        "total_questions": 5,
    }


async def process_interview_answer(session_id: str, answer: str,
                                   question_number: int, job_title: str,
                                   user_id: str, llm: BaseLLM) -> dict:
    # 保存面试消息
    db = await get_db()
    await db.execute(
        "INSERT INTO messages (id, session_id, user_id, role, content) VALUES (?, ?, ?, 'user', ?)",
        (uuid4().hex, session_id, user_id, answer),
    )

    total = 5
    if question_number >= total:
        feedback = "这是最后一个问题了。请用 POST /interview-simulator/report 生成面试评估报告。"
        return {"feedback": feedback, "next_question": None, "question_number": question_number, "total_questions": total}

    # 生成反馈和下一题
    prompt = [
        {"role": "system", "content": f"你是{job_title}岗位的面试官，正在进行第{question_number}/{total}轮面试。"},
        {"role": "user", "content": f"候选人的回答：{answer}\n\n请给出简短反馈（1-2句），然后提出第{question_number+1}个面试问题。"},
    ]

    try:
        response = await llm.chat(prompt)
        content = response.content
        parts = content.split("\n", 1)
        feedback = parts[0].strip()
        next_q = parts[1].strip() if len(parts) > 1 else "请继续下一个问题。"
    except Exception:
        feedback = "好的，感谢你的回答。"
        next_q = f"请描述一个你在实际项目中遇到的挑战以及你是如何解决的？"

    return {"feedback": feedback, "next_question": next_q, "question_number": question_number + 1, "total_questions": total}


async def generate_interview_report(session_id: str, job_title: str, llm: BaseLLM) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT content FROM messages WHERE session_id = ? AND role = 'user'", (session_id,)
    )
    answers = [dict(row)["content"] for row in await cursor.fetchall()]

    prompt = [
        {"role": "system", "content": "你是一位资深面试官，请根据候选人的回答生成面试评估报告。"},
        {"role": "user", "content": f"岗位：{job_title}\n回答记录：\n" + "\n---\n".join(answers) + "\n\n请给出：优点、待改进点、总体评价。"},
    ]
    try:
        response = await llm.chat(prompt)
        return {
            "session_id": session_id,
            "job_title": job_title,
            "strengths": ["根据 LLM 评估"],
            "improvements": ["根据 LLM 评估"],
            "overall_feedback": response.content,
        }
    except Exception as e:
        logger.error(f"生成面试报告失败: {e}")
        return {"session_id": session_id, "job_title": job_title, "strengths": [], "improvements": [], "overall_feedback": "评估生成失败"}
