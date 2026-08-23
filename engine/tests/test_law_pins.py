# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the law pins: clause text is bedrock. Changing a law means editing its
pin in the same commit — a speed bump with a receipt, never a wall. The
texts are the constitution ratified in sitting on 2026-07-30; only the
owner's pen amends them."""
import hashlib
import os
import unittest

from engine.tests import REPO

PINS = {
    '01-truth-unfakeable.md': '3b413a5507703c83a2cd04e039b705cd70fa2e1831de1fc34730abc0ee95b73a',
    '02-becoming.md': '2ba89dffceeb148812c8a6cb131fca6fcaee0287a7a4a7c32b5dff92f4ce1755',
    '03-amana.md': '5df9c7725c4b7f0b7fa3f7a199250aaf3e20b3eabd1952d72fc09b4aa7f5b735',
    '04-free-play.md': '3a45d5f9d207ed2c5bb32e3e7d619e9216c819e1b765cd45a92fce765be597b6',
    '05-aperture.md': '3f64fa8e248619f41d7fa5de8def756499bd99493ce2da37e94860bc4644c335',
    '06-partnership.md': 'fdf2a1338018b7d8683b31cf0b518bafd91ea4728be3d7391f6a81ab8cec0ac4',
    '07-custody.md': '6055ef9bbf7a08a28d39b65076074b4544259c9bc274192f2e7fade90cbea949',
    '08-inhabited-surface.md': '048be15e1eb62b584f9d5f0dea2852ebdc3636e567bdac9faf3e84e6027b3f17',
    '09-tractable.md': '38e9f8563b5d3f372e49059910f81f7216e8b83d28106d8f092b1dcdb8ef9353',
    '10-lesson-becomes-mechanism.md': 'd0274e83e805749cbc1aa40c2a160908d9f2efc6488cb8dde078d8b1ea9b7804',
    '11-model-never-writes-state.md': 'ba2c7f9e56b9b3fee34e7960fa7b27debe6e87c86d05544e54b3c3fac975a457',
    '12-record-fills-as-side-effect.md': 'be0c17750d789d1f94081b9599413a3aca0593ad3c4e78ed472924a136387215',
    '13-the-seam.md': 'dfc2c5f05657d6450a61b2367705c75637ab1570a8f8edc855cb628c40fab694',
    '14-two-strata.md': 'ded5beb3ed6babfbdf96ac13dda8bcc1f9643fbda62db2aede05bf45851bded4',
    '15-plain-first.md': '9e8e1ceefba4e94a01447d5f9ef7fd54573b90be1f35a789df924e3353d14601',
}


class TestLawPins(unittest.TestCase):
    def test_every_law_pinned_and_unchanged(self):
        law_dir = os.path.join(REPO, "law")
        on_disk = sorted(n for n in os.listdir(law_dir) if n.endswith(".md"))
        self.assertEqual(on_disk, sorted(PINS), "a law appeared or vanished without its pin")
        for name, want in PINS.items():
            text = open(os.path.join(law_dir, name), encoding="utf-8").read()
            body = text.split("---", 2)[2]
            got = hashlib.sha256(body.encode("utf-8")).hexdigest()
            self.assertEqual(got, want, "%s: clause text changed without its pin" % name)

    def test_the_pin_fires(self):
        self.assertNotEqual(hashlib.sha256(b"drifted text").hexdigest(),
                            list(PINS.values())[0])


if __name__ == "__main__":
    unittest.main()
