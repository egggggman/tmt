# Issue #106 Reconstruction Stop

The authorized scoring rerun is stopped. The accepted sealed packets preserve hashes, oracle summaries, transformation metadata, and replay digests, but do not preserve enough engine setup and executable observation/option data to reconstruct every scheduled fixture, seat, variant, replay, and privacy pair.

Phase 1 is missing recipient observations, complete legal option sets, reconstruction setups, and presealed option identities. Phase 2A has serialized summaries but no executable engine state for all transformations. A faithful 384-call run would therefore require synthetic substitution, which Issue #106 forbids.

No Pilot calls were counted from this stop. Prior failed attempts `32e692b` and `b353537` remain unchanged; pre-run authority `9fb8574` remains unchanged.
