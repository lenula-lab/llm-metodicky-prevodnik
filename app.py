import os
import json
import tempfile
from typing import List, Dict, Any

import streamlit as st
from openai import OpenAI
from gtts import gTTS

# ---------- Nastavení ----------
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")  # klidně nech takto
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("Chybí proměnná prostředí OPENAI_API_KEY. Nastav ji na Renderu v Settings → Environment.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

st.set_page_config(page_title="Zjednodušovač metodických pokynů", page_icon="🧭", layout="wide")

st.title("🧭 Zjednodušovač metodických pokynů (Elements of AI – demo)")
st.caption("Vlož veřejné metodické pokyny (bez citlivých údajů). Aplikace vrátí srozumitelný text, schéma a audio.")

with st.sidebar:
    st.header("Nastavení")
    tone = st.selectbox("Styl výstupu", ["úředně srozumitelný", "popis pro veřejnost", "stručný bodový výtah"], index=0)
    target_len = st.slider("Požadovaná délka shrnutí (znaky)", 800, 4000, 1600, 100)
    make_audio = st.checkbox("Vytvořit audio (MP3)", value=True)
    st.markdown("---")
    st.markdown("**Pozn.:** LLM běží serverově, klíč je v bezpečí v proměnných prostředí.")

st.subheader("Vstup")
source = st.text_area(
    "Vlož text metodických pokynů (ideálně celý postup, seznam kroků, role, vstupy/výstupy, lhůty).",
    height=260,
    placeholder="Sem vlož metodické pokyny…",
)

col1, col2 = st.columns([1,1])
with col1:
    if st.button("▶ Zpracovat"):
        if not source or len(source.strip()) < 50:
            st.warning("Prosím vlož delší text (aspoň několik vět).")
        else:
            with st.spinner("Zpracovávám…"):
                # 1) Požádáme LLM o JSON s částmi: simplified_text + steps (pro diagram)
                user_prompt = USER_PROMPT_TEMPLATE.format(
                    tone=tone, target_len=target_len, source_text=source
                )
                try:
                    resp = client.chat.completions.create(
                        model=MODEL_NAME,
                        temperature=0.2,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        response_format={"type": "json_object"},
                    )
                    raw = resp.choices[0].message.content
                    data = json.loads(raw)
                except Exception as e:
                    st.error(f"LLM odpověď se nepodařilo zpracovat: {e}")
                    st.stop()

                simplified = data.get("simplified_text", "").strip()
                steps: List[Dict[str, Any]] = data.get("process_steps", [])
                title = data.get("title", "Zjednodušené pokyny")

                if not simplified:
                    st.error("Model nevrátil zjednodušený text. Zkus prosím delší/strukturovanější vstup.")
                    st.stop()

                st.success("Hotovo!")

                # 2) Zobrazení srozumitelného textu
                st.subheader("📄 Srozumitelný dokument")
                st.write(simplified)

                # 3) Schéma procesu (Graphviz DOT -> Streamlit graf)
                def steps_to_dot(steps: List[Dict[str, Any]]) -> str:
                    # Očekáváme položky: {"id": "S1", "label": "Název kroku", "next": ["S2", "S3"], "role": "HR", "type": "action|decision|start|end"}
                    lines = ["digraph G {", 'rankdir=LR;', 'node [shape=box, style="rounded"];']
                    # uzly
                    for s in steps:
                        label = s.get("label", s.get("id", "Krok"))
                        node_shape = {"start":"oval", "end":"oval", "decision":"diamond"}.get(s.get("type",""), "box")
                        lines.append(f'"{s["id"]}" [label="{label.replace(chr(34), "")}", shape={node_shape}];')
                    # hrany
                    for s in steps:
                        for nx in s.get("next", []):
                            lines.append(f'"{s["id"]}" -> "{nx}";')
                    lines.append("}")
                    return "\n".join(lines)

                if steps:
                    st.subheader("🗺️ Schéma procesu")
                    dot = steps_to_dot(steps)
                    st.graphviz_chart(dot, use_container_width=True)
                    with st.expander("Zobrazit DOT kód (pro kopírování do jiných nástrojů)"):
                        st.code(dot, language="dot")
                else:
                    st.info("Nepodařilo se vygenerovat kroky procesu. Zkus do vstupu přidat očíslované kroky a role.")

                # 4) Audio výstup (gTTS) – čeština
                if make_audio:
                    try:
                        tts = gTTS(text=simplified, lang="cs")
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                        tts.save(tmp.name)
                        st.subheader("🔊 Audio shrnutí (MP3)")
                        with open(tmp.name, "rb") as f:
                            st.download_button("Stáhnout audio", f, file_name="shrnutí.mp3", mime="audio/mpeg")
                    except Exception as e:
                        st.warning(f"Audio se nepodařilo vytvořit: {e}")

with col2:
    st.markdown("### Ukázky vhodného vstupu")
    st.write("""
- **Proces žádosti o studijní volno**: kdo podává, jaké přílohy, kdo schvaluje, lhůty, kdy se vrací k žadateli, co je výstup.
- **Pracovní cesta**: zadání, schválení, vyúčtování, kontrola náležitostí, uložení do spisu, role (zaměstnanec, nadřízený, účetní).
- **Přijímání do služby**: vyhlášení VŘ, přihlášky, posouzení, pohovory, rozhodnutí, jmenování, nástup, dokumentace.
""")
    st.markdown("---")
    st.caption("Tento nástroj je demonstrační, bez záruky. Nevkládej citlivá data.")
