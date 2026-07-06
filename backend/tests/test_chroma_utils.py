from app.services.chroma_utils import ensure_chroma_collection


class DummyCollection:
    def __init__(self, name: str):
        self.name = name


class DummyClient:
    def __init__(self):
        self.deleted_collections: list[str] = []
        self.create_calls = 0

    def get_or_create_collection(self, name: str):
        self.create_calls += 1
        if self.create_calls == 1:
            raise RuntimeError("Collection expecting embedding with dimension of 384, got 768")
        return DummyCollection(name)

    def delete_collection(self, name: str):
        self.deleted_collections.append(name)


def test_ensure_chroma_collection_recreates_after_dimension_mismatch():
    client = DummyClient()

    collection = ensure_chroma_collection(client, "snserp_documents")

    assert collection is not None
    assert client.deleted_collections == ["snserp_documents"]
    assert client.create_calls == 2
