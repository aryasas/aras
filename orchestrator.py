from agents.uiux_agent import run_uiux
from agents.coder_agent import run_coder
from agents.reviewer_agent import run_reviewer

MAX_REVIEW_ATTEMPTS = 3


def run_project(feature_request: str) -> str:
    print(f"\n{'='*60}")
    print(f"🚀 ARAS Agent System Starting")
    print(f"📋 Feature: {feature_request}")
    print(f"{'='*60}\n")

    # Step 1: UI/UX Agent
    print("🎨 UI/UX Agent designing spec...")
    spec = run_uiux(feature_request)
    print("✅ Spec complete\n")
    print(f"--- SPEC ---\n{spec}\n")

    # Step 2: Coder + Reviewer loop
    code = None
    for attempt in range(1, MAX_REVIEW_ATTEMPTS + 1):
        print(f"💻 Coder Agent implementing... (attempt {attempt}/{MAX_REVIEW_ATTEMPTS})")
        code = run_coder(spec, previous_code=code)
        print("✅ Code generated\n")

        print("🔍 Reviewer Agent checking...")
        review = run_reviewer(spec, code)
        print(f"--- REVIEW ---\n{review}\n")

        if "PASS" in review:
            print("✅ Code approved by Reviewer!\n")
            break
        else:
            if attempt == MAX_REVIEW_ATTEMPTS:
                print("⚠️  Max attempts reached. Returning last version.\n")
            else:
                print(f"❌ Review failed. Sending feedback to Coder...\n")

    print(f"{'='*60}")
    print("📦 ARAS Agent System Done")
    print(f"{'='*60}\n")
    return code


if __name__ == "__main__":
    import sys
    feature = sys.argv[1] if len(sys.argv) > 1 else "Create a Flask route for user login with username and password"
    result = run_project(feature)
    print("Final Output:\n")
    print(result)
