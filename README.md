# 🧭 LLM Metodický převodník

> Jednoduchý nástroj, který převede složité metodické pokyny do srozumitelného textu, vytvoří schéma procesu a nabídne audio výstup (v češtině).  
> Vzniklo pro kurz **Elements of AI**, určeno pro kolegy ze služebních úřadů.

---

## ✨ Co umí
- Převod textu do srozumitelnější řeči (plain language)
- Automatické schéma procesu (vývojový diagram)
- Audio shrnutí ve formátu MP3
- Veřejně přístupné (např. přes Render), bez nutnosti přihlašování

---

## 🧩 Jak to spustit lokálně
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="tvůj_klíč"   # nebo set OPENAI_API_KEY=... ve Windows
streamlit run app.py
