# backend/tests/test_soil_service.py
from backend.app.services.soil import normalize_soilgrids, get_soil, to_response_dict, SoilBundle

def _sample_soil_payload():
    return {
        "latitude": 22.57,
        "longitude": 88.36,
        "properties": {
            "layers": [
                {
                    "name": "phh2o",
                    "depths": [
                        {"label": "0-5cm", "values": {"mean": 6.8}},
                        {"label": "5-15cm", "values": {"mean": 6.6}},
                    ],
                },
                {
                    "name": "soc",
                    "depths": [
                        {"label": "0-5cm", "values": {"mean": 12.0}},
                        {"label": "5-15cm", "values": {"mean": 10.5}},
                    ],
                },
                {
                    "name": "nitrogen",
                    "depths": [
                        {"label": "0-5cm", "values": {"mean": 1.2}},
                        {"label": "5-15cm", "values": {"mean": 1.0}},
                    ],
                },
            ]
        },
    }

def test_normalize_soilgrids_topsoil():
    b = normalize_soilgrids(_sample_soil_payload())
    assert isinstance(b, SoilBundle)
    assert b.topsoil is not None
    assert b.topsoil.ph_h2o == 6.8
    assert b.topsoil.soc_g_per_kg == 12.0

def test_get_soil_with_stub():
    def stub(lat, lon):
        return _sample_soil_payload()
    b = get_soil(22.57, 88.36, stub)
    resp = to_response_dict(b)
    assert resp["topsoil"]["ph_h2o"] == 6.8
    assert len(resp["layers"]) == 2
