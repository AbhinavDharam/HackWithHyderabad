"""
Automated Streamlit UI Tests for RecallOps Command Center.
Uses official streamlit.testing.v1.AppTest to verify the unified incident workflow.
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
    """Verifies that app.py loads the Command Center without unhandled exceptions."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception, f"App threw exception: {at.exception}"
    print("✓ Command Center loads cleanly without errors.")


def test_app_memory_mode_toggle():
    """Verifies investigation mode toggle between WITH TEAM MEMORY and WITHOUT MEMORY."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Find the mode radio selector
    assert len(at.radio) > 0, "No radio selector found."
    radio = at.radio[0]

    # Verify options exist
    assert any("MEMORY" in opt for opt in radio.options)
    print("✓ Default agent mode is active.")

    # Select the second option (WITHOUT MEMORY)
    cold_opt = next(opt for opt in radio.options if "WITHOUT" in opt)
    radio.set_value(cold_opt).run()
    assert not at.exception
    assert radio.value == cold_opt
    print("✓ Successfully toggled to WITHOUT MEMORY mode without error.")


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
        print("✓ Selected INC-102 and verified Command Center renders cleanly.")


def test_app_form_submit():
    """Verifies resolving incident and committing to Hindsight memory via UI."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Find the Resolve & Remember button
    resolve_btn = next((b for b in at.button if "RESOLVE INCIDENT" in b.label), None)
    assert resolve_btn is not None, "Resolve & Remember button not found."
    
    # Click resolve button
    resolve_btn.click().run()
    assert not at.exception
    print("✓ Successfully executed 'RESOLVE INCIDENT & REMEMBER' workflow.")


if __name__ == "__main__":
    print("Running RecallOps Command Center Automated UI Tests...")
    test_app_loads_cleanly()
    test_app_memory_mode_toggle()
    test_app_incident_selection()
    test_app_form_submit()
    print("\nAll RecallOps Command Center UI tests passed successfully! 🎉")
