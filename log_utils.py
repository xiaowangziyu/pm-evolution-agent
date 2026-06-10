"""
日志工具函数 - 提供脱敏和安全日志功能
"""

import logging

# 敏感字段列表
SENSITIVE_FIELDS = ['api_key', 'API_KEY', 'ZHIPU_API_KEY', 'password', 'secret']

def redact_sensitive(value, max_length=50):
    """
    脱敏处理敏感信息
    
    Args:
        value: 要脱敏的值
        max_length: 最大显示长度（超过则截断）
    
    Returns:
        脱敏后的值（保留原始类型）
    """
    if value is None:
        return "None"
    
    # 检查是否为敏感字段值
    value_str = str(value)
    for field in SENSITIVE_FIELDS:
        if field.lower() in value_str.lower() or "key" in value_str.lower():
            return "[REDACTED]"
    
    # 对于字符串类型，截断过长的内容
    if isinstance(value, str):
        if len(value) > max_length:
            return value[:max_length] + "..."
    
    # 保留原始类型（整数、浮点数等）
    return value

def safe_log(message, *args, level='info'):
    """
    安全日志函数 - 自动脱敏敏感信息
    
    Args:
        message: 日志消息模板（支持 %s 占位符）
        args: 要替换到模板中的参数（会被脱敏处理）
        level: 日志级别（info/warning/error/debug）
    """
    # 对所有参数进行脱敏
    safe_args = tuple(redact_sensitive(arg) for arg in args)
    
    # 根据级别记录日志
    logger = logging.getLogger(__name__)
    log_message = message % safe_args
    
    if level == 'debug':
        logger.debug(log_message)
    elif level == 'warning':
        logger.warning(log_message)
    elif level == 'error':
        logger.error(log_message)
    else:
        logger.info(log_message)

def format_user_data(data):
    """
    格式化用户数据用于日志输出（自动脱敏）
    
    Args:
        data: 用户数据字典
    
    Returns:
        脱敏后的字符串表示
    """
    if not isinstance(data, dict):
        return redact_sensitive(data)
    
    safe_data = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            safe_data[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 50:
            safe_data[key] = value[:50] + "..."
        else:
            safe_data[key] = value
    
    return str(safe_data)
