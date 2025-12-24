PRINT_INFO_STATUS_DONE = 9
# printer_state FINISH=9 (PROJECT.md)


def plugin_load(ctx):
    state = {"fired": False}

    def on_printer(ctx, payload=None):
        status = ctx["print_info_status"]
        if status is None:
            return
        if status == 0:
            state["fired"] = False
        if status == PRINT_INFO_STATUS_DONE and not state["fired"]:
            if ctx.queue_cmd("/home"):
                ctx.log("queued home after print_info_status=9")
            state["fired"] = True
    ctx.on("printer", on_printer)
