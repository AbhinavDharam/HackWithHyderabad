"""
Automated Streamlit UI Tests for RecallOps.
Uses official streamlit.testing.v1.AppTest to verify the interactive workbench.
"""
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest


def test_app_loads_cleanly():
    """Verifies that app.py loads without unhandled exceptions."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception, f"App threw exception: {at.exception}"
    assert len(at.tabs) == 4, f"Expected 4 tabs, found {len(at.tabs)}"
    print("✓ App loads cleanly with 4 primary tabs.")


def test_app_memory_mode_toggle():
    """Verifies agent mode toggle between WITH_HINDSIGHT_MEMORY and WITHOUT_MEMORY."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Find the agent mode radio
    assert len(at.radio) > 0, "No radio widgets found."
    radio = at.radio[0]

    # Verify options exist
    assert any("Memory" in opt for opt in radio.options)
    print("✓ Default agent mode is active.")

    # Select the second option (Without Memory)
    cold_opt = next(opt for opt in radio.options if "Without Memory" in opt or "Standard" in opt)
    radio.set_value(cold_opt).run()
    assert not at.exception
    assert radio.value == cold_opt
    print("✓ Successfully toggled to Without Memory (Cold Start) mode without error.")


def test_app_incident_selection():
    """Verifies changing the selected active incident."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Check selectbox for incidents
    assert len(at.selectbox) >= 1
    inc_select = at.selectbox[0]
    
    # Select another scenario (e.g. INC-102)
    options = inc_select.options
    inc_102_option = next((opt for opt in options if "INC-102" in opt), None)
    if inc_102_option:
        inc_select.set_value(inc_102_option).run()
        assert not at.exception
        print("✓ Selected INC-102 and verified incident workbench renders cleanly.")


def test_app_form_submit_and_memory_query():
    """Verifies resolving incident and querying Hindsight via UI."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Find the Save Resolution button
    resolve_btn = next((b for b in at.button if "Save Resolution" in b.label), None)
    assert resolve_btn is not None, "Save Resolution button not found."
    
    # Click resolve button
    resolve_btn.click().run()
    assert not at.exception
    assert len(at.success) > 0
    print("✓ Successfully executed 'Save Resolution and Commit to Memory' workflow.")

    # Find the Memory Query button
    query_btn = next((b for b in at.button if "Execute Memory Query" in b.label), None)
    if query_btn:
        query_btn.click().run()
        assert not at.exception
        print("✓ Successfully queried Hindsight live memory console from UI.")


if __name__ == "__main__":
    print("Running RecallOps Streamlit Automated UI Tests...")
    test_app_loads_cleanly()
    test_app_memory_mode_toggle()
    test_app_incident_selection()
    test_app_form_submit_and_memory_query()
    print("\nAll Streamlit UI tests passed successfully! 🎉")
