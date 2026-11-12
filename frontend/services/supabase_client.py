import os
import logging
from pathlib import Path
from typing import Any, Dict
import streamlit as st
from supabase import Client, create_client

logger = logging.getLogger('ats_resume_scorer')


try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / '.env')
except ImportError:
    pass


def _secret(key: str, section: str = 'supabase') -> str:
    """Read from env first, then fall back to st.secrets[section][key]."""
    val = os.getenv(key, '')
    if val:
        return val
    try:
        return st.secrets[section][key]
    except (KeyError, FileNotFoundError, AttributeError):
        return ''


SUPABASE_URL = _secret('SUPABASE_URL')
SUPABASE_ANON_KEY = _secret('SUPABASE_ANON_KEY')

OAUTH_REDIRECT_URL = (
    os.getenv('AUTH_REDIRECT_URL')
    or _secret('redirect_uri', 'google_oauth')
    or 'http://localhost:8501'
)


def _missing_config() -> str | None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return 'Supabase is not configured — set SUPABASE_URL and SUPABASE_ANON_KEY in .env or .streamlit/secrets.toml'
    return None


@st.cache_resource
def get_client() -> Client | None:
    """Cached singleton — preserves PKCE state across Streamlit reruns."""
    if _missing_config():
        return None
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _session_dict(session, user) -> Dict[str, Any]:
    return {
        'access_token':  session.access_token,
        'refresh_token': session.refresh_token,
        'user_id':       user.id,
        'email':         user.email,
    }


def sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_in_with_password(
            {'email': email, 'password': password}
        )
        if not resp.session or not resp.user:
            return {'error': 'Invalid credentials'}
        return _session_dict(resp.session, resp.user)
    except Exception as exc:
        logger.warning(f'sign_in_with_password failed: {exc}')
        return {'error': _humanize(exc)}


def sign_up_with_password(email: str, password: str) -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_up({
            'email': email,
            'password': password,
            'options': {'email_redirect_to': OAUTH_REDIRECT_URL},
        })
        if resp.session and resp.user:
            return _session_dict(resp.session, resp.user)
        if resp.user:
            return {'pending_confirmation': True, 'email': email}
        return {'error': 'Sign-up failed'}
    except Exception as exc:
        logger.warning(f'sign_up failed: {exc}')
        return {'error': _humanize(exc)}


def verify_signup_email_token(token_hash: str) -> Dict[str, Any]:
    """Verify a signup email using Supabase TokenHash."""
    err = _missing_config()
    if err:
        return {'error': err}

    try:
        # Use a separate client so verification does not disturb
        # the existing cached authentication client.
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

        resp = client.auth.verify_otp({
            'token_hash': token_hash,
            'type': 'email',
        })

        if not resp.user:
            return {'error': 'Email verification could not be completed.'}

        # Do not keep the verification-created session.
        try:
            client.auth.sign_out()
        except Exception:
            logger.warning('Could not clear temporary verification session')

        return {'success': True, 'email': resp.user.email}

    except Exception as exc:
        logger.warning(f'email verification failed: {exc}')
        return {'error': _humanize(exc)}


def send_password_reset_email(email: str) -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}

    try:
        get_client().auth.reset_password_for_email(
            email,
            options={
                'redirect_to': f'{OAUTH_REDIRECT_URL}?auth_flow=recovery',
            },
        )
        return {'success': True}

    except Exception as exc:
        logger.warning(f'password reset email failed: {exc}')
        return {'error': _humanize(exc)}

def update_user_password(new_password: str) -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}

    try:
        resp = get_client().auth.update_user({
            'password': new_password,
        })

        if not resp.user:
            return {'error': 'Password update failed.'}

        return {'success': True}

    except Exception as exc:
        logger.warning(f'password update failed: {exc}')
        return {'error': _humanize(exc)}
    
def google_oauth_url() -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {'redirect_to': OAUTH_REDIRECT_URL},
        })
        return {'url': resp.url}
    except Exception as exc:
        logger.warning(f'oauth url generation failed: {exc}')
        return {'error': _humanize(exc)}


def exchange_code_for_session(auth_code: str) -> Dict[str, Any]:
    """Exchange the Supabase PKCE code for an authenticated session."""
    err = _missing_config()
    if err:
        return {'error': err}

    client = get_client()

    try:
        resp = client.auth.exchange_code_for_session({
            'auth_code': auth_code,
            'redirect_to': OAUTH_REDIRECT_URL,
        })

        if not resp.session or not resp.user:
            return {'error': 'Authentication exchange returned no session'}

        return _session_dict(resp.session, resp.user)

    except Exception as exc:
        logger.warning(f'exchange_code_for_session failed: {exc}')
        return {'error': _humanize(exc)}


def sign_out() -> None:
    if _missing_config():
        return
    try:
        get_client().auth.sign_out()
    except Exception as exc:
        logger.warning(f'sign_out failed: {exc}')


def _humanize(exc: Exception) -> str:
    msg = str(exc)
    # supabase errors arrive as "<status>: {json blob}" — surface the human bit
    if 'invalid_grant' in msg.lower() or 'invalid login' in msg.lower():
        return 'Wrong email or password'
    if 'user already registered' in msg.lower() or 'already been registered' in msg.lower():
        return 'An account with this email already exists — try signing in'
    if 'email not confirmed' in msg.lower() or 'email_not_confirmed' in msg.lower():
        return 'Please confirm your email using the link sent to your inbox before signing in.'
    if 'password should be at least' in msg.lower():
        return 'Password too short (Supabase default is 6 characters)'
    return msg
