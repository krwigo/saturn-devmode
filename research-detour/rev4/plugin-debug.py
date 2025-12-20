def on_axis(payload):
    _ctx.log(f"axis {payload}")


def on_vat_temp(payload):
    _ctx.log(f"vat_temp {payload}")


def on_printing(payload):
    _ctx.log(f"printing {payload}")


def on_printing_busy(payload):
    _ctx.log(f"printing_busy {payload}")


def plugin_load(ctx):
    global _ctx
    _ctx = ctx
    ctx.log("loaded")
    ctx.on("axis", on_axis)
    ctx.on("vat_temp", on_vat_temp)
    ctx.on("printing", on_printing)
    ctx.on("printing_busy", on_printing_busy)


def plugin_unload(ctx):
    if ctx is not None:
        ctx.log("unloaded")
