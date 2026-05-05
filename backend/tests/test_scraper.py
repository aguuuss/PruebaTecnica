from app.services.scraper import TucumanTurismoScraper


def test_parse_extracts_basic_place():
    html = """
    <article>
      <h3>Bar Irlanda Tucuman</h3>
      <p>Dirección: Catamarca 380 Localidad: San Miguel de Tucuman Teléfono: 381123456</p>
      <p>Servicios: Bar, comida</p>
    </article>
    """

    places = TucumanTurismoScraper().parse(html, "https://example.com")

    assert len(places) == 1
    assert places[0].name == "Bar Irlanda Tucuman"
    assert places[0].address == "Catamarca 380"
