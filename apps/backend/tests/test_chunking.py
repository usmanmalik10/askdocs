import math

import pytest

from chunking import chunk_pages
from extraction import Page
from provider import normalize


def test_chunks_cover_content_and_preserve_page_numbers():
    pages = [Page(3, "alpha beta gamma " * 200), Page(8, "a" * 3500)]
    chunks = chunk_pages(pages)
    assert {chunk.page for chunk in chunks} == {3, 8}
    assert all(0 < len(chunk.content) <= 1400 for chunk in chunks)
    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))
    assert chunks[-1].content.endswith("a" * 100)
    assert len(chunks) < 12


def test_embedding_normalization_is_finite_unit_length():
    result = normalize([2.0] * 768)
    assert math.isclose(sum(v * v for v in result), 1.0)


@pytest.mark.parametrize("values", [[0.0] * 768, [float("nan")] * 768, [1.0] * 767])
def test_invalid_embeddings_are_rejected(values):
    with pytest.raises(ValueError):
        normalize(values)
