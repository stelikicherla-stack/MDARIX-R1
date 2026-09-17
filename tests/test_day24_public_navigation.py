from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = (ROOT / "frontend" / "src" / "PublicMegaSite.tsx").read_text(encoding="utf-8")
MAIN = (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")
STYLES = (ROOT / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")


def test_public_navigation_exposes_required_categories_and_actions():
    for label in (
        "Platform & AI",
        "Solutions",
        "Product Lifecycle",
        "Why MDARIX",
        "Resources",
        "Plans",
        "Sign in",
        "Get started",
    ):
        assert label in SITE


def test_current_and_future_capabilities_are_explicitly_distinguished():
    assert "future?: boolean" in SITE
    assert "Current capabilities" in SITE
    assert "Broader lifecycle intelligence" in SITE
    assert "does not represent available functionality" in SITE
    assert "Available in R1" not in SITE
    assert 'status: "R1"' not in SITE
    assert "R1" not in SITE


def test_public_story_preserves_system_of_record_and_human_authority_boundaries():
    assert "System of Intelligence, not System of Record" in SITE
    assert "Authorized humans make controlled decisions" in SITE
    assert "AI does not create the final regulated decision" in SITE


def test_private_application_routes_require_authenticated_session():
    assert 'fetch("/api/v1/auth/session")' in MAIN
    assert 'window.location.replace(`/signin?returnTo=' in MAIN
    assert "Customer application routes require an authenticated session" in MAIN


def test_mega_menu_supports_escape_and_responsive_navigation():
    assert 'event.key === "Escape"' in SITE
    assert 'aria-expanded={openMenu === name}' in SITE
    assert 'aria-controls="public-navigation"' in SITE


def test_authenticated_home_tells_and_connects_the_workflow_story():
    for phrase in (
        "Ask MDARIX",
        "What changed before complaints increased?",
        "Understand product reality",
        "Follow the evidence",
        "Review trusted evidence",
        "Keep humans accountable",
        "Requires my attention",
        "Active investigations",
        "Product signals",
        "Recent product activity",
        "Recent decisions & assurance",
    ):
        assert phrase in MAIN
    assert 'onNavigate("investigations")' in MAIN
    assert 'onNavigate("products")' in MAIN


def test_semantic_design_tokens_cover_business_meaning():
    for token in ("--brand-primary", "--text-primary", "--background-page", "--status-critical", "--ai-advisory", "--evidence", "--contradiction", "--unknown", "--human-decision", "--assurance"):
        assert token in STYLES
