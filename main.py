import streamlit as st
import os
import google.generativeai as genai
import time

# ✅ Detect language from file extension
def detect_language(file_name):
    ext = os.path.splitext(file_name)[1]
    lang_map = {
        '.py': 'python',
        '.cpp': 'cpp',
        '.c': 'c',
        '.java': 'java',
        '.js': 'javascript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
    }
    return lang_map.get(ext, 'text')


# ✅ Call Google Gemini API to clean code
def call_gemini_ai(messy_code):
    GEMINI_API_KEY = st.secrets.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        st.error("⚠️ Google Gemini API key not found. Please set it in `.streamlit/secrets.toml` or as environment variable.")
        st.stop()

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"Please clean, format, and optimize the following code. Focus on readability, best practices, and minor efficiency improvements. Provide only the cleaned code:\n\n```\n{messy_code}\n```"

    try:
        response = model.generate_content(prompt)
        if response.parts:
            cleaned_text = "".join([part.text for part in response.parts if hasattr(part, 'text')])

            # Remove surrounding code block if present
            if cleaned_text.startswith("```") and cleaned_text.endswith("```"):
                inner = cleaned_text[3:-3]
                if '\n' in inner:
                    first_newline = inner.find('\n')
                    if inner[:first_newline].strip().isalpha():
                        cleaned_text = inner[first_newline + 1:].strip()
                    else:
                        cleaned_text = inner.strip()
                else:
                    cleaned_text = inner.strip()

            return cleaned_text.strip()
        else:
            return "⚠️ Google Gemini API returned no content."
    except Exception as e:
        return f"⚠️ Exception during Google Gemini API call: {str(e)}"


# ✅ Streamlit App
st.set_page_config(page_title="🧹 Clean Code AI", layout="wide")
st.title("🧹 Clean Code AI Assistant (Powered by Google Gemini)")

st.info("💡 Upload your messy code and Gemini AI will clean, format, and optimize it. Set your API key in `.streamlit/secrets.toml`!")

uploaded_file = st.file_uploader("📤 Upload your messy code file", type=['py', 'cpp', 'c', 'java', 'js', 'html', 'css', 'json', 'xml'])

if uploaded_file:
    try:
        raw_code = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        st.error("⚠️ Unable to decode file. Please upload a UTF-8 encoded code file.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
        st.stop()

    language = detect_language(uploaded_file.name)
    st.markdown(f"**🧠 Detected Language:** `{language.upper()}`")

    if st.button("✨ Clean This Code"):
        with st.spinner("🧠 Cleaning code using Gemini..."):
            start = time.time()
            cleaned_code = call_gemini_ai(raw_code)
            end = time.time()

        if "⚠️" in cleaned_code:
            st.error(cleaned_code)
        else:
            st.success("✅ Code cleaned successfully!")
            st.caption(f"🕒 Processed in {end - start:.2f} seconds")

            # ✅ Side-by-side comparison
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🔍 Original Code")
                st.code(raw_code, language=language)

            with col2:
                st.markdown("### ✅ Cleaned Code")
                st.code(cleaned_code, language=language)

            # ✅ Download button
            name, ext = os.path.splitext(uploaded_file.name)
            download_name = f"{name}_cleaned{ext or '.txt'}"

            st.download_button(
                label="⬇️ Download Cleaned Code",
                data=cleaned_code,
                file_name=download_name,
                mime='text/plain'
            )

            # ✅ Explain cleaned code
            if st.checkbox("🧠 Explain the cleaned code"):
                with st.spinner("📘 Generating explanation using Gemini..."):
                    try:
                        GEMINI_API_KEY = st.secrets.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
                        genai.configure(api_key=GEMINI_API_KEY)

                        explain_prompt = f"Explain what this {language} code does in simple terms:\n\n{cleaned_code}"
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(explain_prompt)

                        if hasattr(response, "text") and response.text:
                            explanation = response.text
                        elif hasattr(response, "parts") and response.parts:
                            explanation = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                        else:
                            explanation = "⚠️ Gemini returned no explanation."

                        st.markdown("### 📘 Code Explanation")
                        st.write(explanation)

                    except Exception as e:
                        st.error(f"⚠️ Failed to get explanation: {e}")

