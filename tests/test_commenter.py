# tests/test_commenter.py
from inference.commenter import generate_comments # type: ignore

def test_commenter_empty():
    comments = generate_comments([])
    assert isinstance(comments, list)
    assert any("No fire extinguisher" in c or "Safety score" in c for c in comments)
