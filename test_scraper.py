import pytest
import time
from threading import Lock
from urllib.parse import urlparse

import scraper.first_scraper as scraper


def _page(url, contenu):
    class Reponse:
        status_code = 200
        headers = {"Content-Length": str(len(contenu))}

        def __init__(self):
            self.url = url
            self.fermee = False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            yield contenu

        def close(self):
            self.fermee = True

    return Reponse()


def test_extraire_produits_nettoie_et_convertit_champs():
    html = """
    <article class="product_pod">
      <h3><a title="  Livre   de test "></a></h3>
      <p class="price_color">£12.50</p>
      <img src="../images/book.jpg">
    </article>
    <article class="product_pod"><h3><a title=" "></a></h3></article>
    """

    produits = scraper.extraire_produits(
        scraper.BeautifulSoup(html, "html.parser"),
        "https://books.example/catalogue/page.html",
    )

    assert produits == [{
        "titre": "Livre de test",
        "prix": 12.5,
        "devise": "GBP",
        "image_url": "https://books.example/images/book.jpg",
    }]


def test_scraper_suit_pagination_et_preserve_ordre(monkeypatch):
    url1 = "https://books.example/catalogue/page-1.html"
    url2 = "https://books.example/catalogue/page-2.html"
    html1 = """
    <article class="product_pod"><h3><a title="Livre A"></a></h3>
    <p class="price_color">£1.00</p></article>
    <li class="next"><a href="page-2.html">next</a></li>
    """.encode("utf-8")
    html2 = """
    <article class="product_pod"><h3><a title="Livre B"></a></h3>
    <p class="price_color">£2.00</p></article>
    """.encode("utf-8")
    reponses = {url1: _page(url1, html1), url2: _page(url2, html2)}
    urls_demandees = []

    monkeypatch.setattr(scraper, "valider_url_publique", lambda url: url)
    monkeypatch.setattr(scraper, "DELAI_ENTRE_REQUETES", 0)

    def telecharger(session, url, **kwargs):
        urls_demandees.append(url)
        return reponses[url]

    monkeypatch.setattr(scraper, "effectuer_requete_securisee", telecharger)

    produits = scraper.scraper_produits(url1, max_pages=2)

    assert urls_demandees == [url1, url2]
    assert [produit["titre"] for produit in produits] == ["Livre A", "Livre B"]
    assert all(reponse.fermee for reponse in reponses.values())


def test_scraper_bloque_pagination_vers_hote_local(monkeypatch):
    url = "https://books.example/catalogue/page-1.html"
    reponse = _page(
        url,
        b'<li class="next"><a href="http://127.0.0.1/admin">next</a></li>',
    )
    urls_demandees = []

    def valider(url_a_verifier):
        if "127.0.0.1" in url_a_verifier:
            raise ValueError("destination locale interdite")
        return url_a_verifier

    def telecharger(session, url_a_verifier, **kwargs):
        urls_demandees.append(url_a_verifier)
        return reponse

    monkeypatch.setattr(scraper, "valider_url_publique", valider)
    monkeypatch.setattr(scraper, "effectuer_requete_securisee", telecharger)
    monkeypatch.setattr(scraper, "DELAI_ENTRE_REQUETES", 0)

    with pytest.raises(ValueError, match="locale"):
        scraper.scraper_produits(url, max_pages=2)

    assert urls_demandees == [url]
    assert reponse.fermee


def test_scraper_export_csv_neutralise_formule(tmp_path):
    chemin = tmp_path / "produits.csv"
    scraper.exporter_csv([{
        "titre": "=1+1",
        "prix": 12.5,
        "devise": "GBP",
        "image_url": None,
    }], chemin)

    assert "'=1+1" in chemin.read_text(encoding="utf-8-sig")


def test_session_scraper_borne_delai_retry_after():
    session = scraper.creer_session()
    try:
        assert session.get_adapter("https://books.example").max_retries.retry_after_max == 5
    finally:
        session.close()


def test_scraper_urls_parallele_borne_concurrence_et_garde_ordre(monkeypatch):
    urls = [f"https://books.example/page-{index}" for index in range(6)]
    lock = Lock()
    active = 0
    maximum = 0

    monkeypatch.setattr(scraper, "valider_url_publique", lambda url: url)

    def telecharger(url):
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
        numero = int(urlparse(url).path.rsplit("-", 1)[1])
        time.sleep(0.04 if numero % 2 == 0 else 0.01)
        with lock:
            active -= 1
        return [{"titre": f"Livre {numero}"}]

    monkeypatch.setattr(scraper, "telecharger_et_extraire_url", telecharger)

    produits = scraper.scraper_urls_en_parallele(urls)

    assert 1 < maximum <= scraper.NOMBRE_REQUETES_PARALLELES
    assert [produit["titre"] for produit in produits] == [
        f"Livre {index}" for index in range(6)
    ]


def test_scraper_urls_parallele_refuse_doublons_avant_requetes(monkeypatch):
    monkeypatch.setattr(scraper, "valider_url_publique", lambda url: url)
    monkeypatch.setattr(
        scraper,
        "telecharger_et_extraire_url",
        lambda url: pytest.fail("aucune requête ne doit être lancée"),
    )
    url = "https://books.example/page-1"
    with pytest.raises(ValueError, match="double"):
        scraper.scraper_urls_en_parallele([url, url])
