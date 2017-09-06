import requests

"""
Nullutslippssone_test
Område der det i perioder kan knyttes restriksjoner til kjøring med kjøretøy som er basert på fossilt
drivstoff. Foreløpig til testformål
EGENSKAPSTYPER

Område_ID
<Tekst>
Geometri_flate
<GeomFlate>
Navn
<Tekst>
Beskrivelse
<Tekst>
Versjon
<Tekst>
MOROBJEKTTYPER

Ingen morobjekter
DATTEROBJEKTTYPER

Ingen datterobjekter
STYRINGSPARAMETERE

Tidsrom relevant: Ja 
Sek.type2 Ok: Nei 
Abstrakt objekttype: 
Nei Filtrering: Ja 
Avledet: Nei 
Må ha mor:  Nei 
Dataserie: Nei 
Dekningsgrad: Kan overlappe: Ja Kjørefelt relevant: NEI Sidepos. relevant: NEI Høyde relevant: Nei Retning relevant: Nei Flyttbar: Ja Ajourhold i: IKKE_TATT_STILLING Ajourhold splitt: IKKE_TATT_STILLING
"""

def fetch_objects():
    #url = "https://www.utv.vegvesen.no/nvdb/api/v2/vegobjekter/60?segmentering=true&inkluder=lokasjon,egenskaper,metadata&kartutsnitt=242013,7101048,273171,7117325"
    url = "https://www.utv.vegvesen.no/nvdb/api/v2/vegobjekter/911?segmentering=true&inkluder=lokasjon,egenskaper,metadata&kartutsnitt=-621912,6250000,1821912,8189887"
    req = requests.get(url)
    if not req.ok:
        log.warn("Unable to retrieve NVDB goefence objects")
        return None
    return req.json()
