import os
import datetime
from dataclasses import dataclass

import streamlit as st
import psycopg2
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Prompt:
    title: str
    prompt: str
    is_favorite: bool
    id: int = None
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

def setup_database():
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur

def prompt_form(prompt=None, mode="add"):
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key="prompt_form"):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt_content:
                st.error('Please fill in both the title and prompt fields.')
                return
            new_prompt = Prompt(title, prompt_content, is_favorite, default.id, default.created_at, datetime.datetime.now())
            return new_prompt, mode

def display_prompts(cur):
    search_query = st.text_input("Search Prompts")
    sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Title Ascending", "Title Descending"], index=0)
    order_query = ""
    if search_query:
        if "Title" in sort_by:
            order_query = "ASC" if sort_by == "Title Ascending" else "DESC"
            cur.execute(
                f"SELECT * FROM prompts WHERE title ILIKE %s OR prompt ILIKE %s ORDER BY title {order_query}",
                ('%' + search_query + '%', '%' + search_query + '%')
            )
        else:
            order_query = "DESC" if sort_by == "Newest First" else "ASC"
            cur.execute(
                f"SELECT * FROM prompts WHERE title ILIKE %s OR prompt ILIKE %s ORDER BY created_at {order_query}",
                ('%' + search_query + '%', '%' + search_query + '%')
            )
    else:
        if "Title" in sort_by:
            order_query = "ASC" if sort_by == "Title Ascending" else "DESC"
            cur.execute(f"SELECT * FROM prompts ORDER BY title {order_query}")
        else:
            order_query = "DESC" if sort_by == "Newest First" else "ASC"
            cur.execute(f"SELECT * FROM prompts ORDER BY created_at {order_query}")

    prompts = cur.fetchall()
    
    for p in prompts:
        title_display = f"⭐ {p[1]}" if p[3] else p[1]
        with st.expander(title_display):
            st.code(p[2])
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Edit", key=f"edit-{p[0]}"):
                    return Prompt(p[1], p[2], p[3], p[0], p[4], p[5])  # Return prompt for editing
            with col2:
                if st.button("Favorite" if not p[3] else "Unfavorite", key=f"fav-{p[0]}"):
                    cur.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (p[0],))
                    con.commit()
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del-{p[0]}"):
                    cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                    con.commit()
                    st.rerun()
    return None

if __name__ == "__main__":
    st.title("Jase's Promptbase✨")
    st.subheader("Here is a website to storage your prompts!💡")
    st.markdown("You can easily CRUD prompts while also you can search and filter your prompts ")

    con, cur = setup_database()

    prompt_to_edit = display_prompts(cur)
    
    if prompt_to_edit:
        result = prompt_form(prompt_to_edit, "edit")
    else:
        result = prompt_form()
    
    if result:
        new_prompt, mode = result  # Unpack only if result is not None
        if new_prompt:
            if mode == "add":
                try:
                    cur.execute(
                        "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                        (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite)
                    )
                    con.commit()
                    st.success("Prompt added successfully!")
                except psycopg2.Error as e:
                    st.error(f"Database error: {e}")
            elif mode == "edit":
                try:
                    cur.execute(
                        "UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s, updated_at = %s WHERE id = %s",
                        (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite, new_prompt.updated_at, new_prompt.id)
                    )
                    con.commit()
                    st.success("Prompt updated successfully!")
                except psycopg2.Error as e:
                    st.error(f"Database error: {e}")
    con.close()