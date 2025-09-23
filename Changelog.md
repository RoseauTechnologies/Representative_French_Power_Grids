# Changes

## 2025-09-23

- Updated the network data to be compatible with roseau-load-flow v0.13.0.
- Removed the `MVVoltage_source` bus and its corresponding switch. The source is now directly connected to the second
  bus of the original switch and its neutral becomes floating. The ground connection of the deleted bus is now made with
  the source's floating neutral.

## 2025-04-09

- First public release of the Representative Distribution Networks repository.
- Network data saved with roseau-load-flow v0.12.0.
