import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import json
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from application.models import audit_logs
from application.models.audit_logs import AuditLog

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def json_serializer(obj):
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if hasattr(obj, '__dict__'):
        return str(obj)
    return str(obj)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if hasattr(record, 'user_id'):
            log_data['user_id'] = str(record.user_id) if record.user_id else None
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_data['response_time'] = record.response_time

        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        try:
            return json.dumps(log_data, default=json_serializer)
        except Exception as e:
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "message": f"Failed to serialize log: {str(e)}",
                "original_message": str(record.getMessage())
            })


class StandardFormatter(logging.Formatter):
    def format(self, record):
        colors = {
            'DEBUG': '\033[36m',  # Cyan
            'INFO': '\033[32m',  # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',  # Red
            'CRITICAL': '\033[35m',  # Magenta
        }
        reset = '\033[0m'

        color = colors.get(record.levelname, '')
        formatted = super().format(record)

        if sys.stdout.isatty():
            return f'{color}{formatted}{reset}'
        return formatted


def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = StandardFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_path = LOGS_DIR / log_file
    else:
        file_path = LOGS_DIR / "jars.log"

    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def setup_audit_logger():
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)

    if audit_logger.handlers:
        return audit_logger

    audit_file = LOGS_DIR / "audit.log"
    audit_handler = RotatingFileHandler(
        audit_file,
        maxBytes=50 * 1024 * 1024,
        backupCount=10
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(JsonFormatter())
    audit_logger.addHandler(audit_handler)

    audit_logger.propagate = False

    return audit_logger


def setup_api_logger():
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.INFO)

    if api_logger.handlers:
        return api_logger

    api_file = LOGS_DIR / "api_requests.log"
    api_handler = RotatingFileHandler(
        api_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(JsonFormatter())
    api_logger.addHandler(api_handler)

    api_logger.propagate = False

    return api_logger


app_logger = setup_logger("jars_app")
audit_logger = setup_audit_logger()
api_logger = setup_api_logger()


async def log_user_action(
        db: AsyncSession,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        trader_profile_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        changes: Optional[dict] = None,
        extra_data: Optional[dict] = None
):
    extra = {
        'user_id': user_id,
        'action': action,
        'ip_address': ip_address or 'unknown'
    }
    message = f"User {user_id} performed action: {action} on {resource_type}"
    if resource_id:
        message += f" (ID: {resource_id})"
    if changes:
        message += f" | Changes: {json.dumps(changes)}"
    if extra_data:
        message += f" | Extra: {json.dumps(extra_data)}"

    audit_logger.info(message, extra=extra)

    try:
        new_audit_log_entry = AuditLog(
            user_id=user_id,
            trader_profile_id=trader_profile_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address or 'unknown',
            user_agent=user_agent,
            changes=json.dumps(changes) if changes else None,
            extra_data=json.dumps(extra_data) if extra_data else None
        )
        db.add(new_audit_log_entry)
        await db.commit()

    except Exception as e:
        app_logger.error(f"Failed to write to AuditLog database table: {e}", exc_info=True)
        await db.rollback()

def log_api_request(
        method: str,
        endpoint: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
):
    extra = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'response_time': response_time,
    }
    if user_id:
        extra['user_id'] = user_id
    if ip_address:
        extra['ip_address'] = ip_address

    message = f"{method} {endpoint} - {status_code} ({response_time:.2f}ms)"
    api_logger.info(message, extra=extra)


def log_security_event(event_type: str, details: dict, severity: str = "WARNING"):
    extra = {'action': f"SECURITY_{event_type}"}
    message = f"Security Event: {event_type} | {json.dumps(details)}"

    if severity == "CRITICAL":
        audit_logger.critical(message, extra=extra)
    elif severity == "ERROR":
        audit_logger.error(message, extra=extra)
    else:
        audit_logger.warning(message, extra=extra)
