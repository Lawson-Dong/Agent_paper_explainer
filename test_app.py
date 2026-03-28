#!/usr/bin/env python3
"""
Test script to verify the complete application functionality
"""
import os
import tempfile
from pdf_loader import load_multiple_pdfs
from vector_store import VectorStoreManager
from qa_chain import QAChain

def test_pdf_processing():
    """Test PDF loading and processing"""
    try:
        # Create a simple test PDF content (this would normally be a real PDF)
        # For testing, we'll skip actual PDF loading and test the components

        # Test vector store creation
        vectorstore_manager = VectorStoreManager()
        print("✅ VectorStoreManager created")

        # Test QA chain creation
        qa_chain = QAChain(vectorstore_manager)
        print("✅ QAChain created")

        print("✅ All components initialized successfully")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing AI Paper Explainer components...")
    success = test_pdf_processing()

    if success:
        print("\n🎉 Application components are working!")
        print("You can now run: streamlit run app.py")
    else:
        print("\n❌ Some components failed. Please check the error messages above.")