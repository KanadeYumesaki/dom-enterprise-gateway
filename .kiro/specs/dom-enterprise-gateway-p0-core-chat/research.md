# Research & Design Decisions: DOM Enterprise Gateway P0 Core Chat

---

## Summary
- **Feature**: `dom-enterprise-gateway-p0-core-chat`
- **Discovery Scope**: New Feature (Greenfield)
- **Key Findings**:
  - **Authentication**: OIDC (Authorization Code + PKCE) with a backend library like `authlib` is the most secure and standard approach for a FastAPI + SPA architecture.
  - **Streaming**: Server-Sent Events (SSE) provide a simpler and sufficient solution for streaming LLM responses compared to WebSockets, as the core requirement is unidirectional data flow.
  - **Data Access**: The async Repository Pattern is a best practice for FastAPI with SQLAlchemy, ensuring separation of concerns and testability.
  - **Vector Store**: `langchain-postgres` offers a native and efficient integration with `pgvector`, simplifying the RAG implementation within the existing PostgreSQL database.
  - **Frontend State**: For the PoC's scope, Angular Signals are more performant and less boilerplate-heavy than NgRx for component-level and simple shared state.

## Research Log

### 1. FastAPI OIDC Authentication Strategy
- **Context**: `REQ-AUTH-1` requires secure OAuth2.0/OIDC authentication for the SPA frontend and FastAPI backend.
- **Sources Consulted**:
  - [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
  - [Authlib Documentation](https://docs.authlib.org/en/latest/fastapi/)
  - Research result: "FastAPI OIDC authentication best practices"
- **Findings**:
  - The recommended flow for SPAs is the Authorization Code Flow with PKCE to prevent authorization code interception.
  - The backend should act as a BFF, handling token validation and keeping tokens from being exposed directly in the browser's local storage where possible.
  - A library like `authlib` handles the complexity of fetching the IdP's `.well-known/openid-configuration`, validating the JWT signature against the JWKS, and checking claims (`iss`, `aud`, `exp`).
- **Implications**: The design will include an `AuthService` that uses `authlib` for OIDC token validation. API endpoints will use a dependency injection to enforce authentication.

### 2. Real-time Streaming: SSE vs. WebSocket
- **Context**: `REQ-CHAT-2` requires streaming responses from the LLM. The choice between SSE and WebSockets impacts complexity and capability.
- **Sources Consulted**:
  - Research result: "FastAPI streaming response SSE vs WebSocket for LLM"
- **Findings**:
  - SSE is a unidirectional protocol (server-to-client) built on standard HTTP, making it easy to implement and compatible with most infrastructure. It has built-in browser support for reconnection.
  - WebSockets are bidirectional, suitable for interactive applications where the client needs to send real-time commands back to the server during a stream.
  - For streaming LLM tokens as a response, the primary flow is one-way. Client input (the next prompt) is a separate, discrete request.
- **Implications**: SSE is the appropriate choice for this PoC. The design will use FastAPI's `StreamingResponse` with a `text/event-stream` media type. This simplifies the architecture while fully meeting the requirement.

### 3. RAG Implementation with LangChain and pgvector
- **Context**: `REQ-RAG-1` and `REQ-RAG-3` require implementing RAG using LangChain v1 with a PostgreSQL-based vector store.
- **Sources Consulted**:
  - [LangChain `langchain-postgres` documentation](https://python.langchain.com/docs/integrations/vectorstores/pgvector)
  - Research result: "LangChain LCEL RAG with pgvector example"
- **Findings**:
  - `langchain-postgres` provides a `PGVector` vector store class that is fully compatible with the LCEL (`Runnable`) interface.
  - The `PGVector.from_documents()` method simplifies the process of embedding and storing documents.
  - The `as_retriever()` method makes it easy to integrate the vector store into an LCEL chain.
  - A common and efficient LCEL pattern for RAG is `RunnableParallel(context=retriever, question=RunnablePassthrough())`, which feeds the retrieved context and the original question into the prompt.
- **Implications**: The `RagService` will be designed around the `PGVector` class. The design will specify the RAG chain using the `RunnableParallel` pattern to ensure efficient data flow.

### 4. Backend Data Access Pattern
- **Context**: The backend needs a structured, scalable, and testable way to interact with the PostgreSQL database.
- **Sources Consulted**:
  - Research result: "FastAPI repository pattern sqlalchemy async"
- **Findings**:
  - The Repository Pattern effectively decouples data access logic from business logic (services).
  - When used with `asyncio` and SQLAlchemy's `AsyncSession`, it prevents blocking the event loop.
  - A common implementation involves creating a generic `BaseRepository` and specific implementations for each data model (e.g., `UserRepository`).
  - FastAPI's dependency injection system is used to provide an `AsyncSession` to the repositories for each request.
- **Implications**: The design will define a `repository` layer containing classes that encapsulate all SQLAlchemy query logic. Services will interact with repositories instead of directly with the DB session, improving modularity.

### 5. Frontend State Management in Angular
- **Context**: The Angular frontend needs an efficient way to manage state, particularly for the chat UI and user settings.
- **Sources Consulted**:
  - [Angular Signals Guide](https://angular.dev/guide/signals)
  - Research result: "Angular Signals vs NgRx performance 2025"
- **Findings**:
  - Angular Signals offer fine-grained reactivity and better performance for most UI-related state by avoiding large-scale change detection cycles (Zone.js).
  - NgRx provides powerful tools for complex, global state (e.g., time-travel debugging) but introduces significant boilerplate and can be overkill for simpler applications.
  - The modern consensus recommends a hybrid approach: Signals for local/component state and NgRx for complex global/domain state.
- **Implications**: For the P0 scope of this project, the state management needs are relatively simple (current chat messages, user settings, loading states). Therefore, the design will specify the use of **Angular Signals** as the primary state management tool to optimize for performance and development simplicity. NgRx will not be included in the P0 design.

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| **Layered Architecture with Repository Pattern** | A classic N-tier architecture separating API (FastAPI routers), Business Logic (Services), and Data Access (Repositories). | Clear separation of concerns, high testability, maintainable. | Can have slightly more boilerplate than a simpler model. | Aligns perfectly with FastAPI's dependency injection and SQLAlchemy's async capabilities. This is the selected pattern. |
| **Simple Service Layer** | Services interact directly with the SQLAlchemy session without a repository abstraction. | Less boilerplate for simple CRUD. | Tightly couples business logic to data access implementation, harder to test and maintain. | Rejected as it sacrifices long-term maintainability for minor short-term simplicity. |

## Design Decisions

### Decision: Adopt Server-Sent Events (SSE) for Real-Time Communication
- **Context**: The system must stream LLM-generated text to the client in real-time (`REQ-CHAT-2`).
- **Alternatives Considered**:
  1. **WebSockets**: Offers bidirectional communication but adds complexity in connection management.
  2. **SSE**: Unidirectional (server-to-client), simpler to implement, and leverages standard HTTP.
- **Selected Approach**: Use SSE. The FastAPI backend will expose an endpoint that returns a `StreamingResponse`.
- **Rationale**: The primary use case is one-way streaming of tokens from server to client. SSE is perfectly suited for this and avoids the unnecessary overhead of WebSocket's bidirectional protocol and connection handling.
- **Trade-offs**: Lacks a native channel for client-to-server commands during a stream, but this is not a P0 requirement.

### Decision: Use `langchain-postgres` for `pgvector` Integration
- **Context**: A vector store is required for RAG (`REQ-RAG-1`), and the chosen DB is PostgreSQL.
- **Alternatives Considered**:
  1. **Use a separate vector database** (e.g., Pinecone, Weaviate): Adds operational overhead (another service to manage).
  2. **Manually manage pgvector**: Requires writing raw SQL or custom functions for vector operations, losing the abstraction benefits of LangChain.
- **Selected Approach**: Use the `PGVector` class from the `langchain-postgres` integration.
- **Rationale**: It keeps the architecture simple by using the existing PostgreSQL database. It is officially supported by LangChain and fully compatible with LCEL, reducing development and maintenance effort.
- **Trade-offs**: Performance at extreme scale might be less than a dedicated vector database, but this is not a concern for the PoC.

## Risks & Mitigations
- **Risk 1: LLM Latency**: The "Time to First Token" from the LLM can be slow, impacting user experience.
  - **Mitigation**: Use streaming (SSE) so the user sees activity immediately. Implement clear "loading" or "thinking" indicators in the UI. For the P0, select a model optimized for speed (e.g., Gemini Flash).
- **Risk 2: Vendor Lock-in (LLM)**: Tightly coupling the logic to a specific LLM provider (e.g., Gemini) makes future changes difficult.
  - **Mitigation**: The design will include a `LlmClient` abstract base class (ABC). All interactions with LLMs will go through this interface, with provider-specific implementations (e.g., `GeminiClient`). This will allow for easier integration of other models in the future.
- **Risk 3: Inaccurate RAG results**: The retriever may pull irrelevant context, leading to incorrect or hallucinatory answers.
  - **Mitigation**: The prompt engineering will explicitly instruct the LLM to answer *only* based on the provided context. The design will also include the ability to easily tweak retrieval parameters (e.g., number of documents `k`, similarity score thresholds). The feedback mechanism (`REQ-UX-1`) will provide data for future tuning.

## References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Expression Language (LCEL)](https://python.langchain.com/docs/expression_language/)
- [Authlib for FastAPI](https://docs.authlib.org/en/latest/fastapi/)
- [Angular Signals](https://angular.dev/guide/signals)
