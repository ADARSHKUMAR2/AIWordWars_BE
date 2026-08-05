"""
Shared exception handlers for all microservices
"""
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import traceback


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle 422 validation errors with detailed information
    """
    print(f"❌ Validation Error on {request.method} {request.url}")
    print(f"   Details: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": exc.errors(),
            "path": str(request.url)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle explicitly raised HTTP exceptions (like 400, 404, 500)
    """
    print(f"❌ HTTP Exception on {request.method} {request.url}")
    print(f"   Status: {exc.status_code}")
    print(f"   Detail: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Exception",
            "detail": exc.detail,
            "type": "HTTPException"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled Python exceptions
    """
    print(f"❌ Unhandled Exception on {request.method} {request.url}")
    print(f"   Type: {type(exc).__name__}")
    print(f"   Message: {str(exc)}")
    print(f"   Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


def register_exception_handlers(app: FastAPI, service_name: str = "Service"):
    """
    Register all exception handlers to a FastAPI app
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service (for logging)
    """
    
    @app.exception_handler(RequestValidationError)
    async def wrapped_validation_handler(request: Request, exc: RequestValidationError):
        print(f"[{service_name}] ", end="")
        return await validation_exception_handler(request, exc)
    
    @app.exception_handler(HTTPException)
    async def wrapped_http_handler(request: Request, exc: HTTPException):
        print(f"[{service_name}] ", end="")
        return await http_exception_handler(request, exc)
    
    @app.exception_handler(Exception)
    async def wrapped_general_handler(request: Request, exc: Exception):
        print(f"[{service_name}] ", end="")
        return await general_exception_handler(request, exc)
    
    print(f"✅ Exception handlers registered for {service_name}")
