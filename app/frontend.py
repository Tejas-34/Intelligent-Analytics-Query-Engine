import os
import requests
import streamlit as st


def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def main():
    load_env()
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

    st.title("Analytics Query Engine")

    query = st.text_input("Enter natural language query:")

    if st.button("Submit"):
        if not query.strip():
            st.warning("Please enter a query.")
            return

        try:
            resp = requests.post(
                f"{api_url}/query",
                json={"query": query.strip()},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.subheader("Generated Logic")
                st.code(data.get("generated_logic", ""), language="sql")

                st.subheader("Result")
                st.write(data.get("result"))

                st.subheader("Confidence Score")
                st.write(data.get("confidence_score"))

                st.subheader("Explanation")
                st.write(data.get("explanation", ""))
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except requests.RequestException as err:
            st.error(f"Failed to connect to query engine: {err}")


if __name__ == "__main__":
    main()
