from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_frontend_serves_built_assets_with_spa_fallback(tmp_path: Path) -> None:
    frontend = tmp_path / "dist"
    assets = frontend / "assets"
    assets.mkdir(parents=True)
    (frontend / "index.html").write_text(
        '<main id="root">governance console</main>',
        encoding="utf-8",
    )
    (assets / "app.js").write_text("export {};", encoding="utf-8")
    client = TestClient(create_app(frontend_directory=frontend))

    index_response = client.get("/")
    fallback_response = client.get(
        "/review-console",
        headers={"Accept": "text/html"},
    )
    asset_response = client.get("/assets/app.js")

    assert index_response.status_code == 200
    assert "governance console" in index_response.text
    assert fallback_response.status_code == 200
    assert "governance console" in fallback_response.text
    assert asset_response.status_code == 200
    assert asset_response.text == "export {};"
