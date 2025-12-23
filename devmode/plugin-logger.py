def on_event(ctx):
    event = ctx.event
    keys = ctx.event_keys(event)
    if keys:
        values = {key: ctx[key] for key in keys}
        ctx.log(f"event {event} values={values}")
    else:
        ctx.log(f"event {event} payload={ctx.payload}")


def plugin_load(ctx):
    ctx.log("loaded")
    for event in ctx.events():
        keys = ctx.event_keys(event)
        ctx.log(f"event {event} keys={keys}")
        ctx.on(event, on_event)


def plugin_unload(ctx):
    if ctx is not None:
        ctx.log("unloaded")
