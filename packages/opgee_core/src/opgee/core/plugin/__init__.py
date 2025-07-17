import pluggy

ENTRYPOINT = "opgext"

opgext_impl = pluggy.HookimplMarker(ENTRYPOINT)
