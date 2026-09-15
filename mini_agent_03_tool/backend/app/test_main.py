from app.main import app


def test_fastapi_app_metadata() -> None:
    """앱이 올바른 제목으로 생성되는지 확인한다."""
    assert app.title == "Mini Agent 03 · Tool Use"


def test_expected_routes_are_registered() -> None:
    """핵심 학습 API와 Lab 라우터가 등록되는지 확인한다."""
    # FastAPI 버전에 따라 포함한 APIRouter가 평탄화된 Route 또는
    # _IncludedRouter(original_router=...)로 보관될 수 있다.
    paths = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)

        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            paths.update(
                child.path
                for child in original_router.routes
                if isinstance(getattr(child, "path", None), str)
            )

    assert "/openapi.json" in paths
    assert "/docs" in paths
    assert "/api/generate" in paths
    assert "/api/structured/validate" in paths
    assert "/api/tools/run" in paths
    assert "/api/labs/run" in paths
