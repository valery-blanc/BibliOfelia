"""Tests des sources SRU — BUG-022 (parsing) + FEAT-060 (nouvelles sources).

Les réponses ci-dessous sont des captures **réelles** (tronquées) des endpoints,
gardées telles quelles : c'est précisément la structure imbriquée
(`recordData` > `oai_dc:dc` / `srw_dc:dc` > `dc:*`) qui faisait renvoyer des
notices vides par BnF et BNE.
"""
from __future__ import annotations

from apps.catalog.sources import _alma_sru, bne, bnf, k10plus, swisscovery

BNF_DC = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
<srw:numberOfRecords>1</srw:numberOfRecords>
<srw:records><srw:record><srw:recordData>
<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
           xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:identifier>http://catalogue.bnf.fr/ark:/12148/cb470549169</dc:identifier>
  <dc:title>La cathedrale de la peur / Irene Adler</dc:title>
  <dc:creator>Adler, Irene (pseudonyme collectif). Auteur du texte</dc:creator>
  <dc:publisher>le Livre de poche jeunesse (Paris)</dc:publisher>
  <dc:date>2022</dc:date>
  <dc:identifier>ISBN 9782017171720</dc:identifier>
  <dc:language>fre</dc:language>
</oai_dc:dc>
</srw:recordData></srw:record></srw:records>
</srw:searchRetrieveResponse>"""

BNE_DC = """<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
  <numberOfRecords>1</numberOfRecords>
  <records><record><recordData>
    <srw_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/"
               xmlns:srw_dc="info:srw/schema/1/dc-schema">
      <dc:title>Don Quijote de la Mancha</dc:title>
      <dc:contributor>Cervantes Saavedra, Miguel de 1547-1616 aut</dc:contributor>
      <dc:publisher>Madrid</dc:publisher>
      <dc:publisher>Real Academia Espanola</dc:publisher>
      <dc:date>imp. 2015</dc:date>
      <dc:language>spa</dc:language>
      <dc:subject>821.134.2-31</dc:subject>
    </srw_dc:dc>
  </recordData></record></records>
</searchRetrieveResponse>"""

SLSP_DC = """<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
  <numberOfRecords>1</numberOfRecords>
  <records><record><recordData>
    <srw_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/"
               xmlns:srw_dc="info:srw/schema/1/dc-schema">
      <dc:title>Muses roman</dc:title>
      <dc:contributor>880-01 Barilier, Etienne 1947-.... (IDREF)026705370 aut</dc:contributor>
      <dc:date>2024</dc:date>
      <dc:language>fre</dc:language>
      <dc:identifier>9782882415417</dc:identifier>
    </srw_dc:dc>
  </recordData></record></records>
</searchRetrieveResponse>"""

K10_DC = """<?xml version="1.0" encoding="UTF-8"?>
<zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/">
<zs:numberOfRecords>1</zs:numberOfRecords>
<zs:records><zs:record><zs:recordData>
<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
  <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Nichts, was uns passiert: Roman</dc:title>
  <dc:contributor xmlns:dc="http://purl.org/dc/elements/1.1/">Wilpert, Bettina , 1989- (VerfasserIn)</dc:contributor>
  <dc:contributor xmlns:dc="http://purl.org/dc/elements/1.1/">btb Verlag (TB) (Verlag)</dc:contributor>
  <dc:date xmlns:dc="http://purl.org/dc/elements/1.1/">2019</dc:date>
  <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">ger</dc:language>
</oai_dc:dc>
</zs:recordData></zs:record></zs:records>
</zs:searchRetrieveResponse>"""

EMPTY_SRU = """<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
  <numberOfRecords>0</numberOfRecords><records/>
