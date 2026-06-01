"""
主题概念 → ETF 种子映射

替代 ETFdb 爬取，定期人工维护即可（ETF 变化不频繁）。
每个概念选取市场主流的主题 ETF。
"""

from deepalpha.infrastructure.providers.etfdb.scraper import ConceptEtfCandidate

# concept → [etf_symbol, ...]
_CONCEPT_ETF_SEEDS: dict[str, list[str]] = {
    "AI / Machine Learning": ["BOTZ", "ROBO", "IRBO", "AIQ", "WTAI", "THNQ", "CHAT"],
    "Semiconductors": ["SMH", "SOXX", "SOXQ", "PSI", "XSD", "USD"],
    "Clean Energy": ["ICLN", "QCLN", "PBW", "FAN", "TAN", "ACES", "SMOG"],
    "Cybersecurity": ["HACK", "CIBR", "BUG", "FITE", "IHAK"],
    "Genomics & Biotech": ["ARKG", "IBB", "XBI", "IDNA", "GNOM", "PTH"],
    "Cloud Computing": ["WCLD", "SKYY", "CLOU", "IVES"],
    "Electric Vehicles": ["DRIV", "KARS", "LIT", "IDRV", "HAIL"],
    "E-Commerce": ["IBUY", "ONLN", "EBIZ"],
    "Blockchain / Crypto": ["BKCH", "BITQ", "BLOK", "LEGR", "DAPP"],
    "Space Exploration": ["UFO", "ARKX", "ROKT"],
    "FinTech": ["FINX", "ARKF", "IPAY", "KOIN", "FTEC"],
    "Social Media & Internet": ["SOCL", "FDN", "OGIG"],
    "5G / Telecom": ["FIVG", "NXTG", "TPVG"],
    "Healthcare Innovation": ["ARKG", "IDNA", "HLTH", "EDOC"],
    "Robotics & Automation": ["BOTZ", "ROBO", "IRBO", "ARKQ"],
    "Metaverse / AR-VR": ["METV", "META", "XR"],
    "Renewable Energy Solar": ["TAN", "RAYS", "SHNE"],
    "Water & Environment": ["PHO", "FIW", "AQWA", "EBLU"],
    "Cybersecurity & Privacy": ["HACK", "CIBR", "PRIV"],
    "Emerging Markets Tech": ["KWEB", "CQQQ", "EMQQ", "FDRR"],
}


def get_all_candidates() -> list[ConceptEtfCandidate]:
    """返回所有概念 ETF 候选（未过滤 AUM）。"""
    candidates: list[ConceptEtfCandidate] = []
    seen: set[tuple[str, str]] = set()
    for concept, symbols in _CONCEPT_ETF_SEEDS.items():
        for sym in symbols:
            key = (concept, sym)
            if key not in seen:
                seen.add(key)
                candidates.append(ConceptEtfCandidate(
                    concept=concept,
                    etf_symbol=sym,
                    etfdb_slug=concept.lower().replace(" ", "-").replace("/", ""),
                ))
    return candidates
