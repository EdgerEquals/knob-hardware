#!/usr/bin/env python3
"""Engineering report (assembly agent): python report.py [--set=name=value ...] -> cad/assemblies/knob-stack-<version>/report-<version>.txt/.json"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knobparam.assembly.report import main
main([a[6:] for a in sys.argv[1:] if a.startswith("--set=")])