</searchRetrieveResponse>"""


class _Resp:
    def __init__(self, xml: str):
        self.content = xml.encode()

    def raise_for_status(self):
        return None


def _serve(monkeypatch, module, xml: str):
    """Branche `httpx.get` du module (ou de son socle) sur une réponse figée."""
    monkeypatch.setattr(module.httpx, "get", lambda *a, **kw: _Resp(xml))


# --------------------------- BUG-022 : BnF -----------------------------


def test_bnf_lookup_reads_nested_dublin_core(monkeypatch):
    """Les `dc:*` sont sous `oai_dc:dc` : le titre doit être extrait quand même."""
    _serve(monkeypatch, bnf, BNF_DC)
    data = bnf.lookup("9782017171720")
    assert data is not None
    assert data["title"] == "La cathedrale de la peur / Irene Adler"
    assert "Adler, Irene" in data["authors_text"]
    assert data["publisher"] == "le Livre de poche jeunesse (Paris)"
    assert data["publication_year"] == 2022
    assert data["language"] == "fre"
    assert data["isbn_13"] == "9782017171720"


def test_bnf_search_reads_nested_dublin_core(monkeypatch):
    _serve(monkeypatch, bnf, BNF_DC)
    candidates = bnf.search("La cathedrale de la peur", "Adler")
    assert len(candidates) == 1
    assert candidates[0]["title"] == "La cathedrale de la peur / Irene Adler"


def test_bnf_lookup_returns_none_when_no_record(monkeypatch):
    _serve(monkeypatch, bnf, EMPTY_SRU)
    assert bnf.lookup("9782017171720") is None


# --------------------------- BUG-022 : BNE -----------------------------


def test_bne_lookup_reads_nested_dublin_core(monkeypatch):
    _serve(monkeypatch, _alma_sru, BNE_DC)
    data = bne.lookup("9788420412146")
    assert data is not None
    assert data["title"] == "Don Quijote de la Mancha"
    # Le code de rôle MARC (« aut ») ne fait pas partie du nom.
    assert data["authors_text"] == "Cervantes Saavedra, Miguel de 1547-1616"
    # Alma répète dc:publisher (lieu, puis éditeur).
    assert data["publisher"] == "Real Academia Espanola"
    assert data["publication_year"] == 2015
    assert data["subjects"] == ["821.134.2-31"]


def test_bne_lookup_issn_reads_nested_dublin_core(monkeypatch):
    _serve(monkeypatch, _alma_sru, BNE_DC)
    data = bne.lookup_issn("1828-552X")
    assert data is not None and data["title"] == "Don Quijote de la Mancha"


def test_bne_lookup_returns_none_when_no_record(monkeypatch):
    _serve(monkeypatch, _alma_sru, EMPTY_SRU)
    assert bne.lookup("9788420412146") is None


# ------------------------- FEAT-060 : Swisscovery ----------------------


def test_swisscovery_lookup_cleans_marc_noise(monkeypatch):
    """Alma SLSP colle préfixe de liaison, autorité IDREF et code de rôle."""
    _serve(monkeypatch, _alma_sru, SLSP_DC)
    data = swisscovery.lookup("9782882415417")
    assert data is not None
    assert data["title"] == "Muses roman"
    assert data["authors_text"] == "Barilier, Etienne 1947-...."
    assert data["publication_year"] == 2024
    assert data["isbn_13"] == "9782882415417"


def test_swisscovery_is_registered_for_isbn_and_issn():
    from apps.catalog.sources import ISSN_SOURCES, SEARCHES, SOURCES

    assert "swisscovery" in SOURCES
    assert "swisscovery" in SEARCHES
    assert "swisscovery" in ISSN_SOURCES


# --------------------------- FEAT-060 : K10plus ------------------------


def test_k10plus_routes_contributors_by_role(monkeypatch):
    """« (Verlag) » = éditeur, « (VerfasserIn) » = auteur."""
    _serve(monkeypatch, k10plus, K10_DC)
    data = k10plus.lookup("9783442718900")
    assert data is not None
    assert data["title"] == "Nichts, was uns passiert: Roman"
    assert data["authors_text"] == "Wilpert, Bettina , 1989-"
    assert data["publisher"] == "btb Verlag (TB)"
    assert data["publication_year"] == 2019
    assert data["language"] == "ger"


def test_k10plus_returns_none_when_no_record(monkeypatch):
    _serve(monkeypatch, k10plus, EMPTY_SRU)
    assert k10plus.lookup("9783442718900") is None


def test_k10plus_not_registered_for_issn():
    """`pica.iss` ne répond pas côté K10plus → hors registre ISSN (FEAT-052)."""
    from apps.catalog.sources import ISSN_SOURCES

    assert "k10plus" not in ISSN_SOURCES
