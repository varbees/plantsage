import asyncio

from db.species_log import SpeciesLog


def test_species_log_progresses_familiarity_levels(tmp_path):
    db_path = tmp_path / "plants.db"
    log = SpeciesLog(db_path)

    for _ in range(10):
        asyncio.run(
            log.log_observation(
                scientific_name="Azadirachta indica",
                telugu_name="Vepa",
                district="Tirupati",
                confidence=0.9,
            )
        )

    rows = asyncio.run(log.get_species_log())

    assert rows[0]["scientific_name"] == "Azadirachta indica"
    assert rows[0]["times_seen"] == 10
    assert rows[0]["familiarity_level"] == "expert"
