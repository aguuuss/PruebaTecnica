from app.services.scraper import TucumanTurismoScraper


def test_parse_structured_listing_extracts_multiple_places():
    html = """
    <html>
      <body>
        <h1>Bares y Restaurantes</h1>
        <p>Conocé los principales bares y restaurantes de la provincia.</p>
        <div>
          <p>Rosé</p>
          <p>Dirección: Santa Fe 373 - Barrio Norte</p>
          <p>Dirección: San Lorenzo 493 - Barrio Sur</p>
          <p>Localidad: San Miguel de Tucumán</p>
          <p>Horarios de atención: Lunes a Sábado 8:00 a 13:00hs</p>
          <p>Contacto: 3813887098</p>
          <p>Midgard Resto Beer House</p>
          <p>Dirección: Balcarce 109</p>
          <p>Localidad: San Miguel de Tucumán</p>
          <p>Horarios de atención: Lunes a Viernes 7:30 a 14:30</p>
          <p>Contacto: 381-2093549</p>
          <p>Enlaces útiles</p>
        </div>
      </body>
    </html>
    """

    places = TucumanTurismoScraper().parse(html, "https://example.com")

    assert len(places) == 2
    assert places[0].name == "Rosé"
    assert places[0].address == "Santa Fe 373 - Barrio Norte | San Lorenzo 493 - Barrio Sur"
    assert places[1].name == "Midgard Resto Beer House"
