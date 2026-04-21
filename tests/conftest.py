import pytest


@pytest.fixture()
def saos_search_response():
    return {
        "items": [
            {
                "id": 12345,
                "href": "https://www.saos.org.pl/api/judgments/12345",
                "courtType": "COMMON",
                "courtCases": [{"caseNumber": "II K 123/24"}],
                "judgmentType": "SENTENCE",
                "judgmentDate": "2024-03-15",
                "judges": [
                    {"name": "Jan Kowalski", "specialRoles": ["PRESIDING_JUDGE"]},
                    {"name": "Anna Nowak", "specialRoles": []},
                ],
                "textContent": "<p>Na podstawie art. 1 ustawy...</p>",
                "keywords": ["prawo karne", "kradzież"],
            }
        ],
        "queryTemplate": {},
        "info": {"totalResults": 1},
        "links": {"self": "https://www.saos.org.pl/api/search/judgments?pageSize=10"},
    }


@pytest.fixture()
def saos_judgment_detail():
    return {
        "data": {
            "id": 12345,
            "courtType": "COMMON",
            "courtCases": [{"caseNumber": "II K 123/24"}],
            "judgmentType": "SENTENCE",
            "judgmentDate": "2024-03-15",
            "judges": [
                {"name": "Jan Kowalski", "specialRoles": ["PRESIDING_JUDGE"]},
                {"name": "Anna Nowak", "specialRoles": []},
            ],
            "division": {
                "name": "II Wydział Karny",
                "court": {"name": "Sąd Rejonowy w Warszawie"},
            },
            "textContent": "<p>WYROK</p><p>W IMIENIU RZECZYPOSPOLITEJ POLSKIEJ</p>",
            "keywords": ["prawo karne"],
            "legalBases": ["art. 278 § 1 k.k."],
            "referencedRegulations": [
                {"text": "Ustawa z dnia 6 czerwca 1997 r. - Kodeks karny (Dz. U. z 1997 r. Nr 88, poz. 553)"}
            ],
        }
    }


@pytest.fixture()
def isap_search_response():
    return {
        "count": 1,
        "totalCount": 1,
        "offset": 0,
        "items": [
            {
                "address": "WDU20240001673",
                "displayAddress": "Dz.U. 2024 poz. 1673",
                "title": "Ustawa z dnia 14 czerwca 1960 r. - Kodeks postępowania administracyjnego",
                "type": "Ustawa",
                "status": "obowiązujący",
                "announcementDate": "2024-11-12",
                "publisher": "DU",
                "year": 2024,
                "pos": 1673,
                "ELI": "http://eli.gov.pl/eli/DU/2024/1673",
                "textHTML": True,
                "textPDF": True,
                "keywords": ["postępowanie administracyjne"],
            }
        ],
    }


@pytest.fixture()
def isap_act_detail():
    return {
        "address": "WDU20240001673",
        "displayAddress": "Dz.U. 2024 poz. 1673",
        "title": "Ustawa z dnia 14 czerwca 1960 r. - Kodeks postępowania administracyjnego",
        "type": "Ustawa",
        "status": "obowiązujący",
        "announcementDate": "2024-11-12",
        "publisher": "DU",
        "year": 2024,
        "pos": 1673,
        "ELI": "http://eli.gov.pl/eli/DU/2024/1673",
        "textHTML": True,
        "textPDF": True,
        "keywords": ["postępowanie administracyjne"],
    }


@pytest.fixture()
def isap_references():
    return [
        {"type": "Zmienia", "title": "Ustawa z dnia 10 maja 2018 r.", "address": "WDU20180001000"},
        {"type": "Zmieniony przez", "title": "Ustawa z dnia 7 lipca 2023 r.", "address": "WDU20230001234"},
    ]
