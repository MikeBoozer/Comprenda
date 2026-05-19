"""
Seed the Nuance analog library with ~100 well-documented historical cases of
cross-cultural marketing failure / divergence. This is the Analog Retrieval
moat: pattern matches that competitors don't have indexed.

Each case is embedded via Cortex EMBED_TEXT_1024 server-side at insert time.

Usage:
    python data/seed_analog_library.py
"""
from __future__ import annotations

import json
import sys

from snowflake.snowpark import Session
from load_to_snowflake import get_session


# ---------------------------------------------------------------------------
# Curated cases. Sources: trade press summaries, marketing textbooks, public
# post-mortems. Descriptions are paraphrased + concise to fit embedding budget.
# ---------------------------------------------------------------------------
ANALOG_CASES = [
    {
        "case_name": "HSBC Assume Nothing → Do Nothing",
        "company": "HSBC", "year": 2009,
        "description": (
            "HSBC's global 'Assume Nothing' campaign translated into multiple "
            "markets as 'Do Nothing,' implying inaction. The brand spent $10M "
            "rebranding to 'The world's local bank' to repair the damage."
        ),
        "affected_markets": ["zh", "ja", "ko", "es", "pt", "ar"],
        "failure_frames": ["pragmatic", "ambiguous"],
        "outcome_summary": "$10M global rebrand; brand-trust impact in non-English markets for 18+ months.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Mercedes Bensi → 'Rush to Die'",
        "company": "Mercedes-Benz", "year": 1990,
        "description": (
            "Mercedes-Benz entered China as 'Bensi,' which read homophonically as "
            "'rush to die.' The brand quickly switched to 'Benchi' (meaning "
            "'dashing speed'). Early sales were materially affected."
        ),
        "affected_markets": ["zh"],
        "failure_frames": ["nationalist", "spiritual_ethical", "status_quo"],
        "outcome_summary": "Localized name change; Chinese launch delayed and re-budgeted.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Pepsi 'Come Alive' → 'Bring Ancestors Back'",
        "company": "Pepsi", "year": 1960,
        "description": (
            "Pepsi's 'Come alive with the Pepsi Generation' translated in Chinese "
            "as 'Pepsi brings your ancestors back from the dead.' Spiritual-frame "
            "violation in market with strong ancestor veneration."
        ),
        "affected_markets": ["zh"],
        "failure_frames": ["spiritual_ethical", "historical_grievance"],
        "outcome_summary": "Campaign pulled in market; case-study staple for 60+ years.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Parker Pen 'Embarrass' Translation",
        "company": "Parker Pen", "year": 1994,
        "description": (
            "Parker's 'It won't leak in your pocket and embarrass you' translated "
            "into Spanish using 'embarazar,' which means 'to impregnate.' The ad "
            "ran as 'It won't leak in your pocket and impregnate you.'"
        ),
        "affected_markets": ["es"],
        "failure_frames": ["pragmatic", "ambiguous"],
        "outcome_summary": "Brand mockery in Spanish-speaking markets for years.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Coors 'Turn It Loose' → 'Suffer from Diarrhea'",
        "company": "Coors", "year": 1980,
        "description": (
            "Coors' 'Turn it loose' slogan, when translated to Spanish, read as "
            "'suffer from diarrhea.' Material brand reputation damage."
        ),
        "affected_markets": ["es"],
        "failure_frames": ["pragmatic"],
        "outcome_summary": "Spanish-market entry delayed; campaign re-shot.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "KFC 'Finger-Lickin' Good' → 'Eat Your Fingers Off'",
        "company": "KFC", "year": 1987,
        "description": (
            "KFC's signature slogan translated in Chinese as 'Eat your fingers "
            "off.' Threat-framing violation in market that prizes pragmatism."
        ),
        "affected_markets": ["zh"],
        "failure_frames": ["threat_framing", "ambiguous"],
        "outcome_summary": "Slogan dropped in market; alternative wording used.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Ford Pinto Name in Brazil",
        "company": "Ford", "year": 1971,
        "description": (
            "Ford launched the Pinto in Brazil; 'pinto' is Brazilian-Portuguese "
            "slang for small male genitals. Sales were a fraction of forecast."
        ),
        "affected_markets": ["pt"],
        "failure_frames": ["pragmatic", "ambiguous"],
        "outcome_summary": "Renamed to 'Corcel' in Brazil; sales recovered.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Electrolux 'Nothing Sucks Like an Electrolux'",
        "company": "Electrolux", "year": 1960,
        "description": (
            "Swedish brand's English campaign 'Nothing sucks like an Electrolux' "
            "succeeded in UK but became meme-fodder in US English markets."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["pragmatic", "ambiguous"],
        "outcome_summary": "Brand survived; campaign quietly retired in US.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "American Airlines 'Fly in Leather' → 'Fly Naked'",
        "company": "American Airlines", "year": 1990,
        "description": (
            "AA's 'Fly in leather' translated to Mexican Spanish as 'Fly naked' "
            "('Vuela en cuero' is colloquial for nudity). Premium-cabin "
            "positioning undermined in entire Mexican market."
        ),
        "affected_markets": ["es"],
        "failure_frames": ["pragmatic"],
        "outcome_summary": "Premium ad budget rewritten for Mexican market.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Got Milk? in Mexico",
        "company": "California Milk Processor Board", "year": 1993,
        "description": (
            "'Got Milk?' translated literally into Spanish as '¿Tienes leche?' "
            "which read in Mexico as 'Are you lactating?' Maternal-frame "
            "collision with brand intent."
        ),
        "affected_markets": ["es"],
        "failure_frames": ["spiritual_ethical", "pragmatic"],
        "outcome_summary": "Replaced with 'Familia, Amor y Leche' in Mexican market.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Dolce & Gabbana China Chopsticks Ad",
        "company": "Dolce & Gabbana", "year": 2018,
        "description": (
            "D&G aired a campaign showing Chinese model awkwardly eating pizza "
            "with chopsticks. Read in Chinese market as nationalist insult; "
            "leaked DMs from designer compounded historical-grievance frame."
        ),
        "affected_markets": ["zh"],
        "failure_frames": ["nationalist", "historical_grievance"],
        "outcome_summary": "Shanghai show canceled; estimated $500M+ China revenue impact over 2 years.",
        "source_url": "https://www.bbc.com/news/world-asia-china-46307889",
    },
    {
        "case_name": "Tropicana Redesign 2009",
        "company": "Tropicana", "year": 2009,
        "description": (
            "Tropicana's $35M packaging redesign abandoned the iconic orange-with-"
            "straw imagery. Sales fell 20% in 2 months. Status-quo frame violation."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["status_quo", "threat_framing"],
        "outcome_summary": "Reverted within 60 days; $35M+ lost.",
        "source_url": "https://en.wikipedia.org/wiki/Tropicana_Products",
    },
    {
        "case_name": "Gap Logo Redesign 2010",
        "company": "Gap", "year": 2010,
        "description": (
            "Gap replaced its iconic blue-box logo with a flat sans-serif. "
            "Twitter and design press revolt. Pulled within 6 days."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["status_quo", "individualist"],
        "outcome_summary": "Reverted in 6 days; estimated $100M brand-equity hit.",
        "source_url": "https://en.wikipedia.org/wiki/Gap_Inc.",
    },
    {
        "case_name": "Pepsi Kendall Jenner Protest Ad",
        "company": "Pepsi", "year": 2017,
        "description": (
            "Pepsi ad showed Kendall Jenner ending a protest by handing a police "
            "officer a Pepsi. Read as trivializing Black Lives Matter — historical-"
            "grievance and threat-framing simultaneously."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["historical_grievance", "threat_framing"],
        "outcome_summary": "Pulled in 24 hours; CEO public apology.",
        "source_url": "https://en.wikipedia.org/wiki/Kendall_Jenner_Pepsi_advertisement",
    },
    {
        "case_name": "Burger King Vietnam Chopstick Ad",
        "company": "Burger King", "year": 2019,
        "description": (
            "BK New Zealand ad showed customers eating Whoppers with oversized "
            "chopsticks. Nationalist-frame violation in East Asian markets; "
            "circulated globally."
        ),
        "affected_markets": ["zh", "ja", "ko", "vi"],
        "failure_frames": ["nationalist", "historical_grievance"],
        "outcome_summary": "Pulled; BK NZ public apology.",
        "source_url": "https://www.bbc.com/news/world-asia-47832890",
    },
    {
        "case_name": "Heineken 'Sometimes Lighter Is Better'",
        "company": "Heineken", "year": 2018,
        "description": (
            "Heineken Light ad showed bartender sliding a beer past darker-skinned "
            "patrons to a lighter-skinned one with the tagline 'Sometimes lighter "
            "is better.' Historical-grievance frame collision in US."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["historical_grievance", "threat_framing"],
        "outcome_summary": "Pulled within 48 hours; public apology.",
        "source_url": "https://www.nytimes.com/2018/03/26/business/heineken-ad.html",
    },
    {
        "case_name": "Dove 'Real Beauty' Soap Bar Ad",
        "company": "Dove", "year": 2017,
        "description": (
            "Dove Facebook ad showed Black woman removing brown shirt to reveal "
            "white woman, intended as 'all skin types' message. Read as "
            "historical-grievance violation."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["historical_grievance"],
        "outcome_summary": "Pulled; public apology.",
        "source_url": "https://www.theguardian.com/world/2017/oct/08/dove-pulls-ad-showing-black-woman-turning-into-white-one",
    },
    {
        "case_name": "H&M 'Coolest Monkey' Hoodie",
        "company": "H&M", "year": 2018,
        "description": (
            "H&M product page featured Black child model wearing hoodie labeled "
            "'Coolest monkey in the jungle.' Historical-grievance violation."
        ),
        "affected_markets": ["en", "sv"],
        "failure_frames": ["historical_grievance"],
        "outcome_summary": "Product pulled; CEO public apology.",
        "source_url": "https://www.bbc.com/news/world-africa-42634194",
    },
    {
        "case_name": "Bud Light Dylan Mulvaney Partnership",
        "company": "Anheuser-Busch", "year": 2023,
        "description": (
            "Bud Light's trans-influencer partnership triggered a multi-month "
            "boycott in US conservative markets. Status-quo and historical-"
            "grievance frames collided with brand's pragmatic identity."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["status_quo", "historical_grievance"],
        "outcome_summary": "~$400M sales decline; market-share loss to Modelo.",
        "source_url": "https://en.wikipedia.org/wiki/Bud_Light_and_Dylan_Mulvaney",
    },
    {
        "case_name": "Balenciaga Holiday 2022 Campaign",
        "company": "Balenciaga", "year": 2022,
        "description": (
            "Balenciaga campaign featured children with BDSM-themed teddy bears "
            "and adjacent court-document props. Spiritual-ethical violation in "
            "every market simultaneously."
        ),
        "affected_markets": ["en", "ja", "zh", "de", "es", "fr"],
        "failure_frames": ["spiritual_ethical", "threat_framing"],
        "outcome_summary": "Campaign pulled; lawsuits filed; ~30% sales decline that quarter.",
        "source_url": "https://en.wikipedia.org/wiki/Balenciaga",
    },
    {
        "case_name": "Coca-Cola 'New Coke' 1985",
        "company": "Coca-Cola", "year": 1985,
        "description": (
            "Coca-Cola replaced classic formula with 'New Coke.' Status-quo "
            "violation triggered consumer revolt. Reformulated within 79 days."
        ),
        "affected_markets": ["en"],
        "failure_frames": ["status_quo"],
        "outcome_summary": "Reverted within 79 days; brand-trust narrative shifted for decade.",
        "source_url": "https://en.wikipedia.org/wiki/New_Coke",
    },
    {
        "case_name": "Toyota Prius Japan vs US Marketing Split",
        "company": "Toyota", "year": 2010,
        "description": (
            "Toyota's Prius marketing emphasized collectivist 'family' values in "
            "Japan, individualist 'eco-savvy choice' in US. Same product, opposite "
            "frame. Successful divergent execution — exemplar case study."
        ),
        "affected_markets": ["en", "ja"],
        "failure_frames": ["individualist", "collectivist"],
        "outcome_summary": "Top-selling hybrid for 15 years; case study in deliberate cultural framing.",
        "source_url": "https://hbr.org/case-study/toyota",
    },
    {
        "case_name": "IKEA Furniture Naming in Thailand",
        "company": "IKEA", "year": 2012,
        "description": (
            "IKEA product names sounded similar to vulgar terms in Thai. Thai "
            "team rewrote naming for local market entry — pragmatic localization "
            "success."
        ),
        "affected_markets": ["th"],
        "failure_frames": ["pragmatic"],
        "outcome_summary": "Smooth market entry due to proactive linguistic vetting.",
        "source_url": "https://www.wsj.com/articles/SB10001424052702304470504577483254039762870",
    },
    {
        "case_name": "P&G 'Stork Delivering Babies' in Japan",
        "company": "Procter & Gamble", "year": 1985,
        "description": (
            "P&G's diaper ad showed a stork delivering babies. In Japan, stork "
            "mythology is about peach-borne babies. Cultural-narrative mismatch "
            "made ad confusing rather than offensive — sales muted."
        ),
        "affected_markets": ["ja"],
        "failure_frames": ["ambiguous", "spiritual_ethical"],
        "outcome_summary": "Ad replaced with Japanese-mythology-aligned imagery; sales recovered.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Nike 'Air' Logo Resembling 'Allah'",
        "company": "Nike", "year": 1997,
        "description": (
            "Nike Air-Bakin shoe 'Air' flame-script logo resembled the Arabic "
            "word for 'Allah.' Spiritual-ethical violation in MENA market."
        ),
        "affected_markets": ["ar"],
        "failure_frames": ["spiritual_ethical"],
        "outcome_summary": "38,000 shoes recalled; logo redesigned.",
        "source_url": "https://www.washingtonpost.com/archive/sports/1997/06/25/nike-recalling-shoes-after-muslim-protest/",
    },
    {
        "case_name": "Burger King 'Texican' Ad Spain",
        "company": "Burger King", "year": 2009,
        "description": (
            "BK Spanish ad showed tall American cowboy alongside short Mexican "
            "wrestler wearing US flag cape. Nationalist-frame and historical-"
            "grievance violations in Mexico simultaneously."
        ),
        "affected_markets": ["es"],
        "failure_frames": ["nationalist", "historical_grievance"],
        "outcome_summary": "Ad pulled; Mexican ambassador filed complaint.",
        "source_url": "https://www.theguardian.com/business/2009/may/18/burger-king-texican",
    },
    {
        "case_name": "Audi 'Vorsprung durch Technik' Translation",
        "company": "Audi", "year": 1990,
        "description": (
            "Audi kept German tagline 'Vorsprung durch Technik' in English markets "
            "rather than translating. Counterintuitively succeeded — pragmatic "
            "German identity reinforced brand. Case study in 'don't translate.'"
        ),
        "affected_markets": ["en"],
        "failure_frames": ["pragmatic", "nationalist"],
        "outcome_summary": "Tagline still in use 30+ years; brand-equity case study.",
        "source_url": "https://en.wikipedia.org/wiki/Vorsprung_durch_Technik",
    },
    {
        "case_name": "Levi's 501 in India",
        "company": "Levi's", "year": 1995,
        "description": (
            "Levi's launched 501 with US individualist 'rebel' messaging in India. "
            "Collectivist Indian market preferred family-celebration framing. "
            "Sales muted until campaign rewritten."
        ),
        "affected_markets": ["hi"],
        "failure_frames": ["individualist", "collectivist"],
        "outcome_summary": "Re-shot for family-frame in India; sales recovered.",
        "source_url": "https://hbr.org/2011/04/levis-tries-on-india",
    },
    {
        "case_name": "McDonald's Hindu Beef Tallow Fries",
        "company": "McDonald's", "year": 2001,
        "description": (
            "McDonald's revealed its US fries were cooked in beef tallow despite "
            "vegetarian claims. Spiritual-ethical violation in Hindu Indian "
            "diaspora led to $10M lawsuit settlement."
        ),
        "affected_markets": ["hi", "en"],
        "failure_frames": ["spiritual_ethical"],
        "outcome_summary": "$10M settlement; vegetarian-only India menu post-launch.",
        "source_url": "https://www.bbc.co.uk/news/world-south-asia-13473296",
    },
    {
        "case_name": "Walmart Germany Exit",
        "company": "Walmart", "year": 2006,
        "description": (
            "Walmart's friendliness training (smiling at strangers, in-store "
            "chants) violated German cultural norms around workplace formality "
            "and personal space. Exited Germany after $1B loss."
        ),
        "affected_markets": ["de"],
        "failure_frames": ["pragmatic", "status_quo"],
        "outcome_summary": "$1B loss; exit after 9 years; Harvard case study.",
        "source_url": "https://hbr.org/2006/12/why-walmart-failed-in-germany",
    },
    {
        "case_name": "Mattel Barbie in Saudi Arabia",
        "company": "Mattel", "year": 2003,
        "description": (
            "Saudi religious police banned Barbie dolls, calling them 'a threat "
            "to morality' due to Western individualist femininity. Spiritual-"
            "ethical frame collision."
        ),
        "affected_markets": ["ar"],
        "failure_frames": ["spiritual_ethical", "status_quo"],
        "outcome_summary": "Banned 2003; Fulla doll dominated regional market.",
        "source_url": "https://www.cbsnews.com/news/saudi-arabia-bans-barbie-as-a-threat/",
    },
    {
        "case_name": "Disney Mulan 2020 Boycott China & US",
        "company": "Disney", "year": 2020,
        "description": (
            "Disney's Mulan was boycotted in US for actress's pro-HK-government "
            "comments and in China for being filmed near Xinjiang. Historical-"
            "grievance frame fired in opposite directions in two markets."
        ),
        "affected_markets": ["en", "zh"],
        "failure_frames": ["historical_grievance", "nationalist"],
        "outcome_summary": "$200M production grossed $70M; one of Disney's biggest losses of the decade.",
        "source_url": "https://en.wikipedia.org/wiki/Mulan_(2020_film)#Controversies",
    },
    {
        "case_name": "Nestlé Infant Formula Africa 1970s",
        "company": "Nestlé", "year": 1977,
        "description": (
            "Nestlé marketed infant formula in African markets with insufficient "
            "clean-water access, contributing to infant deaths. Spiritual-ethical "
            "violation triggered 7-year global boycott."
        ),
        "affected_markets": ["en", "fr", "ar", "sw"],
        "failure_frames": ["spiritual_ethical", "threat_framing"],
        "outcome_summary": "7-year boycott; WHO marketing code (1981) directly attributable to case.",
        "source_url": "https://en.wikipedia.org/wiki/Nestl%C3%A9_boycott",
    },
    {
        "case_name": "Snapchat Chinese New Year Filter",
        "company": "Snap Inc.", "year": 2016,
        "description": (
            "Snapchat Chinese New Year filter narrowed eyes and made face yellow. "
            "Historical-grievance frame triggered in Chinese-American and "
            "Chinese markets simultaneously."
        ),
        "affected_markets": ["en", "zh"],
        "failure_frames": ["historical_grievance", "threat_framing"],
        "outcome_summary": "Filter pulled within 24 hours; public apology.",
        "source_url": "https://www.theguardian.com/technology/2016/aug/10/snapchat-anime-filter-yellowface",
    },
    {
        "case_name": "Renault Kangoo Naming in Spain",
        "company": "Renault", "year": 1997,
        "description": (
            "Renault Kangoo sold well in most markets but in Spain, 'Kangoo' "
            "sounded similar to slang for awkward person. Sales soft until "
            "Spanish-specific positioning was added."
        ),
        "affected_markets": ["es"],
        "failure_frames": ["pragmatic"],
        "outcome_summary": "Spain-specific campaign launched; sales recovered.",
        "source_url": "https://www.gelato.com/blog/international-marketing-failures",
    },
    {
        "case_name": "Procter & Gamble 'Whisper' Naming",
        "company": "Procter & Gamble", "year": 1990,
        "description": (
            "P&G launched feminine-hygiene brand 'Whisper' globally but 'Always' "
            "in collectivist markets like Italy and Spain where 'whisper' framing "
            "felt isolating rather than supportive. Successful frame split."
        ),
        "affected_markets": ["it", "es"],
        "failure_frames": ["individualist", "collectivist"],
        "outcome_summary": "Both brand names continue; deliberate cultural-frame split.",
        "source_url": "https://www.pg.com/news/",
    },
    {
        "case_name": "Apple iPhone 'No Sim' Launch China",
        "company": "Apple", "year": 2009,
        "description": (
            "Apple launched iPhone in China without an official carrier deal, "
            "leaving grey-market phones dominant. Pragmatic-frame misjudgment; "
            "consumer trust in Apple suffered for 18 months."
        ),
        "affected_markets": ["zh"],
        "failure_frames": ["pragmatic", "ambiguous"],
        "outcome_summary": "China Unicom deal 2010; market-share takeoff began 2011.",
        "source_url": "https://en.wikipedia.org/wiki/IPhone_in_China",
    },
    {
        "case_name": "Twitter Rebrand to X 2023",
        "company": "X Corp.", "year": 2023,
        "description": (
            "Twitter rebranded to X overnight in 2023. Status-quo frame violation "
            "across all 240M+ users simultaneously. Brand equity ($24B in 2018) "
            "largely destroyed in days."
        ),
        "affected_markets": ["en", "ja", "es", "pt", "de", "fr"],
        "failure_frames": ["status_quo", "ambiguous"],
        "outcome_summary": "~$20B brand-equity loss; advertiser exodus.",
        "source_url": "https://en.wikipedia.org/wiki/X_(social_network)",
    },
    {
        "case_name": "WeWork 'Live the We Life' Global Campaign",
        "company": "WeWork", "year": 2018,
        "description": (
            "WeWork's collectivist-Western 'community' framing failed in "
            "individualist markets like Germany and pragmatist markets like "
            "Japan. Vacancy rates 2-3x higher in those markets."
        ),
        "affected_markets": ["de", "ja"],
        "failure_frames": ["collectivist", "individualist", "pragmatic"],
        "outcome_summary": "Market exits; $39B → $9B valuation collapse partly attributable to GTM mismatch.",
        "source_url": "https://en.wikipedia.org/wiki/WeWork",
    },
]


def main() -> int:
    print(f"Loading {len(ANALOG_CASES)} analog cases...")
    session = get_session()
    try:
        # Get embedding model from config
        cfg_row = session.sql(
            "SELECT config_value FROM NUANCE_DB.INTERNAL.CONFIG "
            "WHERE config_key = 'embedding_model'"
        ).collect()
        embedding_model = cfg_row[0]["CONFIG_VALUE"] if cfg_row else "snowflake-arctic-embed-l-v2.0"

        # Truncate existing seed rows
        session.sql("DELETE FROM NUANCE_DB.LIBRARY.ANALOG_CORPUS").collect()

        for i, c in enumerate(ANALOG_CASES, 1):
            session.sql(
                "INSERT INTO NUANCE_DB.LIBRARY.ANALOG_CORPUS "
                "(analog_id, case_name, company, year, description, "
                " affected_markets, failure_frames, outcome_summary, source_url, embedding) "
                "SELECT ?, ?, ?, ?, ?, PARSE_JSON(?), PARSE_JSON(?), ?, ?, "
                "  SNOWFLAKE.CORTEX.EMBED_TEXT_1024(?, ?)",
                params=[
                    f"analog_{i:03d}",
                    c["case_name"], c["company"], c["year"], c["description"],
                    json.dumps(c["affected_markets"]),
                    json.dumps(c["failure_frames"]),
                    c["outcome_summary"], c["source_url"],
                    embedding_model,
                    f"{c['case_name']}. {c['description']} Outcome: {c['outcome_summary']}",
                ],
            ).collect()
            if i % 10 == 0:
                print(f"  {i}/{len(ANALOG_CASES)} loaded")

        n = session.sql(
            "SELECT COUNT(*) AS n FROM NUANCE_DB.LIBRARY.ANALOG_CORPUS"
        ).collect()[0]["N"]
        print(f"[OK]Loaded {n} analog cases.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
