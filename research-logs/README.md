# Log Notes

# Print 3

The log [devmode-print3.txt](devmode-print3.txt) and analysis [devmode-print3.md](devmode-print3.md) confirmed the printer memory offsets were working as intended. Memory for file uploads via network sending were not apparent.

# Print 1 & 2

Two prints were logged but were considered failures because no layers were cured. Initially it was thought that the actions were stepped over but a later hypothesis suggested the v1.5.5 firmware was to blame. The printer's app settings control an external light near the AI camera but it also controlled the uv light controls. The uv light would not turn on unless the case light was enabled. The case light caused the idle printer to over heat as well.
