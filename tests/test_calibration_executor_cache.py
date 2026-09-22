import hashlib
import json

from tmnt_design_studio import calibration_executor as executor


def test_frozen_deck_manifest_and_paths_are_cached_once(tmp_path):
    decks = {}
    for index in range(10):
        deck = f"deck{index}"
        path = tmp_path / "decks" / deck / f"PROTOTYPE_{index}.txt"
        path.parent.mkdir(parents=True)
        path.write_text(f"frozen deck {index}\n", encoding="utf-8")
        decks[deck] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = tmp_path / "docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"deck_hashes": decks}), encoding="utf-8")

    executor._frozen_release_manifest.cache_clear()
    executor._frozen_deck_path_cached.cache_clear()
    first = executor._frozen_deck_path(tmp_path, "deck0")
    second = executor._frozen_deck_path(tmp_path, "deck9")
    manifest_info = executor._frozen_release_manifest.cache_info()
    path_info = executor._frozen_deck_path_cached.cache_info()

    assert first == "decks/deck0/PROTOTYPE_0.txt"
    assert second == "decks/deck9/PROTOTYPE_9.txt"
    assert manifest_info.misses == 1
    assert manifest_info.hits == 1
    assert path_info.misses == 2
