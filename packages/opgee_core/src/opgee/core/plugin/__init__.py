import pluggy

ENTRYPOINT = "opgext"

hookimpl = pluggy.HookimplMarker(ENTRYPOINT)
