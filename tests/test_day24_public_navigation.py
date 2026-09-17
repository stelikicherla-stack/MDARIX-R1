from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = (ROOT / "frontend" / "src" / "PublicMegaSite.tsx").read_text(encoding="utf-8")
MAIN = (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")


def test_public_navigation_exposes_required_categories_and_actions():
    for label in (
        "Platform & AI",
        "Product Lifecycle",
        "Post-Market Intelligence",
        "Trust & Governance",
        "Resources",
        "Plans",
        "Sign in",
        "Get started",
    ):
        assert label in SITE


def test_r1_and_future_capabilities_are_explicitly_distinguished():
    assert 'status: "R1" | "Future"' in SITE
    assert "Available in R1" in SITE
    assert "Broader lifecycle intelligence" in SITE
    assert "without promised release dates" in SITE


def test_public_story_preserves_system_of_record_and_human_authority_boundaries():
    assert "System of Intelligence, not System of Record" in SITE
    assert "authorized humans retain decision authority" in SITE
    assert "AI does not create the final regulated decision" in SITE


def test_private_application_routes_require_authenticated_session():
    assert 'fetch("/api/v1/auth/session")' in MAIN
    assert 'window.location.replace(`/signin?returnTo=' in MAIN
    assert "Customer application routes require an authenticated session" in MAIN


def test_mega_menu_supports_escape_and_responsive_navigation():
    assert 'event.key === "Escape"' in SITE
    assert 'aria-expanded={openMenu === name}' in SITE
    assert 'aria-controls="public-navigation"' in SITE


def test_authenticated_home_tells_and_connects_the_r1_workflow_story():
    for phrase in (
        "Your R1 investigation story",
        "Understand product reality",
        "Follow the evidence",
        "Review trusted evidence",
        "Keep humans accountable",
        "Authorized human reviewers",
    ):
        assert phrase in MAIN
    assert 'onNavigate("investigations")' in MAIN
    assert 'onNavigate("products")' in MAIN
