from app.services.agents import build_factpack
from app.services.llm.schemas import FactSource


class FakeCard:
    def __init__(self, domain, title):
        self.id = f"fake-{title}"
        self.domain = domain
        self.title = title
        self.claim_lines = ["Факт 1", "Факт 2"]
        self.sources = [{"title": "Источник", "url": "https://example.com", "date": "2000-01-01"}]
        self.tags = ["marketing"]


class FakeIdea:
    def __init__(self):
        self.domain = "marketing"
        self.object_title = "Тест"


class FakeSession:
    pass


def test_build_factpack(monkeypatch):
    def fake_get_fact_cards(session, domain, tags, limit=10):
        return [FakeCard(domain, "A"), FakeCard(domain, "B"), FakeCard(domain, "C")]

    monkeypatch.setattr("app.crud.get_fact_cards", fake_get_fact_cards)
    pack = build_factpack(FakeSession(), FakeIdea())
    assert len(pack.facts) >= 6
    assert isinstance(pack.facts[0].sources[0], FactSource)
