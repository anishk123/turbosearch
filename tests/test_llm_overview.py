from turbosearch.overview import OpenAICompatibleSummarizer


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": "A concise cited overview."}}]}


def test_openai_compatible_summarizer_posts_chat_completion() -> None:
    calls = []

    def fake_post(url: str, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    summarizer = OpenAICompatibleSummarizer(
        base_url="http://llm.local/v1",
        api_key="test-key",
        model="qwen-local",
        post=fake_post,
    )

    text = summarizer.summarize(
        "marriage",
        [{"title": "Pride and Prejudice", "author": "Jane Austen", "body": "It is a truth..."}],
    )

    assert text == "A concise cited overview."
    assert calls[0][0] == "http://llm.local/v1/chat/completions"
    assert calls[0][1]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0][1]["json"]["model"] == "qwen-local"
    assert "Pride and Prejudice" in calls[0][1]["json"]["messages"][1]["content"]

