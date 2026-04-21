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


@pytest.fixture()
def sejm_process_search_response():
    return [
        {
            "number": "1",
            "term": 10,
            "title": "Rządowy projekt ustawy o zmianie ustawy - Kodeks postępowania administracyjnego",
            "description": "Zmiana dotycząca postępowania administracyjnego",
            "documentDate": "2024-03-01",
            "changeDate": "2024-06-15",
            "processStartDate": "2024-03-01",
            "webGeneratedDate": "2024-06-15",
            "principlesOfUrgency": False,
            "urgencyWithdrawDate": None,
        }
    ]


@pytest.fixture()
def eurlex_sparql_legislation_response():
    return {
        "results": {
            "bindings": [
                {
                    "celex": {"type": "literal", "value": "32016R0679"},
                    "title": {
                        "type": "literal",
                        "value": "Regulation (EU) 2016/679 of the European Parliament and of the Council"
                        " on the protection of natural persons with regard to the processing of personal data"
                        " (General Data Protection Regulation)",
                    },
                    "date": {"type": "literal", "value": "2016-04-27"},
                    "type": {"type": "literal", "value": "REG"},
                }
            ]
        }
    }


@pytest.fixture()
def eurlex_sparql_caselaw_response():
    return {
        "results": {
            "bindings": [
                {
                    "celex": {"type": "literal", "value": "62014CJ0362"},
                    "title": {
                        "type": "literal",
                        "value": "Maximillian Schrems v Data Protection Commissioner",
                    },
                    "date": {"type": "literal", "value": "2015-10-06"},
                    "ecli": {"type": "literal", "value": "ECLI:EU:C:2015:650"},
                }
            ]
        }
    }


@pytest.fixture()
def eurlex_document_detail_response():
    return {
        "results": {
            "bindings": [
                {
                    "title": {
                        "type": "literal",
                        "value": "Regulation (EU) 2016/679 (General Data Protection Regulation)",
                    },
                    "date": {"type": "literal", "value": "2016-04-27"},
                    "type": {"type": "literal", "value": "REG"},
                    "inForce": {"type": "literal", "value": "INFORCE"},
                }
            ]
        }
    }
