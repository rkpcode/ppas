from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions.base import PharmacyBaseException

def pharmacy_exception_handler(request: Request, exc: PharmacyBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
