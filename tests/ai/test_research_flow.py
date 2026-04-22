from ai.src.application.services.research_flow import ResearchFlow


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, content):
        self._content = content

    def create(self, **kwargs):
        return _Resp(self._content)


class _Client:
    def __init__(self, content):
        class _Chat:
            def __init__(self, c):
                self.completions = _Completions(c)

        self.chat = _Chat(content)


class FakeOpenAIClient:
    model = "gpt"

    def __init__(self, completion_content="[]"):
        self.client = _Client(completion_content)

    def recommend_articles_fast(self, query, analyzed_articles, top_k=5):
        return {
            "total_analyzed": len(analyzed_articles),
            "relevant_found": 1,
            "recommendations": [
                {
                    "article_title": "A1",
                    "relevance_score": 8.5,
                    "relevance_reasons": ["r1"],
                    "research_applications": ["a1"],
                    "url": "u1",
                    "organisms": [],
                    "key_concepts": [],
                }
            ],
        }

    def chat_with_articles(self, question, context):
        return "answer"


def test_get_research_recommendations():
    flow = ResearchFlow(FakeOpenAIClient())
    out = flow.get_research_recommendations("query", [{"id": 1}], top_k=1)
    assert out["status"] == "success"
    assert out["recommendations"][0]["title"] == "A1"


def test_prepare_article_context():
    flow = ResearchFlow(FakeOpenAIClient())
    context = flow._prepare_article_context([{"title": "t", "url": "u"}])
    assert context == [{"title": "t", "summary": "", "organisms": [], "key_concepts": [], "url": "u"}]


def test_generate_suggested_questions_fallback_on_bad_json():
    flow = ResearchFlow(FakeOpenAIClient("not-json"))
    questions = flow._generate_suggested_questions({"id": "a1", "title": "t"}, "rq")
    assert len(questions) == 1
    assert questions[0]["type"] == "conceptual"


def test_generate_follow_up_questions_fallback_on_bad_json():
    flow = ResearchFlow(FakeOpenAIClient())
    out = flow._generate_follow_up_questions("q", "a", [], "rq")
    assert out == []
