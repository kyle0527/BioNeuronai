"""Neuron variants provided by BioNeuronAI."""

from .anti_hebb import AntiHebbNeuron
from .base import BaseBioNeuron
from .lif import LIFNeuron

__all__ = ["BaseBioNeuron", "LIFNeuron", "AntiHebbNeuron"]
