import streamlit as st
import time
import threading
from queue import Queue

st.set_page_config(page_title="Test App", page_icon="📄", layout="wide")

st.title("Test New Features")

# Test async processing
if "processing_status" not in st.session_state:
    st.session_state.processing_status = {"progress": 0, "message": "", "eta": 0, "is_processing": False}

def test_async_processing(progress_queue):
    """Test async processing function"""
    try:
        for i in range(10):
            progress = (i + 1) * 10
            progress_queue.put({"progress": progress, "message": f"Processing step {i+1}/10"})
            time.sleep(0.5)  # Simulate processing time

        progress_queue.put({"progress": 100, "message": "Processing complete", "result": "Success"})
    except Exception as e:
        progress_queue.put({"error": str(e)})

if st.button("Test Async Processing"):
    st.session_state.processing_status = {
        "progress": 0, "message": "Starting...", "eta": 0, "is_processing": True
    }

    progress_queue = Queue()
    processing_thread = threading.Thread(target=test_async_processing, args=(progress_queue,))
    processing_thread.start()

    progress_bar = st.progress(0)
    status_text = st.empty()

    while processing_thread.is_alive() or not progress_queue.empty():
        try:
            status = progress_queue.get(timeout=0.1)

            if "progress" in status:
                progress_bar.progress(status["progress"] // 10)

            if "message" in status:
                status_text.text(status["message"])

            if "result" in status:
                st.success(f"Result: {status['result']}")
                break

            if "error" in status:
                st.error(f"Error: {status['error']}")
                break

        except:
            continue

    st.session_state.processing_status["is_processing"] = False

# Test citation network
st.header("Test Citation Network")
try:
    from citation_network import CitationNetwork
    st.success("CitationNetwork imported successfully")

    # Create a simple test
    network = CitationNetwork()
    st.write("CitationNetwork instance created")

except Exception as e:
    st.error(f"CitationNetwork import failed: {e}")

st.markdown("---")
st.markdown("Test completed!")