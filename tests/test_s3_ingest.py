from turbosearch.ingest import iter_s3_documents


class FakeBody:
    def __init__(self, text: str) -> None:
        self.text = text

    def read(self) -> bytes:
        return self.text.encode("utf-8")


class FakeS3Client:
    def get_paginator(self, name: str):
        assert name == "list_objects_v2"
        return self

    def paginate(self, **kwargs):
        assert kwargs["Bucket"] == "docs-bucket"
        assert kwargs["Prefix"] == "notes/"
        return [
            {
                "Contents": [
                    {"Key": "notes/a.txt"},
                    {"Key": "notes/b.md"},
                    {"Key": "notes/image.png"},
                ]
            }
        ]

    def get_object(self, Bucket: str, Key: str):
        return {"Body": FakeBody(f"contents for {Bucket}/{Key}")}


def test_iter_s3_documents_reads_text_objects() -> None:
    documents = list(iter_s3_documents("docs-bucket", "notes/", client=FakeS3Client()))

    assert [doc["title"] for doc in documents] == ["a.txt", "b.md"]
    assert documents[0]["source"] == "s3"
    assert documents[0]["source_url"] == "s3://docs-bucket/notes/a.txt"
    assert "contents for docs-bucket/notes/a.txt" in documents[0]["text"]

