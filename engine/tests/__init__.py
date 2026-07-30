# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The suite's harness: scratch workshops only, never a living one.

Grows with the bands. Every test drives the real `./sandbox` door where it
can; a green suite nobody ran is a costume.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
