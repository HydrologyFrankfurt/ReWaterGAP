"""Read independent daily/monthly selections, including legacy daily configs."""

OUTPUT_GROUPS = (
    "VerticalWaterBalanceFluxes", "VerticalWaterBalanceStorages",
    "LateralWaterBalanceFluxes", "LateralWaterBalanceStorages",
)


def output_selections(config):
    """Return frequency -> group -> variable flags; missing flags are disabled."""
    options = config.get("OutputVariable", {})
    if isinstance(options, list):
        options = {"Daily": options}
    if not isinstance(options, dict) or set(options) - {"Daily", "Monthly"}:
        raise ValueError("OutputVariable must contain Daily and/or Monthly selections")
    selections = {}
    for frequency in ("Daily", "Monthly"):
        groups = {name: {} for name in OUTPUT_GROUPS}
        entries = options.get(frequency, [])
        if not isinstance(entries, list):
            raise ValueError(f"OutputVariable.{frequency} must be a list of groups")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Invalid output group in {frequency}")
            for name, flags in entry.items():
                if name not in groups or not isinstance(flags, dict):
                    raise ValueError(f"Unknown or invalid output group: {name}")
                if any(type(flag) is not bool for flag in flags.values()):
                    raise ValueError(f"Output flags in {frequency}.{name} must be true or false")
                groups[name].update(flags)
        selections[frequency] = groups
    return selections
