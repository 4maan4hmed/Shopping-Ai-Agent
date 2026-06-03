import streamlit as st

from shopping_agent import agent


st.set_page_config(page_title="Shopping AI Agent", page_icon="🛍️", layout="wide")


def main() -> None:
    st.title("Shopping AI Agent")
    st.caption("Ask for product suggestions, ratings, and checkout help in a simple chat UI.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("What would you like to shop for?")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_history = st.session_state.messages + [{"role": "user", "content": prompt}]
                result = agent.invoke({"messages": chat_history})
                reply = result["messages"][-1].content
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
