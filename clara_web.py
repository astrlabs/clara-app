import streamlit as st
import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import random

from clara_app.constants import FREE_DAILY_MESSAGE_LIMIT, PLUS_DAILY_MESSAGE_LIMIT, BETA_ACCESS_KEY
from clara_app.services import storage, llm, memory
from clara_app.utils import helpers
from clara_app.ui import styles, components

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Clara Aster", layout="centered")

# Initialize Firebase (The Memory & Security)
storage.initialize_firebase()

# Apply Styles
styles.apply_styles()

# Initialize Session State
if "username" not in st.session_state:
    st.session_state.username = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "display_name" not in st.session_state:
    st.session_state.display_name = None
if "beta_authenticated" not in st.session_state:
    st.session_state.beta_authenticated = False

# --- 1.1. BETA ACCESS GATE ---
if not st.session_state.beta_authenticated:
    st.title("Clara Aster™")
    with st.form("beta_gate_form"):
        key_input = st.text_input("Enter Early Access Key", type="password")
        submit_key = st.form_submit_button("Enter")
    
    if submit_key:
        if key_input == BETA_ACCESS_KEY:
            st.session_state.beta_authenticated = True
            st.rerun()
        else:
            st.error("Invalid Key.")
    st.stop()

# --- 1.5. PAGE ROUTING (Legal Content) ---
# If query params indicate a legal page, render it and stop execution.
if "page" in st.query_params:
    page = st.query_params["page"]
    if page == "terms":
         components.render_terms_page()
         st.stop()
    elif page == "legal":
         components.render_privacy_policy_page()
         st.stop()
    elif page == "account":
         components.render_account_page()
         st.stop()

# --- 2. THE WEB INTERFACE ---

# --- 2. THE WEB INTERFACE ---

# --- VIEW A: IDENTIFICATION SCREEN ---
if st.session_state.username is None:
    st.title("Clara")
    st.write("")  # Visual breathing room

    with st.form("clara_id_form"):
        name_input = st.text_input("Name", label_visibility="collapsed", placeholder="Enter your First and Last Name")
        submit_id = st.form_submit_button("Start Chat", type="primary")

    if submit_id and name_input:
        clean_name = name_input.strip()
        if clean_name:
            stable_id = helpers.name_to_id(clean_name)
            first_name = clean_name.split()[0]
            
            # Set Session State
            st.session_state.user_id = stable_id
            st.session_state.username = stable_id
            st.session_state.display_name = clean_name
            
            # Initialize Identity (creates doc if new)
            storage.ensure_user_identity(stable_id, f"{stable_id}@placeholder.com")
            storage.save_user_name(stable_id, clean_name)

            # Load past history immediately if it exists
            history = storage.get_chat_history(stable_id)
            if history:
                st.session_state.messages = history
            else:
                # Generate the first greeting if this is a new conversation
                st.session_state.messages = []
                greeting = f"Nice to meet you, {first_name}. I’m here as a partner in thought for whatever is on your mind today."
                st.session_state.messages.append({"role": "assistant", "content": greeting})
                storage.append_chat_message(stable_id, "assistant", greeting)
            
            st.rerun()

    components.render_footer()

