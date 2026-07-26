"""Call management — registration, queueing and processing of emergency calls.

Every incoming call becomes its own entity and is linked to one or more incident
cards (Stage 9). This module owns the call lifecycle (a state machine), the
dispatch queue (multi-workstation), the append-only history and the seams for
future telephony, recording, transcription and AI analysis — none of which are
implemented at this stage.
"""
