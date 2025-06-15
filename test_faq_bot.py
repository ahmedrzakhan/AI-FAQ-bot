#!/usr/bin/env python3
"""
Simple test script for the FAQ bot
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print("=== Health Check ===")
    print(json.dumps(response.json(), indent=2))
    print()

def test_question(question):
    response = requests.post(
        f"{BASE_URL}/ask",
        headers={"Content-Type": "application/json"},
        json={"question": question}
    )
    print(f"=== Question: {question} ===")
    result = response.json()
    print(f"Answer: {result['answer']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Relevant FAQs found: {len(result['relevant_faqs'])}")
    print()

def test_all_faqs():
    response = requests.get(f"{BASE_URL}/faqs")
    result = response.json()
    print("=== All FAQs ===")
    print(f"Total FAQs in database: {result['count']}")
    for i, faq in enumerate(result['faqs'][:3], 1):  # Show first 3
        print(f"{i}. Q: {faq.get('question', 'Unknown')}")
    print()

if __name__ == "__main__":
    print("🤖 Testing FAQ Bot\n")

    # Test health
    test_health()

    # Test all FAQs
    test_all_faqs()

    # Test specific questions
    questions = [
        "What is your return policy?",
        "How long does shipping take?",
        "Do you offer customer support?",
        "What about refunds?",
        "What is your phone number?"  # This one won't be in FAQ
    ]

    for question in questions:
        test_question(question)

    print("✅ All tests completed!")
    print("💡 Try running: streamlit run frontend/app.py")
    print("   Then visit: http://localhost:8501")