# --- VIEW C: THE CHAT INTERFACE ---
else:
    # 1. Simple header
    st.title("Clara")

    # 2. Plan & daily usage limits
    plan = storage.get_user_plan(st.session_state.username)
    today_str = datetime.date.today().isoformat()
    message_count_today = storage.get_daily_message_count(st.session_state.username, today_str)
    if plan == "plus":
        daily_limit = PLUS_DAILY_MESSAGE_LIMIT
    else:
        daily_limit = FREE_DAILY_MESSAGE_LIMIT
    over_limit = daily_limit is not None and message_count_today >= daily_limit

    # 3. Render Sidebar
    components.render_sidebar()

    # 4. Load Memory (If first load)
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = storage.get_chat_history(st.session_state.username)
    if "topic_counts" not in st.session_state:
        st.session_state.topic_counts = {}
    
    # Initialize the Chat Object with History for Gemini
    gemini_history = []
    # Add durable summary first (if available) so Clara has a compact memory across long chats
    summary_text = storage.get_chat_summary(st.session_state.username)
    if summary_text:
        gemini_history.append(
            {
                "role": "user",
                "parts": [
                    "[CONTEXT] Durable summary:\n" + summary_text
                ],
            }
        )
    if st.session_state.display_name:
        first_name = st.session_state.display_name.split()[0]
        gemini_history.append({"role": "user", "parts": [f"[CONTEXT] User name: {st.session_state.display_name}. Address the user as {first_name}."]})

    # If the user has written an explicit profile note, surface it as
    # durable context so Clara can tailor conversations more precisely.
    profile_note = storage.get_user_profile_note(st.session_state.username)
    if profile_note:
        gemini_history.append(
            {
                "role": "user",
                "parts": [
                    "[CONTEXT] Profile note:\n" + profile_note
                ],
            }
        )

    # Add lightweight time context so Clara can speak naturally about being in London
    try:
        london_now = helpers.get_london_now()
        london_str = london_now.strftime("%A, %H:%M")
        time_context = f"[CONTEXT] Time context: Right now it’s {london_str} in London."

        user_timezone = storage.get_user_timezone(st.session_state.username)
        if user_timezone:
            tz_key = user_timezone.strip()
            # Basic mapping from common city names to IANA timezone IDs
            city_to_tz = {
                "london": "Europe/London",
                "new york": "America/New_York",
                "nyc": "America/New_York",
                "los angeles": "America/Los_Angeles",
                "la": "America/Los_Angeles",
                "san francisco": "America/Los_Angeles",
                "chicago": "America/Chicago",
                "toronto": "America/Toronto",
                "paris": "Europe/Paris",
                "berlin": "Europe/Berlin",
                "tokyo": "Asia/Tokyo",
                "singapore": "Asia/Singapore",
                "sydney": "Australia/Sydney",
                "melbourne": "Australia/Melbourne",
            }
            tz_id = city_to_tz.get(tz_key.lower(), tz_key)
            try:
                user_now = datetime.datetime.now(ZoneInfo(tz_id))
                user_str = user_now.strftime("%A, %H:%M")
                time_context += f" The user’s local time is approximately {user_str} ({user_timezone})."
            except Exception:
                # If we can't interpret their input as a timezone, just note the place.
                time_context += f" The user has told you they are in {user_timezone}."

        gemini_history.append({"role": "user", "parts": [time_context]})
    except Exception:
        pass

    # Only send the most recent part of the conversation to keep context manageable
    recent_messages = st.session_state.messages[-50:]
    for msg in recent_messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    
    # Get Model
    model = llm.get_model()
    try:
        chat_session = model.start_chat(history=gemini_history)
    except:
        chat_session = model.start_chat(history=[]) # Fallback if history error

    # 4. Optional search over this conversation
    search_query = st.text_input("Search this chat", "", placeholder="Type a word or phrase to search…")
    if search_query and st.session_state.messages:
        q = search_query.lower()
        matches = [
            (idx, m)
            for idx, m in enumerate(st.session_state.messages)
            if isinstance(m.get("content"), str) and q in m["content"].lower()
        ]
        with st.expander(f"Found {len(matches)} matching message(s)", expanded=True):
            if matches:
                for idx, m in matches:
                    speaker = "You" if m["role"] == "user" else "Clara"
                    snippet = m["content"]
                    if len(snippet) > 220:
                        snippet = snippet[:217] + "..."
                    st.markdown(f"**{speaker}** · `#{idx+1}`  \n{snippet}")
            else:
                st.caption("No matches in this chat yet.")

    # 5. Display Chat History
    for message in st.session_state.messages:
        components.render_chat_message(message["role"], message["content"])

    # 6. Simple chat input at the bottom, with limits
    if over_limit:
        st.warning(
            "You’ve reached today’s free message limit with the standard Clara experience.\n\n"
            "Clara Plus gives you more daily messages, richer long‑term memory, and room for more detailed answers "
            "when you actually want them.\n\n"
            "For now, reach out directly if you’d like Clara Plus turned on for your account."
        )
        st.chat_input("Talk to Clara...", disabled=True)
    elif True:
        # Capture chat input
        chat_val = st.chat_input("Talk to Clara...")
        
        # Capture button input (Quick Reply)
        # We show the button if the last message was from the assistant, 
        # giving the user an easy one-tap way to carry on.
        btn_val = None
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            last_msg = st.session_state.messages[-1]["content"]
            if helpers.should_show_continue_button(last_msg):
                # Just a subtle button
                if st.button("Continue ➔", key=f"cont_{len(st.session_state.messages)}"):
                    btn_val = "Continue"

        # Prioritise chat input if both exist (rare), otherwise use button
        prompt = chat_val or btn_val
        
        if prompt:
            # A. Display User Message
            components.render_chat_message("user", prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            storage.append_chat_message(st.session_state.username, "user", prompt)
            storage.increment_daily_message_count(st.session_state.username, today_str, 1)

            # Anonymous topic classification (no raw text stored in metrics)
            try:
                topic = llm.classify_topic(prompt)
                st.session_state.topic_counts[topic] = st.session_state.topic_counts.get(topic, 0) + 1
                storage.log_ml_topic_metric(topic)
            except Exception:
                pass

            # Anonymous aggregate topic logging (no raw text or user IDs stored)
            try:
                topic = helpers.classify_conversation_topic(prompt)
                storage.log_topic_metric(topic)
            except Exception:
                pass

            # B. Get Clara's Response (with Clarity/Integrity Mirror)
            try:
                # 1. Emotional Analysis & Memory Retrieval
                memory_context = ""
                try:
                    # Async-like extraction (conceptually)
                    emotion_data = llm.extract_emotional_metadata(prompt)
                    
                    # Store current thought in vector DB (we do it before response so it's searchable in future immediate turns if needed, 
                    # but typically we'd do it after. Here we do it after response to correspond to the 'memory' of the interaction)
                    # Actually, for the Integrity Mirror, we want to know if *this* feeling matches *past* feelings.
                    
                    # a) Semantic Search (General context)
                    related_memories = memory.search_memories(st.session_state.username, prompt, n_results=3)
                    
                    # b) Pattern Search (Integrity Mirror)
                    pattern_memories = []
                    if emotion_data["weight"] >= 7:
                        pattern_memories = memory.search_patterns(st.session_state.username, emotion_data["tone"], n_results=3)
                    
                    # Combine & Deduplicate
                    all_memories = {}
                    for m in related_memories + pattern_memories:
                        all_memories[m["id"]] = m
                    
                    if all_memories:
                        memory_context = "\n[INTEGRITY MIRROR - RELEVANT MEMORIES]\n"
                        for m in all_memories.values():
                            memory_context += f"- ({m['metadata']['timestamp'][:10]}) {m['content']} [Tone: {m['metadata'].get('tone')}]\n"
                except Exception as e:
                    print(f"Memory error: {e}") 

                # 2. Add Context to Prompt (Hidden from user UI)
                final_prompt = prompt
                if memory_context:
                    # We prepend semantic context so Clara knows it immediately
                    final_prompt = f"{memory_context}\n\nUser: {prompt}"

                response = chat_session.send_message(final_prompt)
                clara_text = response.text or ""
                
                # 3. Store this interaction in long-term memory
                try:
                    memory.store_memory(
                        st.session_state.username, 
                        prompt, 
                        {
                            "tone": emotion_data["tone"], 
                            "weight": emotion_data["weight"],
                            "topic": topic if 'topic' in locals() else "General"
                        }
                    )
                except Exception:
                    pass


                # If the user explicitly asks for a full / detailed answer,
                # don't trim; otherwise, keep replies concise based on plan.
                if not helpers.user_wants_full_answer(prompt):
                    # Adjust answer length based on plan:
                    # free users get more concise replies, Clara Plus users get more room.
                    if plan == "plus":
                        max_chars = 1400
                    else:
                        max_chars = 700
                    clara_text = helpers.trim_response_for_conciseness(clara_text, max_chars=max_chars)

                components.render_chat_message("assistant", clara_text)
                st.session_state.messages.append({"role": "assistant", "content": clara_text})
                
                # D. SAVE TO DATABASE (Long-term Memory)
                storage.append_chat_message(st.session_state.username, "assistant", clara_text)

                # E. Occasionally refresh the long-term summary so Clara remembers enduring context
                try:
                    if len(st.session_state.messages) >= 20:
                        # Refresh every ~15 messages, with a bit of randomness to
                        # avoid unnecessary calls in very long chats.
                        if len(st.session_state.messages) % 15 == 0 and random.random() < 0.6:
                            # Summarise the recent conversation into a short, durable memory
                            recent_for_summary = st.session_state.messages[-60:]
                            convo_text = []
                            for m in recent_for_summary:
                                speaker = "User" if m["role"] == "user" else "Clara"
                                convo_text.append(f"{speaker}: {m['content']}")
                            summary_prompt = (
                                "Below is a conversation between the user and Clara.\n\n"
                                + "\n".join(convo_text)
                                + "\n\nWrite a durable memory summary of the user."
                            )
                            # Use concise summary model
                            summary_response = llm.get_summary_model().generate_content(summary_prompt)
                            summary_text = getattr(summary_response, "text", "").strip()
                            if summary_text:
                                storage.save_chat_summary(st.session_state.username, summary_text)
                except Exception:
                    pass

                # F. Refresh Logic
                # We force a rerun so that the "Continue" button disappears from its old spot
                # and reappears at the bottom of the new chat history if needed.
                st.rerun()
                
            except Exception as e:
                error_message = str(e)
                if "429" in error_message or "quota" in error_message.lower():
                    st.warning(
                        "Clara’s thinking is hitting the limits of the current plan for a moment.\n\n"
                        "Give it a little time and try again. If this keeps happening, check your Gemini API usage and billing."
                    )
                else:
                    st.error(f"Clara hit an unexpected error: {type(e).__name__}: {error_message}")
