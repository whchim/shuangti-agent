"""认证相关 UI 组件：登录/注册页面、用户菜单、管理对话框"""
import streamlit as st
from api_client import (
    api_login, api_register,
    api_change_password, api_delete_account, api_update_username,
)


# ==================== 全局 CSS ====================

def inject_auth_css():
    st.markdown("""
    <style>
    /* 登录卡片 */
    .auth-card {
        background: linear-gradient(135deg, #667eea0d 0%, #764ba20d 100%);
        border: 1px solid #e8e8e8;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        backdrop-filter: blur(10px);
    }
    .auth-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0;
    }
    .auth-subtitle {
        text-align: center;
        color: #999;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    /* 用户菜单 */
    .user-menu-btn {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .user-menu-btn:hover {
        background: #f0f0f0 !important;
        border-radius: 8px !important;
    }
    /* 对话框内表单 */
    div[data-testid="stDialog"] div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ==================== 登录/注册页面 ====================

def check_auth() -> bool:
    return "token" in st.session_state and st.session_state.token


def require_auth():
    if not check_auth():
        inject_auth_css()
        show_login_page()
        st.stop()


def show_login_page():
    """渲染登录/注册页面。

    使用 session_state.auth_tab 控制当前显示的标签页 (0=登录, 1=注册)，
    替代 st.tabs() 以支持注册成功后编程切换到登录栏。

    注册成功后的流程:
      1. 将账号密码存入 session_state (prefill_username / prefill_password)
      2. 切换 auth_tab 到登录栏
      3. 登录表单自动填充注册时的账号密码
      4. 等待用户手动点击「登录」按钮，不自动提交
    """
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<p class="auth-header">🤖 双体智能体系统</p>', unsafe_allow_html=True)
        st.markdown('<p class="auth-subtitle">双体软件精英产业学院 · 智能对话平台</p>', unsafe_allow_html=True)

        # ── 标签页状态管理 ──
        if "auth_tab" not in st.session_state:
            st.session_state.auth_tab = 0  # 0=登录, 1=注册

        # 注册成功后用于自动填充登录栏的账号密码
        prefill_user = st.session_state.get("prefill_username", "")
        prefill_pw = st.session_state.get("prefill_password", "")

        # ── 自定义标签栏 (按钮模拟 tab，支持编程切换) ──
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("🔑 登录", key="tab_btn_login", use_container_width=True,
                         type="primary" if st.session_state.auth_tab == 0 else "secondary"):
                st.session_state.auth_tab = 0
                st.rerun()
        with col_t2:
            if st.button("📝 注册", key="tab_btn_register", use_container_width=True,
                         type="primary" if st.session_state.auth_tab == 1 else "secondary"):
                st.session_state.auth_tab = 1
                st.rerun()

        st.markdown("---")

        # ── 登录栏 ──
        if st.session_state.auth_tab == 0:
            # 注册成功后显示提示，引导用户点击登录
            if st.session_state.get("just_registered"):
                st.success("✅ 注册成功！已为您填充账号信息，请点击「登录」按钮完成登录。")
                st.session_state.pop("just_registered", None)

            with st.form("login_form"):
                username = st.text_input(
                    "用户名",
                    value=prefill_user,
                    placeholder="请输入用户名（1-10位，含英文、数字）",
                )
                password = st.text_input(
                    "密码",
                    type="password",
                    value=prefill_pw,
                    placeholder="请输入密码（6-12位，含英文、数字）",
                )
                submitted = st.form_submit_button("登 录", type="primary", use_container_width=True)
                if submitted:
                    if not username or not password:
                        st.error("请输入用户名和密码")
                    else:
                        try:
                            result = api_login(username, password)
                            st.session_state.token = result["token"]
                            st.session_state.user = result["user"]
                            # 清除预填充数据
                            st.session_state.pop("prefill_username", None)
                            st.session_state.pop("prefill_password", None)
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        # ── 注册栏 ──
        else:
            with st.form("register_form"):
                st.caption("创建新账户，注册后跳转至登录")
                username = st.text_input("用户名", placeholder="1-10位，含英文、数字", key="reg_username")
                password = st.text_input("密码", type="password", placeholder="6-12位，含英文、数字", key="reg_password")
                password2 = st.text_input("确认密码", type="password", placeholder="请再次确认密码", key="reg_password2")
                submitted = st.form_submit_button("注 册", type="primary", use_container_width=True)
                if submitted:
                    if not all([username, password, password2]):
                        st.error("请填写所有字段")
                    elif password != password2:
                        st.error("两次密码不一致")
                    elif len(password) < 6 or len(password) > 12:
                        st.error("密码需6-12位")
                    elif len(username) < 1 or len(username) > 10:
                        st.error("用户名需1-10位")
                    else:
                        try:
                            api_register(username, password, "")
                            # 注册成功：存储账号密码用于自动填充登录栏
                            st.session_state.prefill_username = username
                            st.session_state.prefill_password = password
                            st.session_state.just_registered = True
                            st.session_state.auth_tab = 0  # 切换到登录栏
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        st.markdown('</div>', unsafe_allow_html=True)


# ==================== 侧边栏用户信息 ====================

def show_sidebar_header():
    """侧边栏底部：Kimi 风格紧凑用户区域"""
    user = st.session_state.get("user", {})
    username = user.get("username", "用户")

    # 紧凑用户行 + 齿轮按钮
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.popover("👤", use_container_width=True):
            st.markdown(f"**{username}**")
            st.caption(f"ID: {user.get('id', '')[:12]}...")
            st.divider()
            if st.button("✏️ 修改用户名", use_container_width=True):
                show_change_username_dialog()
            if st.button("🔒 修改密码", use_container_width=True):
                show_change_password_dialog()
            st.divider()
            if st.button("🔄 切换账号", use_container_width=True):
                st.session_state.clear()
                st.rerun()
            if st.button("🗑 注销账号", use_container_width=True):
                show_delete_account_dialog()
            if st.button("🚪 退出登录", use_container_width=True):
                st.session_state.clear()
                st.rerun()
    with c2:
        with st.popover("⚙️"):
            api_base = st.text_input("API 地址", value=st.session_state.get("api_base", "http://localhost:8000"))
            if api_base != st.session_state.get("api_base"):
                st.session_state.api_base = api_base


# ==================== 用户管理对话框 ====================

@st.dialog("修改密码")
def show_change_password_dialog():
    st.markdown("请输入当前密码和新密码")
    with st.form("change_password_form"):
        old_pw = st.text_input("旧密码", type="password", placeholder="请输入当前密码")
        new_pw = st.text_input("新密码", type="password", placeholder="6-12位，含英文、数字")
        confirm_pw = st.text_input("确认密码", type="password", placeholder="请再次确认新密码")
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("确认修改", type="primary", use_container_width=True):
                if not all([old_pw, new_pw, confirm_pw]):
                    st.error("请填写所有字段")
                elif new_pw != confirm_pw:
                    st.error("两次密码不一致")
                elif len(new_pw) < 6:
                    st.error("新密码至少6位")
                else:
                    try:
                        api_change_password(old_pw, new_pw)
                        st.success("密码修改成功")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        with col2:
            if st.form_submit_button("取消", use_container_width=True):
                st.rerun()


@st.dialog("注销账号")
def show_delete_account_dialog():
    st.warning("⚠️ 此操作不可恢复！将删除您的账号及所有关联数据。")
    with st.form("delete_account_form"):
        password = st.text_input("请输入密码确认", type="password", placeholder="输入当前密码")
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("确认注销", type="primary", use_container_width=True):
                if not password:
                    st.error("请输入密码")
                else:
                    try:
                        api_delete_account(password)
                        st.session_state.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        with col2:
            if st.form_submit_button("取消", use_container_width=True):
                st.rerun()


@st.dialog("修改用户名")
def show_change_username_dialog():
    st.markdown("输入新的用户名（1-10位，含英文、数字）")
    with st.form("change_username_form"):
        new_name = st.text_input("新用户名", placeholder="请输入新用户名")
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("确认修改", type="primary", use_container_width=True):
                if not new_name.strip():
                    st.error("请输入新用户名")
                elif len(new_name) > 10:
                    st.error("用户名不超过10位")
                else:
                    try:
                        result = api_update_username(new_name.strip())
                        st.session_state.user = {
                            **st.session_state.user,
                            "username": result.get("username", new_name),
                        }
                        st.success("用户名修改成功")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        with col2:
            if st.form_submit_button("取消", use_container_width=True):
                st.rerun()
