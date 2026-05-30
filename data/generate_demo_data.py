"""
Generate a synthetic-but-realistic multilingual social-post demo dataset for
Nuance development and demos.

Output: data/nuance_demo.csv -- one row per DISTINCT post_text per (event,
language). Corpus size is set by template variety (~1,400-1,900 rows), not a
target row count. This is the dedup'd, honest corpus: downstream post counts and
cds_confidence are then real, and Narrative Search shows variety instead of the
old ~17x duplication. (See docs/07_audit_and_fixes.md Findings A & C.)

Why synthetic? It's faster than GDELT/HF for a first demo and deterministic so
demo recordings stay repeatable. Cross-language divergence comes from each
community's distinct frame-template composition (e.g. English emphasizes
individualist/opportunity framings, Japanese collectivist/status-quo), which the
Cortex frame classifier then labels per post.

The dataset is intentionally biased toward signal-rich content; for a real
production deployment, swap in GDELT / Marketplace social-data providers.

Usage:
    python data/generate_demo_data.py [--out PATH] [--seed 42]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Demo events and language community tendencies
# ---------------------------------------------------------------------------
# Each event has per-language "frame tendency" tuples that drive realistic
# divergence patterns. The numbers encode % weight on (frame, sentiment_bias).
# This is what makes the demo look like real cross-cultural data, not random noise.

EVENTS = [
    "iPhone_17_launch",
    "Olympics_2026_opening",
    "BrandX_rebrand",
    "Tesla_robotaxi_debut",
    "K-pop_global_tour",
    "World_Cup_2026_final",
    "EU_AI_act_enforcement",
    "Climate_Summit_2026",
]

LANGUAGES = ["en", "ja", "zh", "de", "es", "fr", "ko", "pt", "ar", "hi", "it", "ru"]

SOURCES = ["twitter", "reddit", "news", "reviews", "support"]

# Frame templates: realistic skeleton phrases per (language, frame).
# For brevity we keep ~5 templates per (lang, frame); enough variety for 25K
# generated rows to look organic. Real corpus would have far more variation.

FRAME_TEMPLATES: Dict[Tuple[str, str], List[str]] = {
    # English
    ("en", "individualist"): [
        "I love that they finally give me {x} my way",
        "My choice, my style — {x} is exactly what I needed",
        "Finally a {x} that respects personal autonomy",
        "Made for me, by me. {x} is freedom",
        "The {x} that lets me be myself",
    ],
    ("en", "opportunity_framing"): [
        "Huge opportunity with this {x} — game changer",
        "{x} opens so many new doors for our team",
        "Exciting times ahead because of {x}",
        "The {x} is a once-in-a-decade chance",
        "What an opportunity! {x} just dropped",
    ],
    ("en", "threat_framing"): [
        "{x} is a step backward and dangerous",
        "We should be worried about {x}",
        "{x} threatens what we built",
        "This is exactly why we need to stop {x}",
        "{x} is bad news for everyone",
    ],
    ("en", "pragmatic"): [
        "{x} works, that's all I care about",
        "Bottom line: {x} delivers results",
        "Whatever — show me the data on {x}",
        "{x} is fine. Move on.",
        "Not perfect, but {x} gets the job done",
    ],

    # Japanese — strong collectivist + status_quo tendencies
    ("ja", "collectivist"): [
        "みんなで{x}を使うのが一番だと思う",
        "{x}は私たちのコミュニティに合っている",
        "家族みんなで{x}を楽しんでいます",
        "私たちみたいな普通の人にも{x}は良い",
        "チームで{x}を共有しています",
    ],
    ("ja", "status_quo"): [
        "{x}は今までの方がよかった",
        "急いで{x}を変える必要はない",
        "従来の方法で十分だ、{x}は不要",
        "{x}より昔のやり方が安心できる",
        "{x}は本当に必要なのだろうか",
    ],
    ("ja", "threat_framing"): [
        "{x}は文化を破壊する恐れがある",
        "{x}には危険なリスクが潜んでいる",
        "{x}を導入するのは時期尚早だ",
        "{x}は社会に悪影響を及ぼす",
        "{x}に反対する声が増えている",
    ],
    ("ja", "spiritual_ethical"): [
        "{x}は道徳的に正しいのか考えるべきだ",
        "{x}と精神性のバランスを取りたい",
        "倫理的観点から{x}を見直すべきだ",
        "{x}を選ぶときは心を込めて選ぶ",
        "{x}に対する我々の責任を忘れてはいけない",
    ],

    # Chinese — nationalist + opportunity tendencies in product contexts
    ("zh", "nationalist"): [
        "{x}必须支持国产品牌的发展",
        "国内的{x}比外国的好得多",
        "我们应该为国货{x}骄傲",
        "外国{x}永远比不上中国制造",
        "{x}应该体现中国特色",
    ],
    ("zh", "opportunity_framing"): [
        "{x}带来巨大的发展机遇",
        "通过{x}我们可以走向更广阔的市场",
        "{x}让未来充满希望",
        "抓住{x}的机会就是抓住未来",
        "{x}是产业升级的好机会",
    ],
    ("zh", "collectivist"): [
        "{x}让我们大家共同进步",
        "整个团队都从{x}中受益",
        "我们一家人都喜欢{x}",
        "{x}是为人民服务的好产品",
        "社区里大家都在用{x}",
    ],
    ("zh", "pragmatic"): [
        "{x}有用就行,别想太多",
        "{x}性价比高就是好东西",
        "实事求是地看,{x}效果可以",
        "我们关心的是{x}能解决问题",
        "{x}够用就行了",
    ],

    # German — pragmatic + reform + uncertainty_avoidance
    ("de", "pragmatic"): [
        "{x} funktioniert solide, mehr nicht",
        "Was zählt: {x} hält, was es verspricht",
        "{x} ist okay, aber nichts Besonderes",
        "Pragmatisch betrachtet ist {x} brauchbar",
        "{x} ist Mittelmaß, aber zuverlässig",
    ],
    ("de", "reform_seeking"): [
        "{x} muss dringend überarbeitet werden",
        "Wir brauchen einen besseren Ansatz als {x}",
        "Es ist Zeit, {x} grundlegend zu reformieren",
        "{x} zeigt, dass wir Veränderung brauchen",
        "Mit {x} können wir Strukturen verbessern",
    ],
    ("de", "threat_framing"): [
        "{x} könnte ein ernstes Risiko darstellen",
        "Wir sollten {x} kritisch hinterfragen",
        "Die Gefahren von {x} werden unterschätzt",
        "{x} bedroht etablierte Standards",
        "Vorsicht ist geboten bei {x}",
    ],

    # Spanish — collectivist + spiritual + opportunity
    ("es", "collectivist"): [
        "Todos en la familia disfrutamos {x}",
        "{x} nos une como comunidad",
        "Nuestro barrio entero apoya {x}",
        "Compartir {x} con los amigos es lo mejor",
        "{x} es para todos nosotros",
    ],
    ("es", "spiritual_ethical"): [
        "{x} tiene un significado más profundo",
        "Hay valores en {x} que no podemos ignorar",
        "{x} debe respetar nuestra dignidad",
        "Lo importante de {x} es su alma",
        "{x} merece reflexión ética",
    ],
    ("es", "opportunity_framing"): [
        "{x} abre puertas que ni imaginábamos",
        "Gran oportunidad con {x} para nuestra región",
        "{x} es justo lo que necesitábamos",
        "Con {x} llega un futuro mejor",
        "Aprovechemos {x} mientras podamos",
    ],

    # French — reform_seeking + spiritual + status_quo
    ("fr", "reform_seeking"): [
        "{x} doit être profondément réformé",
        "Il faut repenser {x} pour le mieux",
        "{x} appelle un changement urgent",
        "Réformons {x} avant qu'il soit trop tard",
        "{x} est un appel à transformer le système",
    ],
    ("fr", "spiritual_ethical"): [
        "{x} pose une question éthique fondamentale",
        "La dimension morale de {x} est essentielle",
        "{x} touche à des valeurs profondes",
        "Réfléchissons à l'éthique de {x}",
        "{x} mérite un débat moral approfondi",
    ],
    ("fr", "status_quo"): [
        "{x} ne devrait pas tout changer",
        "Préservons ce qui marche, méfions-nous de {x}",
        "{x} bouscule trop nos traditions",
        "On aimait les choses comme avant, sans {x}",
        "{x} va trop vite, attendons",
    ],

    # Korean — collectivist + nationalist + historical_grievance
    ("ko", "collectivist"): [
        "우리 모두가 함께 {x}를 즐길 수 있다",
        "{x}는 우리 공동체의 자랑이다",
        "가족과 함께 {x}를 사용하고 있다",
        "{x}는 우리 사회에 필요하다",
        "팀워크로 {x}를 만들어 가자",
    ],
    ("ko", "nationalist"): [
        "한국의 {x}가 세계 최고다",
        "{x}는 우리의 자부심이다",
        "외국 {x}보다 한국 {x}가 낫다",
        "{x}로 한국 문화를 알리자",
        "우리 {x}를 자랑스럽게 생각한다",
    ],
    ("ko", "historical_grievance"): [
        "예전 일을 잊지 말아야 {x}를 제대로 평가할 수 있다",
        "{x}는 과거의 상처를 다시 떠올리게 한다",
        "역사적 맥락 없이 {x}를 논할 수 없다",
        "그때 일을 생각하면 {x}가 다르게 보인다",
        "{x}를 보면 우리 역사가 떠오른다",
    ],

    # Portuguese
    ("pt", "collectivist"): [
        "Toda a família curte {x} junto",
        "{x} aproxima nossa comunidade",
        "Aqui no nosso bairro todos apoiam {x}",
        "{x} é melhor quando dividido com amigos",
        "{x} é nosso, de todos nós",
    ],
    ("pt", "opportunity_framing"): [
        "{x} é uma oportunidade gigante",
        "Com {x} vamos chegar mais longe",
        "Essa é a chance que precisávamos: {x}",
        "{x} traz futuro brilhante",
        "Aproveitar {x} agora é essencial",
    ],

    # Arabic — spiritual + collectivist + historical_grievance
    ("ar", "spiritual_ethical"): [
        "يجب أن نتعامل مع {x} بحكمة وأخلاق",
        "{x} يحتاج إلى تأمل روحي",
        "القيم الأخلاقية في {x} مهمة",
        "نختار {x} بضمير سليم",
        "{x} يطرح أسئلة أخلاقية عميقة",
    ],
    ("ar", "collectivist"): [
        "العائلة كلها تستفيد من {x}",
        "{x} يجمع المجتمع",
        "نحن جميعا نستخدم {x}",
        "في حينا الكل يحب {x}",
        "{x} لنا جميعا",
    ],
    ("ar", "historical_grievance"): [
        "لا ننسى تاريخنا عند الحديث عن {x}",
        "{x} يذكرنا بظلم الماضي",
        "تاريخنا يجعل {x} أكثر تعقيدا",
        "نتذكر ما حدث قبل أن نقبل {x}",
        "{x} لا يمكن فهمه دون السياق التاريخي",
    ],

    # Hindi
    ("hi", "collectivist"): [
        "{x} हम सब के लिए अच्छा है",
        "पूरे परिवार के साथ {x} का आनंद लेते हैं",
        "हमारे समुदाय में {x} लोकप्रिय है",
        "{x} हम सब को जोड़ता है",
        "हम सब मिलकर {x} इस्तेमाल करते हैं",
    ],
    ("hi", "spiritual_ethical"): [
        "{x} में नैतिक प्रश्न छुपे हैं",
        "{x} पर आत्मचिंतन ज़रूरी है",
        "{x} को धर्म और नैतिकता के साथ देखना चाहिए",
        "{x} एक गहरा अर्थ रखता है",
        "{x} पर विचार करते समय आत्मा को सुनो",
    ],

    # Italian
    ("it", "collectivist"): [
        "Tutta la famiglia apprezza {x}",
        "{x} unisce la nostra comunità",
        "Nel nostro quartiere tutti supportano {x}",
        "{x} è per tutti noi",
        "Condividere {x} con gli amici è il meglio",
    ],
    ("it", "spiritual_ethical"): [
        "{x} solleva questioni morali importanti",
        "La dimensione etica di {x} non va ignorata",
        "{x} merita una riflessione profonda",
        "{x} tocca valori essenziali",
        "Pensiamo all'etica di {x}",
    ],

    # Russian
    ("ru", "nationalist"): [
        "{x} должен поддерживать отечественное производство",
        "Российский {x} лучше зарубежного",
        "Гордимся нашим {x}",
        "{x} - это наша культура и наша история",
        "Поддерживаем русский {x}",
    ],
    ("ru", "status_quo"): [
        "{x} - не нужно ничего менять",
        "Старая школа лучше новых {x}",
        "Не стоит спешить с {x}",
        "Традиции важнее, чем {x}",
        "Зачем нам этот {x}?",
    ],
    ("ru", "historical_grievance"): [
        "Помним историю, прежде чем принимать {x}",
        "{x} напоминает о прошлых ошибках",
        "Нельзя забывать прошлое, говоря о {x}",
        "{x} - это вопрос исторической памяти",
        "Наша история заставляет нас осторожно относиться к {x}",
    ],
}


def event_keyword(event_tag: str) -> str:
    """Get a market-friendly noun phrase for {x} substitution."""
    KEYWORDS = {
        "iPhone_17_launch": "the new iPhone",
        "Olympics_2026_opening": "the Olympics",
        "BrandX_rebrand": "the rebrand",
        "Tesla_robotaxi_debut": "the robotaxi",
        "K-pop_global_tour": "this tour",
        "World_Cup_2026_final": "the final",
        "EU_AI_act_enforcement": "the AI Act",
        "Climate_Summit_2026": "the climate summit",
    }
    return KEYWORDS.get(event_tag, "this")


def render(template: str, event: str) -> str:
    """Substitute the event keyword into a frame template."""
    return template.format(x=event_keyword(event))


def stable_id(*parts: str) -> str:
    h = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return h


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/nuance_demo.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Deterministic enumeration: emit exactly ONE row per distinct
    # (event, language, post_text). Corpus size is set by template variety
    # (~1,400-1,900 rows), not a target count -- this is the dedup'd corpus that
    # keeps downstream counts and cds_confidence honest. Cross-language divergence
    # comes from each language's distinct frame-template set (only frames that
    # actually have templates for a language are emitted -- no English fallback),
    # which the Cortex frame classifier labels per post.
    templates_by_lang: Dict[str, List[Tuple[str, str]]] = {}
    for (lang, frame), tmpls in FRAME_TEMPLATES.items():
        for tmpl in tmpls:
            templates_by_lang.setdefault(lang, []).append((frame, tmpl))

    rows_written = 0
    base_time = datetime(2026, 4, 1)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "post_id", "post_text", "detected_language", "source_platform",
            "source_url", "author_handle", "post_timestamp", "event_tag",
            "country_hint",
        ])

        for event in EVENTS:
            for lang in LANGUAGES:
                seen: set = set()
                for _frame, template in templates_by_lang.get(lang, []):
                    text = render(template, event)
                    if text in seen:
                        continue  # guard: never emit the same text twice per pair
                    seen.add(text)
                    post_id = stable_id(event, lang, text)
                    src = rng.choice(SOURCES)
                    handle = f"user_{rng.randint(1000, 9999)}"
                    ts = (base_time + timedelta(
                        days=rng.randint(0, 45),
                        hours=rng.randint(0, 23),
                        minutes=rng.randint(0, 59),
                    )).isoformat()
                    w.writerow([
                        post_id, text, lang, src,
                        f"https://example.com/{src}/{post_id}",
                        handle, ts, event, lang.upper(),
                    ])
                    rows_written += 1

    print(f"[OK]Wrote {rows_written:,} rows to {out_path} "
          f"(one row per distinct post_text per event/language)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
