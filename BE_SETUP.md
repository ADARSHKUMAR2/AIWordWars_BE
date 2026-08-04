# FreshrAI Backend Setup

This document provides a comprehensive overview of the backend setup for the FreshrAI project. It is intended to help new developers get up to speed quickly and can be used as a reference for future projects with a similar architecture.

## Table of Contents

- [Overall Architecture](#overall-architecture)
- [Running the Backend](#running-the-backend)
- [API Gateway](#api-gateway)
- [Microservices](#microservices)
  - [Service Structure](#service-structure)
  - [Auth Service Example](#auth-service-example)
- [Shared Modules](#shared-modules)
- [Communication Flow](#communication-flow)

## Overall Architecture

The FreshrAI backend is built using a microservices architecture. This means that the backend is composed of several small, independent services that communicate with each other over the network. This approach has several advantages, including:

- **Scalability:** Each service can be scaled independently, allowing us to allocate resources where they are needed most.
- **Flexibility:** Each service can be developed and deployed independently, making it easier to add new features and fix bugs.
- **Resilience:** If one service fails, the rest of the system can continue to function.

The main components of the backend are:

- **API Gateway:** The single entry point for all incoming requests. It is responsible for authenticating requests, routing them to the appropriate microservice, and forwarding the response back to the client.
- **Microservices:** A collection of services that provide the core functionality of the application. The current services include:
  - `auth`: Handles user authentication and session management.
  - `resume`: Manages resume-related operations.
  - `billing`: (Assumed) Handles billing and payments.
  - `interview`: (Assumed) Handles interview-related features.
  - `roadmap`: (Assumed) Handles roadmap generation.
- **Shared Modules:** A collection of modules that provide common functionality used across multiple services, such as exception handling, Redis client, and session management.
- **Redis:** An in-memory data store that is used for caching and session management.

## Running the Backend

The backend can be run locally using `docker-compose` and a process manager like `uvicorn`.

1.  **Start Redis:** The `docker-compose.yml` file defines the Redis service. To start it, run the following command from the `backend` directory:

    ```bash
    docker-compose up -d
    ```

2.  **Run the Microservices:** Each microservice is a FastAPI application that can be started with `uvicorn`. To run the services, you will need to open a separate terminal for each one and run the following commands:

    ```bash
    # Terminal 1: API Gateway
    cd backend/gateway
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

    # Terminal 2: Auth Service
    cd backend/services/auth
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload

    # Terminal 3: Resume Service
    cd backend/services/resume
    uvicorn main:app --host 0.0.0.0 --port 8002 --reload

    # ... and so on for the other services
    ```

## API Gateway

The API Gateway is the single entry point for all incoming requests. It is a FastAPI application located in the `backend/gateway` directory. Its primary responsibilities are:

- **Authentication:** It can verify the authenticity of a request before forwarding it to a downstream service.
- **Routing:** It routes incoming requests to the appropriate microservice based on the request path.
- **Proxying:** It forwards the request to the target microservice and then forwards the response back to the client.

The routing and proxying logic is defined in `backend/gateway/main.py`. It uses the `register_proxy` and `register_proxy_with_header` functions from `backend/gateway/utils/proxy.py` to create reverse proxy routes.

- **`register_proxy`:** This function creates a simple reverse proxy that forwards requests to a target URL.
- **`register_proxy_with_header`:** This function is a specialized version of `register_proxy` that also injects an `X-User-Id` header into the request before forwarding it. This is used for services that require authentication.

## Microservices

Each microservice is a self-contained FastAPI application that is responsible for a specific set of features.

### Service Structure

A typical microservice has the following directory structure:

- `main.py`: The entry point for the service. It initializes the FastAPI application, sets up lifespan events (startup and shutdown), includes the API router, and starts the server.
- `config/`: Contains configuration files for the service, such as database connections (`db.py`), Firebase initialization (`firebase.py`), and LLM configuration (`llm.py`).
- `controllers/`: Contains the business logic for the service.
- `models/`: Contains the data models for the service.
- `routes/`: Defines the API endpoints for the service.
- `utils/`: Contains utility functions for the service.

### Auth Service Example

The `auth` service, located in `backend/services/auth`, is a good example of a typical microservice.

- **`main.py`:** Initializes the FastAPI app, connects to the database and Redis on startup, and includes the `auth_router`.
- **`routes/routes.py`:** Defines the `/api/login`, `/api/logout`, `/api/me`, and `/api/session/validate` endpoints.
- **`controllers/controller.py`:** Contains the logic for the `login_or_register`, `logout`, and `get_session_user` functions.
  - The `login_or_register` function is the core of the authentication process. It verifies a Firebase ID token, finds or creates a user in the database, creates a session in Redis, and sets a session cookie in the response.

## Shared Modules

The `backend/shared` directory contains modules that are used by multiple services. This helps to reduce code duplication and ensure consistency across the backend.

- **`redis_client.py`:** Provides functions for getting a Redis client and closing the connection.
- **`session_manager.py`:** Provides a `SessionManager` class for creating, retrieving, deleting, and updating sessions in Redis.
- **`exception_handlers.py`:** Provides a function for registering custom exception handlers.
- **`exceptions.py`:** Defines custom exception classes.

## Communication Flow

Here is a high-level overview of the communication flow for a typical request:

1.  The client sends a request to the API Gateway.
2.  The API Gateway receives the request.
3.  If the request requires authentication, the gateway will validate the session cookie.
4.  The gateway uses the request path to determine which microservice to forward the request to. For example, a request to `/auth/api/login` will be forwarded to the `auth` service.
5.  The gateway forwards the request to the target microservice. If the route was registered with `register_proxy_with_header`, it will also inject the `X-User-Id` header.
6.  The microservice receives the request, processes it, and sends a response back to the gateway.
7.  The gateway receives the response from the microservice and forwards it back to the client.
