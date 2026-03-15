import unittest

from backend.services.text_normalizer import TextNormalizer


class TextNormalizerTests(unittest.TestCase):
    def test_normalize_document_produces_canonical_text_once(self):
        normalizer = TextNormalizer()
        raw_text = """
        Page 1
        CONFIDENTIAL

        This    Agreement   is made on 12 March 2024.


        Payment terms apply.

        2
        """

        normalized = normalizer.normalize_document(raw_text)

        self.assertEqual(
            normalized.text,
            "This Agreement is made on 12 March 2024.\n\nPayment terms apply.",
        )
        self.assertEqual(
            normalized.sentences,
            (
                "This Agreement is made on 12 March 2024.",
                "Payment terms apply.",
            ),
        )
        self.assertEqual(normalized.chunks, (normalized.text,))


if __name__ == "__main__":
    unittest.main()
