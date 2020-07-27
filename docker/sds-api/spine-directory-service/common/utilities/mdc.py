import contextvars

correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id', default='')
