# test_parsers.py
from src.parsers.pdf_parser import parse_pdf
from src.parsers.image_parser import parse_image

def test_pdf():
    path = "tests\Выписка_по_счёту_дебетовой_карты.pdf"
    transactions = parse_pdf(path)
    for t in transactions:
        print(t)

def test_image():
    path = "tests/photo_2025-04-23_20-33-19.jpg"
    categories = parse_image(path)
    for c in categories:
        print(c)

if __name__ == "__main__":
    print("=== PDF TEST ===")
    test_pdf()
    print("\n=== IMAGE TEST ===")
    test_image()
