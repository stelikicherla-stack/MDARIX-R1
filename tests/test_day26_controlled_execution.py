from ask_mdarix import QueryInterpreter
from ask_mdarix.model_boundary import build_model_context, dependency_failure
from ask_mdarix.retrieval import build_retrieval_plan


def test_retrieval_plan_is_bounded_and_tenant_scoped():
    spec = QueryInterpreter().interpret("show complaints after Rev D")
    plan = build_retrieval_plan(spec, max_records=5000)
    assert plan.status == "READY"
    assert plan.limit == 1000
    assert plan.tenant_scoped and plan.authorized_only
    assert plan.product_version_scope == ("d",)


def test_unresolved_question_cannot_execute_retrieval():
    spec = QueryInterpreter().interpret("Compare Rev C")
    assert build_retrieval_plan(spec).status == "NOT_EXECUTABLE"


def test_model_context_filters_before_model_boundary():
    result = build_model_context([
        {"tenant_id": "a", "id": "1", "title": "safe", "password": "bad", "hidden": "bad"},
        {"tenant_id": "b", "id": "2", "title": "cross tenant"},
    ], tenant_id="a", authorized_fields={"id", "title"})
    assert result.context == ({"id": "1", "title": "safe"},)
    assert all("password" not in item and "hidden" not in item for item in result.context)
    assert result.response["model_invocation"] == "NOT_IMPLEMENTED"


def test_dependency_failure_is_not_a_successful_answer():
    failure = dependency_failure()
    assert failure["status"] == "DEPENDENCY_UNAVAILABLE"
    assert "answer" not in failure
