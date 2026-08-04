import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

PROXY_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


def register_proxy(app: FastAPI, path_prefix: str, target_url: str):
    """
    Registers a simple reverse proxy route.
    e.g. /auth/api/login  →  http://localhost:8001/api/login
    """
    async_client = httpx.AsyncClient(base_url=target_url, timeout=PROXY_TIMEOUT)
    route_pattern = f"{path_prefix.rstrip('/')}/{{path:path}}"

    async def proxy_handler(request: Request, path: str):
        target_path = f"/{path}"
        try:
            req = async_client.build_request(
                method=request.method,
                url=target_path,
                headers=request.headers.raw,
                params=request.query_params,
                content=await request.body(),
            )
            response = await async_client.send(req, stream=True)
            return Response(
                content=await response.aread(),
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            return Response(content=f"Service unavailable: {str(e)}", status_code=503)

    app.api_route(
        route_pattern,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        include_in_schema=False,
    )(proxy_handler)

    if not hasattr(app.state, "proxy_clients"):
        app.state.proxy_clients = []
    app.state.proxy_clients.append(async_client)


def register_proxy_with_header(app: FastAPI, path_prefix: str, target_url: str):
    """
    Registers a reverse proxy that also injects the X-User-Id header.
    Used for protected routes that require authentication.
    """
    async_client = httpx.AsyncClient(base_url=target_url, timeout=PROXY_TIMEOUT)
    route_pattern = f"{path_prefix.rstrip('/')}/{{path:path}}"

    async def proxy_with_header_handler(request: Request, path: str):
        target_path = f"/{path}"
        try:
            body_bytes = await request.body()
            headers = {
                k: v for k, v in request.headers.items()
                if k.lower() not in ("host", "content-length")
            }
            # X-User-Id will be injected here once we add session middleware
            req = async_client.build_request(
                method=request.method,
                url=target_path,
                headers=headers,
                params=request.query_params,
                content=body_bytes,
            )
            response = await async_client.send(req, stream=True)
            return Response(
                content=await response.aread(),
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            return Response(content=f"Service unavailable: {str(e)}", status_code=503)

    app.api_route(
        route_pattern,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        include_in_schema=False,
    )(proxy_with_header_handler)

    if not hasattr(app.state, "proxy_clients"):
        app.state.proxy_clients = []
    app.state.proxy_clients.append(async_client)
