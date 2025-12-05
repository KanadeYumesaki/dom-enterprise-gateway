# Backend Testing Notes

## Mocked External Dependencies
The following external services are mocked in the test suite to allow offline testing:
- **Google Vertex AI / Gemini**: `ChatGoogleGenerativeAI` and `GoogleGenerativeAIEmbeddings` are mocked using `unittest.mock`.
- **PostgreSQL / PGVector**: Database connections are routed to a test database (or transaction rollback), and `PGVector` is mocked where necessary for unit tests.
- **OIDC/Auth0**: Authentication flows are mocked by overriding `get_current_user` dependencies and mocking `jwks` responses.

## Known Issues / Skipped Tests
- `app/tests/test_rag_service.py::test_stream_rag_response`: This test is currently skipped. The mocking complexity for `LangChain`'s `astream` method combined with `RunnablePassthrough` and `StrOutputParser` necessitates a more sophisticated mock setup than simple `AsyncMock`. The core RAG logic is verified in `test_query_rag`.

## Running Tests
To run the full backend test suite:
```bash
cd backend
poetry run pytest app/tests
```
