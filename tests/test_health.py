from fastapi.testclient import (
    TestClient,
)  # Import the synchronous FastAPI testing client

from app.main import app  # Import the fully configured FastAPI application


client = TestClient(app)  # Create an in-memory HTTP client bound to the application


def test_health_check_returns_http_200() -> (
    None
):  # Verify that the health endpoint is available
    response = client.get("/health")  # Send an in-memory HTTP GET request

    assert response.status_code == 200  # Confirm that the endpoint returns HTTP success


def test_health_check_returns_expected_payload() -> (
    None
):  # Verify the complete API response contract
    response = client.get("/health")  # Request the health endpoint

    assert (
        response.json()
        == {  # Compare the JSON body with the expected public contract
            "status": "ok",
            "application": "Swiss AI Job Hunter V1",
            "version": "0.1.0",
            "environment": "development",
        }
    )


def test_openapi_documentation_contains_health_endpoint() -> (
    None
):  # Verify endpoint registration in OpenAPI
    response = client.get(
        "/openapi.json"
    )  # Request the generated OpenAPI specification
    openapi_schema = (
        response.json()
    )  # Convert the JSON response into a Python dictionary

    assert (
        response.status_code == 200
    )  # Confirm that OpenAPI documentation is available
    assert (
        "/health" in openapi_schema["paths"]
    )  # Confirm that the health route is documented
