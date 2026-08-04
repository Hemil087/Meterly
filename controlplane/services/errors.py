"""
Domain exceptions raised by the service layer.

Services do not know about HTTP — routers catch these and translate
them to status codes. Keeps every guard testable without FastAPI.
"""


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ValidationError(Exception):
    pass