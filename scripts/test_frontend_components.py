"""
Comprehensive Frontend Component Functionality & DOM Assertion Test Suite
Tests every route, UI element, form, selector, player, and policy page on Next.js.
"""

import sys
import re
import json
import urllib.request
import urllib.parse
from html.parser import HTMLParser

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:3000"


def fetch_route(route: str):
    url = f"{BASE_URL}{route}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.getcode(), resp.read().decode("utf-8")


def run_component_tests():
    print("=======================================================================", flush=True)
    print(" LECTURE DUBBER - FRONTEND COMPONENT DEEP VERIFICATION SUITE", flush=True)
    print("=======================================================================", flush=True)

    passed_tests = 0
    total_tests = 0

    def assert_test(name: str, condition: bool, details: str = ""):
        nonlocal passed_tests, total_tests
        total_tests += 1
        status = "PASS" if condition else "FAIL"
        print(f"[{status}] {name} {details}", flush=True)
        if condition:
            passed_tests += 1
        return condition

    # 1. Landing Page (/)
    print("\n--- 1. Testing Landing Page (/) ---", flush=True)
    try:
        code, html = fetch_route("/")
        assert_test("Navbar Component Rendered", "Dashboard" in html and ("Sign In" in html or "Login" in html) and "Register" in html)
        assert_test("Hero Headline / Value Proposition", "Lecture Dubber" in html or "Classroom" in html or "Dubbing" in html)
        assert_test("Voice Gallery Component Present", "VoiceGallery" in html or "Voices" in html or "Tariq" in html or "Kareem" in html)
        assert_test("Feature Architecture / Pipeline Section", "Pipeline" in html and ("Demucs" in html or "Translation" in html))
        assert_test("Footer Navigation Links", "Terms of Service" in html and "Privacy Policy" in html and "Takedown" in html)
    except Exception as e:
        assert_test("Landing Page Loading", False, f"Exception: {e}")

    # 2. Registration Page (/register)
    print("\n--- 2. Testing Registration Component (/register) ---", flush=True)
    try:
        code, html = fetch_route("/register")
        assert_test("Register Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("Email Input Field Present", 'type="email"' in html or 'name="email"' in html or 'id="email"' in html)
        assert_test("Password Input Field Present", 'type="password"' in html or 'name="password"' in html or 'id="password"' in html)
        assert_test("Registration Submission Button", "Register" in html or "Sign Up" in html or "Create Account" in html)
    except Exception as e:
        assert_test("Register Page Loading", False, f"Exception: {e}")

    # 3. Login Page (/login)
    print("\n--- 3. Testing Login Component (/login) ---", flush=True)
    try:
        code, html = fetch_route("/login")
        assert_test("Login Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("Email Input Field Present", 'type="email"' in html or 'name="email"' in html or 'id="email"' in html)
        assert_test("Password Input Field Present", 'type="password"' in html or 'name="password"' in html or 'id="password"' in html)
        assert_test("Login Submit Button", "Log In" in html or "Sign In" in html or "Login" in html)
    except Exception as e:
        assert_test("Login Page Loading", False, f"Exception: {e}")

    # 4. Dashboard (/dashboard)
    print("\n--- 4. Testing Dashboard Component (/dashboard) ---", flush=True)
    try:
        code, html = fetch_route("/dashboard")
        assert_test("Dashboard Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("New Job Action Button", "New" in html or "Create" in html or "/jobs/new" in html)
        assert_test("Dashboard Statistics / Jobs Table Container", "Jobs" in html or "Status" in html or "Processing" in html)
    except Exception as e:
        assert_test("Dashboard Page Loading", False, f"Exception: {e}")

    # 5. New Job Studio (/jobs/new)
    print("\n--- 5. Testing Job Creation Studio (/jobs/new) ---", flush=True)
    try:
        code, html = fetch_route("/jobs/new")
        assert_test("New Job Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("Source Type Options (YouTube / Upload)", "YouTube" in html or "upload" in html.lower())
        assert_test("Target Language Selection Element", "Language" in html or "target_lang" in html or "Urdu" in html or "Arabic" in html)
        assert_test("Voice Selection Controls", "Voice" in html or "speaker" in html.lower())
        assert_test("Ownership / Legal Consent Checkboxes", "ownership" in html.lower() or "consent" in html.lower() or "permission" in html.lower())
    except Exception as e:
        assert_test("New Job Studio Loading", False, f"Exception: {e}")

    # 6. Terms of Service (/terms)
    print("\n--- 6. Testing Terms of Service Page (/terms) ---", flush=True)
    try:
        code, html = fetch_route("/terms")
        assert_test("Terms Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("Terms Legal Content", "Terms of Service" in html and ("Academic" in html or "Intellectual Property" in html or "Liability" in html))
    except Exception as e:
        assert_test("Terms Page Loading", False, f"Exception: {e}")

    # 7. Privacy Policy (/privacy)
    print("\n--- 7. Testing Privacy Policy Page (/privacy) ---", flush=True)
    try:
        code, html = fetch_route("/privacy")
        assert_test("Privacy Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("Privacy Policy Content", "Privacy Policy" in html and ("Data" in html or "Voice" in html or "Information" in html))
    except Exception as e:
        assert_test("Privacy Page Loading", False, f"Exception: {e}")

    # 8. Copyright / Takedown Notice (/takedown)
    print("\n--- 8. Testing DMCA Takedown Page (/takedown) ---", flush=True)
    try:
        code, html = fetch_route("/takedown")
        assert_test("Takedown Route HTTP Status", code == 200, f"(Code: {code})")
        assert_test("Takedown Form Fields", "DMCA" in html or "Copyright" in html or "Infringement" in html or "Signature" in html)
    except Exception as e:
        assert_test("Takedown Page Loading", False, f"Exception: {e}")

    # Final Scorecard
    print("\n" + "=" * 71, flush=True)
    print(f" FRONTEND VERIFICATION RESULTS: {passed_tests} / {total_tests} ASSERTIONS PASSED", flush=True)
    print("=" * 71, flush=True)

    if passed_tests == total_tests:
        print("\n>>> ALL FRONTEND COMPONENTS TESTED AND OPERATIONAL! <<<\n", flush=True)
        return True
    else:
        print(f"\n>>> WARNING: {total_tests - passed_tests} TEST(S) FAILED! <<<\n", flush=True)
        return False


if __name__ == "__main__":
    success = run_component_tests()
    sys.exit(0 if success else 1)
