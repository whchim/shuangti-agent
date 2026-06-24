"""API 客户端封装"""
import streamlit as st
import requests
from typing import Optional


def get_api_base() -> str:
    return st.session_state.get("api_base", "http://localhost:8000")


def get_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def handle_response(resp: requests.Response):
    if resp.status_code == 401:
        st.session_state.clear()
        st.rerun()
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text or f"HTTP {resp.status_code}"
        raise Exception(detail)
    return resp.json()


# ===================== Auth =====================

def api_register(username: str, password: str, email: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/auth/register", json={
        "username": username, "password": password, "email": email,
    })
    return handle_response(resp)


def api_login(username: str, password: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/auth/login", json={
        "username": username, "password": password,
    })
    return handle_response(resp)


def api_get_profile() -> dict:
    resp = requests.get(f"{get_api_base()}/api/user/profile", headers=get_headers())
    return handle_response(resp)


def api_update_profile(data: dict) -> dict:
    resp = requests.put(f"{get_api_base()}/api/user/profile", json=data, headers=get_headers())
    return handle_response(resp)


# ===================== Chat =====================

def api_send_message(session_id: Optional[str], message: str, model: str,
                     search_mode: str, knowledge_base_ids: list[str] = None) -> dict:
    payload = {
        "message": message,
        "model": model,
        "search_mode": search_mode,
        "knowledge_base_ids": knowledge_base_ids or [],
    }
    if session_id:
        payload["session_id"] = session_id

    resp = requests.post(f"{get_api_base()}/api/chat/send", json=payload, headers=get_headers())
    return handle_response(resp)


def api_send_message_stream(session_id: Optional[str], message: str, model: str,
                            search_mode: str, knowledge_base_ids: list[str] = None):
    """SSE 流式请求，返回 (event_type, data) 生成器"""
    import json as _json
    payload = {
        "message": message,
        "model": model,
        "search_mode": search_mode,
        "knowledge_base_ids": knowledge_base_ids or [],
    }
    if session_id:
        payload["session_id"] = session_id

    resp = requests.post(
        f"{get_api_base()}/api/chat/send/stream",
        json=payload, headers=get_headers(), stream=True,
    )
    if resp.status_code != 200:
        handle_response(resp)

    for line in resp.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            raw = line[5:].strip()
            if raw:
                try:
                    event = _json.loads(raw)
                    yield event  # {"type": "chunk"|"session"|"done"|"error", ...}
                except _json.JSONDecodeError:
                    yield {"type": "chunk", "content": raw}


def api_list_sessions() -> list:
    resp = requests.get(f"{get_api_base()}/api/chat/sessions", headers=get_headers())
    return handle_response(resp)


def api_create_session() -> dict:
    resp = requests.post(f"{get_api_base()}/api/chat/sessions", headers=get_headers())
    return handle_response(resp)


def api_get_session_messages(session_id: str, page: int = 1, page_size: int = 100) -> dict:
    resp = requests.get(
        f"{get_api_base()}/api/chat/sessions/{session_id}",
        params={"page": page, "page_size": page_size},
        headers=get_headers(),
    )
    return handle_response(resp)


def api_delete_session(session_id: str) -> dict:
    resp = requests.delete(f"{get_api_base()}/api/chat/sessions/{session_id}", headers=get_headers())
    return handle_response(resp)


# ===================== Knowledge =====================

def api_upload_document(file_bytes: bytes, filename: str, category: str = "未分类") -> dict:
    files = {"file": (filename, file_bytes)}
    data = {"category": category}
    # 文件上传不传 Content-Type，让 requests 自动设置 multipart boundary
    headers = {k: v for k, v in get_headers().items() if k != "Content-Type"}
    resp = requests.post(
        f"{get_api_base()}/api/knowledge/upload",
        files=files, data=data, headers=headers,
    )
    return handle_response(resp)


def api_list_documents() -> dict:
    resp = requests.get(f"{get_api_base()}/api/knowledge/documents", headers=get_headers())
    return handle_response(resp)


def api_delete_document(doc_id: str) -> dict:
    resp = requests.delete(f"{get_api_base()}/api/knowledge/documents/{doc_id}", headers=get_headers())
    return handle_response(resp)


def api_reload_documents() -> dict:
    resp = requests.post(f"{get_api_base()}/api/knowledge/reload", headers=get_headers())
    return handle_response(resp)


# ===================== Search =====================

def api_search_query(query: str, engine: str = None) -> dict:
    payload = {"query": query}
    if engine:
        payload["engine"] = engine
    resp = requests.post(f"{get_api_base()}/api/search/query", json=payload, headers=get_headers())
    return handle_response(resp)


def api_get_search_config() -> dict:
    resp = requests.get(f"{get_api_base()}/api/search/config", headers=get_headers())
    return handle_response(resp)


def api_update_search_config(data: dict) -> dict:
    resp = requests.put(f"{get_api_base()}/api/search/config", json=data, headers=get_headers())
    return handle_response(resp)


# ===================== Model =====================

def api_get_model_config() -> dict:
    resp = requests.get(f"{get_api_base()}/api/model/config", headers=get_headers())
    return handle_response(resp)


def api_update_model_config(data: dict) -> dict:
    resp = requests.put(f"{get_api_base()}/api/model/config", json=data, headers=get_headers())
    return handle_response(resp)


# ===================== Tools =====================

def api_get_career_questions() -> dict:
    resp = requests.get(f"{get_api_base()}/api/tools/career-assessment/questions")
    return handle_response(resp)


def api_career_assessment(answers: list[int]) -> dict:
    resp = requests.post(f"{get_api_base()}/api/tools/career-assessment", json={
        "answers": answers,
    }, headers=get_headers())
    return handle_response(resp)


def api_resume_optimize(content: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/tools/resume-optimize", json={
        "content": content,
    }, headers=get_headers())
    return handle_response(resp)


def api_job_match(target_job: str, skills: list[str]) -> dict:
    resp = requests.post(f"{get_api_base()}/api/tools/job-match", json={
        "target_job": target_job, "skills": skills,
    }, headers=get_headers())
    return handle_response(resp)


def api_start_interview(job_title: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/tools/interview-simulator", json={
        "job_title": job_title,
    }, headers=get_headers())
    return handle_response(resp)


def api_answer_interview(session_id: str, answer: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/tools/interview-simulator/answer", json={
        "session_id": session_id, "answer": answer,
    }, headers=get_headers())
    return handle_response(resp)


def api_interview_report(session_id: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/tools/interview-simulator/report", json={
        "session_id": session_id,
    }, headers=get_headers())
    return handle_response(resp)


# ===================== User Management =====================

def api_change_password(old_password: str, new_password: str) -> dict:
    resp = requests.post(f"{get_api_base()}/api/auth/change-password", json={
        "old_password": old_password, "new_password": new_password,
    }, headers=get_headers())
    return handle_response(resp)


def api_delete_account(password: str) -> dict:
    resp = requests.delete(f"{get_api_base()}/api/user/account", json={
        "password": password,
    }, headers=get_headers())
    return handle_response(resp)


def api_update_username(new_username: str) -> dict:
    resp = requests.put(f"{get_api_base()}/api/user/username", json={
        "new_username": new_username,
    }, headers=get_headers())
    return handle_response(resp)


# ===================== Health =====================

def api_health() -> dict:
    resp = requests.get(f"{get_api_base()}/health")
    return handle_response(resp)
